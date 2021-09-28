.. _Serializing Nettlesome Data:

Serializing Nettlesome Data
===========================

Nettlesome relies on
`Marshmallow <https://marshmallow.readthedocs.io/en/stable/>`__ for
dumping and loading data (also known as “serializing and
deserializing”). These methods will convert Nettlesome objects back and
forth from a JSON format that can be easily transmitted over the web.

Loading JSON Data
-----------------

When loading data from a JSON string or from a Python dictionary,
Nettlesome’s data schemas will apply some validation to check that the
data has the right fields, and then load a Nettlesome object such as a
:class:`~nettlesome.predicates.Predicate`,
:class:`~nettlesome.statements.Statement`,
or :class:`~nettlesome.assertions.Assertion`. Here’s an example of
creating a Predicate from a JSON string.

First, create a schema by making an instance of the schema class named
for the type of object you want to create. (The syntax for making an
instance of a class is the class name followed by a pair of
parentheses.)

    >>> from nettlesome.schemas import PredicateSchema
    >>> schema = PredicateSchema()

If we were loading an object from a Python dictionary, we would use the
:meth:`~marshmallow.schema.Schema.load` method. But when we load from a JSON string, we use
:meth:`~marshmallow.schema.Schema.loads`\. (The extra ‘s’ at the end means ‘string’.)

    >>> json_string = """{"content": "$defendant stole ${victim}'s car","truth": false}"""
    >>> predicate = schema.loads(json_string)
    >>> predicate
    Predicate(template='$defendant stole ${victim}'s car', truth=False)
    >>> str(predicate)
    "it was false that $defendant stole ${victim}'s car"

Note that :class:`~nettlesome.predicates.Predicate`
and :class:`~nettlesome.quantities.Comparison` both share
the :class:`~nettlesome.schemas.PredicateSchema` schema, because
Comparison is a subclass of Predicate.

    >>> data = {"content": "the size of the farm was", "sign": ">", "expression": "20 acres"}
    >>> comparison = schema.load(data)
    >>> comparison
    Comparison(template='the size of the farm was', truth=True, quantity_range=UnitRange(quantity="20 acre", sign=">", include_negatives=False))
    >>> str(comparison)
    'that the size of the farm was greater than 20 acre'


Generating Schema Documentation
-------------------------------

Nettlesome can use the
`apispec <https://github.com/marshmallow-code/apispec>`__ library to
automatically generate
`OpenAPI <https://github.com/OAI/OpenAPI-Specification>`__ documentation
of what fields need to be passed to a schema to create a Nettlesome
object. To use this feature, pass the Schema class you want to document
to the :class:`~nettlesome.spec.make_spec` function.

    >>> from nettlesome import make_spec
    >>> spec = make_spec(PredicateSchema)
    >>> print(spec)
    <apispec.core.APISpec object at 0x7fa4ad641a30>

To actually read the schema specification, either use the :meth:`~apispec.APISpec.to_dict`
method to get the specification as a Python object or use the
:meth:`~apispec.APISpec.to_yaml` method to see it in the less cluttered YAML format.

    >>> print(spec.to_yaml())\
    components:
      schemas:
        Predicate:
          properties:
            content:
              type: string
            expression:
              default: null
              nullable: true
            sign:
              default: null
              enum:
              - ''
              - '>='
              - ==
              - '!='
              - <=
              - <>
              - '>'
              - <
              nullable: true
              type: string
            truth:
              default: true
              type: boolean
          type: object
    info:
      description: Metadata tags designed for semantic comparisons
      title: Nettlesome API Specification
      version: 0.1.0
    openapi: 3.0.2
    paths: {}


Dumping Objects to JSON
-----------------------

When you’re ready to take data out of a Nettlesome object, you can
either use :meth:`~marshmallow.schema.Schema.dump` to convert it to a basic Python dictionary, or use
:meth:`~marshmallow.schema.Schema.dumps` to convert it directly to a JSON string. Here’s an example of
creating a Nettlesome :class:`~nettlesome.assertions.Assertion` object using Python, but then converting
it to JSON.

    >>> from nettlesome import Assertion, Statement, Entity
    >>> fact = Statement(predicate="$suspect stole bread", terms=Entity(name="Valjean"))
    >>> accusation = Assertion(statement=fact, authority=Entity(name="Javert"))
    >>> print(accusation)
    the assertion, by <Javert>, of the statement that <Valjean> stole bread
    >>> from nettlesome.schemas import AssertionSchema
    >>> schema = AssertionSchema()
    >>> schema.dumps(accusation)
    '{"generic": false, "statement": {"generic": false, "terms": [{"generic": true, "plural": false, "name": "Valjean", "type": "Entity"}], "absent": false, "predicate": {"content": "$suspect stole bread", "truth": true, "expression": null}}, "absent": false, "authority": {"generic": true, "plural": false, "name": "Javert"}}'
