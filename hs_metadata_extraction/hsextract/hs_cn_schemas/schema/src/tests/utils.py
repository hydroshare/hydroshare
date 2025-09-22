import pytest
from pydantic import ValidationError


async def validate_data_model(data, model_class):
    """Helper function to validate pydantic schema data models."""

    try:
        model_instance = model_class(**data)
    except ValidationError as e:
        pytest.fail(f"Schema model validation failed: {str(e)}")
    # checking some core metadata
    assert model_instance.name == "Test Dataset"
    assert model_instance.description == "This is a test dataset metadata json file to test catalog api"
    return model_instance
