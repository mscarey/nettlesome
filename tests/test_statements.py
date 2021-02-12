import operator

import pytest

from nettlesome.comparable import ContextRegister, FactorSequence, means
from nettlesome.terms import Term
from nettlesome.predicates import Comparison, Q_, Predicate
from nettlesome.statements import Statement


class TestStatements:
    def test_Statement(self):
        """
        Check that terms is created as a (hashable) tuple, not list
        """
        shooting = Statement(
            Predicate("$shooter shot $victim"),
            terms=[Term("alice"), Term("bob")],
        )
        assert isinstance(shooting.terms, tuple)

    def test_string_representation_of_factor(self):
        city = Predicate("$place was a city")
        statement = Statement(city, terms=Term("New York"))
        assert "<New York> was a city" in str(statement)

    def test_string_representation_of_absent_factor(self):
        predicate = Predicate("$company was the best brand")
        statement = Statement(predicate, terms=Term("Acme"), absent=True)
        assert "absence of the statement" in str(statement).lower()

    def test_string_no_truth_value(self):
        predicate = Predicate("$bird came before $ovum", truth=None)
        statement = Statement(predicate, terms=[Term("the chicken"), Term("the egg")])
        assert "whether <the chicken> came before <the egg>" in str(statement)

    def test_terms_param_can_be_dict(self):
        predicate = Predicate("$advisor told $employer to hire $applicant")
        three_entities = Statement(
            predicate,
            terms={
                "advisor": Term("Alice"),
                "employer": Term("Bob"),
                "applicant": Term("Craig"),
            },
        )
        assert (
            "Statement that <Alice> told <Bob> to hire <Craig>".lower()
            in str(three_entities).lower()
        )

    def test_string_for_fact_with_identical_terms(self):
        devon = Term("Devon", generic=True)
        elaine = Term("Elaine", generic=True)
        opened_account = Statement(
            Predicate("$applicant opened a bank account for $applicant and $cosigner"),
            terms=(devon, elaine),
        )
        assert "<Devon> opened a bank account for <Devon> and <Elaine>" in str(
            opened_account
        )

    def test_complex_fact_no_line_break_in_predicate(self):
        """
        Tests that the string representation of this Holding's only input
        Fact does not contain indented new lines, except in the "SPECIFIC
        CONTEXT" part, if present.

        The representation of the Exhibit mentioned in the Fact should
        not introduce any indented lines inside the Fact's string.
        """
        predicate_shot = Predicate("$shooter shot $victim")
        predicate_told = Predicate("$speaker told $hearer $statement")
        shot = Statement(predicate_shot, terms=[Term("Alice"), Term("Bob")])
        told = Statement(predicate_told, terms=[Term("Henry"), Term("Jenna"), shot])

        fact_text = str(told)
        if "SPECIFIC CONTEXT" in fact_text:
            fact_text = fact_text.split("SPECIFIC CONTEXT")[0].strip()
        assert "\n  " not in fact_text

    def test_new_context_replace_fact(self):
        predicate_shot = Predicate("$shooter shot $victim")
        predicate_no_gun = Predicate("$suspect had a gun", truth=False)
        predicate_told = Predicate("$speaker told $hearer $statement")
        shot = Statement(predicate_shot, terms=[Term("Alice"), Term("Bob")])
        told = Statement(predicate_told, terms=[Term("Henry"), Term("Jenna"), shot])
        no_gun = Statement(predicate_no_gun, terms=Term("Dan"))

        changes = ContextRegister.from_lists(
            [Term("Alice"), Term("Henry"), Term("Jenna"), shot],
            [Term("Dan"), Term("Leslie"), Term("Mike"), no_gun],
        )
        result = told.new_context(changes)
        assert (
            "told <Mike> the Statement it was false that <Dan> had a gun".lower()
            in result.short_string.lower()
        )

    def test_too_much_info_to_change_context(self):
        """Test that a list of terms to replace requires "changes" to be consistent."""
        statement = Statement(
            "$person1 loved $person2",
            terms=[Term("Donald"), Term("Daisy")],
        )
        with pytest.raises(ValueError):
            statement.new_context(
                changes=Term("Mickey"),
                terms_to_replace=[Term("Donald"), Term("Daisy")],
            )

    def test_get_factor_from_recursive_search(self):
        predicate_shot = Predicate("$shooter shot $victim")
        predicate_told = Predicate("$speaker told $hearer $statement")
        shot = Statement(predicate_shot, terms=[Term("Alice"), Term("Bob")])
        told = Statement(predicate_told, terms=[Term("Henry"), Term("Jenna"), shot])
        factors = told.recursive_factors
        assert factors["<Alice>"].name == "Alice"

    def test_new_concrete_context(self):
        """
        "Dragonfly Inn" is still a string representation of an Term
        object, but it's not in angle brackets because it can't be
        replaced by another Term object without changing the meaning
        of the Fact.
        """
        predicate = Predicate("$place was a hotel")
        statement = Statement(predicate, terms=[Term("Independence Inn")])
        different = statement.new_context(Term("Dragonfly Inn", generic=False))
        assert "Dragonfly Inn was a hotel" in str(different)

    def test_new_statement_from_entities(self):
        predicate = Predicate("$person managed $place")
        statement = Statement(predicate, terms=[Term("Steve Jobs"), Term("Apple")])
        different = statement.new_context([Term("Darth Vader"), Term("the Death Star")])
        assert "<Darth Vader> managed" in str(different)
        assert isinstance(different.terms, FactorSequence)

    def test_term_cannot_be_string(self):
        city = Predicate("$place was a city")
        with pytest.raises(TypeError):
            Statement(city, terms=["New York"])

    def test_concrete_to_abstract(self):
        predicate = Predicate("$person had a farm")
        statement = Statement(predicate, terms=Term("Old MacDonald"))
        assert str(statement).lower() == "the statement that <old macdonald> had a farm"
        generic_str = str(statement.make_generic()).lower()
        assert generic_str == "<the statement that <old macdonald> had a farm>"

    def test_entity_slots_as_length_of_factor(self):
        predicate = Predicate("$person had a farm")
        statement = Statement(predicate, terms=Term("Old MacDonald"))
        assert len(statement.predicate) == 1
        assert len(statement) == 1

    def test_predicate_with_entities(self):
        predicate = Predicate("$person1 and $person2 went up the hill")
        terms = [Term("Jack"), Term("Jill")]
        assert (
            predicate.content_with_terms(terms) == "<Jack> and <Jill> went up the hill"
        )

    def test_factor_terms_do_not_match_predicate(self):
        """
        predicate has only one slot for context factors, but
        this tells it to look for three.
        """
        with pytest.raises(ValueError):
            Statement(
                Predicate("$sentence had only one context term"),
                terms=[Term("Al"), Term("Ed"), Term("Xu")],
            )

    def test_repeated_placeholder_in_fact(self):
        predicate = Predicate(
            "the precise formulation "
            "of ${program}'s code was necessary for $program to work",
            truth=False,
        )
        fact = Statement(predicate, terms=Term("Lotus 1-2-3"))

        assert fact.short_string.lower() == (
            "the statement it was false that the precise formulation "
            "of <lotus 1-2-3>'s code was necessary for <lotus 1-2-3> to work"
        )
        assert len(fact.terms) == 1


class TestSameMeaning:
    def test_equality_factor_from_same_predicate(self):
        predicate = Predicate("$speaker greeted $listener")
        fact = Statement(predicate, terms=[Term("Al"), Term("Meg")])
        fact_b = Statement(predicate, terms=[Term("Al"), Term("Meg")])
        assert fact.means(fact_b)

    def test_equality_factor_from_equal_predicate(self):
        predicate = Predicate("$speaker greeted $listener")
        equal_predicate = Predicate("$speaker greeted $listener")
        fact = Statement(predicate, terms=[Term("Al"), Term("Meg")])
        fact_b = Statement(equal_predicate, terms=[Term("Al"), Term("Meg")])
        assert fact.means(fact_b)

    def test_equality_because_factors_are_generic_entities(self):
        predicate = Predicate("$speaker greeted $listener")
        fact = Statement(predicate, terms=[Term("Al"), Term("Meg")])
        fact_b = Statement(predicate, terms=[Term("Ed"), Term("Imogene")])
        assert fact.means(fact_b)

    def test_unequal_because_a_factor_is_not_generic(self):
        predicate = Predicate("$speaker greeted $listener")
        fact = Statement(predicate, terms=[Term("Al"), Term("Meg")])
        fact_b = Statement(
            predicate, terms=[Term("Ed"), Term("Imogene", generic=False)]
        )
        assert not fact.means(fact_b)

    def test_true_and_false_generic_factors_equal(self):
        predicate = Predicate("$speaker greeted $listener")
        false_predicate = Predicate("$speaker greeted $listener", truth=False)
        fact = Statement(predicate, terms=[Term("Al"), Term("Meg")], generic=True)
        false_fact = Statement(
            false_predicate, terms=[Term("Ed"), Term("Imogene")], generic=True
        )
        assert fact.means(false_fact)

    def test_generic_factors_with_different_text_equal(self):
        predicate = Predicate("$speaker greeted $listener")
        different_predicate = Predicate("$speaker attacked $listener")
        fact = Statement(predicate, terms=[Term("Al"), Term("Meg")], generic=True)
        different_fact = Statement(
            different_predicate, terms=[Term("Al"), Term("Meg")], generic=True
        )
        assert fact.means(different_fact)

    def test_equal_referencing_diffent_generic_factors(self):
        predicate = Predicate("$speaker greeted $listener")
        fact = Statement(predicate, terms=[Term("Al"), Term("Meg")])
        fact_b = Statement(predicate, terms=[Term("Jim"), Term("Ned")])
        assert fact.means(fact_b)

    def test_factor_reciprocal_unequal(self):
        predicate = Predicate("$advisor told $employer to hire $applicant")
        three_entities = Statement(
            predicate,
            terms={
                "advisor": Term("Alice"),
                "employer": Term("Bob"),
                "applicant": Term("Craig"),
            },
        )
        repeating_predicate = Predicate("$applicant told $employer to hire $applicant")
        two_entities = Statement(
            repeating_predicate,
            terms={
                "applicant": Term("Alice"),
                "employer": Term("Bob"),
            },
        )
        assert not three_entities.means(two_entities)

    def test_factor_different_predicate_truth_unequal(self):
        predicate = Predicate("$shooter shot $victim")
        false_predicate = Predicate("$shooter shot $victim", truth=False)
        fact = Statement(predicate, terms=[Term("Al"), Term("Meg")])
        fact_b = Statement(false_predicate, terms=[Term("Al"), Term("Meg")])
        assert not fact.means(fact_b)

    def test_unequal_because_one_factor_is_absent(self):
        predicate = Predicate("$shooter shot $victim")
        fact = Statement(predicate, terms=[Term("Al"), Term("Meg")])
        fact_b = Statement(predicate, terms=[Term("Al"), Term("Meg")], absent=True)
        assert not fact.means(fact_b)

    def test_equal_with_different_generic_subfactors(self):
        shot_predicate = Predicate("$shooter shot $victim")
        shot_fact = Statement(shot_predicate, terms=[Term("Alice"), Term("Bob")])
        murder_predicate = Predicate("$shooter murdered $victim")
        murder_fact = Statement(murder_predicate, terms=[Term("Alice"), Term("Bob")])
        relevant_predicate = Predicate("$clue was relevant to $conclusion")
        relevant_fact = Statement(relevant_predicate, terms=[shot_fact, murder_fact])

        changes = ContextRegister.from_lists(
            [Term("Alice"), Term("Bob")], [Term("Deb"), Term("Eve")]
        )
        new_fact = relevant_fact.new_context(changes)

        assert relevant_fact.means(new_fact)

    def test_interchangeable_concrete_terms(self):
        """Detect that placeholders differing only by a final digit are interchangeable."""
        ann = Term("Ann", generic=False)
        bob = Term("Bob", generic=False)

        ann_and_bob_were_family = Statement(
            Predicate("$relative1 and $relative2 both were members of the same family"),
            terms=(ann, bob),
        )
        bob_and_ann_were_family = Statement(
            Predicate("$relative1 and $relative2 both were members of the same family"),
            terms=(bob, ann),
        )

        assert ann_and_bob_were_family.means(bob_and_ann_were_family)

    def test_means_despite_plural(self):
        directory = Term("the telephone directory", plural=False)
        listings = Term("the telephone listings", plural=True)
        directory_original = Statement(
            Predicate("$thing was original"), terms=directory
        )
        listings_original = Statement(Predicate("$thing were original"), terms=listings)
        assert directory_original.means(listings_original)

    def test_same_meaning_no_terms(self):
        assert Statement(Predicate("good morning")).means(
            Statement(Predicate("good morning"))
        )


class TestImplication:
    def test_statement_implies_none(self):
        assert Statement(Predicate("good morning")).implies(None)

    def test_specific_statement_implies_generic(self):
        concrete = Statement(Predicate("$person was a person"), terms=Term("Alice"))
        generic = Statement(
            Predicate("$person was a person"), terms=Term("Alice"), generic=True
        )
        assert concrete > generic
        assert not generic > concrete

    def test_specific_implies_generic_explain(self):
        concrete = Statement(Predicate("$person was a person"), terms=Term("Alice"))
        generic = Statement(
            Predicate("$person was a person"), terms=Term("Alice"), generic=True
        )

        answer = concrete.explain_implication(generic)
        assert (str(concrete), generic) in answer.items()

    def test_specific_implies_generic_form_of_another_fact(self):
        concrete = Statement(Predicate("$person was a person"), terms=Term("Alice"))
        generic_merperson = Statement(
            Predicate("$person was a merperson"), terms=Term("Alice"), generic=True
        )

        assert concrete > generic_merperson

    def test_specific_fact_does_not_imply_generic_entity(self):
        concrete = Statement(Predicate("$person was a person"), terms=Term("Alice"))
        assert not concrete > Term("Tim")

    def test_statement_does_not_imply_comparison(self):
        phrase = Comparison(
            "the distance north from $south to $north was",
            sign=">",
            expression="180 miles",
        )
        statement = Statement(phrase, terms=[Term("Austin"), Term("Dallas")])

        with pytest.raises(TypeError):
            statement > phrase

    def test_statement_implies_because_of_quantity(self):
        statement = Statement(
            Comparison(
                "the distance north from $south to $north was",
                sign=">",
                expression="180 miles",
            ),
            terms=[Term("Austin"), Term("Dallas")],
        )
        statement_meters = Statement(
            Comparison(
                "the distance north from $south to $north was",
                sign=">",
                expression="180 meters",
            ),
            terms=[Term("Austin"), Term("Dallas")],
        )

        assert statement > statement_meters

    def test_statement_implies_with_int_and_float(self):
        statement = Statement(
            Comparison(
                "the distance north from $south to $north was",
                sign=">",
                expression=180,
            ),
            terms=[Term("Austin"), Term("Dallas")],
        )
        statement_float = Statement(
            Comparison(
                "the distance north from $south to $north was",
                sign=">",
                expression=170.22,
            ),
            terms=[Term("Austin"), Term("Dallas")],
        )

        assert statement > statement_float

    def test_statement_implies_with_ints(self):
        statement_higher = Statement(
            Comparison(
                "the distance north from $south to $north was",
                sign=">",
                expression=180,
            ),
            terms=[Term("Austin"), Term("Dallas")],
        )
        statement_lower = Statement(
            Comparison(
                "the distance north from $south to $north was",
                sign=">",
                expression=170,
            ),
            terms=[Term("Austin"), Term("Dallas")],
        )

        assert statement_lower < statement_higher

    def test_statement_implies_no_truth_value(self):
        fact = Statement(Predicate("$person was a person"), terms=Term("Alice"))
        whether = Statement(
            Predicate("$person was a person", truth=None), terms=Term("Alice")
        )
        assert fact >= whether
        assert not whether > fact

    def test_comparison_implies_no_truth_value(self):
        fact = Statement(
            Comparison("${person}'s weight was", sign=">", expression="150 pounds"),
            terms=Term("Alice"),
        )
        whether = Statement(
            Comparison(
                "${person}'s weight was", sign=">", expression="150 pounds", truth=None
            ),
            terms=Term("Alice"),
        )

        assert fact >= whether
        assert not whether > fact

    def test_factor_implies_because_of_exact_quantity(self):
        fact_exact = Statement(
            Comparison("${person}'s height was", sign="=", expression="66 inches"),
            terms=Term("Alice"),
        )
        fact_greater = Statement(
            Comparison("${person}'s height was", sign=">", expression="60 inches"),
            terms=Term("Alice"),
        )

        assert fact_exact >= fact_greater
        assert not fact_greater >= fact_exact

    def test_no_implication_pint_quantity_and_int(self):
        fact_exact = Statement(
            Comparison("${person}'s height was", sign="=", expression=66),
            terms=Term("Alice"),
        )
        fact_greater = Statement(
            Comparison("${person}'s height was", sign=">", expression="60 inches"),
            terms=Term("Alice"),
        )
        assert not fact_exact >= fact_greater
        assert not fact_greater >= fact_exact

    def test_absent_factor_implies_absent_factor_with_lesser_quantity(self):
        absent_broader = Statement(
            Comparison(
                "the distance north from $south to $north was",
                sign="<",
                expression="200 miles",
            ),
            terms=[Term("Austin"), Term("Dallas")],
            absent=True,
        )
        absent_narrower = Statement(
            Comparison(
                "the distance north from $south to $north was",
                sign="<",
                expression="50 miles",
            ),
            terms=[Term("Austin"), Term("Dallas")],
            absent=True,
        )
        assert absent_broader >= absent_narrower
        assert not absent_narrower >= absent_broader

    def test_equal_factors_not_gt(self):
        fact = Statement(Predicate("$person was a person"), terms=Term("Alice"))
        assert fact >= fact
        assert fact <= fact
        assert not fact > fact

    shot_predicate = Predicate("$shooter shot $victim")
    shot_fact = Statement(shot_predicate, terms=[Term("Alice"), Term("Bob")])
    murder_predicate = Predicate("$shooter murdered $victim")
    murder_fact = Statement(murder_predicate, terms=[Term("Alice"), Term("Bob")])
    relevant_predicate = Predicate("$clue was relevant to $conclusion")
    relevant_fact = Statement(relevant_predicate, terms=[shot_fact, murder_fact])
    predicate_whether = Predicate("$clue was relevant to $conclusion", truth=None)
    relevant_whether = Statement(predicate_whether, terms=[shot_fact, murder_fact])

    def test_implication_complex_whether(self):

        assert self.relevant_fact > self.relevant_whether

    def test_implication_complex_explain(self):
        """
        Check that when .implies() provides a ContextRegister as an "explanation",
        it uses elements only from the left as keys and from the right as values.
        """

        context_names = ContextRegister()
        context_names.insert_pair(key=Term("Alice"), value=Term("Craig"))
        context_names.insert_pair(key=Term("Bob"), value=Term("Dan"))

        complex_whether = self.relevant_whether.new_context(context_names)
        explanation = self.relevant_fact.explain_implication(complex_whether)
        assert (str[Term("Alice")], Term("Craig")) in explanation.items()
        assert (
            str(explanation)
            == "ContextRegister(<Alice> is like <Craig>, <Bob> is like <Dan>)"
        )
        assert (str[Term("Craig")], Term("Alice")) not in explanation.items()
        assert (str[Term("Alice")], Term("Craig")) in explanation.items()

    def test_context_registers_for_complex_comparison(self):
        context_names = ContextRegister()
        context_names.insert_pair(key=Term("Alice"), value=Term("Bob"))
        context_names.insert_pair(key=Term("Bob"), value=Term("Alice"))

        swapped_entities = self.relevant_fact.new_context(context_names)
        gen = swapped_entities._context_registers(self.relevant_fact, operator.ge)
        register = next(gen)
        assert register.matches.get("<Alice>") == Term("Bob")

    def test_no_implication_complex(self):
        murder_fact = Statement(
            self.murder_predicate, terms=[Term("Alice"), Term("Craig")]
        )
        relevant_to_craig = Statement(
            self.relevant_predicate, terms=[self.shot_fact, murder_fact]
        )

        assert not self.relevant_fact >= relevant_to_craig

    def test_implied_by(self):
        assert self.relevant_whether.implied_by(self.relevant_fact)

    def test_explanation_implied_by(self):
        explanation = self.relevant_whether.explain_implied_by(self.relevant_fact)
        assert explanation["<Alice>"].name == "Alice"


class TestContradiction:
    def test_factor_different_predicate_truth_contradicts(self):
        predicate = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression=Q_("30 miles"),
        )
        predicate_opposite = Comparison(
            "the distance between $place1 and $place2 was",
            sign="<",
            expression=Q_("30 miles"),
        )
        terms = [Term("New York"), Term("Los Angeles")]
        fact = Statement(predicate, terms=terms)
        fact_opposite = Statement(predicate_opposite, terms=terms)

        assert fact.contradicts(fact_opposite)
        assert fact_opposite.contradicts(fact)

    def test_same_predicate_true_vs_false(self):
        fact = Statement(Predicate("$person was a person"), terms=Term("Alice"))
        fiction = Statement(
            Predicate("$person was a person", truth=False), terms=Term("Alice")
        )
        assert fact.contradicts(fiction)
        assert fact.truth != fiction.truth

    def test_factor_does_not_contradict_predicate(self):
        predicate = Predicate("$person was a person")
        fact = Statement(predicate, terms=Term("Alice"))

        with pytest.raises(TypeError):
            fact.contradicts(predicate)

    def test_factor_contradiction_absent_predicate(self):
        predicate = Predicate("$person was a person")
        fact = Statement(predicate, terms=Term("Alice"))
        absent_fact = Statement(predicate, terms=Term("Alice"), absent=True)

        assert fact.contradicts(absent_fact)
        assert absent_fact.contradicts(fact)

    def test_absences_of_contradictory_facts_consistent(self):
        predicate = Comparison(
            "the distance between $place1 and $place2 was",
            sign=">",
            expression=Q_("30 miles"),
        )
        predicate_opposite = Comparison(
            "the distance between $place1 and $place2 was",
            sign="<",
            expression=Q_("30 miles"),
        )
        terms = [Term("New York"), Term("Los Angeles")]
        fact = Statement(predicate, terms=terms, absent=True)
        fact_opposite = Statement(predicate_opposite, terms=terms, absent=True)

        assert not fact.contradicts(fact_opposite)
        assert not fact_opposite.contradicts(fact)

    def test_factor_no_contradiction_no_truth_value(self):
        fact = Statement(Predicate("$person was a person"), terms=Term("Alice"))
        fact_no_truth = Statement(
            Predicate("$person was a person"), terms=Term("Alice")
        )
        assert not fact.contradicts(fact_no_truth)
        assert not fact_no_truth.contradicts(fact)

    def test_broader_absent_factor_contradicts_quantity_statement(self):
        predicate_less = Comparison(
            "${vehicle}'s speed was",
            sign=">",
            expression=Q_("30 miles per hour"),
        )
        predicate_more = Comparison(
            "${vehicle}'s speed was",
            sign=">",
            expression=Q_("60 miles per hour"),
        )
        terms = [Term("the car")]
        absent_general_fact = Statement(predicate_less, terms=terms, absent=True)
        specific_fact = Statement(predicate_more, terms=terms)

        assert absent_general_fact.contradicts(specific_fact)
        assert specific_fact.contradicts(absent_general_fact)

    def test_less_specific_absent_contradicts_more_specific(self):
        predicate_less = Comparison(
            "${vehicle}'s speed was",
            sign="<",
            expression=Q_("30 miles per hour"),
        )
        predicate_more = Comparison(
            "${vehicle}'s speed was",
            sign="<",
            expression=Q_("60 miles per hour"),
        )
        terms = [Term("the car")]
        absent_general_fact = Statement(predicate_more, terms=terms, absent=True)
        specific_fact = Statement(predicate_less, terms=terms)

        assert absent_general_fact.contradicts(specific_fact)
        assert specific_fact.contradicts(absent_general_fact)

    def test_no_contradiction_with_more_specific_absent(self):
        predicate_less = Comparison(
            "${vehicle}'s speed was",
            sign="<",
            expression=Q_("30 miles per hour"),
        )
        predicate_more = Comparison(
            "${vehicle}'s speed was",
            sign="<",
            expression=Q_("60 miles per hour"),
        )
        terms = [Term("the car")]
        general_fact = Statement(predicate_more, terms=terms)
        absent_specific_fact = Statement(predicate_less, terms=terms, absent=True)

        assert not general_fact.contradicts(absent_specific_fact)
        assert not absent_specific_fact.contradicts(general_fact)

    def test_contradiction_complex(self):
        shot_predicate = Predicate("$shooter shot $victim")
        shot_fact = Statement(shot_predicate, terms=[Term("Alice"), Term("Bob")])
        murder_predicate = Predicate("$shooter murdered $victim")
        murder_fact = Statement(murder_predicate, terms=[Term("Alice"), Term("Bob")])
        relevant_predicate = Predicate("$clue was relevant to $conclusion")
        relevant_fact = Statement(relevant_predicate, terms=[shot_fact, murder_fact])
        irrelevant_predicate = Predicate(
            "$clue was relevant to $conclusion", truth=False
        )
        irrelevant_fact = Statement(
            irrelevant_predicate, terms=[shot_fact, murder_fact]
        )
        assert relevant_fact.contradicts(irrelevant_fact)

    def test_no_contradiction_complex(self):
        shot_predicate = Predicate("$shooter shot $victim")
        shot_fact = Statement(shot_predicate, terms=[Term("Alice"), Term("Bob")])
        murder_predicate = Predicate("$shooter murdered $victim")
        murder_fact = Statement(murder_predicate, terms=[Term("Alice"), Term("Bob")])
        murder_socrates = Statement(
            murder_predicate, terms=[Term("Alice"), Term("Socrates")]
        )
        relevant_predicate = Predicate("$clue was relevant to $conclusion")
        relevant_fact = Statement(relevant_predicate, terms=[shot_fact, murder_fact])
        irrelevant_predicate = Predicate(
            "$clue was relevant to $conclusion", truth=False
        )
        irrelevant_fact = Statement(
            irrelevant_predicate, terms=[shot_fact, murder_socrates]
        )
        assert not relevant_fact.contradicts(irrelevant_fact)
        assert not irrelevant_fact.contradicts(relevant_fact)

    def test_no_contradiction_of_None(self):
        shot_predicate = Predicate("$shooter shot $victim")
        shot_fact = Statement(shot_predicate, terms=[Term("Alice"), Term("Bob")])
        assert not shot_fact.contradicts(None)

    def test_contradicts_if_present_both_present(self):
        """
        Test a helper function that checks whether there would
        be a contradiction if neither Factor was "absent".
        """
        shot_fact = Statement(
            Predicate("$shooter shot $victim"), terms=[Term("Alice"), Term("Bob")]
        )
        shot_false = Statement(
            Predicate("$shooter shot $victim", truth=False),
            terms=[Term("Alice"), Term("Bob")],
        )
        assert shot_fact._contradicts_if_present(shot_false, context=ContextRegister())
        assert shot_false._contradicts_if_present(shot_fact, context=ContextRegister())

    def test_contradicts_if_present_one_absent(self):
        shot_fact = Statement(
            Predicate("$shooter shot $victim"), terms=[Term("Alice"), Term("Bob")]
        )
        shot_false = Statement(
            Predicate("$shooter shot $victim", truth=False),
            terms=[Term("Alice"), Term("Bob")],
            absent=True,
        )
        assert shot_fact._contradicts_if_present(shot_false, context=ContextRegister())
        assert shot_false._contradicts_if_present(shot_fact, context=ContextRegister())

    def test_false_does_not_contradict_absent(self):
        absent_fact = Statement(
            predicate=Predicate(
                template="${rural_s_telephone_directory} was copyrightable", truth=True
            ),
            terms=[Term(name="Rural's telephone directory")],
            absent=True,
        )
        false_fact = Statement(
            predicate=Predicate(
                template="${the_java_api} was copyrightable", truth=False
            ),
            terms=[Term(name="the Java API", generic=True, plural=False)],
            absent=False,
        )
        assert not false_fact.contradicts(absent_fact)
        assert not absent_fact.contradicts(false_fact)

    def test_inconsistent_statements_about_different_entities(self):
        """
        Alice and Bob are both generics. So it's possible to reach a
        contradiction if you assume they correspond to one another.
        """
        p_small_weight = Comparison(
            "the amount of gold $person possessed was",
            sign="<",
            expression=Q_("1 gram"),
        )
        p_large_weight = Comparison(
            "the amount of gold $person possessed was",
            sign=">=",
            expression=Q_("100 kilograms"),
        )
        alice = Term("Alice")
        bob = Term("Bob")
        alice_rich = Statement(p_large_weight, terms=alice)
        bob_poor = Statement(p_small_weight, terms=bob)
        assert alice_rich.contradicts(bob_poor)

    def test_inconsistent_statements_about_corresponding_entities(self):
        """
        Even though Alice and Bob are both generics, it's known that
        Alice in the first context corresponds with Alice in the second.
        So there's no contradiction.
        """
        p_small_weight = Comparison(
            "the amount of gold $person possessed was",
            sign="<",
            expression=Q_("1 gram"),
        )
        p_large_weight = Comparison(
            "the amount of gold $person possessed was",
            sign=">=",
            expression=Q_("100 kilograms"),
        )
        alice = Term("Alice")
        bob = Term("Bob")
        alice_rich = Statement(p_large_weight, terms=alice)
        bob_poor = Statement(p_small_weight, terms=bob)
        register = ContextRegister()
        register.insert_pair(alice, alice)
        assert not alice_rich.contradicts(bob_poor, context=register)

    def test_check_entity_consistency_true(self):
        left = Statement(
            Predicate("$shooter shot $victim"), terms=[Term("Alice"), Term("Bob")]
        )
        right = Statement(
            Predicate("$shooter shot $victim"), terms=[Term("Craig"), Term("Dan")]
        )
        register = ContextRegister.from_lists([Term("Alice")], [Term("Craig")])
        update = left.update_context_register(right, register, comparison=means)
        assert any(register is not None for register in update)

    def test_check_entity_consistency_false(self):
        left = Statement(
            Predicate("$shooter shot $victim"), terms=[Term("Alice"), Term("Bob")]
        )
        right = Statement(
            Predicate("$shooter shot $victim"), terms=[Term("Craig"), Term("Dan")]
        )
        register = ContextRegister.from_lists([Term("Alice")], [Term("Dan")])
        update = left.update_context_register(right, register, comparison=means)
        assert not any(register is not None for register in update)

    def test_entity_consistency_identity_not_equality(self):
        left = Statement(
            Predicate("$shooter shot $victim"), terms=[Term("Alice"), Term("Bob")]
        )
        right = Statement(
            Predicate("$shooter shot $victim"), terms=[Term("Craig"), Term("Dan")]
        )
        register = ContextRegister.from_lists([Term("Dan")], [Term("Dan")])
        update = left.update_context_register(right, register, comparison=means)
        assert not any(register is not None for register in update)

    def test_check_entity_consistency_type_error(self, make_factor, make_predicate):
        """
        There would be no TypeError if it used "means"
        instead of .gt. The comparison would just return False.
        """
        right = Statement(
            Predicate("$shooter shot $victim"), terms=[Term("Craig"), Term("Dan")]
        )
        register = ContextRegister.from_lists([Term("Dan")], [Term("Dan")])
        update = right.update_context_register(
            right.predicate,
            register,
            operator.gt,
        )
        with pytest.raises(TypeError):
            any(register is not None for register in update)


class TestConsistent:
    p_small_weight = Comparison(
        "the amount of gold $person possessed was",
        sign="<",
        expression=Q_("1 gram"),
    )
    p_large_weight = Comparison(
        "the amount of gold $person possessed was",
        sign=">=",
        expression=Q_("100 kilograms"),
    )
    small = Statement(p_large_weight, terms=Term("Alice"))
    big = Statement(p_small_weight, terms=Term("Bob"))

    def test_contradictory_facts_about_same_entity(self):
        register = ContextRegister()
        register.insert_pair(Term("Alice"), Term("Bob"))
        assert not self.small.consistent_with(self.big, register)
        explanations = list(
            self.small.explanations_consistent_with(self.big, context=register)
        )
        assert not explanations

    def test_factor_consistent_with_none(self):
        assert self.small.consistent_with(None)


class TestAddition:

    predicate_less = Comparison(
        "${vehicle}'s speed was",
        sign=">",
        expression=Q_("30 miles per hour"),
    )
    predicate_more = Comparison(
        "${vehicle}'s speed was",
        sign=">=",
        expression=Q_("60 miles per hour"),
    )
    general_fact = Statement(predicate_less, terms=Term("the car"))
    specific_fact = Statement(predicate_more, terms=Term("the motorcycle"))

    def test_addition_returns_broader_operand(self):
        answer = self.specific_fact + self.general_fact
        assert answer.means(self.specific_fact)

    def test_addition_uses_terms_from_left(self):
        answer = self.general_fact + self.specific_fact
        assert "<the car>" in str(answer)

    def test_add_unrelated_factors(self):
        murder = Statement(Predicate("$person committed a murder"), terms=Term("Al"))
        crime = Statement(Predicate("$person committed a crime"), terms=Term("Al"))
        assert murder + crime is None
        assert murder | crime is None

    def test_union_with_string_fails(self):
        murder = Statement(Predicate("$person committed a murder"), terms=Term("Al"))
        with pytest.raises(TypeError):
            murder | "a string"

    def test_union_same_as_adding(self):
        dave = Term("Dave")
        speed_template = "${driver}'s driving speed was"
        fast_fact = Statement(
            Comparison(speed_template, sign=">=", expression="100 miles per hour"),
            terms=dave,
        )
        slow_fact = Statement(
            Comparison(
                speed_template,
                sign=">=",
                expression="20 miles per hour",
            ),
            terms=dave,
        )
        new = fast_fact | slow_fact
        assert new.means(fast_fact)

    def test_union_uses_terms_from_left(self):
        new = self.general_fact | self.specific_fact
        assert new.means(self.specific_fact)
        assert new.terms[0].name == "the car"
