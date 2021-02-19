from datetime import date
from math import exp

from pint import Quantity, quantity
import pytest
import sympy
from sympy import Eq, Interval, oo


from nettlesome.entities import Entity
from nettlesome.predicates import Predicate, Comparison, Q_
from nettlesome.statements import Statement


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

    def test_implication_with_no_truth_value(self):
        assert not self.whether_lived_at > self.lived_at
        assert self.lived_at > self.whether_lived_at

    def test_error_predicate_imply_factor(self):
        with pytest.raises(TypeError):
            self.same > Statement("$animal was a cat", terms=Entity("Mittens"))

    def test_same_does_not_contradict(self):
        again = Predicate("$thing was an apple")
        assert not self.same.contradicts(again)

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
