.. _Serializing Nettlesome Data:

Serializing Nettlesome Data
===========================

Nettlesome objects are Pydantic models. That means serialization and
deserialization use Pydantic's built-in methods instead of separate
schema classes.

Loading Data
------------

Use :meth:`~pydantic.main.BaseModel.model_validate` to load from a
Python dictionary and :meth:`~pydantic.main.BaseModel.model_validate_json`
to load from a JSON string.

    >>> from nettlesome import Predicate
    >>> data = {"content": "$defendant stole bread", "truth": False}
    >>> predicate = Predicate.model_validate(data)
    >>> str(predicate)
    'it was false that $defendant stole bread'
    >>> json_string = '{"content": "$defendant stole bread", "truth": false}'
    >>> loaded = Predicate.model_validate_json(json_string)
    >>> loaded == predicate
    True

Dumping Data
------------

Use :meth:`~pydantic.main.BaseModel.model_dump` to get a Python
dictionary and :meth:`~pydantic.main.BaseModel.model_dump_json` to get
JSON.

    >>> from nettlesome import Assertion, Statement, Entity, Predicate
    >>> fact = Statement(predicate=Predicate(content="$suspect stole bread"), terms=[Entity(name="Valjean")])
    >>> accusation = Assertion(statement=fact, authority=Entity(name="Javert"))
    >>> dumped = accusation.model_dump()
    >>> sorted(dumped.keys())
    ['authority', 'generic', 'name', 'statement']
    >>> dumped["authority"]["name"]
    'Javert'
    >>> accusation.model_dump_json().startswith('{"generic":false')
    True

Schema Information
------------------

If you need a JSON Schema for integration or docs tooling, call
:meth:`~pydantic.main.BaseModel.model_json_schema` on a Nettlesome class.

    >>> from nettlesome import Statement
    >>> schema = Statement.model_json_schema()
    >>> sorted(schema.keys())
    ['$defs', 'description', 'properties', 'required', 'title', 'type']
