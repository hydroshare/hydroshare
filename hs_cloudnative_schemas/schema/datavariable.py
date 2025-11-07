#!/usr/bin/env python3

"""
CUAHSI's extension to the SchemaOrg vocabulary to better encapsulate
scientific data variable metadata.
"""

from typing import Optional, Literal, Union
from pydantic import Field, BaseModel, HttpUrl


class Dimension(BaseModel):
    """
    A variable dimension defines an axes of a variable; it provides the shape of the variable.

    """

    context: HttpUrl = Field(
        alias="@context",  # type: ignore
        default=HttpUrl(
            "https://hydroshare.org/schema"
        ),  # TODO: This is a placeholder for now.
        description="Specifies the vocabulary employed for understanding the structured data markup.",
    )
    type: Literal["Dimension"] = Field(
        alias="@type",  # type: ignore
        default="Dimension",
        description="A body of structured information describing variable dimensions.",
    )
    name: str = Field(
        title="Dimension Name",
        description="The name of the dimension",
    )
    shape: int = Field(
        title="Variable Shape",
        description="The shape of the variable",
    )
    description: Optional[str] = Field(
        default=None,
        title="Variable Description",
        description="The description of the variable measured",
    )

class DataVariable(BaseModel):

    context: HttpUrl = Field(
        alias="@context",  # type: ignore
        default=HttpUrl(
            "https://hydroshare.org/schema"
        ),  # TODO: This is a placeholder for now.
        description="Specifies the vocabulary employed for understanding the structured data markup.",
    )
    type: Literal["DataVariable"] = Field(
        alias="@type",  # type: ignore
        default="DataVariable",
        description="A body of structured information describing core metadata shared by all data variables.",
    )

    name: str = Field(
        title="Variable Name",
        description="The name of the variable measured",
    )
    dimensions: Union[str, list[str]] = Field(
        title="Variable Dimensions",
        description="The dimension names corresponding to the variable being measured",
    )
    description: Optional[str] = Field(
        default=None,
        title="Variable Description",
        description="The description of the variable measured",
    )
    dataType: Optional[str] = Field(
        default=None,
        title="The data type of the variable",
        description="The data type of the variable measured",
    )
    unit: Optional[str] = Field(
        default=None,
        title="Variable Unit",
        description="The unit of the variable measured",
    )
    minValue: Optional[Union[float,str]] = Field(
        title="Minimum Value",
        description="The minimum value in the raster grid",
        default=None,
    )
    maxValue: Optional[Union[float,str]] = Field(
        title="Maximum Value",
        description="The maximum value in the raster grid",
        default=None,
    )
    noDataValue: Optional[Union[float,str]] = Field(
        title="No Data Value",
        description="The numerical value used to represent null data in the raster grid",
        default=None,
    )