from datetime import date

from pint import UnitRegistry, Quantity
import pytest
import sympy
from sympy import Interval, oo

from nettlesome.predicates import Predicate
from nettlesome.quantities import Comparison, NumberRange
from nettlesome.statements import Statement

ureg = UnitRegistry()
Q_ = ureg.Quantity


class TestQuantityInterval:
    def test_comparison_with_wrong_comparison_symbol(self):
        with pytest.raises(ValueError):
            _ = Comparison(
                "the height of {} was {}",
                sign=">>",
                expression=Q_("160 centimeters"),
            )

    def test_comparison_with_string_for_int(self):
        scones = Comparison(
            "the number of scones $diner ate was", sign="<", expression="5"
        )
        assert scones.interval == sympy.Interval(0, 5, right_open=True)

    def test_comparison_with_string_for_float(self):
        scones = Comparison(
            "the number of scones $diner ate was", sign=">", expression="2.5"
        )
        assert scones.interval == sympy.Interval(2.5, oo, left_open=True)

    def test_comparison_interval_does_not_include_negatives(self):
        party = Comparison(
            "the number of people at the party was", sign="<", expression=25
        )
        assert -5 not in party.interval
        assert party.quantity_range.include_negatives is False

    def test_comparison_negative_magnitude(self):
        comparison = Comparison(
            "the balance in the bank account was", sign="<=", expression=-100
        )
        assert comparison.quantity_range.magnitude == -100
        assert comparison.quantity_range.include_negatives is True

    def test_comparison_interval(self):
        comparison = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression=Q_("20 miles"),
        )
        assert comparison.interval == Interval(20, oo, left_open=True)
        assert 'quantity="20 mile' in repr(comparison)

    def test_negated_method(self, make_comparison):
        as_false = make_comparison["exact"].negated()
        assert (
            str(as_false)
            == "that the distance between $place1 and $place2 was not equal to 25 foot"
        )

    def test_negated_method_same_meaning(self, make_comparison):
        assert make_comparison["less"].negated().means(make_comparison["more"])

    def test_convert_false_statement_about_quantity_to_obverse(self):
        distance = Comparison(
            "the distance between $place1 and $place2 was",
            truth=False,
            sign=">",
            expression=Q_("35 feet"),
        )
        assert distance.truth is True
        assert distance.sign == "<="
        assert isinstance(distance.quantity, Quantity)
        assert str(distance.quantity) == "35 foot"

    def test_string_for_date_as_expression(self):
        copyright_date_range = Comparison(
            "the date when $work was created was",
            sign=">=",
            expression=date(1978, 1, 1),
        )
        assert str(copyright_date_range).endswith("1978-01-01")

    def test_comparison_not_equal(self):
        comparison = Comparison(
            "the distance between $place1 and $place2 was",
            sign="!=",
            expression=Q_("20 miles"),
        )
        assert comparison.interval == sympy.Union(
            Interval(0, 20, right_open=True), Interval(20, oo, left_open=True)
        )

    def test_str_not_equal(self, make_comparison):
        assert (
            "the distance between $place1 and $place2 was not equal to 35 foot"
            in str(make_comparison["not_equal"])
        )

    def test_content_not_ending_with_was(self):
        with pytest.raises(ValueError):
            Comparison(
                "$person drove for",
                sign=">=",
                expression=Q_("20 miles"),
            )

    def test_cannot_reuse_quantity_range_for_number(self):
        dogs = Comparison("the number of dogs was", sign=">", expression="3 gallons")
        with pytest.raises(TypeError):
            NumberRange(quantity=dogs.quantity)


class TestCompareQuantities:
    def test_does_not_exclude_other_quantity(self):
        comparison = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression=Q_("20 miles"),
        )
        comparison_opposite = Comparison(
            "the distance between $place1 and $place2 was",
            sign="<",
            expression=Q_("30 miles"),
        )
        left = comparison.quantity_range
        right = comparison_opposite.quantity_range
        assert left.contradicts(right.interval) is False

    def test_convert_quantity_of_Comparison(self):
        comparison = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression=Q_("20 miles"),
        )
        comparison_km = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression=Q_("30 kilometers"),
        )
        result = comparison.quantity_range.get_unit_converted_interval(
            comparison_km.quantity_range
        )
        assert 18 < result.left < 19

    def test_cannot_convert_date_to_time_period(self):
        time = Comparison(
            "the time $object took to biodegrade was",
            sign=">",
            expression=Q_("2000 years"),
        )
        day = Comparison(
            "the day was",
            sign="=",
            expression=date(2020, 1, 1),
        )
        with pytest.raises(TypeError):
            time.quantity_range.get_unit_converted_interval(day.quantity_range)

    def test_inconsistent_dimensionality_quantity(self):
        number = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression=20,
        )
        distance = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression=Q_("20 miles"),
        )
        assert not number.quantity_range.consistent_dimensionality(
            distance.quantity_range
        )
        assert not distance.quantity_range.consistent_dimensionality(
            number.quantity_range
        )

    def test_inconsistent_dimensionality_date(self):
        number = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression=20,
        )
        day = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression=date(2000, 1, 1),
        )
        assert not number.quantity_range.consistent_dimensionality(day.quantity_range)
        assert not day.quantity_range.consistent_dimensionality(number.quantity_range)

    def test_quantity_comparison_to_predicate(self):
        distance = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression="20 miles",
        )
        predicate = Predicate("the distance between $place1 and $place2 was")
        assert not distance.quantity_range.implies(predicate)

    def test_compare_intervals_different_units(self):
        miles = Comparison("the distance was", sign="<", expression=Q_("30 miles"))
        kilos = Comparison("the distance was", sign="<", expression=Q_("40 kilometers"))
        assert kilos.quantity_range.implies(miles.quantity_range)


class TestSameMeaning:
    def test_same_meaning_float_and_int(self, make_comparison):
        """
        These now evaluate equal even though their equal quantities are different types
        """
        assert make_comparison["int_distance"].means(make_comparison["float_distance"])

    def test_no_equality_with_inconsistent_dimensionality(self, make_comparison):
        assert not make_comparison["more"].means(make_comparison["acres"])


class TestImplication:
    def test_predicate_not_same_with_interchangeable_terms(self):
        interchangeable = Comparison(
            "the distance between $place1 and $place2 was",
            sign="<",
            expression=Q_("20 feet"),
        )
        not_interchangeable = Comparison(
            "the distance between $west and $east was",
            sign="<",
            expression=Q_("20 feet"),
        )
        assert not interchangeable.means(not_interchangeable)

    def test_error_predicate_means_statement(self, make_predicate):
        with pytest.raises(TypeError):
            make_predicate["crime"].means(Statement("any text"))

    def test_greater_than_because_of_quantity(self, make_comparison):
        assert make_comparison["less_than_20"] > make_comparison["less"]
        assert make_comparison["less_than_20"] != make_comparison["less"]

    def test_greater_float_and_int(self, make_comparison):
        assert make_comparison["int_distance"] > make_comparison["int_higher"]
        assert make_comparison["int_higher"] < make_comparison["int_distance"]

    def test_any_truth_value_implies_none(self, make_predicate):
        assert make_predicate["murder"] > make_predicate["murder_whether"]
        assert make_predicate["murder_false"] > make_predicate["murder_whether"]

    def test_no_implication_by_exact_quantity(self, make_predicate):
        assert not make_predicate["quantity=3"] > make_predicate["quantity>5"]

    def test_no_implication_of_exact_quantity(self, make_predicate):
        assert not make_predicate["quantity>5"] > make_predicate["quantity=3"]

    def test_no_implication_by_greater_or_equal_quantity(self, make_predicate):
        assert not make_predicate["quantity>=4"] > make_predicate["quantity>5"]

    def test_no_implication_of_greater_or_equal_quantity(self):
        less = Comparison(template="The number of mice was", sign=">", expression=4)
        more = Comparison(template="The number of mice was", sign=">=", expression=5)
        assert not less.implies(more)

    def test_no_contradiction_inconsistent_dimensions(self):
        equal = Comparison(
            "${defendant}'s sentence was", sign="=", expression="8 years"
        )
        less = Comparison(
            "${defendant}'s sentence was", sign="<=", expression="10 parsecs"
        )
        assert not equal.contradicts(less)
        assert not equal.implies(less)

    def test_equal_implies_greater_or_equal(self, make_comparison):
        assert make_comparison["exact"] > make_comparison["less"]

    def test_implication_with_not_equal(self, make_comparison):
        assert make_comparison["less"] > make_comparison["not_equal"]

    def test_no_implication_with_inconsistent_dimensionality(self, make_comparison):
        assert not make_comparison["less"] >= make_comparison["acres"]
        assert not make_comparison["less"] <= make_comparison["acres"]

    def test_implication_due_to_dates(self):
        copyright_date_range = Comparison(
            "the date when $work was created was",
            sign=">=",
            expression="1978-01-01",
        )
        copyright_date_specific = Comparison(
            "the date when $work was created was",
            sign="=",
            expression=date(1980, 6, 20),
        )
        assert copyright_date_specific.implies(copyright_date_range)

    def test_not_equal_does_not_imply(self):
        yards = Comparison(
            "the length of the football field was",
            sign="!=",
            expression="100 yards",
        )
        meters = Comparison(
            "the length of the football field was",
            sign="!=",
            expression="80 meters",
        )
        assert not yards >= meters

    def test_not_equal_implies(self):
        meters = Comparison(
            "the length of the football field was",
            sign="!=",
            expression="1000 meter",
        )
        kilometers = Comparison(
            "the length of the football field was",
            sign="!=",
            expression="1 kilometer",
        )
        assert meters.means(kilometers)

    def test_same_volume(self):
        volume_in_liters = Comparison(
            "the volume of fuel in the tank was", sign="=", expression="10 liters"
        )
        volume_in_milliliters = Comparison(
            "the volume of fuel in the tank was",
            sign="=",
            expression="10000 milliliters",
        )
        assert volume_in_liters.means(volume_in_milliliters)


class TestContradiction:
    def test_not_more_does_not_contradict_less(self, make_comparison):
        assert not make_comparison["not_more"].contradicts(make_comparison["less"])

    def test_predicate_does_not_contradict(self, make_comparison):
        irrelevant = Predicate("things happened")
        assert not irrelevant.contradicts(make_comparison["less"])

    def test_contradiction_by_exact(self, make_comparison):
        assert make_comparison["exact"].contradicts(make_comparison["less_than_20"])
        assert make_comparison["less_than_20"].contradicts(make_comparison["exact"])

    def test_contradiction_by_equal_quantity(self, make_predicate):
        assert make_predicate["quantity=3"].contradicts(make_predicate["quantity>5"])

    def test_contradiction_of_equal_quantity(self, make_predicate):
        assert make_predicate["quantity>5"].contradicts(make_predicate["quantity=3"])

    def test_no_contradiction_by_greater_or_equal_quantity(self, make_predicate):
        assert not make_predicate["quantity>=4"].contradicts(
            make_predicate["quantity>5"]
        )

    def test_no_contradiction_of_greater_or_equal_quantity(self, make_predicate):
        assert not make_predicate["quantity>5"].contradicts(
            make_predicate["quantity>=4"]
        )

    def test_no_contradiction_with_inconsistent_dimensionality(self, make_comparison):
        assert not make_comparison["meters"].contradicts(make_comparison["acres"])
        assert not make_comparison["acres"].contradicts(make_comparison["meters"])

    def test_contradiction_with_quantity(self, make_comparison):
        assert make_comparison["less_than_20"].contradicts(make_comparison["meters"])

    def test_contradictory_date_ranges(self):
        later = Comparison(
            "the date $dentist became a licensed dentist was",
            sign=">",
            expression=date(2010, 1, 1),
        )
        earlier = Comparison(
            "the date $dentist became a licensed dentist was",
            sign="<",
            expression=date(1990, 1, 1),
        )
        assert later.contradicts(earlier)
        assert earlier.contradicts(later)

    def test_no_contradiction_without_truth_value(self):
        later = Comparison(
            "the date $dentist became a licensed dentist was",
            sign=">",
            expression=date(2010, 1, 1),
            truth=None,
        )
        earlier = Comparison(
            "the date $dentist became a licensed dentist was",
            sign="<",
            expression=date(1990, 1, 1),
        )
        assert not later.contradicts(earlier)
        assert not earlier.contradicts(later)

    def test_no_contradiction_date_and_time_period(self):
        later = Comparison(
            "the date $dentist became a licensed dentist was",
            sign=">",
            expression=date(2010, 1, 1),
        )
        earlier = Comparison(
            "the date $dentist became a licensed dentist was",
            sign="<",
            expression="2000 years",
        )
        assert not later.contradicts(earlier)
        assert not earlier.contradicts(later)

    def test_no_contradiction_irrelevant_quantities(self):
        more_cows = Comparison(
            "the number of cows $person owned was",
            sign=">",
            expression=10,
        )
        fewer_horses = Comparison(
            "the number of horses $person owned was",
            sign="<",
            expression=3,
        )
        assert not more_cows.contradicts(fewer_horses)
        assert not fewer_horses.contradicts(more_cows)

    def test_no_contradiction_of_predicate(self):
        more_cows = Comparison(
            "the number of cows $person owned was",
            sign=">",
            expression=10,
        )
        no_cows = Predicate("the number of cows $person owned was", truth=False)
        assert not more_cows.contradicts(no_cows)
        assert not no_cows.contradicts(more_cows)

    def test_contradiction_exact_different_unit(self):
        acres = Comparison(
            "the size of the farm was", sign=">", expression=Q_("2000 acres")
        )
        kilometers = Comparison(
            "the size of the farm was", sign="=", expression=Q_("2 square kilometers")
        )
        assert acres.contradicts(kilometers)

    def test_no_contradiction_exact_different_unit(self):
        acres = Comparison(
            "the size of the farm was", sign=">", expression=Q_("20 acres")
        )
        kilometers = Comparison(
            "the size of the farm was", sign="=", expression=Q_("100 square kilometers")
        )
        assert not acres.contradicts(kilometers)

    def test_reuse_quantity_range_for_contradiction(self):
        dogs = Comparison("the number of dogs was", sign=">", expression=3)
        cats = Comparison("the number of cats was", quantity_range=dogs.quantity_range)
        fewer_cats = Comparison("the number of cats was", sign="<", expression=3)
        assert cats.contradicts(fewer_cats)
