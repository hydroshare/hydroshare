import concurrent.futures
import csv
import logging
import os
from typing import Optional, List
from typing import Literal as TypeLiteral

import pandas as pd
from django.core.exceptions import ValidationError
from django.db import models
from django.template import Template, Context
from dominate import tags as html_tags
from pydantic import BaseModel, field_validator, PositiveInt
from rdflib import Literal, BNode, Graph

from hs_core.hs_rdf import HSTERMS, DC
from hs_core.signals import post_add_csv_aggregation
from .base import AbstractLogicalFile, FileTypeContext
from .generic import GenericFileMetaDataMixin
from ..enums import AggregationMetaFilePath


class _CSVColumnSchema(BaseModel):
    column_number: PositiveInt
    titles: Optional[str] = None
    description: Optional[str] = None
    datatype: TypeLiteral["string", "number", "datetime", "boolean"]    # noqa: F821


class _CSVColumnsSchema(BaseModel):
    columns: List[_CSVColumnSchema]

    @field_validator("columns")
    def columns_validator(cls, v: List[_CSVColumnSchema]) -> List[_CSVColumnSchema]:
        if not v:
            raise ValueError("list of columns must not be empty")

        # check either all titles are empty or no title is empty
        for col in v:
            if col.titles == "":
                col.titles = None
        titles = [col.titles for col in v]
        if not all(title is None for title in titles):
            if any(title is None for title in titles):
                raise ValueError("All column titles maybe empty/null or no column title must be empty/null")
            if len(titles) != len(set(titles)):
                raise ValueError("Column titles must be unique")
        column_numbers = [col.column_number for col in v]
        if any(cn < 1 or cn > len(v) for cn in column_numbers):
            raise ValueError("column_number value must be between 1 and number of columns")
        if len(column_numbers) != len(set(column_numbers)):
            raise ValueError("column_number values must be unique")
        # order columns by column_number
        v.sort(key=lambda _col: _col.column_number)
        return v


class CSVMetaSchemaModel(BaseModel):
    rows: PositiveInt = 1
    delimiter: TypeLiteral[",", ";", "\t"]  # noqa: F722
    table: _CSVColumnsSchema


class CSVFileMetaData(GenericFileMetaDataMixin):
    # this field is used for storing the extracted CSV metadata
    tableSchema = models.JSONField(default=dict)

    def get_table_schema_model(self):
        return CSVMetaSchemaModel(**self.tableSchema)

    def ingest_metadata(self, graph):
        # remove the tableSchema node and its children from the graph before passing to base ingest_metadata
        # needed to do this because of dc:title in tableSchema that would conflict with dc:title at the graph root level
        table_schema_node = None
        subject = None
        for s, p, o in graph.triples((None, HSTERMS.tableSchema, None)):
            table_schema_node = o
            subject = s

        table_schema_graph = Graph()
        if table_schema_node:
            table_schema_graph.add((subject, HSTERMS.tableSchema, table_schema_node))
            for s, p, o in graph.triples((table_schema_node, None, None)):
                # adding the columns node to the table schema node
                table_schema_graph.add((s, p, o))
                for ss, pp, oo in graph.triples((o, None, None)):
                    # adding the column node to the columns node
                    table_schema_graph.add((ss, pp, oo))
                    for sss, ppp, ooo in graph.triples((oo, None, None)):
                        # adding the children of the column node to the column node
                        table_schema_graph.add((sss, ppp, ooo))
                        graph.remove((sss, ppp, ooo))
                    graph.remove((ss, pp, oo))
                graph.remove((s, p, o))
            graph.remove((None, HSTERMS.tableSchema, table_schema_node))

        super(CSVFileMetaData, self).ingest_metadata(graph)

        # extract all columns from the graph
        columns = []
        for _, _, column_node in table_schema_graph.triples((None, HSTERMS.column, None)):
            column_name = table_schema_graph.value(column_node, DC.title)
            if not column_name:
                column_name = None
            else:
                column_name = str(column_name.toPython())
            description = table_schema_graph.value(column_node, DC.description)
            if not description:
                description = None
            else:
                description = str(description.toPython())
            column_number = table_schema_graph.value(column_node, HSTERMS.columnNumber)
            column_number = int(column_number.toPython())
            datatype = table_schema_graph.value(column_node, HSTERMS.dataType)
            datatype = str(datatype.toPython())
            column_model = _CSVColumnSchema(titles=column_name, datatype=datatype, column_number=column_number,
                                            description=description)
            columns.append(column_model)

        # check the number of columns have not changed
        if len(columns) != len(self.tableSchema["table"]["columns"]):
            raise ValueError("Number of data columns can't be changed")

        columns_model = _CSVColumnsSchema(columns=columns)

        rows = None
        for s, p, o in table_schema_graph.triples((None, HSTERMS.numberOfDataRows, None)):
            rows = o.toPython()
            break
        if rows is None:
            raise ValueError("Could not find number of rows")

        delimiter = None
        for s, p, o in table_schema_graph.triples((None, HSTERMS.delimiter, None)):
            delimiter = o.toPython()
            break
        if delimiter is None:
            raise ValueError("Could not find delimiter")

        csv_meta_model_instance = CSVMetaSchemaModel(rows=rows, delimiter=delimiter, table=columns_model)
        self.tableSchema = csv_meta_model_instance.model_dump()
        self.save()

    def get_rdf_graph(self):
        graph = super(CSVFileMetaData, self).get_rdf_graph()
        subject = self.rdf_subject()
        csv_meta_model = self.get_table_schema_model()
        tableSchema = BNode()
        graph.add((subject, HSTERMS.tableSchema, tableSchema))
        graph.add((tableSchema, HSTERMS.numberOfDataRows, Literal(csv_meta_model.rows)))
        graph.add((tableSchema, HSTERMS.delimiter, Literal(csv_meta_model.delimiter)))
        columns = BNode()
        graph.add((tableSchema, HSTERMS.columns, columns))
        for col_number, col in enumerate(csv_meta_model.table.columns, start=1):
            column = BNode()
            graph.add((columns, HSTERMS.column, column))
            graph.add((column, HSTERMS.columnNumber, Literal(col_number)))
            if col.titles:
                graph.add((column, DC.title, Literal(col.titles)))
            if col.description:
                graph.add((column, DC.description, Literal(col.description)))

            graph.add((column, HSTERMS.dataType, Literal(col.datatype)))

        return graph

    def get_html(self, include_extra_metadata=True, **kwargs):
        """overrides the base class function to generate html needed to display metadata
        in view mode"""

        html_string = super(CSVFileMetaData, self).get_html()
        if self.tableSchema:
            table_schema_model = self.get_table_schema_model()
            root_div = html_tags.div(cls="content-block")
            with root_div:
                html_tags.h3("CSV File Properties")
                html_tags.p(f"Number of data rows: {table_schema_model.rows}", cls="font-weight-bold",
                            style="padding-top: 10px; font-size: 1.3em;")
                delimiter = self._get_delimiter_name(table_schema_model.delimiter)
                html_tags.p(f"Delimiter: {delimiter}",
                            style="padding-top: 10px; font-size: 1.3em;")
                with html_tags.div():
                    html_tags.legend("Column Properties:")
                    for col_no, col in enumerate(table_schema_model.table.columns):
                        html_tags.legend(f"Column {col_no + 1}", csl="w-auto", style="font-size: 1.2em;")
                        col_title = col.titles if col.titles else ""
                        html_tags.p(f"Title: {col_title}")
                        col_desc = col.description if col.description else ""
                        html_tags.p(f"Description: {col_desc}")
                        html_tags.p(f"Data type: {col.datatype}")
                        html_tags.hr()

            html_string += root_div.render()

        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        root_div, context = super(CSVFileMetaData, self).get_html_forms(render=False)
        with root_div:
            with html_tags.div(cls="content-block"):
                with html_tags.div():
                    html_tags.legend("CSV File Properties:")
                    table_schema_model = self.get_table_schema_model()
                    form_action = f"/hsapi/_internal/{self.logical_file.id}/update-csv-table-schema/"
                    with html_tags.form(id="id-csv-metadata", action=form_action, method="post",
                                        encrtype="multipart/form-data"):
                        column_input_cls = "form-control input-sm textinput textInput"
                        row_div = html_tags.div(cls="control-group", id="id-csv-metadata-row-count")
                        with row_div:
                            html_tags.label("Number of data rows:", fr="id-csv-metadata-rows",
                                            cls="control-label")
                            with html_tags.div(cls="controls"):
                                html_tags.input(type="text", id="id-csv-metadata-rows", name="rows",
                                                readonly="readonly",
                                                value=table_schema_model.rows,
                                                cls=column_input_cls)
                        delimiter_div = html_tags.div(cls="control-group", id="id-csv-metadata-row-count")
                        with delimiter_div:
                            delimiter = self._get_delimiter_name(table_schema_model.delimiter)
                            html_tags.label("Delimiter:", fr="id-csv-metadata-delimiter",
                                            cls="control-label")
                            with html_tags.div(cls="controls"):
                                html_tags.input(type="text", id="id-csv-metadata-delimiter", name="rows",
                                                readonly="readonly",
                                                value=delimiter,
                                                cls=column_input_cls)
                        col_div = html_tags.div(cls="control-group", id="id-csv-metadata-columns")
                        with col_div:
                            with html_tags.div():
                                html_tags.legend("Column Properties:", style="font-size: 1.2em;")
                                for col_no, col in enumerate(table_schema_model.table.columns):
                                    with html_tags.fieldset(cls="border p-2"):
                                        html_tags.legend(f"Column {col_no + 1}", csl="w-auto")
                                        titles_id = f"id-csv-metadata-column-{col_no}-titles"
                                        html_tags.label("Title", fr=titles_id,)
                                        col_title = col.titles if col.titles else ""
                                        html_tags.input(type="text", id=titles_id, name=f"column-{col_no}-titles",
                                                        value=col_title, cls=column_input_cls)

                                        desc_id = f"id-csv-metadata-column-{col_no}-description"
                                        html_tags.label("Description", fr=desc_id)
                                        col_description = col.description if col.description else ""
                                        html_tags.input(type="text", id=desc_id, name=f"column-{col_no}-description",
                                                        value=col_description, cls=column_input_cls)

                                        datatype_id = f"id-csv-metadata-column-{col_no}-datatype"
                                        html_tags.label("Data type", fr=datatype_id)
                                        with html_tags.select(cls='form-control', id=datatype_id,
                                                              name=f"column-{col_no}-datatype"):
                                            for dt in ('string', 'number', 'datetime', 'boolean'):
                                                if col.datatype == dt:
                                                    html_tags.option(dt, selected="selected")
                                                else:
                                                    html_tags.option(dt)

                        with html_tags.div(cls="row", style="margin-top:10px;"):
                            with html_tags.div(cls="col-md-offset-10 col-xs-offset-6 " "col-md-2 col-xs-6"):
                                html_tags.button(
                                    "Save changes",
                                    type="button",
                                    cls="btn btn-primary pull-right",
                                    style="display: none;",
                                )

        template = Template(root_div.render())
        return template.render(context)

    def get_preview_data_html(self):
        toggle_preview_div = html_tags.div(style="clear: both;")
        with toggle_preview_div:
            html_tags.button("Preview CSV Data (First 10 data rows only)", type="button", cls="btn btn-info",
                             data_toggle="collapse",
                             data_target="#preview-data", style="margin-bottom: 10px;")
            preview_div = html_tags.div(style="clear: both; padding-bottom: 10px;", id="preview-data", cls="collapse")
            with preview_div:
                logical_file = self.logical_file
                html_tags.textarea(logical_file.preview_data, rows=10, readonly="readonly", wrap="soft",
                                   style="min-width: 100%; resize: vertical; overflow-x: auto; white-space: pre;")
        return toggle_preview_div

    @staticmethod
    def _get_delimiter_name(delimiter):
        delimiters = {',': 'comma', ';': 'semicolon', '\t': 'tab'}
        return delimiters[delimiter]


class CSVLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(CSVFileMetaData, on_delete=models.CASCADE, related_name="logical_file")
    preview_data = models.TextField(null=False, blank=False)
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
    def get_main_file_type(cls):
        """The main file type for this aggregation"""
        return ".csv"

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
        return "CSV File Aggregation"

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
        # only comma, tab or semicolon as a CSV delimiter is supported
        return ['\t', ',', ';']

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
            if res_file.extension.lower() != '.csv':
                raise ValidationError("File extension should be .csv")
            csv_temp_file = ft_ctx.temp_file
            try:
                metadata = cls._extract_metadata(csv_temp_file)
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

            preview_data = cls._get_preview_data(csv_temp_file)
            logical_file.preview_data = preview_data
            logical_file.save()
            logical_file.metadata.tableSchema = metadata
            logical_file.metadata.save()
            ft_ctx.logical_file = logical_file
            log.info(f"CSV aggregation was created for file:{res_file.storage_path}.")
            return logical_file

    @classmethod
    def _extract_metadata(cls, csv_file_path: str) -> dict:
        """
        Extracts metadata from the CSV file
        :param csv_file_path: a temporary file path of the CSV file after the file is copied from S3
        :return: a dictionary of extracted metadata
        """

        try:
            rows_count, delimiter, skip_rows = cls._get_rows_count(csv_file_path)
        except pd.errors.ParserError as ex:
            raise ValidationError(f"Error parsing CSV file: {str(ex)}")
        if rows_count == 0:
            err_msg = "No data rows found in the CSV file"
            raise ValidationError(err_msg)

        columns, has_header = cls._get_column_data_types(csv_file_path, delimiter, skip_rows=skip_rows)
        if has_header:
            rows_count -= 1
            if rows_count <= 0:
                err_msg = "No data rows found in the CSV file"
                raise ValidationError(err_msg)

        table = _CSVColumnsSchema(columns=columns)
        csv_meta_schema = CSVMetaSchemaModel(rows=rows_count, delimiter=delimiter, table=table)
        return csv_meta_schema.model_dump()

    @classmethod
    def _get_rows_count(cls, csv_file_path: str) -> tuple[int, str, int]:
        """Get the number of rows/records in the csv file (includes header row), the delimiter, and number of rows
        to skip (to find the header row or first data row).
        As part of finding the number of rows, also doing validation of the csv file"""

        def is_data_row(row):
            if not row:
                return False
            if not row[0].startswith("#"):
                if len(row) > number_of_columns:
                    raise pd.errors.ParserError("Invalid CSV file. Parsing error - number of data "
                                                "columns more than number of header columns.")
                return True
            return False

        def check_for_non_comment_text(delimiter=','):
            """Checks if there is any non-comment text line (line that doesn't start with #) in the file"""

            with open(csv_file_path, 'r') as csv_file:
                reader = csv.reader(csv_file, delimiter=delimiter)
                # to handle the edge case when there is only one column in the csv file
                _one_column_data = False

                data_row_count = 0
                _MAX_DATA_ROWS_TO_READ = 5
                _has_matching_delimiter = False
                maybe_invalid_csv = False
                _number_of_columns = 1
                _skip_rows = 0
                for row in reader:
                    # skip line starting with # (comment line) or empty line
                    if len(row) == 0 or row[0].startswith("#") or not ''.join(row).strip():
                        _skip_rows += 1
                        continue
                    data_row_count += 1

                    if len(row) > 1 and _one_column_data:
                        raise pd.errors.ParserError("Invalid CSV file. Contains non-comment text")
                    elif len(row) == 1:
                        if len(row[0].split()) > 1:
                            maybe_invalid_csv = True
                        elif _number_of_columns == 1:
                            _one_column_data = True
                    elif len(row) > 1:
                        _has_matching_delimiter = True
                        if _number_of_columns == 1:
                            _number_of_columns = len(row)
                        elif len(row) > _number_of_columns:
                            raise pd.errors.ParserError("Invalid CSV file. Parsing error - number of data "
                                                        "columns more than number of header columns.")

                    if data_row_count > _MAX_DATA_ROWS_TO_READ:
                        break

            if data_row_count == 0:
                raise pd.errors.ParserError("Invalid CSV file. No data rows found")
            if maybe_invalid_csv:
                if _has_matching_delimiter or delimiter == ';':
                    _err_msg = ("Invalid CSV file. Contains non-comment text - possibly space delimiter"
                                " used instead of comma, semicolon, or tab")
                    raise pd.errors.ParserError(_err_msg)

            return _has_matching_delimiter, _number_of_columns, _skip_rows

        default_delimiter = ','
        for _delimiter in cls.get_csv_allowed_delimiters():
            has_matching_delimiter, number_of_columns, skip_rows = check_for_non_comment_text(delimiter=_delimiter)
            one_column_data = number_of_columns == 1
            if has_matching_delimiter:
                matching_delimiter = _delimiter
                break

            # delimiter semicolon is the last one we tried
            if _delimiter == ';' and one_column_data:
                # if there is only one data column in the csv file, use comma as the delimiter
                matching_delimiter = default_delimiter
                break
        else:
            err_msg = "Invalid CSV file. No supported delimiter found - comma, semicolon, or tab"
            raise pd.errors.ParserError(err_msg)

        with open(csv_file_path, 'r') as file:
            # using csv.reader to efficiently count the rows instead of using pandas
            row_count = sum(1 for _row in csv.reader(file, delimiter=matching_delimiter) if is_data_row(_row))
            return row_count, matching_delimiter, skip_rows

    @classmethod
    def _get_pd_data_types(cls, csv_file_path: str, delimiter: str, skip_rows: int) -> dict:
        """Loads the first chunk of the file to pandas dataframe and get the initial data type of each column in
        the data frame based on the limited number of data rows.
        """

        def apply_column_data_type(_df, col_index, dt_types):
            # check if the given column is of datetime or boolean type

            column = _df.iloc[:, col_index]
            # drop null values
            column = column.dropna()
            if column.empty:
                return

            column_copy = column.copy()

            column = column.astype('object')
            column = column.apply(str)
            bool_tf_options = [['true', 'false'], ['True', 'False'], ['TRUE', 'FALSE'], ['T', 'F']]
            bool_yn_options = [['yes', 'no'], ['Yes', 'No'], ['YES', 'NO'], ['Y', 'N']]

            for tf_options in bool_tf_options:
                if column.isin(tf_options).all():
                    dt_types[col_index] = "boolean"
                    return

            for yn_options in bool_yn_options:
                if column.isin(yn_options).all():
                    dt_types[col_index] = "boolean"
                    return

            try:
                pd.to_datetime(column_copy, errors='raise', format='mixed')
                dt_types[col_index] = "datetime"
                return
            except ValueError:
                # column data type is string as originally determined by pandas
                pass

        # number of rows to read - column data types are computed based on data in those sample data rows only
        # using all data rows to compute column data type can be slow and cause memory issues in case of very large
        # file
        _CHUNK_SIZE = 1000

        pd_data_types = {}
        df = pd.read_csv(
            csv_file_path,
            skiprows=skip_rows,
            nrows=_CHUNK_SIZE,
            sep=delimiter,
            engine='python'
        )

        col_counter = 0
        for _, dtype in df.dtypes.items():
            # pandas sets the data type of column to boolean if the column contains 'True' or 'False'
            if pd.api.types.is_bool_dtype(dtype):
                pd_data_types[col_counter] = "boolean"
            elif pd.api.types.is_numeric_dtype(dtype):
                pd_data_types[col_counter] = "number"
            else:
                pd_data_types[col_counter] = "string"
            col_counter += 1

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for col, data_type in pd_data_types.items():
                if data_type == "string":
                    # further checking if the column actually contains datetime or boolean data type
                    futures.append(executor.submit(apply_column_data_type, df, col, pd_data_types))
                    for future in concurrent.futures.as_completed(futures):
                        future.result()

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
            line_count = 0
            seek_position = 0
            while line and line_count < _MAX_LINES_TO_READ:
                if line.startswith("#") or not ''.join(line).strip():
                    line = csvfile.readline()
                    continue
                if not line.startswith("#") and ''.join(line).strip():
                    seek_position = csvfile.tell() - len(line) - 1  # adjust for the newline character
                    break
                line_count += 1
                line = csvfile.readline()

            if line:
                if seek_position < 0:
                    seek_position = 0
                csvfile.seek(seek_position)

                # feed the first 5 non-empty lines into the csv Sniffer
                csv_data = ""
                line_count = 0
                while line_count <= 5:
                    line = csvfile.readline()
                    if not line:
                        break
                    csv_data += line
                    line_count += 1

                sniffer = csv.Sniffer()
                try:
                    has_header = sniffer.has_header(csv_data)
                except csv.Error:
                    has_header = False

                if not has_header:
                    # try custom check for header row
                    has_header = is_header_row()
                return has_header
            return False

    @classmethod
    def _get_column_data_types(cls, csv_file_path: str, delimiter: str,
                               skip_rows: int = 0) -> tuple[List[_CSVColumnSchema], bool]:
        """
        Compute the data type of each column in the csv file
        """

        # read the first few rows of the file to estimate column headers
        _CHUNK_SIZE = 100
        df = pd.read_csv(
            csv_file_path,
            skiprows=skip_rows,
            nrows=_CHUNK_SIZE,
            sep=delimiter,
            dtype='string',
            engine='python',
            on_bad_lines='skip'
        )

        has_header = cls._has_header_row(csv_file_path, df)

        # collect the column names
        headers = []
        if has_header:
            for column_name in df.columns:
                column_name = column_name.strip("\"")
                headers.append(column_name)
        else:
            headers = [None for _ in range(len(df.columns))]

        pd_data_types = cls._get_pd_data_types(csv_file_path, delimiter, skip_rows=skip_rows)

        csv_column_models = []
        for col_no, data_type in pd_data_types.items():
            col_name = headers[col_no]
            col_no += 1
            csv_column_model = _CSVColumnSchema(titles=col_name, datatype=data_type, column_number=col_no)
            csv_column_models.append(csv_column_model)

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
            while line and line_count <= _MAX_LINES_TO_READ:
                csv_preview_data += line
                if not line.startswith("#") and ''.join(line).strip():
                    data_line_count += 1
                    if data_line_count > _MAX_DATA_ROWS_TO_READ:
                        break
                line = csvfile.readline()
                line_count += 1

            return csv_preview_data

    @classmethod
    def get_primary_resource_file(cls, resource_files):
        """Gets any resource file as the primary file  from the list of files *resource_files* """

        return resource_files[0] if resource_files else None

    @property
    def metadata_json_file_path(self):
        """Returns the storage path of the aggregation metadata json file"""

        primary_file = self.get_primary_resource_file(self.files.all())
        meta_file_path = primary_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        return meta_file_path

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(CSVLogicalFile, self).create_aggregation_xml_documents(create_map_xml)
        self.metadata.is_dirty = False
        self.metadata.save()

    def get_copy(self, copied_resource):
        """Overrides the base class method"""

        copy_of_logical_file = super(CSVLogicalFile, self).get_copy(copied_resource)
        copy_of_logical_file.metadata.tableSchema = self.metadata.tableSchema
        copy_of_logical_file.metadata.save()
        copy_of_logical_file.preview_data = self.preview_data
        copy_of_logical_file.save()

        return copy_of_logical_file
