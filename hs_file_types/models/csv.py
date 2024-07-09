import csv
import logging
import os
from typing import Optional, List

import pandas as pd
from django.core.exceptions import ValidationError
from django.db import models
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from hs_core.signals import post_add_csv_aggregation
from .base import AbstractFileMetaData, AbstractLogicalFile, FileTypeContext


class _CSVColumnSchema(BaseModel):
    titles: Optional[str] = None
    description: Optional[str] = None
    datatype: str
    unitCode: Optional[str] = None


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
    def _extract_metadata(cls, csv_file_path):
        """
        Extracts metadata from the CSV file
        :param csv_file_path: a temporary file path of the CSV file after the file is copied from iRODS
        :return: a dictionary of extracted metadata
        """

        # number of rows to read at one time
        # _CHUNK_SIZE = 1000

        def get_rows_count():
            # we have to read the whole file chunk by chunk to get the total number of rows
            # reading the whole file at once may cause memory issues if the file is large
            # for finding the number of rows, we could have just loaded the first column for the chunk instead of all
            # the columns. However, to detect parsing errors (to detect invalid csv file), we have to load data
            # for all columns.

            # number of rows to read at one time
            _CHUNK_SIZE = 1000

            data_rows_count = 0
            _err_msg = ""
            try:
                for _df in pd.read_csv(csv_file_path, comment='#', chunksize=_CHUNK_SIZE, sep=None, engine='python'):
                    # skip any rows with all null values
                    if _df.dropna(how='all').empty:
                        continue
                    data_rows_count += len(_df.index)
                return data_rows_count, _err_msg
            except pd.errors.EmptyDataError:
                _err_msg = "Invalid CSV file. No data rows found"
                return 0, _err_msg
            except pd.errors.ParserError as err:
                _err_msg = f"Invalid CSV file. Error: {str(err)}"
                return 0, _err_msg

        def get_pd_data_types():
            """Load the first chunk of the file to pandas dataframe and get the initial data type of each column in
            the data frame based on this limited number of data rows.
            """

            # number of rows to read
            _CHUNK_SIZE = 100

            pd_data_types = {}
            df = next(pd.read_csv(
                csv_file_path,
                comment='#',
                chunksize=_CHUNK_SIZE,
                sep=None,
                engine='python')
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

        def is_header_row(df_):
            """
            Check if the row is a header row - if there are no nulls in the row and the data types of the columns
            are of the same type, then we assume it is a header row
            """
            data_types = []
            for item in df_.columns:
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

        def has_header_row(df):
            """
            Check if the csv file has a header row. First using the csv module Sniffer to detect the header row. If
            Sniffer does not detect the header row, then we use our custom logic to check for header row. This allows
            us to guess the header row in most cases.
            """
            with open(csv_file_path, 'r') as csvfile:
                _MAX_LINES_TO_READ = 100
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
                    csvfile.seek(position)
                    csv_data = line
                    for _ in range(5):
                        while line:
                            line = csvfile.readline()
                            csv_data += line

                    print(f"First 5 data rows of the file: {csv_data}", flush=True)

                    sniffer = csv.Sniffer()
                    _has_header = sniffer.has_header(csv_data)
                    if not _has_header:
                        print(">> csv module Sniffer did not detect header row", flush=True)
                        _has_header = is_header_row(df)
                    return _has_header
                return False

        def apply_column_data_type(col_index, data_type):
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

            df = pd.read_csv(csv_file_path, comment='#', usecols=[col_index], engine='python')

            # drop any rows with all null values
            df = df.dropna(how='all')

            if data_type == bool:
                # convert the column to string type
                df.iloc[:, 0] = df.iloc[:, 0].astype('object')
                df.iloc[:, 0] = df.iloc[:, 0].apply(str)
                options_true_false = ['true', 'false', 'True', 'False', 'TRUE', 'FALSE']
                options_yes_no = ['yes', 'no', 'Yes', 'No', 'YES', 'NO']

                # filter out(note the ~ for exclude operation) based on the above options
                df_tf = df[~df.iloc[:, 0].isin(options_true_false)]
                if not df_tf.empty:
                    # it seems there are values other than the boolean values as in options_true_false above
                    # check for yes/no values
                    df_yn = df[~df.iloc[:, 0].isin(options_yes_no)]
                    if not df_yn.empty:
                        # there are values other than the boolean values
                        raise ValueError("Invalid boolean values found")
            else:
                # apply the data type to the column - excluding the null values
                # this can raise ValueError if the data type is not valid for all data in the column
                print(f">> Applying data type: {passed_data_type} to column: {col_index}", flush=True)
                df.iloc[:, 0] = df.iloc[:, 0].apply(data_type)

        def get_column_data_types():
            """
            Compute the data type of each column in the csv file
            """

            # read the first few rows of data of the file to estimate column data type based on the data
            _CHUNK_SIZE = 100
            df = next(pd.read_csv(
                csv_file_path,
                comment='#',
                chunksize=_CHUNK_SIZE,
                sep=None,
                dtype='string',
                engine='python')
            )

            _has_header = has_header_row(df)
            if _has_header:
                print(">> Header row is present", flush=True)
            else:
                print(">> Header row is missing", flush=True)

            # collect the column names
            headers = []
            if _has_header:
                for index, column_name in enumerate(df.columns, start=1):
                    print(f"Column # {index}: {column_name}")
                    headers.append(column_name)
            else:
                for col in range(len(df.columns)):
                    # col_name = f"Column_{col + 1}_Missing"
                    col_name = None
                    headers.append(col_name)

            # skip any data rows with null values in any of the columns so that we can possibly can get the first row
            # with data in all columns - we need data in all columns to determine the data type of the column
            data_row_index = 0

            # NOTE: df.dropna() returns a new data frame with the rows with null values in all columns removed
            df = df.dropna(how='all')

            # NOTE: df.dropna() returns a new data frame with the rows with null values in any column removed
            df_with_no_null = df.dropna(how='any')

            if df_with_no_null.empty:
                print("No data rows found with no null values")

                # using these two fill methods to get a row with data in all columns

                # fill the df empty cell with previous cell data
                df = df.ffill()

                # file the df empty cell with next cell data
                df = df.bfill()

                # get the first row with data in all columns
                while df.iloc[data_row_index].isnull().any():
                    data_row_index += 1

                    if data_row_index > df.shape[0]:
                        # no data row found with data in all columns - will just use the first row data
                        data_row_index = 0
                        break
                first_row = df.iloc[data_row_index, :]
            else:
                first_row = df_with_no_null.iloc[data_row_index, :]

            pd_data_types = get_pd_data_types()

            # iterate over the data value of the first row and print the data type of each value
            if _has_header:
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
                    if value.lower() in ('true', 'false', 'yes', 'no'):
                        value_type = "boolean"
                    else:
                        try:
                            pd.to_datetime(value)
                            value_type = "datetime"
                        except ValueError:
                            pass
                col_name = headers[index]
                try:
                    apply_column_data_type(index, value_type)
                except ValueError as e:
                    # assume that the column has mixed data types so make it string
                    value_type = "string"
                    print(f"Error applying data type:{value_type} for column:{index + 1}, error: {str(e)}")

                csv_column_model = _CSVColumnSchema(titles=col_name, datatype=value_type)
                csv_column_models.append(csv_column_model)
                print(f"Data type for column:{index + 1} of value: {value}, is of type: {value_type}")

            return csv_column_models, _has_header

        rows_count, err_msg = get_rows_count()
        if rows_count == 0:
            if not err_msg:
                err_msg = "No data rows found in the CSV file"
            raise ValidationError(err_msg)

        columns, has_header = get_column_data_types()
        if not has_header:
            rows_count += 1
        csv_meta_schema = CSVMetaSchemaModel(rows=rows_count, columns=columns)
        return csv_meta_schema.model_dump()

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
