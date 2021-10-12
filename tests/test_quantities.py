from datetime import date

import pytest
from sympy import S, oo

from nettlesome.entities import Entity
from nettlesome.quantities import UnitRange, IntRange, DateRange, Q_, Comparison
from nettlesome.statements import Statement


class TestQuantities:
    def test_unitregistry_imports_do_not_conflict(self, make_comparison):
        left = UnitRange(quantity=Q_("20 meters"), sign=">")
        right = make_comparison["meters"].quantity_range
        assert left.implies(right)
        assert left.pint_quantity == Q_("20 meters")

    def test_quantity_from_string(self):
        left = UnitRange(quantity="2000 days", sign="<")
        assert left.magnitude == 2000
        assert left.domain == S.Reals
        assert left.interval.start == 0

    def test_quantity_from_string_include_negatives(self):
        left = UnitRange(quantity="2000 days", sign="<", include_negatives=True)
        assert left.magnitude == 2000
        assert left.domain == S.Reals
        assert left.interval.start == -oo

    def test_no_contradiction_between_classes(self):
        left = UnitRange(quantity=Q_("2000 days"), sign="<")
        right = IntRange(quantity=2000, sign=">")
        assert right.q == 2000
        assert right.domain == S.Naturals0
        assert str(right) == "greater than 2000"
        assert left.magnitude == right.magnitude
        assert not left.contradicts(right)

    def test_contradiction_between_date_ranges(self):
        left = DateRange(quantity=date(2000, 1, 1), sign="<")
        right = DateRange(quantity=date(2020, 12, 12), sign=">")
        assert left.q == date(2000, 1, 1)
        assert left.domain == S.Naturals
        assert str(left) == "less than 2000-01-01"
        assert left.contradicts(right)


class TestCompareQuantities:
    def test_expression_comparison(self, make_comparison):
        assert (
            make_comparison["meters"].quantity_range.expression_comparison()
            == "at least 10 meter"
        )
        assert "20 foot" in repr(make_comparison["less_than_20"])
        assert (
            str(make_comparison["less_than_20"].quantity_range) == "less than 20 foot"
        )

    def test_compare_decimal_to_int(self, make_comparison):
        assert make_comparison["int_distance"].implies(
            make_comparison["float_distance"]
        )
        assert make_comparison["float_distance"].quantity_range.q == (
            make_comparison["int_distance"].quantity_range.q
        )

    def test_context_slots(self, make_comparison):
        assert len(make_comparison["meters"]) == 2

    def test_str_for_predicate_with_number_quantity(self, make_comparison):
        assert "distance between $place1 and $place2 was less than 20" in str(
            make_comparison["int_distance"]
        )
        assert "distance between $place1 and $place2 was less than 20.0" in str(
            make_comparison["float_distance"]
        )
        assert make_comparison["float_distance"].quantity_range.domain == S.Reals
        assert "distance between $place1 and $place2 was less than 20 foot" in str(
            make_comparison["less_than_20"]
        )

    def test_error_predicate_contradict_factor(self, make_comparison):
        with pytest.raises(TypeError):
            make_comparison["exact"].contradicts(
                Statement(
                    make_comparison["exact"],
                    terms=[Entity(name="thing"), Entity(name="place")],
                )
            )

    def test_comparison_from_expression_without_sign(self):
        comparison = Comparison(
            **{"content": "{}'s favorite number was", "expression": 42}
        )
        assert comparison.sign == "=="
        assert str(comparison) == "that {}'s favorite number was exactly equal to 42"
