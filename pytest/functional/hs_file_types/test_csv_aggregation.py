import os

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare import add_file_to_resource
from hs_file_types.models import CSVLogicalFile, CSVMetaSchemaModel


@pytest.mark.django_db(transaction=True)
def test_create_csv_aggregation_1(composite_resource):
    # here we are testing that we can create a CSV file type aggregation from a csv file that
    # is part of a resource
    # here we are using a csv file that has headers and data in all columns

    res, user = composite_resource

    # upload a csv file to the resource
    res_file = _upload_csv_file(res, 'csv_with_header_and_data.csv')

    # check there are no CSV file type logical files
    assert CSVLogicalFile.objects.count() == 0

    # set the uploaded csv file to be part of a csv aggregation
    CSVLogicalFile.set_file_type(res, user, res_file.id)

    # test that we have one logical file of type CSV
    assert CSVLogicalFile.objects.count() == 1
    csv_aggr = CSVLogicalFile.objects.first()

    # check extracted metadata
    metadata = csv_aggr.metadata
    assert metadata.tableSchema is not None
    table_schema = metadata.tableSchema
    csv_meta_schema_model = CSVMetaSchemaModel(**table_schema)
    assert csv_meta_schema_model.rows == 9
    assert len(csv_meta_schema_model.columns) == 17

    # check that the column names are correctly set - the csv file has headers
    assert csv_meta_schema_model.columns[0].titles == "VIN (1-10)"
    assert csv_meta_schema_model.columns[1].titles == "County"
    assert csv_meta_schema_model.columns[2].titles == "City"
    assert csv_meta_schema_model.columns[3].titles == "State"
    assert csv_meta_schema_model.columns[4].titles == "Postal Code"
    assert csv_meta_schema_model.columns[5].titles == "Model Year"
    assert csv_meta_schema_model.columns[6].titles == "Make"
    assert csv_meta_schema_model.columns[7].titles == "Model"
    assert csv_meta_schema_model.columns[8].titles == "Electric Vehicle Type"
    assert csv_meta_schema_model.columns[9].titles == "Clean Alternative Fuel Vehicle (CAFV) Eligibility"
    assert csv_meta_schema_model.columns[10].titles == "Electric Range"
    assert csv_meta_schema_model.columns[11].titles == "Base MSRP"
    assert csv_meta_schema_model.columns[12].titles == "Legislative District"
    assert csv_meta_schema_model.columns[13].titles == "DOL Vehicle ID"
    assert csv_meta_schema_model.columns[14].titles == "Vehicle Location"
    assert csv_meta_schema_model.columns[15].titles == "Electric Utility"
    assert csv_meta_schema_model.columns[16].titles == "2020 Census Tract"

    # check column data types
    for col_number, col in enumerate(csv_meta_schema_model.columns, start=1):
        assert not col.description
        assert not col.unitCode
        if col_number in (5, 6, 11, 12, 13, 14, 17):
            assert col.datatype == "number"
        else:
            assert col.datatype == "string"


@pytest.mark.django_db(transaction=True)
def test_create_csv_aggregation_2(composite_resource):
    # here we are testing that we can create a CSV file type aggregation from a csv file that
    # is part of a resource
    # here we are using a csv file that has no headers and data in all columns

    res, user = composite_resource

    # upload a csv file to the resource
    res_file = _upload_csv_file(res, 'csv_with_no_header.csv')

    # check there are no CSV file type logical files
    assert CSVLogicalFile.objects.count() == 0

    # set the uploaded csv file to be part of a csv aggregation
    CSVLogicalFile.set_file_type(res, user, res_file.id)

    # test that we have one logical file of type CSV
    assert CSVLogicalFile.objects.count() == 1
    csv_aggr = CSVLogicalFile.objects.first()

    # check extracted metadata
    metadata = csv_aggr.metadata
    assert metadata.tableSchema is not None
    table_schema = metadata.tableSchema
    csv_meta_schema_model = CSVMetaSchemaModel(**table_schema)
    assert csv_meta_schema_model.rows == 6
    assert len(csv_meta_schema_model.columns) == 5

    # check column properties
    for col_number, col in enumerate(csv_meta_schema_model.columns, start=1):
        # check that the column headers are missing
        assert not col.titles

        assert not col.description
        assert not col.unitCode
        if col_number in (1, 3):
            assert col.datatype == "string"
        elif col_number == 2:
            assert col.datatype == "number"
        elif col_number == 4:
            assert col.datatype == "datetime"
        else:
            assert col.datatype == "boolean"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("delimiter", ["comma", "tab", "semi-colon"])
def test_create_csv_aggregation_3(composite_resource, delimiter):
    # here we are testing that we can create a CSV file type aggregation from a csv file that
    # is part of a resource
    # the csv file has one of the three types of supported delimiters and has all 4 types of data

    res, user = composite_resource

    if delimiter == "comma":
        file_name = "csv_comma_separated_with_all_data_types.csv"
    elif delimiter == "tab":
        file_name = "csv_tab_separated_with_all_data_types.csv"
    else:
        file_name = "csv_semicolon_separated_with_all_data_types.csv"

    # upload a csv file to the resource
    res_file = _upload_csv_file(res, file_name)

    # check there are no CSV file type logical files
    assert CSVLogicalFile.objects.count() == 0

    # set the uploaded csv file to be part of a csv aggregation
    CSVLogicalFile.set_file_type(res, user, res_file.id)

    # test that we have one logical file of type CSV
    assert CSVLogicalFile.objects.count() == 1
    csv_aggr = CSVLogicalFile.objects.first()

    # check extracted metadata
    metadata = csv_aggr.metadata
    assert metadata.tableSchema is not None
    table_schema = metadata.tableSchema
    csv_meta_schema_model = CSVMetaSchemaModel(**table_schema)
    assert csv_meta_schema_model.rows == 6
    assert len(csv_meta_schema_model.columns) == 5

    # check column properties
    for col_number, col in enumerate(csv_meta_schema_model.columns, start=1):
        # check that the column headers are there
        assert col.titles

        assert not col.description
        assert not col.unitCode
        if col_number == 1:
            assert col.datatype == "string"
        elif col_number in (3, 4):
            assert col.datatype == "number"
        elif col_number == 2:
            assert col.datatype == "datetime"
        else:
            assert col.datatype == "boolean"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("use_csv_with_missing_data", [True, False])
def test_create_csv_aggregation_column_data_types(composite_resource, use_csv_with_missing_data):
    # here we are testing that we can create a CSV file type aggregation from a csv file that
    # is part of a resource
    # test param: use_csv_with_missing_data == True: here we are using a csv file that has headers and
    # data missing in some cells - should still be able to find data type for all columns (all 4 data types)
    # test param: use_csv_with_missing_data == False: here we are using a csv file that has headers and data
    # in all cells - should be able to find data type for all columns (all 4 data types)

    res, user = composite_resource

    # upload a csv file to the resource
    if use_csv_with_missing_data:
        csv_file = 'csv_with_missing_data.csv'
    else:
        csv_file = 'csv_with_header_and_all_data_types.csv'

    res_file = _upload_csv_file(res, csv_file)

    # check there are no CSV file type logical files
    assert CSVLogicalFile.objects.count() == 0

    # set the uploaded csv file to be part of a csv aggregation
    CSVLogicalFile.set_file_type(res, user, res_file.id)

    # test that we have one logical file of type CSV
    assert CSVLogicalFile.objects.count() == 1
    csv_aggr = CSVLogicalFile.objects.first()

    # check extracted metadata
    metadata = csv_aggr.metadata
    assert metadata.tableSchema is not None
    table_schema = metadata.tableSchema
    csv_meta_schema_model = CSVMetaSchemaModel(**table_schema)
    assert csv_meta_schema_model.rows == 6
    assert len(csv_meta_schema_model.columns) == 5

    # check column properties
    for col_number, col in enumerate(csv_meta_schema_model.columns, start=1):
        # check that the column headers are there
        assert col.titles == f"Col-{col_number}"

        assert not col.description
        assert not col.unitCode
        if col_number in (1, 3):
            assert col.datatype == "string"
        elif col_number == 2:
            assert col.datatype == "number"
        elif col_number == 4:
            assert col.datatype == "datetime"
        else:
            assert col.datatype == "boolean"


@pytest.mark.django_db(transaction=True)
def test_create_csv_aggregation_from_one_data_column_file(composite_resource):
    # here we are testing that we can create a CSV file type aggregation from a csv file that
    # is part of a resource
    # here we are using a csv file that has only one column with data

    res, user = composite_resource

    # upload a csv file to the resource
    res_file = _upload_csv_file(res, 'csv_with_one_column_data.csv')

    # check there are no CSV file type logical files
    assert CSVLogicalFile.objects.count() == 0

    # set the uploaded csv file to be part of a csv aggregation
    CSVLogicalFile.set_file_type(res, user, res_file.id)

    # test that we have one logical file of type CSV
    assert CSVLogicalFile.objects.count() == 1
    csv_aggr = CSVLogicalFile.objects.first()

    # check extracted metadata
    metadata = csv_aggr.metadata
    assert metadata.tableSchema is not None
    table_schema = metadata.tableSchema
    csv_meta_schema_model = CSVMetaSchemaModel(**table_schema)
    assert csv_meta_schema_model.rows == 6
    assert len(csv_meta_schema_model.columns) == 1

    # check column properties
    col = csv_meta_schema_model.columns[0]
    assert col.titles == "Col-1"

    assert not col.description
    assert not col.unitCode
    assert col.datatype == "number"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("csv_file", [
    "csv_boolean_column_TRUE_and_FALSE.csv",
    "csv_boolean_column_True_and_False_.csv",
    "csv_boolean_column_true_false.csv",
    "csv_boolean_column_T_and_F.csv",
    "csv_boolean_column_Yes_and_No_.csv",
    "csv_boolean_column_yes_no.csv",
    "csv_boolean_column_YES_NO_.csv",
    "csv_boolean_column_Y_and_N.csv",
])
def test_create_csv_aggregation_boolean_data_type(composite_resource, csv_file):
    # here we are testing that we can create a CSV file type aggregation from a csv file that
    # is part of a resource
    # test param: use_csv_with_missing_data == True: here we are using a csv file that has headers and
    # data missing in some cells - should still be able to find data type for all columns (all 4 data types)
    # test param: use_csv_with_missing_data == False: here we are using a csv file that has headers and data
    # in all cells - should be able to find data type for all columns (all 4 data types)

    res, user = composite_resource

    # upload a csv file to the resource
    res_file = _upload_csv_file(res, csv_file)

    # check there are no CSV file type logical files
    assert CSVLogicalFile.objects.count() == 0

    # set the uploaded csv file to be part of a csv aggregation
    CSVLogicalFile.set_file_type(res, user, res_file.id)

    # test that we have one logical file of type CSV
    assert CSVLogicalFile.objects.count() == 1
    csv_aggr = CSVLogicalFile.objects.first()

    # check extracted metadata
    metadata = csv_aggr.metadata
    assert metadata.tableSchema is not None
    table_schema = metadata.tableSchema
    csv_meta_schema_model = CSVMetaSchemaModel(**table_schema)
    assert csv_meta_schema_model.rows == 6
    assert len(csv_meta_schema_model.columns) == 5

    # check column properties
    for col_number, col in enumerate(csv_meta_schema_model.columns, start=1):
        # check that the column headers are there
        assert col.titles == f"Col-{col_number}"

        assert not col.description
        assert not col.unitCode
        if col_number in (1, 3):
            assert col.datatype == "string"
        elif col_number == 2:
            assert col.datatype == "number"
        elif col_number == 4:
            assert col.datatype == "datetime"
        else:
            assert col.datatype == "boolean"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("invalid_csv_file",
                         ['csv_with_additional_data_columns_invalid.csv',
                          'csv_no_data_rows_invalid.csv',
                          'csv_missing_data_rows_invalid.csv',
                          'csv_with_invalid_file_extension.txt',
                          'csv_column_with_comment_character_invalid.csv',
                          'csv_with_non_comment_line_invalid.csv',
                          'csv_space_delimiter_invalid.csv',])
def test_create_csv_aggregation_with_invalid_file(composite_resource, invalid_csv_file):
    # here we are testing that trying to create a CSV file type aggregation from an invalid csv file should fail

    res, user = composite_resource

    # upload  a csv file
    res_file = _upload_csv_file(res, invalid_csv_file)

    # check there are no CSV file type logical files
    assert CSVLogicalFile.objects.count() == 0

    # setting the uploaded invalid csv file to be part of a csv aggregation should fail
    with pytest.raises(ValidationError):
        CSVLogicalFile.set_file_type(res, user, res_file.id)

    # test that we did not create a logical file of type CSV
    assert CSVLogicalFile.objects.count() == 0


def _upload_csv_file(resource, csv_file):
    # upload a csv file to the resource
    file_path = f'pytest/assets/{csv_file}'
    file_to_upload = UploadedFile(file=open(file_path, 'rb'), name=os.path.basename(file_path))
    upload_folder = ""
    res_file = add_file_to_resource(
        resource, file_to_upload, folder=upload_folder, check_target_folder=True
    )
    return res_file
