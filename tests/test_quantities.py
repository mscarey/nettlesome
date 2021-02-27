from datetime import date

from pint import UnitRegistry

from nettlesome.quantities import UnitRange, NumberRange, DateRange

ureg = UnitRegistry()
Q_ = ureg.Quantity


class TestQuantities:
    def test_no_contradiction_between_classes(self):
        left = UnitRange(quantity=Q_("2000 days"), sign="<")
        right = NumberRange(quantity=2000, sign=">")
        assert left.magnitude == right.magnitude
        assert not left.contradicts(right)

    def test_contradiction_between_date_ranges(self):
        left = DateRange(quantity=date(2000, 1, 1), sign="<")
        right = DateRange(quantity=date(2020, 12, 12), sign=">")
        assert left.contradicts(right)