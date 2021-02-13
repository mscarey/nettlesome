import operator

import pytest

from nettlesome.comparable import ContextRegister, means
from nettlesome.terms import Term
from nettlesome.groups import ComparableGroup
from nettlesome.predicates import Predicate
from nettlesome.statements import Statement


class TestContextRegisters:
    bird = Predicate("$bird was a bird")
    paid = Predicate("$employer paid $employee")

    def test_possible_context_without_empty_spaces(self):
        left = Statement(self.bird, terms=Term("Owl"))
        right = Statement(self.bird, terms=Term("Owl"))
        contexts = list(left.possible_contexts(right))
        assert len(contexts) == 1
        assert contexts[0].check_match(Term("Owl"), Term("Owl"))

    def test_possible_context_different_terms(self):
        left = Statement(self.bird, terms=Term("Foghorn"))
        right = Statement(self.bird, terms=Term("Woody"))
        contexts = list(left.possible_contexts(right))
        assert len(contexts) == 1
        assert contexts[0].check_match(Term("Foghorn"), Term("Woody"))

    def test_all_possible_contexts_identical_factor(self):
        left = Statement(self.paid, terms=[Term("Irene"), Term("Bob")])
        contexts = list(left.possible_contexts(left))
        assert len(contexts) == 2
        assert any(
            context.check_match(Term("Irene"), Term("Bob")) for context in contexts
        )

    def test_context_not_equal_to_list(self):
        changes = ContextRegister.from_lists(
            [Term("Alice")],
            [Term("Dan")],
        )
        assert changes != [[Term("Alice")], [Term("Dan")]]

    def test_cannot_update_context_register_from_lists(self):
        left = Statement("$shooter shot $victim", terms=[Term("Alice"), Term("Bob")])
        right = Statement("$shooter shot $victim", terms=[Term("Craig"), Term("Dan")])
        update = left.update_context_register(
            right, context=[[Term("Alice")], [Term("Craig")]], comparison=means
        )
        with pytest.raises(TypeError):
            next(update)

    def test_limited_possible_contexts_identical_factor(self):
        statement = Statement(self.paid, terms=[Term("Al"), Term("Xu")])
        context = ContextRegister()
        context.insert_pair(Term("Al"), Term("Xu"))
        contexts = list(statement.possible_contexts(statement, context=context))
        assert len(contexts) == 1
        assert contexts[0].check_match(Term("Al"), Term("Xu"))

    def test_context_register_empty(self, make_complex_fact):
        """
        Yields no context_register because the Term in f1 doesn't imply
        the Fact in f_relevant_murder.
        """
        statement = Statement("$person was a defendant", terms=Term("Alice"))
        complex_statement = make_complex_fact["relevant_murder"]
        gen = statement._context_registers(complex_statement, operator.ge)
        with pytest.raises(StopIteration):
            next(gen)

    def test_context_register_valid(self, make_statement):
        expected = ContextRegister()
        expected.insert_pair(Term("Alice"), Term("Bob"))
        generated = next(
            make_statement["no_crime"]._context_registers(
                make_statement["no_crime_entity_order"], operator.le
            )
        )
        assert len(generated) == len(expected)
        assert generated["<Alice>"].name == expected["<Alice>"].name

    def test_import_to_context_register(self, make_statement):

        left = ContextRegister.from_lists(
            keys=[make_statement["shooting"], Term("Alice")],
            values=[make_statement["shooting_entity_order"], Term("Bob")],
        )
        right = ContextRegister()
        right.insert_pair(Term("Bob"), Term("Alice"))
        assert len(left.merged_with(right)) == 3

    def test_import_to_mapping_no_change(self):
        old_mapping = ContextRegister.from_lists([Term("Al")], [Term("Li")])
        new_mapping = ContextRegister.from_lists([Term("Al")], [Term("Li")])
        merged = old_mapping.merged_with(new_mapping)
        assert len(merged) == 1
        assert merged["<Al>"].name == "Li"

    def test_import_to_mapping_conflict(self):
        old_mapping = ContextRegister.from_lists([Term("Al")], [Term("Li")])
        new_mapping = ContextRegister.from_lists([Term("Al")], [Term("Al")])
        merged = old_mapping.merged_with(new_mapping)
        assert merged is None

    def test_import_to_mapping_reciprocal(self, make_statement):
        mapping = ContextRegister.from_lists(
            [make_statement["shooting"]], [make_statement["shooting"]]
        ).merged_with(
            ContextRegister.from_lists(
                [make_statement["shooting_entity_order"]],
                [make_statement["shooting_entity_order"]],
            )
        )
        assert (
            mapping.get_factor(make_statement["shooting"]).short_string
            == make_statement["shooting"].short_string
        )

    def test_registers_for_interchangeable_context(self, make_statement):
        """
        Test that _registers_for_interchangeable_context swaps the first two
        items in the ContextRegister
        """
        factor = Statement(
            "$person1 and $person2 met with each other", terms=[Term("Al"), Term("Ed")]
        )
        first_pattern, second_pattern = list(factor.term_permutations())
        assert first_pattern[0].name == second_pattern[1].name
        assert first_pattern[1].name == second_pattern[0].name
        assert first_pattern[0].name != first_pattern[1].name


class TestLikelyContext:
    def test_likely_context_one_factor(self, make_statement):
        left = make_statement["murder"]
        right = make_statement["murder"]
        context = next(left.likely_contexts(right))
        assert context.check_match(Term("Bob"), Term("Bob"))

    def test_likely_context_implication_one_factor(self, make_statement):
        left = make_statement["large_weight"]
        right = make_statement["small_weight"]
        context = next(left.likely_contexts(right))
        assert context.check_match(Term("Alice"), Term("Alice"))

    def test_likely_context_two_factors(self, make_statement):
        left = ComparableGroup(make_statement["murder"], make_statement["large_weight"])
        right = make_statement["small_weight_bob"]
        context = next(left.likely_contexts(right))
        assert context.check_match(Term("Alice"), Term("Bob"))

    def test_likely_context_two_by_two(self, make_statement):
        left = ComparableGroup(
            [make_statement["murder"], make_statement["large_weight"]]
        )
        right = ComparableGroup(
            (make_statement["murder_entity_order"], make_statement["small_weight_bob"])
        )
        context = next(left.likely_contexts(right))
        assert context.check_match(Term("Alice"), Term("Bob"))

    def test_likely_context_different_terms(self):
        copyright_registered = Statement(
            "$entity registered a copyright covering $work",
            terms=[
                Term("Lotus Development Corporation"),
                Term("the Lotus menu command hierarchy"),
            ],
        )
        copyrightable = Statement(
            "$work was copyrightable", terms=Term("the Lotus menu command hierarchy")
        )
        left = ComparableGroup([copyrightable, copyright_registered])
        right = ComparableGroup(
            Statement("$work was copyrightable", terms=Term("the Java API"))
        )
        context = next(left.likely_contexts(right))
        assert (
            context.get_factor(Term("the Lotus menu command hierarchy")).short_string
            == Term("the Java API").short_string
        )

    def test_likely_context_from_factor_meaning(self):
        left = Statement(
            "$part provided the means by which users controlled and operated $whole",
            terms=[Term("the Java API"), Term("the Java language")],
        )
        right = Statement(
            "$part provided the means by which users controlled and operated $whole",
            terms=[Term("the Lotus menu command hierarchy"), Term("Lotus 1-2-3")],
        )
        likely = left._likely_context_from_meaning(right, context=ContextRegister())

        assert (
            likely.get_factor(Term("the Java API")).short_string
            == Term("the Lotus menu command hierarchy").short_string
        )

    def test_union_one_generic_not_matched(self):
        """
        Here, both ComparableGroups have "fact that <> was a computer program".
        But they each have another generic that can't be matched:
        that <the Java API> was a literal element of <the Java language>
        and
        that <the Lotus menu command hierarchy> provided the means by
        which users controlled and operated <Lotus 1-2-3>

        Tests that Factors from "left" should be keys and Factors from "right" values.
        """
        language_program = Statement(
            "$program was a computer program", terms=Term("the Java language")
        )
        lotus_program = Statement(
            "$program was a computer program", terms=Term("Lotus 1-2-3")
        )

        controlled = Statement(
            "$part provided the means by which users controlled and operated $whole",
            terms=[Term("the Lotus menu command hierarchy"), Term("Lotus 1-2-3")],
        )
        part = Statement(
            "$part was a literal element of $whole",
            terms=[Term("the Java API"), Term("the Java language")],
        )

        left = ComparableGroup([lotus_program, controlled])
        right = ComparableGroup([language_program, part])

        new = left | right
        text = (
            "that <the Lotus menu command hierarchy> was a "
            "literal element of <Lotus 1-2-3>"
        )
        assert text in new[0].short_string


class TestChangeRegisters:
    def test_reverse_key_and_value_of_register(self):
        left = Term("Siskel")
        right = Term("Ebert")

        register = ContextRegister.from_lists([left], [right])

        assert len(register.keys()) == 1
        assert register.get("<Siskel>").name == "Ebert"

        new = register.reversed()
        assert new.get("<Ebert>").name == "Siskel"

    def test_factor_pairs(self):
        register = ContextRegister.from_lists(
            [Term("apple"), Term("lemon")], [Term("pear"), Term("orange")]
        )
        gen = register.factor_pairs()
        assert next(gen)[0].name == "apple"
