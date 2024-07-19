import csv
import logging
import os
import time
from typing import Optional, List

import pandas as pd
from django.core.exceptions import ValidationError
from django.db import models
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from hs_core.signals import post_add_csv_aggregation
from .base import AbstractFileMetaData, AbstractLogicalFile, FileTypeContext


class _CSVColumnSchema(BaseModel):
    titles: Optional[str] = ""
    description: Optional[str] = ""
    datatype: str
    unitCode: Optional[str] = ""


class CSVMetaSchemaModel(BaseModel):
    rows: int = 0
    columns: List[_CSVColumnSchema]


class CSVFileMetaData(AbstractFileMetaData):
    model_app_label = 'hs_file_types'

    # this field is used for storing the extracted CSV metadata
    tableSchema = models.JSONField(default=dict)

    @staticmethod
    def validate_table_schema(table_schema: dict):
        err = None
        try:
            schem_model = CSVMetaSchemaModel(**table_schema)
            return schem_model.model_dump(), err
        except PydanticValidationError as e:
            err = str(e)
            return None, err

    def get_table_schema_model(self):
        return CSVMetaSchemaModel(**self.tableSchema)

    def get_html(self, include_extra_metadata=True, **kwargs):
        raise NotImplementedError("Method get_html must be implemented in a subclass")

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        raise NotImplementedError("Method get_html_forms must be implemented in a subclass")


class CSVLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(CSVFileMetaData, on_delete=models.CASCADE, related_name="logical_file")
    data_type = "CSV"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        csv_metadata = CSVFileMetaData.objects.create(keywords=[], extra_metadata={})
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=csv_metadata, resource=resource)

    @classmethod
    def get_metadata_model(cls):
        return CSVFileMetaData

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        return [".csv"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        return [".csv"]

    @staticmethod
    def get_aggregation_display_name():
        return 'CSV Content: One CSV file with specific metadata'

    @staticmethod
    def get_aggregation_term_label():
        return "CSV Aggregation"

    @staticmethod
    def get_aggregation_type_name():
        return "CSVFileAggregation"

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types.
        """
        return "CSV Data"

    @property
    def is_single_file_aggregation(self):
        """This aggregation supports only one file"""
        return True

    @staticmethod
    def get_csv_allowed_delimiters():
        # only comma or semi-colon as delimiter is considered a valid csv file
        return [',', ';']

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=''):
        """
        Makes any physical file part of a generic aggregation type. The physical file must
        not already be a part of any aggregation.
        :param resource:
        :param user:
        :param file_id: id of the resource file to set logical file type
        :param folder_path: ignored here and a value for file_id is required
        corresponding logical file of the resource file
        :return: an instance of CSVLogicalFile
        """

        log = logging.getLogger()
        with FileTypeContext(aggr_cls=cls, user=user, resource=resource, file_id=file_id,
                             folder_path=folder_path,
                             post_aggr_signal=post_add_csv_aggregation,
                             is_temp_file=True) as ft_ctx:
            res_file = ft_ctx.res_file
            # check file extension is .csv
            if res_file.extension.lower() != '.csv':
                raise ValidationError("File extension should be .csv")
            csv_temp_file = ft_ctx.temp_file
            try:
                metadata = cls._extract_metadata(csv_temp_file)
                print(">> Extracted Metadata", flush=True)
                print(metadata, flush=True)
            except Exception as ex:
                log.exception(f"Error extracting metadata from CSV file: {str(ex)}")
                raise ValidationError(f"Error extracting metadata from CSV file: {str(ex)}")

            upload_folder = res_file.file_folder
            dataset_name, _ = os.path.splitext(res_file.file_name)
            # create a csv logical file object
            logical_file = cls.create_aggregation(dataset_name=dataset_name,
                                                  resource=resource,
                                                  res_files=[res_file],
                                                  new_files_to_upload=[],
                                                  folder_path=upload_folder)

            logical_file.metadata.tableSchema = metadata
            logical_file.metadata.save()
            ft_ctx.logical_file = logical_file
            log.info(f"CSV aggregation was created for file:{res_file.storage_path}.")
            return logical_file

    @classmethod
    def _extract_metadata(cls, csv_file_path: str) -> dict:
        """
        Extracts metadata from the CSV file
        :param csv_file_path: a temporary file path of the CSV file after the file is copied from iRODS
        :return: a dictionary of extracted metadata
        """

        rows_count, err_msg = cls._get_rows_count(csv_file_path)
        if rows_count == 0:
            if not err_msg:
                err_msg = "No data rows found in the CSV file"
            raise ValidationError(err_msg)

        columns, has_header = cls._get_column_data_types(csv_file_path)
        if not has_header:
            rows_count += 1
        csv_meta_schema = CSVMetaSchemaModel(rows=rows_count, columns=columns)
        return csv_meta_schema.model_dump()

    @classmethod
    def _get_rows_count(cls, csv_file_path: str) -> tuple[int, str]:
        # we have to read the whole file chunk by chunk to get the total number of rows
        # reading the whole file at once may cause memory issues if the file is large
        # for finding the number of rows, we could have just loaded the first column for the chunk instead of all
        # the columns. However, to detect parsing errors (to detect invalid csv file), we have to load data
        # for all columns.

        def check_for_non_comment_text(delimiter=','):
            # check if there is non-comment text line (line that doesn't start with #) in the file
            assert delimiter in cls.get_csv_allowed_delimiters()

            with open(csv_file_path, 'r') as csv_file:
                reader = csv.reader(csv_file, delimiter=delimiter)
                # to handle the edge case when there is only one column in the csv file
                one_column_data = False

                line_count = 0
                _MAX_LINES_TO_READ = 5
                has_matching_delimiter = False
                for row in reader:
                    # skip line starting with # or empty line
                    if (len(row) == 1 and row[0].startswith("#")) or len(row) == 0:
                        continue
                    line_count += 1

                    # check if there is comment character '#' in the row
                    # since we are using pandas to load the csv file passing the parameter comment set to #,
                    # if there is a comment character in the row, pandas will drop anything after the
                    # comment character for that row - this will mess up the whole dataframe structure
                    # resulting very bad metadata as part of the metadata extraction
                    for col in row:
                        if "#" in col:
                            raise pd.errors.ParserError(
                                "Invalid CSV file. Found comment character '#' in a non-comment row"
                            )

                    if len(row) > 1 and one_column_data:
                        raise pd.errors.ParserError("Invalid CSV file. Contains non-comment text")
                    elif len(row) == 1:
                        has_matching_delimiter = False
                        if len(row[0].split()) > 1:
                            _error_msg = ("Invalid CSV file. Contains non-comment text - possibly space delimiter"
                                          " used instead of comma or semicolon")
                            raise pd.errors.ParserError(_error_msg)
                        one_column_data = True
                    elif len(row) > 1:
                        has_matching_delimiter = True

                    if line_count > _MAX_LINES_TO_READ:
                        break
            return has_matching_delimiter

        has_comma_delimiter = check_for_non_comment_text()
        if not has_comma_delimiter:
            # try using semicolon
            check_for_non_comment_text(delimiter=';')

        # number of rows to read at one time
        _CHUNK_SIZE = 1000

        _DELIMITER = '|'.join(cls.get_csv_allowed_delimiters())
        data_rows_count = 0
        err_msg = ""
        try:
            for df in pd.read_csv(csv_file_path, comment='#', chunksize=_CHUNK_SIZE, sep=_DELIMITER,
                                  engine='python', iterator=True, skip_blank_lines=True):

                data_rows_count += len(df.index)
            return data_rows_count, err_msg
        except pd.errors.EmptyDataError:
            err_msg = "Invalid CSV file. No data rows found"
            return 0, err_msg
        except pd.errors.ParserError as err:
            err_msg = f"Invalid CSV file. Error: {str(err)}"
            return 0, err_msg

    @classmethod
    def _get_pd_data_types(cls, csv_file_path: str) -> dict:
        """Load the first chunk of the file to pandas dataframe and get the initial data type of each column in
        the data frame based on this limited number of data rows.
        """

        # number of rows to read
        _CHUNK_SIZE = 100
        _DELIMITER = '|'.join(cls.get_csv_allowed_delimiters())
        pd_data_types = {}

        df = pd.read_csv(
            csv_file_path,
            comment='#',
            nrows=_CHUNK_SIZE,
            sep=_DELIMITER,
            engine='python'
        )

        col_counter = 0
        for _, dtype in df.dtypes.items():
            if pd.api.types.is_bool_dtype(dtype):
                pd_data_types[col_counter] = "boolean"
            elif pd.api.types.is_numeric_dtype(dtype):
                pd_data_types[col_counter] = "number"
            else:
                pd_data_types[col_counter] = "string"
            col_counter += 1

        return pd_data_types

    @classmethod
    def _has_header_row(cls, csv_file_path: str, df: pd.DataFrame) -> bool:
        """
        Check if the csv file has a header row. First using the csv module Sniffer to detect the header row. If
        Sniffer does not detect the header row, then we use our custom logic to check for header row. This allows
        us to guess the header row in most cases.
        """

        def is_header_row():
            """
            Check if the row is a header row - if there are no nulls in the row and the data types of the columns
            are of the same type, then we assume it is a header row
            """
            data_types = []
            for item in df.columns:
                if pd.isnull(item):
                    return False
                if item.startswith("Unnamed:"):
                    # empty cell is loaded as 'Unnamed:' by pandas
                    return False

                try:
                    float(item)
                    data_types.append("number")
                except ValueError:
                    data_types.append("string")

                if len(set(data_types)) > 1:
                    return False
            return True

        with open(csv_file_path, 'r') as csvfile:
            _MAX_LINES_TO_READ = 10
            line = csvfile.readline()
            line_count = 1
            while line:
                if not line.startswith("#") and ''.join(line).strip():
                    position = csvfile.tell() - len(line) - 1  # Adjust for the newline character
                    break

                line = csvfile.readline()
                line_count += 1
                if line_count > _MAX_LINES_TO_READ:
                    break

            if line and line_count <= _MAX_LINES_TO_READ:
                if position < 0:
                    position = 0
                csvfile.seek(position)

                # feed the first 5 non-empty lines into the csv Sniffer
                csv_data = ""
                line_count = 0
                while line_count <= 5:
                    line = csvfile.readline()
                    if not line:
                        break
                    csv_data += line
                    line_count += 1

                print(f"First 5 data rows of the file: {csv_data}", flush=True)

                sniffer = csv.Sniffer()
                try:
                    has_header = sniffer.has_header(csv_data)
                except csv.Error:
                    has_header = False

                if not has_header:
                    print(">> csv module Sniffer did not detect header row", flush=True)
                    # try custom check for header row
                    has_header = is_header_row()
                return has_header
            return False

    @classmethod
    def _apply_column_data_type(cls, csv_file_path: str, column_index: int, data_type: str) -> None:
        """
        Apply data type to the column to verify that the column does not have mixed data types
        """
        assert data_type in ("unknown", "string", "number", "boolean", "datetime")

        passed_data_type = data_type
        if data_type in ("unknown", "string"):
            return
        if data_type == "number":
            data_type = pd.to_numeric
        elif data_type == "boolean":
            data_type = bool
        elif data_type == "datetime":
            data_type = pd.to_datetime

        df = pd.read_csv(csv_file_path, comment='#', usecols=[column_index], engine='python')

        # drop any rows with null values in the column
        df = df.dropna(how='all')
        if df.empty:
            # empty column - no need to apply data type
            return

        if data_type == bool:
            # convert the column to string type
            df.iloc[:, 0] = df.iloc[:, 0].astype('object')
            df.iloc[:, 0] = df.iloc[:, 0].apply(str)

            bool_tf_options = [['true', 'false'], ['True', 'False'], ['TRUE', 'FALSE'], ['T', 'F']]
            bool_yn_options = [['yes', 'no'], ['Yes', 'No'], ['YES', 'NO'], ['Y', 'N']]

            # filter out(note the ~ for exclude operation) based on the above options
            for tf_options in bool_tf_options:
                df_tf = df[~df.iloc[:, 0].isin(tf_options)]
                if df_tf.empty:
                    break
            else:
                for yn_options in bool_yn_options:
                    df_yn = df[~df.iloc[:, 0].isin(yn_options)]
                    if df_yn.empty:
                        break
                else:
                    raise ValueError("Invalid boolean values found")

        else:
            # apply the data type to the column - excluding the null values
            # this can raise ValueError if the data type is not valid for all data in the column
            print(f">> Applying data type: {passed_data_type} to column: {column_index}", flush=True)
            if passed_data_type == "datetime":
                df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='raise', infer_datetime_format=True)
            else:
                df.iloc[:, 0] = df.iloc[:, 0].apply(data_type)

    @classmethod
    def _get_column_data_types(cls, csv_file_path: str) -> tuple[List[_CSVColumnSchema], bool]:
        """
        Compute the data type of each column in the csv file
        """

        # read the first 100 rows of data of the file to estimate column data type based on the data
        _CHUNK_SIZE = 100
        _DELIMITER = "|".join(cls.get_csv_allowed_delimiters())
        df = pd.read_csv(
            csv_file_path,
            comment='#',
            nrows=_CHUNK_SIZE,
            sep=_DELIMITER,
            dtype='string',
            engine='python',
            on_bad_lines='skip'
        )
        print(">> Reading first few rows of data", flush=True)
        print(df)

        has_header = cls._has_header_row(csv_file_path, df)
        if has_header:
            print(">> Header row is present", flush=True)
        else:
            print(">> Header row is missing", flush=True)

        # collect the column names
        headers = []
        if has_header:
            for index, column_name in enumerate(df.columns, start=1):
                print(f"Column # {index}: {column_name}")
                # remove any leading and trailing quotes from the column name
                column_name = column_name.strip("\"")
                headers.append(column_name)
        else:
            for col in range(len(df.columns)):
                col_name = ""
                headers.append(col_name)

        # skip any data rows with null values in any of the columns so that we can possibly can get the first row
        # with data in all columns - we need data in all columns to determine the data type of the column
        data_row_index = 0

        # NOTE: df.dropna() returns a new data frame with the rows with null values in all columns removed
        df = df.dropna(how='all')

        # NOTE: df.dropna() returns a new data frame with the rows with null values in any column removed
        df_with_no_null = df.dropna(how='any')

        if df_with_no_null.empty:
            print("No data rows found with not having no null values")

            # using these two fill methods to get a row with data in all columns

            # fill the df empty cell with previous cell data
            df = df.ffill()

            # file the df empty cell with next cell data
            df = df.bfill()

            # get the first row with data in all columns
            while df.iloc[data_row_index].isnull().any():
                data_row_index += 1

                if data_row_index >= df.shape[0]:
                    # no data row found with data in all columns - will just use the first row data
                    data_row_index = 0
                    break
            first_row = df.iloc[data_row_index, :]
        else:
            first_row = df_with_no_null.iloc[data_row_index, :]

        pd_data_types = cls._get_pd_data_types(csv_file_path)

        if has_header:
            enumerator = enumerate(first_row)
        else:
            enumerator = enumerate(first_row.index)

        csv_column_models = []

        for index, value in enumerator:
            value_type = "string"
            if pd_data_types[index] == "number":
                value_type = "number"
            elif pd.isnull(value) or value.startswith("Unnamed:") or value == "":
                if pd_data_types[index] == "number":
                    value_type = "number"
            else:
                if value.lower() in ('true', 'false', 'yes', 'no', 't', 'f', 'y', 'n'):
                    value_type = "boolean"
                else:
                    try:
                        pd.to_datetime(value)
                        value_type = "datetime"
                    except ValueError:
                        pass
            col_name = headers[index]
            print(f"Applying data type:{value_type} for column:{index + 1}", flush=True)
            # time the call to apply_column_data_type
            start_time = time.time()

            try:
                cls._apply_column_data_type(csv_file_path, index, value_type)
            except ValueError as e:
                # assume that the column has mixed data types so make it string
                value_type = "string"
                print(f"Error applying data type:{value_type} for column:{index + 1}, error: {str(e)}")

            end_time = time.time()
            print(f"Time taken to apply data type for column:{index + 1} is: {end_time - start_time} secs",
                  flush=True)
            csv_column_model = _CSVColumnSchema(titles=col_name, datatype=value_type)
            csv_column_models.append(csv_column_model)
            print(f"Data type for column:{index + 1} of value: {value}, is of type: {value_type}")

        return csv_column_models, has_header

    @classmethod
    def _get_preview_data(cls, csv_file_path: str) -> str:
        """Retrieves the first few rows of data from the CSV file to be used as a preview data
        Get maximum of a predetermined number of data rows for preview
        :param csv_file_path: path of the CSV file
        """

        with open(csv_file_path, 'r') as csvfile:
            _MAX_LINES_TO_READ = 100
            _MAX_DATA_ROWS_TO_READ = 10

            line_count = 1
            data_line_count = 0
            csv_preview_data = ""

            line = csvfile.readline()
            while line:
                csv_preview_data += line
                if not line.startswith("#") and ''.join(line).strip():
                    data_line_count += 1
                    if data_line_count > _MAX_DATA_ROWS_TO_READ:
                        break
                line = csvfile.readline()
                line_count += 1
                if line_count > _MAX_LINES_TO_READ:
                    break

            return csv_preview_data

    @classmethod
    def get_primary_resource_file(cls, resource_files):
        """Gets any resource file as the primary file  from the list of files *resource_files* """

        return resource_files[0] if resource_files else None

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(CSVLogicalFile, self).create_aggregation_xml_documents(create_map_xml)
        self.metadata.is_dirty = False
        self.metadata.save()

    @classmethod
    def get_main_file_type(cls):
        # a single file extension in the group which is considered the main file
        return ".csv"
