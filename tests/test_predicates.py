from datetime import date

from pint import Quantity, quantity
import pytest
import sympy
from sympy import Eq, Interval, oo


from nettlesome.entities import Entity
from nettlesome.predicates import Predicate, Comparison, Q_
from nettlesome.statements import Statement


class TestComparisons:
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
        assert scones.interval == sympy.Interval(-oo, 5, right_open=True)

    def test_comparison_with_string_for_float(self):
        scones = Comparison(
            "the number of scones $diner ate was", sign=">", expression="2.5"
        )
        assert scones.interval == sympy.Interval(2.5, oo, left_open=True)

    def test_comparison_interval(self):
        comparison = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression=Q_("20 miles"),
        )
        assert comparison.interval == Interval(20, oo, left_open=True)

    def test_comparison_not_equal(self):
        comparison = Comparison(
            "the distance between $place1 and $place2 was",
            sign="!=",
            expression=Q_("20 miles"),
        )
        assert comparison.interval == sympy.Union(
            Interval(-oo, 20, right_open=True), Interval(20, oo, left_open=True)
        )


class TestPredicates:
    def test_no_sign_allowed_for_predicate(self):
        with pytest.raises(TypeError):
            Predicate(
                "the date when $work was created was",
                sign=">=",
                expression=date(1978, 1, 1),
            )

    def test_term_positions(self):
        predicate = Predicate(
            template="$organizer1 and $organizer2 planned for $player1 to play $game with $player2."
        )
        assert predicate.term_positions() == {
            "organizer1": {0, 1},
            "organizer2": {0, 1},
            "player1": {2, 4},
            "game": {3},
            "player2": {2, 4},
        }

    def test_term_positions_with_repetition(self):
        predicate = Predicate(
            template="$organizer1 and $organizer2 planned for $organizer1 to play $game with $organizer2."
        )
        assert predicate.term_positions() == {
            "organizer1": {0, 1},
            "organizer2": {0, 1},
            "game": {2},
        }

    def test_term_permutations(self):
        predicate = Predicate(
            template="$organizer1 and $organizer2 planned for $player1 to play $game with $player2."
        )
        assert predicate.term_index_permutations() == [
            (0, 1, 2, 3, 4),
            (0, 1, 4, 3, 2),
            (1, 0, 2, 3, 4),
            (1, 0, 4, 3, 2),
        ]

    def test_term_permutations_with_repetition(self):
        predicate = Predicate(
            template="$organizer1 and $organizer2 planned for $organizer1 to play $game with $organizer2."
        )
        assert predicate.term_index_permutations() == [
            (0, 1, 2),
            (1, 0, 2),
        ]

    def test_convert_false_statement_about_quantity_to_obverse(self):
        distance = Comparison(
            "the distance between $place1 and $place2 was",
            truth=False,
            sign=">",
            expression=Q_("35 feet"),
        )
        assert distance.truth is True
        assert distance.sign == "<="
        assert isinstance(distance.expression, Quantity)
        assert str(distance.expression) == "35 foot"

    def test_string_for_date_as_expression(self):
        copyright_date_range = Comparison(
            "the date when $work was created was",
            sign=">=",
            expression=date(1978, 1, 1),
        )
        assert str(copyright_date_range).endswith("1978-01-01")


class TestCompare:
    same = Predicate("$thing was an apple")
    lived_at = Predicate("$person lived at $place")
    whether_lived_at = Predicate("$person lived at $place", truth=None)

    @pytest.mark.skip("placeholders break comparison")
    def test_predicate_content_comparison(self):
        lived_at = Predicate("$person lived at $place")
        also_lived_at = Predicate("$resident lived at $house")
        assert lived_at.content == also_lived_at.content

    def test_expression_comparison(self, make_comparison):
        assert make_comparison["meters"].expression_comparison() == "at least 10 meter"
        assert (
            make_comparison["less_than_20"].expression_comparison()
            == "less than 20 foot"
        )

    def test_predicate_has_no_expression_comparison(self):
        with pytest.raises(AttributeError):
            self.same.expression_comparison() == ""

    def test_context_slots(self, make_comparison):
        assert len(make_comparison["meters"]) == 2

    def test_str_for_predicate_with_number_quantity(self, make_comparison):
        assert "distance between $place1 and $place2 was less than 20" in str(
            make_comparison["int_distance"]
        )
        assert "distance between $place1 and $place2 was less than 20.0" in str(
            make_comparison["float_distance"]
        )
        assert "distance between $place1 and $place2 was less than 20 foot" in str(
            make_comparison["less_than_20"]
        )

    def test_template_singular_by_default(self):
        predicate = Predicate("$people were in $city")
        assert str(predicate.template) == 'StatementTemplate("$people was in $city")'

    @pytest.mark.parametrize(
        "context, expected",
        [
            (
                [Entity(name="the book", plural=False)],
                "<the book> was names, towns,",
            ),
            (
                [Entity(name="the book's listings", plural=True)],
                "<the book's listings> were names, towns,",
            ),
        ],
    )
    def test_make_str_plural(self, context, expected):
        phrase = (
            "$thing were names, towns, and telephone numbers of telephone subscribers"
        )
        predicate = Predicate(phrase)
        with_context = predicate.content_with_terms(context)
        assert with_context.startswith(expected)

    def test_str_not_equal(self, make_comparison):
        assert (
            "the distance between $place1 and $place2 was not equal to 35 foot"
            in str(make_comparison["not_equal"])
        )

    def test_negated_method(self, make_comparison):
        assert make_comparison["less"].negated().means(make_comparison["more"])
        as_false = make_comparison["exact"].negated()
        assert (
            str(as_false)
            == "that the distance between $place1 and $place2 was not equal to 25 foot"
        )

    def test_predicate_equality(self):
        assert self.same.means(self.same)

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

    def test_error_predicate_means_fact(self, make_predicate):
        with pytest.raises(TypeError):
            make_predicate["crime"].means(Statement("any text"))

    def test_same_meaning_float_and_int(self, make_comparison):
        """
        These now evaluate equal even though their equal quantities are different types
        """
        assert make_comparison["int_distance"].means(make_comparison["float_distance"])

    def test_no_equality_with_inconsistent_dimensionality(self, make_comparison):
        assert not make_comparison["more"].means(make_comparison["acres"])

    def test_different_truth_value_prevents_equality(self, make_predicate):
        assert not make_predicate["murder"].means(make_predicate["murder_whether"])
        assert not make_predicate["murder_false"].means(
            make_predicate["murder_whether"]
        )
        assert not make_predicate["murder_false"].means(make_predicate["murder"])

    def test_term_placeholders_do_not_change_result(self):
        left = Predicate(
            template="$organizer1 and $organizer2 planned for $player1 to play $game with $player2."
        )
        right = Predicate(
            template="$promoter1 and $promoter2 planned for $player1 to play $chess with $player2."
        )
        assert left.means(right)

    def test_term_positions_change_result(self):
        left = Predicate(
            template="$organizer1 and $organizer2 planned for $player1 to play $game with $player2."
        )
        right = Predicate(
            template="$organizer1 and $organizer2 planned for $organizer1 to play $game with $organizer2."
        )
        assert not left.means(right)

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

    def test_implication_with_no_truth_value(self):
        assert not self.whether_lived_at > self.lived_at
        assert self.lived_at > self.whether_lived_at

    def test_error_predicate_imply_factor(self):
        with pytest.raises(TypeError):
            self.same > Statement("$animal was a cat", terms=Entity("Mittens"))

    def test_implication_due_to_dates(self):
        copyright_date_range = Comparison(
            "the date when $work was created was",
            sign=">=",
            expression=date(1978, 1, 1),
        )
        copyright_date_specific = Comparison(
            "the date when $work was created was",
            sign="=",
            expression=date(1980, 6, 20),
        )
        assert copyright_date_specific.implies(copyright_date_range)

    def test_same_does_not_contradict(self):
        again = Predicate("$thing was an apple")
        assert not self.same.contradicts(again)

    def test_not_more_does_not_contradict_less(self, make_comparison):
        assert not make_comparison["not_more"].contradicts(make_comparison["less"])

    def test_irrelevant_does_not_contradict(self, make_comparison):
        assert not self.same.contradicts(make_comparison["less"])

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

    def test_error_predicate_contradict_factor(self, make_comparison):
        with pytest.raises(TypeError):
            make_comparison["exact"].contradicts(
                Statement(
                    make_comparison["exact"], terms=[Entity("thing"), Entity("place")]
                )
            )

    def test_no_contradiction_with_no_truth_value(self):
        assert not self.whether_lived_at.contradicts(self.lived_at)
        assert not self.lived_at.contradicts(self.whether_lived_at)

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


class TestQuantities:
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
        assert comparison.excludes_other_quantity(comparison_opposite) is False

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
        result = comparison.convert_other_quantity(comparison_km.expression)
        assert Q_("18 miles") < result < Q_("19 miles")

    def test_cannot_convert_date_to_time_period(self):
        time = Comparison(
            "the time $object took to biodegrade was",
            sign=">",
            expression=Q_("2000 years"),
        )
        with pytest.raises(TypeError):
            time.convert_other_quantity(date(2020, 1, 1))

    def test_cannot_convert_time_period_to_date(self):
        time = Comparison(
            "the date $buyer bought $object was",
            sign=">",
            expression=date(2020, 1, 1),
        )
        with pytest.raises(TypeError):
            time.convert_other_quantity(date(2020, 1, 1))

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
        assert not number.consistent_dimensionality(distance)
        assert not distance.consistent_dimensionality(number)

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
        assert not number.consistent_dimensionality(day)
        assert not day.consistent_dimensionality(number)

    def test_quantity_comparison_to_predicate(self):
        distance = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression="20 miles",
        )
        predicate = Predicate("the distance between $place1 and $place2 was")
        assert not distance.compare_other_quantity(predicate)
