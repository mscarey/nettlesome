from datetime import date

from nettlesome import predicates
from nettlesome.quantities import UnitRange, NumberRange, DateRange, Q_


class TestQuantities:
    def test_unitregistry_imports_do_not_conflict(self, make_comparison):
        left = UnitRange(quantity=Q_("20 meters"), sign=">")
        right = make_comparison["meters"].quantity_range
        assert left.implies(right)

    def test_quantity_from_string(self):
        left = UnitRange(quantity="2000 days", sign="<")
        assert left.magnitude == 2000

    def test_no_contradiction_between_classes(self):
        left = UnitRange(quantity=Q_("2000 days"), sign="<")
        right = NumberRange(quantity=2000, sign=">")
        assert left.magnitude == right.magnitude
        assert not left.contradicts(right)

    def test_contradiction_between_date_ranges(self):
        left = DateRange(quantity=date(2000, 1, 1), sign="<")
        right = DateRange(quantity=date(2020, 12, 12), sign=">")
        assert left.contradicts(right)