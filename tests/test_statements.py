import operator

import pytest

from nettlesome.terms import (
    ContextRegister,
    TermSequence,
    Explanation,
    means,
    expand_string_from_source,
)
from nettlesome.entities import Entity
from nettlesome.predicates import Predicate
from nettlesome.quantities import Comparison, Q_
from nettlesome.statements import Statement


class TestStatements:
    def test_Statement(self):
        """
        Check that terms is created as a list, not TermSequence.
        """
        shooting = Statement(
            predicate=Predicate(content="$shooter shot $victim"),
            terms=[Entity(name="alice"), Entity(name="bob")],
        )
        assert isinstance(shooting.terms, list)

    def test_cannot_use_string_for_term(self):
        predicate = Predicate(content="$person visited $place")
        entity = Entity(name="Austin")
        with pytest.raises(AttributeError):
            Statement(
                predicate=predicate,
                terms=[entity, "Dallas as a string"],
            )

    def test_string_representation_of_factor(self):
        city = Predicate(content="$place was a city")
        statement = Statement(predicate=city, terms=Entity(name="New York"))
        assert "<New York> was a city" in str(statement)
        assert ", terms=[Entity(" in repr(statement)
        assert "name='New York'" in repr(statement)

    def test_get_terms(self, make_statement):
        terms = make_statement["friends"].terms
        assert terms[0].name == "Alice"

    def test_string_representation_of_absent_factor(self):
        predicate = Predicate(content="$company was the best brand")
        statement = Statement(
            predicate=predicate, terms=Entity(name="Acme"), absent=True
        )
        assert "absence of the statement" in str(statement).lower()

    def test_string_no_truth_value(self):
        predicate = Predicate(content="$bird came before $ovum", truth=None)
        statement = Statement(
            predicate=predicate,
            terms=[Entity(name="the chicken"), Entity(name="the egg")],
        )
        assert "whether <the chicken> came before <the egg>" in str(statement)

    def test_terms_param_can_be_dict(self):
        predicate = Predicate(content="$advisor told $employer to hire $applicant")
        three_entities = Statement(
            predicate=predicate,
            terms={
                "advisor": Entity(name="Alice"),
                "employer": Entity(name="Bob"),
                "applicant": Entity(name="Craig"),
            },
        )
        assert (
            "Statement that <Alice> told <Bob> to hire <Craig>".lower()
            in str(three_entities).lower()
        )

    def test_string_for_fact_with_identical_terms(self):
        devon = Entity(name="Devon", generic=True)
        elaine = Entity(name="Elaine", generic=True)
        opened_account = Statement(
            predicate=Predicate(
                content="$applicant opened a bank account for $applicant and $cosigner"
            ),
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
        predicate_shot = Predicate(content="$shooter shot $victim")
        predicate_told = Predicate(content="$speaker told $hearer $statement")
        shot = Statement(
            predicate=predicate_shot, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        told = Statement(
            predicate=predicate_told,
            terms=[Entity(name="Henry"), Entity(name="Jenna"), shot],
        )

        fact_text = str(told)
        if "SPECIFIC CONTEXT" in fact_text:
            fact_text = fact_text.split("SPECIFIC CONTEXT")[0].strip()
        assert "\n  " not in fact_text

    def test_new_context_replace_fact(self):
        predicate_shot = Predicate(content="$shooter shot $victim")
        predicate_no_gun = Predicate(content="$suspect had a gun", truth=False)
        predicate_told = Predicate(content="$speaker told $hearer $statement")
        shot = Statement(
            predicate=predicate_shot, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        told = Statement(
            predicate=predicate_told,
            terms=[Entity(name="Henry"), Entity(name="Jenna"), shot],
        )
        no_gun = Statement(predicate=predicate_no_gun, terms=Entity(name="Dan"))

        changes = ContextRegister.from_lists(
            [Entity(name="Alice"), Entity(name="Henry"), Entity(name="Jenna"), shot],
            [Entity(name="Dan"), Entity(name="Leslie"), Entity(name="Mike"), no_gun],
        )
        result = told.new_context(changes)
        assert (
            "told <Mike> the Statement it was false that <Dan> had a gun".lower()
            in result.short_string.lower()
        )

    def test_new_context_from_term_list(self):
        predicate_shot = Predicate(content="$shooter shot $victim")
        shot = Statement(
            predicate=predicate_shot, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        changes = [Entity(name="Leslie"), Entity(name="Mike")]
        result = shot.new_context(changes)
        assert (
            "the Statement that <leslie> shot <mike>".lower()
            in result.short_string.lower()
        )

    def test_new_context_from_string_list(self):
        predicate_shot = Predicate(content="$shooter shot $victim")
        predicate_no_gun = Predicate(content="$suspect had a gun", truth=False)
        predicate_told = Predicate(content="$speaker told $hearer $statement")
        shot = Statement(
            predicate=predicate_shot, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        no_gun = Statement(predicate=predicate_no_gun, terms=Entity(name="Dan"))
        told = Statement(
            predicate=predicate_told,
            terms=[Entity(name="Henry"), Entity(name="Jenna"), no_gun],
        )
        new = shot.new_context(changes=["Henry", Entity(name="Jenna")], source=told)
        assert "<henry> shot <jenna>" in new.short_string.lower()

    def test_new_context_changes_as_strings_replacements_as_entities(self):
        predicate_shot = Predicate(content="$shooter shot $victim")
        predicate_no_gun = Predicate(content="$suspect had a gun", truth=False)
        predicate_told = Predicate(content="$speaker told $hearer $statement")
        shot = Statement(
            predicate=predicate_shot, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        no_gun = Statement(predicate=predicate_no_gun, terms=Entity(name="Dan"))
        told = Statement(
            predicate=predicate_told,
            terms=[Entity(name="Henry"), Entity(name="Jenna"), no_gun],
        )
        new = shot.new_context(
            changes=["Henry", "Jenna"],
            terms_to_replace=[Entity(name="Alice"), Entity(name="Bob")],
            source=told,
        )
        assert str(new).lower() == "the statement that <henry> shot <jenna>"

    def test_new_context_use_terms_to_replace(self):
        predicate_shot = Predicate(content="$shooter shot $victim")
        shot = Statement(
            predicate=predicate_shot, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        new = shot.new_context(
            changes=[Entity(name="Henry"), Entity(name="Jenna")],
            terms_to_replace=[Entity(name="Alice"), Entity(name="Bob")],
        )
        assert "<henry> shot <jenna>" in new.short_string.lower()

    def test_new_context_wrong_list_length(self):
        predicate_shot = Predicate(content="$shooter shot $victim")
        shot = Statement(
            predicate=predicate_shot, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        changes = [Entity(name="Leslie"), Entity(name="Mike"), Entity(name="Dan")]
        with pytest.raises(ValueError):
            shot.new_context(changes)

    def test_too_much_info_to_change_context(self):
        """Test that new Statement is created with truncated ContextRegister."""
        statement = Statement(
            predicate="$person1 loved $person2",
            terms=[Entity(name="Donald"), Entity(name="Daisy")],
        )
        new = statement.new_context(
            changes=[Entity(name="Mickey")],
            terms_to_replace=[Entity(name="Donald"), Entity(name="Daisy")],
        )
        assert "<Mickey> loved <Daisy>".lower() in str(new).lower()

    def test_get_factor_from_recursive_search(self):
        predicate_shot = Predicate(content="$shooter shot $victim")
        predicate_told = Predicate(content="$speaker told $hearer $statement")
        shot = Statement(
            predicate=predicate_shot, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        told = Statement(
            predicate=predicate_told,
            terms=[Entity(name="Henry"), Entity(name="Jenna"), shot],
        )
        factors = told.recursive_terms
        assert factors["<Alice>"].name == "Alice"

    def test_new_concrete_context(self):
        """
        "Dragonfly Inn" is still a string representation of an Term
        object, but it's not in angle brackets because it can't be
        replaced by another Term object without changing the meaning
        of the Fact.
        """
        predicate = Predicate(content="$place was a hotel")
        statement = Statement(
            predicate=predicate, terms=[Entity(name="Independence Inn")]
        )
        different = statement.new_context([Entity(name="Dragonfly Inn", generic=False)])
        assert "Dragonfly Inn was a hotel" in str(different)

    def test_new_statement_from_entities(self):
        predicate = Predicate(content="$person managed $place")
        statement = Statement(
            predicate=predicate, terms=[Entity(name="Steve Jobs"), Entity(name="Apple")]
        )
        different = statement.new_context(
            [Entity(name="Darth Vader"), Entity(name="the Death Star")]
        )
        assert "<Darth Vader> managed" in str(different)
        assert isinstance(different.terms, list)
        assert isinstance(different.term_sequence, TermSequence)

    def test_term_cannot_be_string(self):
        city = Predicate(content="$place was a city")
        with pytest.raises(TypeError):
            Statement(city, terms=["New York"])

    def test_expand_string_from_statement(self, make_complex_fact):
        source = make_complex_fact["relevant_murder"]
        expanded = expand_string_from_source(term="Alice", source=source)
        assert expanded.name == "Alice"

    def test_expand_string_from_statement_with_key(self, make_complex_fact):
        source = make_complex_fact["relevant_murder"]
        expanded = expand_string_from_source(term="<Alice>", source=source)
        assert expanded.name == "Alice"

    def test_dont_expand_string_from_statement(self, make_complex_fact):
        source = make_complex_fact["relevant_murder"]
        with pytest.raises(ValueError):
            expand_string_from_source(term="Jim", source=source)

    def test_concrete_to_abstract(self):
        predicate = Predicate(content="$person had a farm")
        statement = Statement(predicate=predicate, terms=Entity(name="Old MacDonald"))
        assert str(statement).lower() == "the statement that <old macdonald> had a farm"
        generic_str = str(statement.make_generic()).lower()
        assert generic_str == "<the statement that <old macdonald> had a farm>"

    def test_entity_slots_as_length_of_factor(self):
        predicate = Predicate(content="$person had a farm")
        statement = Statement(predicate=predicate, terms=Entity(name="Old MacDonald"))
        assert len(statement.predicate) == 1
        assert len(statement) == 1

    def test_predicate_with_entities(self):
        predicate = Predicate(content="$person1 and $person2 went up the hill")
        terms = [Entity(name="Jack"), Entity(name="Jill")]
        assert (
            predicate._content_with_terms(terms) == "<Jack> and <Jill> went up the hill"
        )

    def test_factor_terms_do_not_match_predicate(self):
        """
        predicate has only one slot for context factors, but
        this tells it to look for three.
        """
        with pytest.raises(ValueError):
            Statement(
                predicate=Predicate(content="$sentence had only one context term"),
                terms=[Entity(name="Al"), Entity(name="Ed"), Entity(name="Xu")],
            )

    def test_repeated_placeholder_in_fact(self):
        predicate = Predicate(
            content="the precise formulation "
            "of ${program}'s code was necessary for $program to work",
            truth=False,
        )
        fact = Statement(predicate=predicate, terms=Entity(name="Lotus 1-2-3"))

        assert fact.short_string.lower() == (
            "the statement it was false that the precise formulation "
            "of <lotus 1-2-3>'s code was necessary for <lotus 1-2-3> to work"
        )
        assert len(fact.terms) == 1

    def test_indented_string(self):
        sued = Statement(
            predicate="$plaintiff sued $defendant for unpaid taxes",
            terms=[
                Entity(name="the State of Texas", generic=False),
                Entity(name="Bob"),
            ],
        )
        text = sued.str_with_concrete_context
        assert "\n" in text
        assert "the State of Texas" in text.split("SPECIFIC CONTEXT")[1]


class TestSameMeaning:
    def test_equality_factor_from_same_predicate(self):
        predicate = Predicate(content="$speaker greeted $listener")
        fact = Statement(
            predicate=predicate, terms=[Entity(name="Al"), Entity(name="Meg")]
        )
        fact_b = Statement(
            predicate=predicate, terms=[Entity(name="Al"), Entity(name="Meg")]
        )
        assert fact.means(fact_b)

    def test_equality_factor_from_equal_predicate(self):
        predicate = Predicate(content="$speaker greeted $listener")
        equal_predicate = Predicate(content="$speaker greeted $listener")
        fact = Statement(
            predicate=predicate, terms=[Entity(name="Al"), Entity(name="Meg")]
        )
        fact_b = Statement(
            predicate=equal_predicate, terms=[Entity(name="Al"), Entity(name="Meg")]
        )
        assert fact.means(fact_b)

    def test_equality_because_factors_are_generic_entities(self):
        predicate = Predicate(content="$speaker greeted $listener")
        fact = Statement(
            predicate=predicate, terms=[Entity(name="Al"), Entity(name="Meg")]
        )
        fact_b = Statement(
            predicate=predicate, terms=[Entity(name="Ed"), Entity(name="Imogene")]
        )
        assert fact.means(fact_b)

    def test_unequal_because_a_factor_is_not_generic(self):
        predicate = Predicate(content="$speaker greeted $listener")
        fact = Statement(
            predicate=predicate, terms=[Entity(name="Al"), Entity(name="Meg")]
        )
        fact_b = Statement(
            predicate=predicate,
            terms=[Entity(name="Ed"), Entity(name="Imogene", generic=False)],
        )
        assert not fact.means(fact_b)

    def test_true_and_false_generic_terms_equal(self):
        predicate = Predicate(content="$speaker greeted $listener")
        false_predicate = Predicate(content="$speaker greeted $listener", truth=False)
        fact = Statement(
            predicate=predicate,
            terms=[Entity(name="Al"), Entity(name="Meg")],
            generic=True,
        )
        false_fact = Statement(
            predicate=false_predicate,
            terms=[Entity(name="Ed"), Entity(name="Imogene")],
            generic=True,
        )
        assert fact.means(false_fact)

    def test_generic_terms_with_different_text_equal(self):
        predicate = Predicate(content="$speaker greeted $listener")
        different_predicate = Predicate(content="$speaker attacked $listener")
        fact = Statement(
            predicate=predicate,
            terms=[Entity(name="Al"), Entity(name="Meg")],
            generic=True,
        )
        different_fact = Statement(
            predicate=different_predicate,
            terms=[Entity(name="Al"), Entity(name="Meg")],
            generic=True,
        )
        assert fact.means(different_fact)

    def test_equal_referencing_diffent_generic_terms(self):
        predicate = Predicate(content="$speaker greeted $listener")
        fact = Statement(
            predicate=predicate, terms=[Entity(name="Al"), Entity(name="Meg")]
        )
        fact_b = Statement(
            predicate=predicate, terms=[Entity(name="Jim"), Entity(name="Ned")]
        )
        assert fact.means(fact_b)

    def test_factor_reciprocal_unequal(self):
        predicate = Predicate(content="$advisor told $employer to hire $applicant")
        three_entities = Statement(
            predicate=predicate,
            terms={
                "advisor": Entity(name="Alice"),
                "employer": Entity(name="Bob"),
                "applicant": Entity(name="Craig"),
            },
        )
        repeating_predicate = Predicate(
            content="$applicant told $employer to hire $applicant"
        )
        two_entities = Statement(
            predicate=repeating_predicate,
            terms={
                "applicant": Entity(name="Alice"),
                "employer": Entity(name="Bob"),
            },
        )
        assert not three_entities.means(two_entities)

    def test_factor_different_predicate_truth_unequal(self):
        predicate = Predicate(content="$shooter shot $victim")
        false_predicate = Predicate(content="$shooter shot $victim", truth=False)
        fact = Statement(
            predicate=predicate, terms=[Entity(name="Al"), Entity(name="Meg")]
        )
        fact_b = Statement(
            predicate=false_predicate, terms=[Entity(name="Al"), Entity(name="Meg")]
        )
        assert not fact.means(fact_b)

    def test_unequal_because_one_factor_is_absent(self):
        predicate = Predicate(content="$shooter shot $victim")
        fact = Statement(
            predicate=predicate, terms=[Entity(name="Al"), Entity(name="Meg")]
        )
        fact_b = Statement(
            predicate=predicate,
            terms=[Entity(name="Al"), Entity(name="Meg")],
            absent=True,
        )
        assert not fact.means(fact_b)

    def test_equal_with_different_generic_subfactors(self):
        shot_predicate = Predicate(content="$shooter shot $victim")
        shot_fact = Statement(
            predicate=shot_predicate, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        murder_predicate = Predicate(content="$shooter murdered $victim")
        murder_fact = Statement(
            predicate=murder_predicate, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        relevant_predicate = Predicate(content="$clue was relevant to $conclusion")
        relevant_fact = Statement(
            predicate=relevant_predicate, terms=[shot_fact, murder_fact]
        )

        changes = ContextRegister.from_lists(
            [Entity(name="Alice"), Entity(name="Bob")],
            [Entity(name="Deb"), Entity(name="Eve")],
        )
        new_fact = relevant_fact.new_context(changes)

        assert relevant_fact.means(new_fact)
        explanation = relevant_fact.explain_same_meaning(new_fact)
        assert explanation.context["<Alice>"].name == "Deb"

    def test_interchangeable_concrete_terms(self):
        """
        Detect that placeholders differing only by a final digit are interchangeable.

        There will be no keys in the explanation because no terms are generic.
        """
        ann = Entity(name="Ann", generic=False)
        bob = Entity(name="Bob", generic=False)

        ann_and_bob_were_family = Statement(
            predicate=Predicate(
                content="$relative1 and $relative2 both were members of the same family"
            ),
            terms=(ann, bob),
        )
        bob_and_ann_were_family = Statement(
            predicate=Predicate(
                content="$relative1 and $relative2 both were members of the same family"
            ),
            terms=(bob, ann),
        )

        assert ann_and_bob_were_family.means(bob_and_ann_were_family)
        explanation = ann_and_bob_were_family.explain_same_meaning(
            bob_and_ann_were_family
        )
        assert len(explanation.context) == 0

    def test_means_despite_plural(self):
        directory = Entity(name="the telephone directory", plural=False)
        listings = Entity(name="the telephone listings", plural=True)
        directory_original = Statement(
            predicate=Predicate(content="$thing was original"), terms=directory
        )
        listings_original = Statement(
            predicate=Predicate(content="$thing were original"), terms=listings
        )
        assert directory_original.means(listings_original)
        assert "plural=True" in repr(listings_original)

    def test_same_meaning_no_terms(self):
        assert Statement(predicate=Predicate(content="good morning")).means(
            Statement(predicate=Predicate(content="good morning"))
        )

    def test_changing_order_of_concrete_terms_changes_meaning(self):
        ann = Entity(name="Ann", generic=False)
        bob = Entity(name="Bob", generic=False)
        parent_sentence = Predicate(content="$mother was ${child}'s parent")
        ann_parent = Statement(predicate=parent_sentence, terms=(ann, bob))
        bob_parent = Statement(predicate=parent_sentence, terms=(bob, ann))
        assert not ann_parent.means(bob_parent)
        assert "generic=False" in repr(ann_parent)


class TestImplication:
    def test_statement_implies_none(self):
        assert Statement(predicate=Predicate(content="good morning")).implies(None)
        assert Statement(predicate=Predicate(content="good morning")) > None

    def test_specific_statement_implies_generic(self):
        concrete = Statement(
            predicate=Predicate(content="$person was a person"),
            terms=Entity(name="Alice"),
        )
        generic = Statement(
            predicate=Predicate(content="$person was a person"),
            terms=Entity(name="Alice"),
            generic=True,
        )
        assert concrete > generic
        assert not generic > concrete

    def test_specific_implies_generic_explain(self):
        concrete = Statement(
            predicate=Predicate(content="$person was a person"),
            terms=Entity(name="Alice"),
        )
        generic = Statement(
            predicate=Predicate(content="$person was a person"),
            terms=Entity(name="Alice"),
            generic=True,
        )

        answer = concrete.explain_implication(generic)
        assert (str(concrete), generic) in answer.context.items()

    def test_specific_implies_generic_form_of_another_fact(self):
        concrete = Statement(
            predicate=Predicate(content="$person was a person"),
            terms=Entity(name="Alice"),
        )
        generic_merperson = Statement(
            predicate=Predicate(content="$person was a merperson"),
            terms=Entity(name="Alice"),
            generic=True,
        )

        assert concrete > generic_merperson

    def test_specific_fact_does_not_imply_generic_entity(self):
        concrete = Statement(
            predicate=Predicate(content="$person was a person"),
            terms=Entity(name="Alice"),
        )
        assert not concrete > Entity(name="Tim")

    def test_statement_does_not_imply_comparison(self):
        phrase = Comparison(
            content="the distance north from $south to $north was",
            sign=">",
            expression="180 miles",
        )
        statement = Statement(
            predicate=phrase, terms=[Entity(name="Austin"), Entity(name="Dallas")]
        )

        with pytest.raises(TypeError):
            statement > phrase

    def test_statement_implies_because_of_quantity(self):
        statement = Statement(
            predicate=Comparison(
                content="the distance north from $south to $north was",
                sign=">",
                expression="180 miles",
            ),
            terms=[Entity(name="Austin"), Entity(name="Dallas")],
        )
        statement_meters = Statement(
            predicate=Comparison(
                content="the distance north from $south to $north was",
                sign=">",
                expression="180 meters",
            ),
            terms=[Entity(name="Austin"), Entity(name="Dallas")],
        )

        assert statement > statement_meters

    def test_statement_implies_with_int_and_float(self):
        statement = Statement(
            predicate=Comparison(
                content="the distance north from $south to $north was",
                sign=">",
                expression=180,
            ),
            terms=[Entity(name="Austin"), Entity(name="Dallas")],
        )
        statement_float = Statement(
            predicate=Comparison(
                content="the distance north from $south to $north was",
                sign=">",
                expression=170.22,
            ),
            terms=[Entity(name="Austin"), Entity(name="Dallas")],
        )

        assert statement > statement_float

    def test_statement_implies_with_ints(self):
        statement_higher = Statement(
            predicate=Comparison(
                content="the distance north from $south to $north was",
                sign=">",
                expression=180,
            ),
            terms=[Entity(name="Austin"), Entity(name="Dallas")],
        )
        statement_lower = Statement(
            predicate=Comparison(
                content="the distance north from $south to $north was",
                sign=">",
                expression=170,
            ),
            terms=[Entity(name="Austin"), Entity(name="Dallas")],
        )

        assert statement_lower < statement_higher

    def test_statement_implies_no_truth_value(self):
        fact = Statement(
            predicate=Predicate(content="$person was a person"),
            terms=Entity(name="Alice"),
        )
        whether = Statement(
            predicate=Predicate(content="$person was a person", truth=None),
            terms=Entity(name="Alice"),
        )
        assert fact >= whether
        assert not whether > fact

    def test_comparison_implies_no_truth_value(self):
        fact = Statement(
            predicate=Comparison(
                content="${person}'s weight was", sign=">", expression="150 pounds"
            ),
            terms=Entity(name="Alice"),
        )
        whether = Statement(
            predicate=Comparison(
                content="${person}'s weight was",
                sign=">",
                expression="150 pounds",
                truth=None,
            ),
            terms=Entity(name="Alice"),
        )

        assert fact >= whether
        assert not whether > fact

    def test_factor_implies_because_of_exact_quantity(self):
        fact_exact = Statement(
            predicate=Comparison(
                content="${person}'s height was", sign="=", expression="66 inches"
            ),
            terms=Entity(name="Alice"),
        )
        fact_greater = Statement(
            predicate=Comparison(
                content="${person}'s height was", sign=">", expression="60 inches"
            ),
            terms=Entity(name="Alice"),
        )

        assert fact_exact >= fact_greater
        assert not fact_greater >= fact_exact

    def test_no_implication_pint_quantity_and_int(self):
        fact_exact = Statement(
            predicate=Comparison(
                content="${person}'s height was", sign="=", expression=66
            ),
            terms=Entity(name="Alice"),
        )
        fact_greater = Statement(
            predicate=Comparison(
                content="${person}'s height was", sign=">", expression="60 inches"
            ),
            terms=Entity(name="Alice"),
        )
        assert not fact_exact >= fact_greater
        assert not fact_greater >= fact_exact

    def test_absent_factor_implies_absent_factor_with_lesser_quantity(self):
        absent_broader = Statement(
            predicate=Comparison(
                content="the distance north from $south to $north was",
                sign="<",
                expression="200 miles",
            ),
            terms=[Entity(name="Austin"), Entity(name="Dallas")],
            absent=True,
        )
        absent_narrower = Statement(
            predicate=Comparison(
                content="the distance north from $south to $north was",
                sign="<",
                expression="50 miles",
            ),
            terms=[Entity(name="Austin"), Entity(name="Dallas")],
            absent=True,
        )
        assert absent_broader >= absent_narrower
        assert not absent_narrower >= absent_broader

    def test_equal_factors_not_gt(self):
        fact = Statement(
            predicate=Predicate(content="$person was a person"),
            terms=Entity(name="Alice"),
        )
        assert fact >= fact
        assert fact <= fact
        assert not fact > fact

    shot_predicate = Predicate(content="$shooter shot $victim")
    shot_fact = Statement(
        predicate=shot_predicate, terms=[Entity(name="Alice"), Entity(name="Bob")]
    )
    murder_predicate = Predicate(content="$shooter murdered $victim")
    murder_fact = Statement(
        predicate=murder_predicate, terms=[Entity(name="Alice"), Entity(name="Bob")]
    )
    relevant_predicate = Predicate(content="$clue was relevant to $conclusion")
    relevant_fact = Statement(
        predicate=relevant_predicate, terms=[shot_fact, murder_fact]
    )
    predicate_whether = Predicate(
        content="$clue was relevant to $conclusion", truth=None
    )
    relevant_whether = Statement(
        predicate=predicate_whether, terms=[shot_fact, murder_fact]
    )

    def test_implication_complex_whether(self):
        assert self.relevant_fact > self.relevant_whether

    def test_implication_complex_explain(self):
        """
        Check that when .implies() provides a ContextRegister as an "explanation",
        it uses elements only from the left as keys and from the right as values.
        """

        context_names = ContextRegister()
        context_names.insert_pair(key=Entity(name="Alice"), value=Entity(name="Craig"))
        context_names.insert_pair(key=Entity(name="Bob"), value=Entity(name="Dan"))

        complex_whether = self.relevant_whether.new_context(context_names)
        explanation = self.relevant_fact.explain_implication(complex_whether)
        assert explanation.context[Entity(name="Alice").key].compare_keys(
            Entity(name="Craig")
        )
        assert "<Alice> is like <Craig>, and <Bob> is like <Dan>" in str(explanation)
        assert explanation.context.get(Entity(name="Craig").key) is None

    def test_context_registers_for_complex_comparison(self):
        context_names = ContextRegister()
        context_names.insert_pair(key=Entity(name="Alice"), value=Entity(name="Bob"))
        context_names.insert_pair(key=Entity(name="Bob"), value=Entity(name="Alice"))

        swapped_entities = self.relevant_fact.new_context(context_names)
        gen = swapped_entities._context_registers(self.relevant_fact, operator.ge)
        register = next(gen)
        assert register.matches.get("<Alice>").compare_keys(Entity(name="Bob"))

    def test_no_implication_complex(self):
        murder_fact = Statement(
            predicate=self.murder_predicate,
            terms=[Entity(name="Alice"), Entity(name="Craig")],
        )
        relevant_to_craig = Statement(
            predicate=self.relevant_predicate, terms=[self.shot_fact, murder_fact]
        )

        assert not self.relevant_fact >= relevant_to_craig

    def test_implied_by(self):
        assert self.relevant_whether.implied_by(self.relevant_fact)

    def test_explanation_implied_by(self):
        explanation = self.relevant_whether.explain_implied_by(self.relevant_fact)
        assert explanation.context["<Alice>"].name == "Alice"

    def test_interchangeable_implication_no_duplicate_explanations(self):
        men = Statement(
            predicate="$winner1 and $winner2 won the US Open against $loser1 and $loser2",
            terms=[
                Entity(name="Pavić"),
                Entity(name="Soares"),
                Entity(name="Koolhof"),
                Entity(name="Mektić"),
            ],
        )
        women = Statement(
            predicate="$winner1 and $winner2 won the US Open against $loser1 and $loser2",
            terms=[
                Entity(name="Siegemund"),
                Entity(name="Zvonareva"),
                Entity(name="Melichar"),
                Entity(name="Yifan"),
            ],
        )
        all_answers = list(men.explanations_implication(women))
        assert len(all_answers) == 4
        limited = list(
            men.explanations_implication(
                women, context=([Entity(name="Mektić")], [Entity(name="Melichar")])
            )
        )
        assert len(limited) == 2


class TestContradiction:
    def test_factor_different_predicate_truth_contradicts(self):
        predicate = Comparison(
            content="the distance between $place1 and $place2 was",
            sign=">",
            expression=Q_("30 miles"),
        )
        predicate_opposite = Comparison(
            content="the distance between $place1 and $place2 was",
            sign="<",
            expression=Q_("30 miles"),
        )
        terms = [Entity(name="New York"), Entity(name="Los Angeles")]
        fact = Statement(predicate=predicate, terms=terms)
        fact_opposite = Statement(predicate=predicate_opposite, terms=terms)

        assert fact.contradicts(fact_opposite)
        assert fact_opposite.contradicts(fact)

    def test_same_predicate_true_vs_false(self):
        fact = Statement(
            predicate=Predicate(content="$person was a person"),
            terms=Entity(name="Alice"),
        )
        fiction = Statement(
            predicate=Predicate(content="$person was a person", truth=False),
            terms=Entity(name="Alice"),
        )
        assert fact.contradicts(fiction)
        assert fact.truth != fiction.truth

    def test_factor_does_not_contradict_predicate(self):
        predicate = Predicate(content="$person was a person")
        fact = Statement(predicate=predicate, terms=Entity(name="Alice"))

        with pytest.raises(TypeError):
            fact.contradicts(predicate)

    def test_factor_contradiction_absent_predicate(self):
        predicate = Predicate(content="$person was a person")
        fact = Statement(predicate=predicate, terms=Entity(name="Alice"))
        absent_fact = Statement(
            predicate=predicate, terms=Entity(name="Alice"), absent=True
        )

        assert fact.contradicts(absent_fact)
        assert absent_fact.contradicts(fact)

    def test_contradiction_with_empty_explanation_for_context(self):
        predicate = Predicate(content="$person was a person")
        fact = Statement(predicate=predicate, terms=Entity(name="Alice"))
        absent_fact = Statement(
            predicate=predicate, terms=Entity(name="Alice"), absent=True
        )
        explanation = Explanation(reasons=[])

        assert fact.contradicts(absent_fact, context=explanation)
        assert absent_fact.contradicts(fact, context=explanation)

    def test_absences_of_contradictory_facts_consistent(self):
        predicate = Comparison(
            content="the distance between $place1 and $place2 was",
            sign=">",
            expression=Q_("30 miles"),
        )
        predicate_opposite = Comparison(
            content="the distance between $place1 and $place2 was",
            sign="<",
            expression=Q_("30 miles"),
        )
        terms = [Entity(name="New York"), Entity(name="Los Angeles")]
        fact = Statement(predicate=predicate, terms=terms, absent=True)
        fact_opposite = Statement(
            predicate=predicate_opposite, terms=terms, absent=True
        )

        assert not fact.contradicts(fact_opposite)
        assert not fact_opposite.contradicts(fact)

    def test_factor_no_contradiction_no_truth_value(self):
        fact = Statement(
            predicate=Predicate(content="$person was a person"),
            terms=Entity(name="Alice"),
        )
        fact_no_truth = Statement(
            predicate=Predicate(content="$person was a person"),
            terms=Entity(name="Alice"),
        )
        assert not fact.contradicts(fact_no_truth)
        assert not fact_no_truth.contradicts(fact)

    def test_broader_absent_factor_contradicts_quantity_statement(self):
        predicate_less = Comparison(
            content="${vehicle}'s speed was",
            sign=">",
            expression=Q_("30 miles per hour"),
        )
        predicate_more = Comparison(
            content="${vehicle}'s speed was",
            sign=">",
            expression=Q_("60 miles per hour"),
        )
        terms = [Entity(name="the car")]
        absent_general_fact = Statement(
            predicate=predicate_less, terms=terms, absent=True
        )
        specific_fact = Statement(predicate=predicate_more, terms=terms)

        assert absent_general_fact.contradicts(specific_fact)
        assert specific_fact.contradicts(absent_general_fact)

    def test_less_specific_absent_contradicts_more_specific(self):
        predicate_less = Comparison(
            content="${vehicle}'s speed was",
            sign="<",
            expression=Q_("30 miles per hour"),
        )
        predicate_more = Comparison(
            content="${vehicle}'s speed was",
            sign="<",
            expression=Q_("60 miles per hour"),
        )
        terms = [Entity(name="the car")]
        absent_general_fact = Statement(
            predicate=predicate_more, terms=terms, absent=True
        )
        specific_fact = Statement(predicate=predicate_less, terms=terms)

        assert absent_general_fact.contradicts(specific_fact)
        assert specific_fact.contradicts(absent_general_fact)

    def test_no_contradiction_with_more_specific_absent(self):
        predicate_less = Comparison(
            content="${vehicle}'s speed was",
            sign="<",
            expression=Q_("30 miles per hour"),
        )
        predicate_more = Comparison(
            content="${vehicle}'s speed was",
            sign="<",
            expression=Q_("60 miles per hour"),
        )
        terms = [Entity(name="the car")]
        general_fact = Statement(predicate=predicate_more, terms=terms)
        absent_specific_fact = Statement(
            predicate=predicate_less, terms=terms, absent=True
        )

        assert not general_fact.contradicts(absent_specific_fact)
        assert not absent_specific_fact.contradicts(general_fact)

    def test_contradiction_complex(self):
        shot_predicate = Predicate(content="$shooter shot $victim")
        shot_fact = Statement(
            predicate=shot_predicate, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        murder_predicate = Predicate(content="$shooter murdered $victim")
        murder_fact = Statement(
            predicate=murder_predicate, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        relevant_predicate = Predicate(content="$clue was relevant to $conclusion")
        relevant_fact = Statement(
            predicate=relevant_predicate, terms=[shot_fact, murder_fact]
        )
        irrelevant_predicate = Predicate(
            content="$clue was relevant to $conclusion", truth=False
        )
        irrelevant_fact = Statement(
            predicate=irrelevant_predicate, terms=[shot_fact, murder_fact]
        )
        assert relevant_fact.contradicts(irrelevant_fact)

    def test_no_contradiction_complex(self):
        shot_predicate = Predicate(content="$shooter shot $victim")
        shot_fact = Statement(
            predicate=shot_predicate, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        murder_predicate = Predicate(content="$shooter murdered $victim")
        murder_fact = Statement(
            predicate=murder_predicate, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        murder_socrates = Statement(
            predicate=murder_predicate,
            terms=[Entity(name="Alice"), Entity(name="Socrates")],
        )
        relevant_predicate = Predicate(content="$clue was relevant to $conclusion")
        relevant_fact = Statement(
            predicate=relevant_predicate, terms=[shot_fact, murder_fact]
        )
        irrelevant_predicate = Predicate(
            content="$clue was relevant to $conclusion", truth=False
        )
        irrelevant_fact = Statement(
            predicate=irrelevant_predicate, terms=[shot_fact, murder_socrates]
        )
        assert not relevant_fact.contradicts(irrelevant_fact)
        assert not irrelevant_fact.contradicts(relevant_fact)

    def test_no_contradiction_of_None(self):
        shot_predicate = Predicate(content="$shooter shot $victim")
        shot_fact = Statement(
            predicate=shot_predicate, terms=[Entity(name="Alice"), Entity(name="Bob")]
        )
        assert not shot_fact.contradicts(None)

    def test_contradicts_if_present_both_present(self):
        """
        Test a helper function that checks whether there would
        be a contradiction if neither Factor was "absent".
        """
        shot_fact = Statement(
            predicate=Predicate(content="$shooter shot $victim"),
            terms=[Entity(name="Alice"), Entity(name="Bob")],
        )
        shot_false = Statement(
            predicate=Predicate(content="$shooter shot $victim", truth=False),
            terms=[Entity(name="Alice"), Entity(name="Bob")],
        )
        assert shot_fact._contradicts_if_present(
            shot_false, explanation=Explanation.from_context()
        )
        assert shot_false._contradicts_if_present(
            shot_fact, explanation=Explanation.from_context()
        )

    def test_contradicts_if_present_one_absent(self):
        shot_fact = Statement(
            predicate=Predicate(content="$shooter shot $victim"),
            terms=[Entity(name="Alice"), Entity(name="Bob")],
        )
        shot_false = Statement(
            predicate=Predicate(content="$shooter shot $victim", truth=False),
            terms=[Entity(name="Alice"), Entity(name="Bob")],
            absent=True,
        )
        assert shot_fact._contradicts_if_present(
            shot_false, explanation=Explanation.from_context()
        )
        assert shot_false._contradicts_if_present(
            shot_fact, explanation=Explanation.from_context()
        )

    def test_false_does_not_contradict_absent(self):
        absent_fact = Statement(
            predicate=Predicate(
                content="${rural_s_telephone_directory} was copyrightable", truth=True
            ),
            terms=[Entity(name="Rural's telephone directory")],
            absent=True,
        )
        false_fact = Statement(
            predicate=Predicate(
                content="${the_java_api} was copyrightable", truth=False
            ),
            terms=[Entity(name="the Java API", generic=True, plural=False)],
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
            content="the amount of gold $person possessed was",
            sign="<",
            expression=Q_("1 gram"),
        )
        p_large_weight = Comparison(
            content="the amount of gold $person possessed was",
            sign=">=",
            expression=Q_("100 kilograms"),
        )
        alice = Entity(name="Alice")
        bob = Entity(name="Bob")
        alice_rich = Statement(predicate=p_large_weight, terms=alice)
        bob_poor = Statement(predicate=p_small_weight, terms=bob)
        assert alice_rich.contradicts(bob_poor)

    def test_inconsistent_statements_about_corresponding_entities(self):
        """
        Even though Alice and Bob are both generics, it's known that
        Alice in the first context corresponds with Alice in the second.
        So there's no contradiction.
        """
        p_small_weight = Comparison(
            content="the amount of gold $person possessed was",
            sign="<",
            expression=Q_("1 gram"),
        )
        p_large_weight = Comparison(
            content="the amount of gold $person possessed was",
            sign=">=",
            expression=Q_("100 kilograms"),
        )
        alice = Entity(name="Alice")
        bob = Entity(name="Bob")
        alice_rich = Statement(predicate=p_large_weight, terms=alice)
        bob_poor = Statement(predicate=p_small_weight, terms=bob)
        register = ContextRegister()
        register.insert_pair(alice, alice)
        assert not alice_rich.contradicts(bob_poor, context=register)

    def test_check_entity_consistency_true(self):
        left = Statement(
            predicate=Predicate(content="$shooter shot $victim"),
            terms=[Entity(name="Alice"), Entity(name="Bob")],
        )
        right = Statement(
            predicate=Predicate(content="$shooter shot $victim"),
            terms=[Entity(name="Craig"), Entity(name="Dan")],
        )
        register = ContextRegister.from_lists(
            [Entity(name="Alice")], [Entity(name="Craig")]
        )
        update = left.update_context_register(right, register, comparison=means)
        assert any(register is not None for register in update)

    def test_check_entity_consistency_false(self):
        left = Statement(
            predicate=Predicate(content="$shooter shot $victim"),
            terms=[Entity(name="Alice"), Entity(name="Bob")],
        )
        right = Statement(
            predicate=Predicate(content="$shooter shot $victim"),
            terms=[Entity(name="Craig"), Entity(name="Dan")],
        )
        register = ContextRegister.from_lists(
            [Entity(name="Alice")], [Entity(name="Dan")]
        )
        update = left.update_context_register(right, register, comparison=means)
        assert all(register is None for register in update)

    def test_entity_consistency_identity_not_equality(self):
        left = Statement(
            predicate=Predicate(content="$shooter shot $victim"),
            terms=[Entity(name="Alice"), Entity(name="Bob")],
        )
        right = Statement(
            predicate=Predicate(content="$shooter shot $victim"),
            terms=[Entity(name="Craig"), Entity(name="Dan")],
        )
        register = ContextRegister.from_lists(
            [Entity(name="Dan")], [Entity(name="Dan")]
        )
        update = left.update_context_register(right, register, comparison=means)
        assert all(register is None for register in update)

    def test_check_entity_consistency_type_error(self, make_statement, make_predicate):
        """
        There would be no TypeError if it used "means"
        instead of .gt. The comparison would just return False.
        """
        right = Statement(
            predicate=Predicate(content="$shooter shot $victim"),
            terms=[Entity(name="Craig"), Entity(name="Dan")],
        )
        register = ContextRegister.from_lists(
            [Entity(name="Dan")], [Entity(name="Dan")]
        )
        update = right.update_context_register(
            right.predicate,
            register,
            operator.gt,
        )
        with pytest.raises(TypeError):
            any(register is not None for register in update)


class TestConsistent:
    p_small_weight = Comparison(
        content="the amount of gold $person possessed was",
        sign="<",
        expression=Q_("1 gram"),
    )
    p_smallish_weight = Comparison(
        content="the amount of gold $person possessed was",
        sign="<",
        expression=Q_("100 grams"),
    )
    p_large_weight = Comparison(
        content="the amount of gold $person possessed was",
        sign=">=",
        expression=Q_("100 kilograms"),
    )
    big = Statement(predicate=p_large_weight, terms=Entity(name="Alice"))
    small = Statement(predicate=p_small_weight, terms=Entity(name="Bob"))
    smallish = Statement(predicate=p_smallish_weight, terms=Entity(name="Karen"))

    def test_contradictory_facts_about_same_entity(self):
        register = ContextRegister()
        register.insert_pair(Entity(name="Alice"), Entity(name="Bob"))
        assert not self.small.consistent_with(self.big, register)
        explanations = list(
            self.small.explanations_consistent_with(self.big, context=register)
        )
        assert not explanations

    def test_not_consistent_different_terms(self, make_statement):
        """Test that terms on left can only be matched with terms on right, where they contradict."""
        assert not make_statement["less"].consistent_with(
            make_statement["more_atlanta"]
        )

    def test_internally_consistent_different_terms(self, make_statement):
        """Test that terms on left can only be matched with terms on right, where they contradict."""
        assert not make_statement["less"].contradicts_same_context(
            make_statement["more_atlanta"]
        )

    def test_factor_consistent_with_none(self):
        assert self.small.consistent_with(None)

    def test_explain_consistent(self):
        gen = self.small.explanations_consistent_with(self.smallish)
        explanation = next(gen)
        assert explanation.context["<Bob>"].compare_keys(Entity(name="Karen"))

    def test_explain_consistent_if_implied(self):
        gen = self.smallish.explanations_consistent_with(self.small)
        explanation = next(gen)
        assert explanation.context["<Karen>"].compare_keys(Entity(name="Bob"))

    def test_no_explanation_consistent(self):
        assert self.small.explain_contradiction(self.smallish) is None


class TestAddition:
    predicate_less = Comparison(
        content="${vehicle}'s speed was",
        sign=">",
        expression=Q_("30 miles per hour"),
    )
    predicate_more = Comparison(
        content="${vehicle}'s speed was",
        sign=">=",
        expression=Q_("60 miles per hour"),
    )
    general_fact = Statement(predicate=predicate_less, terms=Entity(name="the car"))
    specific_fact = Statement(
        predicate=predicate_more, terms=Entity(name="the motorcycle")
    )

    def test_addition_returns_broader_operand(self):
        answer = self.specific_fact + self.general_fact
        assert answer.means(self.specific_fact)

    def test_addition_uses_terms_from_left(self):
        answer = self.general_fact + self.specific_fact
        assert "<the car>" in str(answer)
        assert "the-car-s-speed" in answer.slug

    def test_add_unrelated_factors(self):
        murder = Statement(
            predicate=Predicate(content="$person committed a murder"),
            terms=Entity(name="Al"),
        )
        crime = Statement(
            predicate=Predicate(content="$person committed a crime"),
            terms=Entity(name="Al"),
        )
        assert murder + crime is None

    def test_add_with_specific_entity(self):
        """Result has specific factors from the implying Factor, but generic factors from the left."""
        left = Statement(
            predicate="$entity bought $item",
            terms=[Entity(name="Alice"), Entity(name="a box of pencils")],
        )
        right = Statement(
            predicate="$entity bought $item",
            terms=[
                Entity(name="the State of Texas", generic=False),
                Entity(name="a box of erasers"),
            ],
        )
        new = left + right
        assert new.terms[0].name == "the State of Texas"
        assert new.terms[1].name == "a box of pencils"
