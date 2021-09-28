from datetime import date

from nettlesome.predicates import Predicate
from nettlesome.quantities import Comparison, Q_
from nettlesome.schemas import PredicateSchema, FactorSchema


class TestPredicateLoad:
    schema = PredicateSchema()

    def test_load_predicate(self):
        p7 = self.schema.load(
            {
                "content": "$defendant stole ${victim}'s car",
                "truth": False,
            }
        )
        assert p7.template.placeholders == ["defendant", "victim"]

    def test_load_comparison(self):
        p7 = self.schema.load(
            {
                "content": "the distance between $place1 and $place2 was",
                "truth": True,
                "sign": "!=",
                "expression": "35 feet",
            }
        )
        assert p7.sign == "!="

    def test_load_and_normalize_comparison(self):
        p7 = self.schema.load(
            data={
                "content": "the distance between $place1 and $place2 was",
                "truth": True,
                "sign": "!=",
                "expression": "35 feet",
            }
        )
        assert p7.sign == "!="


class TestPredicateDump:

    schema = PredicateSchema()

    def test_dump_predicate(self):
        predicate = Predicate(content="$defendant stole ${victim}'s car")
        dumped = self.schema.dump(predicate)
        assert dumped["truth"] is True

    def test_dump_to_dict_with_units(self):
        predicate = Comparison(
            content="the distance between $place1 and $place2 was",
            truth=True,
            sign="<>",
            expression=Q_("35 feet"),
        )
        dumped = self.schema.dump(predicate)
        assert dumped["expression"] == "35 foot"

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
        dumped = self.schema.dump(copyright_date_range)
        assert dumped["expression"] == "1978-01-01"


class TestFactorLoad:
    schema = FactorSchema()

    def test_round_trip_assertion(self):
        data = {
            "type": "Assertion",
            "statement": {
                "predicate": {"content": "$defendant jaywalked"},
                "terms": [{"type": "Entity", "name": "Alice"}],
            },
            "authority": {"name": "Bob"},
        }
        loaded = self.schema.load(data)
        assert loaded.statement.terms[0].name == "Alice"
        dumped = self.schema.dump(loaded)
        assert dumped["authority"]["name"] == "Bob"
