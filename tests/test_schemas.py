from datetime import date
from decimal import Decimal

from pydantic import ValidationError
import pytest

from nettlesome.predicates import Predicate
from nettlesome.entities import Entity
from nettlesome.quantities import Comparison, Q_
from nettlesome.statements import Assertion


class TestPredicateLoad:
    def test_load_predicate(self):
        p7 = Predicate(
            **{
                "content": "$defendant stole ${victim}'s car",
                "truth": False,
            }
        )
        assert p7.template.placeholders == ["defendant", "victim"]

    def test_load_comparison(self):
        p7 = Comparison(
            **{
                "content": "the distance between $place1 and $place2 was",
                "truth": True,
                "sign": "!=",
                "expression": "35 feet",
            }
        )
        assert p7.sign == "!="

    def test_load_and_normalize_comparison(self):
        data = {
            "content": "the distance between $place1 and $place2 was",
            "truth": True,
            "sign": "!=",
            "expression": "35 feet",
        }
        p7 = Comparison(**data)
        assert p7.sign == "!="


class TestPredicateDump:
    def test_dump_predicate(self):
        predicate = Predicate(content="$defendant stole ${victim}'s car")
        dumped = predicate.dict()
        assert dumped["truth"] is True

    def test_dump_to_dict_with_units(self):
        predicate = Comparison(
            content="the distance between $place1 and $place2 was",
            truth=True,
            sign="<>",
            expression=Q_("35 feet"),
        )
        dumped = predicate.dict()
        assert dumped["quantity_range"]["quantity_magnitude"] == Decimal("35")
        assert dumped["quantity_range"]["quantity_units"] == "foot"

    def test_round_trip(self):
        predicate = Comparison(
            **{"content": "{}'s favorite number was", "sign": "==", "expression": 42}
        )
        dumped = predicate.dict()
        new_statement = Comparison(**dumped)
        assert "{}'s favorite number was exactly equal to 42" in str(new_statement)

    def test_dump_comparison_with_date_expression(self):
        copyright_date_range = Comparison(
            content="the date when $work was created was",
            sign=">=",
            expression=date(1978, 1, 1),
        )
        dumped = copyright_date_range.dict()
        assert dumped["quantity_range"]["quantity"] == date(1978, 1, 1)


class TestFactorLoad:
    def test_round_trip_assertion(self):
        data = {
            "type": "Assertion",
            "statement": {
                "predicate": {"content": "$defendant jaywalked"},
                "terms": [{"name": "Alice"}],
            },
            "authority": {"name": "Bob"},
        }
        loaded = Assertion(**data)
        assert loaded.statement.terms[0].name == "Alice"
        dumped = loaded.dict()
        assert dumped["authority"]["name"] == "Bob"

    def test_load_entity_with_type_field(self):
        data = {"type": "Entity", "name": "Ed"}
        loaded = Entity(**data)
        assert loaded.name == "Ed"

    def test_load_entity_with_wrong_type_field(self):
        data = {"type": "Statement", "name": "Ed"}
        with pytest.raises(TypeError):
            Entity(**data)
