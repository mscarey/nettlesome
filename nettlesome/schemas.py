from datetime import date
from nettlesome.assertions import Assertion
from typing import Any, Dict, Optional, Sequence, Type, Union

from apispec import APISpec
from apispec_oneofschema import MarshmallowPlugin
from marshmallow import Schema, fields, validate, post_load
from marshmallow_oneofschema import OneOfSchema

from nettlesome.entities import Entity
from nettlesome.factors import Factor
from nettlesome.predicates import Predicate
from nettlesome.quantities import Comparison, QuantityRange
from nettlesome.statements import Statement


RawPredicate = Dict[str, Union[str, bool]]
RawFactor = Dict[str, Union[RawPredicate, Sequence[Any], str, bool]]


def dump_quantity(
    obj: Union[Predicate, Comparison]
) -> Optional[Union[date, float, int, str]]:
    """Convert quantity to string if it's a pint ureg.Quantity object."""
    if not hasattr(obj, "quantity"):
        return None
    if isinstance(obj.quantity, date):
        return obj.quantity.isoformat()
    if isinstance(obj.quantity, (int, float)):
        return obj.quantity
    return f"{obj.quantity.magnitude} {obj.quantity.units}"


class PredicateSchema(Schema):
    """Schema for phrases, separate from any claim about their truth or who asserts them."""

    __model__ = Predicate
    content = fields.Str()
    truth = fields.Bool(missing=True)
    sign = fields.Str(
        missing=None,
        validate=validate.OneOf([""] + list(QuantityRange.opposite_comparisons.keys())),
    )
    expression = fields.Function(
        dump_quantity, deserialize=Comparison.read_quantity, missing=None
    )

    @post_load
    def make_object(self, data, **kwargs):
        """Make either a Predicate or a Comparison."""
        if data.get("expression") is not None:
            return Comparison(**data)
        data.pop("expression", None)
        data.pop("sign", None)
        return self.__model__(**data)


class EntitySchema(Schema):
    """Schema for Entities, which shouldn't be at the top level of a FactorGroup."""

    __model__: Type = Entity
    name = fields.Str(missing=None)
    generic = fields.Bool(missing=True)
    plural = fields.Bool()

    @post_load
    def make_object(self, data: Dict[str, Union[bool, str]], **kwargs) -> Entity:
        return self.__model__(**data)


class StatementSchema(Schema):
    """Schema for Statement, which may contain arbitrary levels of nesting."""

    __model__: Type = Statement
    predicate = fields.Nested(PredicateSchema)
    terms = fields.Nested(lambda: FactorSchema(many=True))
    absent = fields.Bool(missing=False)
    generic = fields.Bool(missing=False)

    @post_load
    def make_object(self, data: RawFactor, **kwargs) -> Statement:
        """Make Statement."""
        return self.__model__(**data)


class AssertionSchema(Schema):
    """Schema for Assertion, which may contain arbitrary levels of nesting."""

    __model__: Type = Assertion
    statement = fields.Nested(StatementSchema)
    authority = fields.Nested(EntitySchema, missing=None)
    absent = fields.Bool(missing=False)
    generic = fields.Bool(missing=False)

    @post_load
    def make_object(self, data: RawFactor, **kwargs) -> Statement:
        """Make Assertion from loaded data."""
        return self.__model__(**data)


class FactorSchema(OneOfSchema):
    """Schema that directs data to "one of" the other schemas."""

    __model__: Type = Factor
    type_schemas = {
        "Assertion": AssertionSchema,
        "Entity": EntitySchema,
        "Statement": StatementSchema,
    }

    def get_obj_type(self, obj) -> str:
        """Return name of object schema."""
        return obj.__class__.__name__
