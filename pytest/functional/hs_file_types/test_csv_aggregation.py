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
    file_path = 'pytest/assets/csv_with_header_and_data.csv'
    file_to_upload = UploadedFile(file=open(file_path, 'rb'), name=os.path.basename(file_path))
    upload_folder = ""
    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

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
        assert col.description is None
        assert col.unitCode is None
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
    file_path = 'pytest/assets/csv_with_no_header.csv'
    file_to_upload = UploadedFile(file=open(file_path, 'rb'), name=os.path.basename(file_path))
    upload_folder = ""
    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

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
        assert col.titles is None

        assert col.description is None
        assert col.unitCode is None
        if col_number in (1, 3):
            assert col.datatype == "string"
        elif col_number == 2:
            assert col.datatype == "number"
        elif col_number == 4:
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
        file_path = 'pytest/assets/csv_with_missing_data.csv'
    else:
        file_path = 'pytest/assets/csv_with_header_and_all_data_types.csv'

    file_to_upload = UploadedFile(file=open(file_path, 'rb'), name=os.path.basename(file_path))
    upload_folder = ""
    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

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

        assert col.description is None
        assert col.unitCode is None
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
                         ['csv_with_additional_data_columns_invalid.csv', 'csv_no_data_rows_invalid.csv',
                          'csv_with_invalid_file_extension.txt'])
def test_create_csv_aggregation_with_invalid_file(composite_resource, invalid_csv_file):
    # here we are testing that trying to create a CSV file type aggregation from an invalid csv file should fail

    res, user = composite_resource

    # upload  a csv file
    file_path = f'pytest/assets/{invalid_csv_file}'
    file_to_upload = UploadedFile(file=open(file_path, 'rb'), name=os.path.basename(file_path))
    upload_folder = ""
    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    # check there are no CSV file type logical files
    assert CSVLogicalFile.objects.count() == 0

    # setting the uploaded invalid csv file to be part of a csv aggregation should fail
    with pytest.raises(ValidationError):
        CSVLogicalFile.set_file_type(res, user, res_file.id)

    # test that we did not create a logical file of type CSV
    assert CSVLogicalFile.objects.count() == 0
