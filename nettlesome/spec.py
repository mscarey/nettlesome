"""Function for generating specification from Marshmallow schemas."""

from apispec import APISpec
from apispec_oneofschema import MarshmallowPlugin
from marshmallow import Schema


def make_spec(schema: Schema) -> APISpec:
    """Generate specification for data used to create Nettlesome objects."""
    result = APISpec(
        title="Nettlesome API Specification",
        version="0.1.0",
        openapi_version="3.0.2",
        info={"description": "Metadata tags designed for semantic comparisons"},
        plugins=[MarshmallowPlugin()],
    )

    result.components.schema(schema.__model__.__name__, schema=schema)

    return result
