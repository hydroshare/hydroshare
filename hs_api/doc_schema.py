import coreapi
from coreapi import Link, Field

from rest_framework import response, schemas
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
from rest_framework.decorators import api_view, renderer_classes


schema = coreapi.Document(
    title='Hydroshare Public REST API, Version 2',
    content={
        "Resources": {
            "create": Link("/hsapi/v2/resources/", "POST",
                           description="Create new resource",
                           encoding="application/json",
                           fields=[
                               Field("body", required=True, location="form")
                           ]),
            "list": Link("/hsapi/v2/resources/", "GET",
                         description="List all available resources"),
            "delete": Link("/hsapi/v2/resources/{key}", "DELETE",
                           fields=[Field("key", required=True, location="path")],
                           description="Delete resource by ID"),
            "read": Link("/hsapi/v2/resources/{key}", "GET",
                         fields=[Field("key", required=True, location="path")],
                         description="Show resource details by ID"),
            "update": Link("/hsapi/v2/resources/{key}", "PUT",
                           encoding="application/json",
                           fields=[
                               Field("key", required=True, location="path"),
                               Field("body", required=True, location="form")
                           ],
                           description="Update single resource details by ID")
        }
    }
)


@api_view()
@renderer_classes([SwaggerUIRenderer, OpenAPIRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='Hydroshare Public REST API, Version 2')
    schema = generator.get_schema(request=request)
    return response.Response(schema)