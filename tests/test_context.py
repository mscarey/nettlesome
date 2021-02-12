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
        with pytest.raises(StopIteration):
            next(
                watt_factor["f1"]._context_registers(
                    make_complex_fact["relevant_murder"], operator.ge
                )
            )

    def test_context_register_valid(self, make_statement):
        expected = ContextRegister()
        expected.insert_pair(Term("Alice"), Term("Bob"))
        generated = next(
            make_statement["no_crime"]._context_registers(
                make_statement["no_crime_entity_order"], operator.le
            )
        )
        assert generated == expected

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
        assert mapping.get(str(make_statement["f7"])).name == make_statement["f7"].name

    def test_registers_for_interchangeable_context(self, make_statement):
        """
        Test that _registers_for_interchangeable_context swaps the first two
        items in the ContextRegister
        """
        factor = make_statement["shooting"]
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
        left = ComparableGroup(make_statement["murder"], make_statement["large_weight"])
        right = ComparableGroup(
            (make_statement["murder_swap_entities"], make_statement["small_weight_bob"])
        )
        context = next(left.likely_contexts(right))
        assert context.check_match(Term("Alice"), Term("Bob"))

    def test_likely_context_different_terms(self):
        lotus = make_opinion_with_holding["lotus_majority"]
        oracle = make_opinion_with_holding["oracle_majority"]
        left = [lotus.holdings[2].outputs[0], lotus.holdings[2].inputs[0].to_effect]
        left = ComparableGroup(left)
        right = ComparableGroup(oracle.holdings[2].outputs[0])
        context = next(left.likely_contexts(right))
        lotus_menu = lotus.holdings[2].generic_factors()[0]
        java_api = oracle.generic_factors()[0]
        assert context.get_factor(lotus_menu) == java_api

    def test_likely_context_from_factor_meaning(self):
        lotus = make_opinion_with_holding["lotus_majority"]
        oracle = make_opinion_with_holding["oracle_majority"]
        left = lotus.holdings[2].outputs[0]
        right = oracle.holdings[2].outputs[0]
        likely = left._likely_context_from_meaning(right, context=ContextRegister())
        lotus_menu = lotus.holdings[2].generic_factors()[0]
        java_api = oracle.generic_factors()[0]
        assert likely.get_factor(lotus_menu) == java_api

    def test_union_one_generic_not_matched(self):
        """
        Here, both ComparableGroups have "fact that <> was a computer program".
        But they each have another generic that can't be matched:
        fact that <the Java API> was a literal element of <the Java language>
        and
        fact that <the Lotus menu command hierarchy> provided the means by
        which users controlled and operated <Lotus 1-2-3>

        Tests that Factors from "left" should be keys and Factors from "right" values.
        """
        lotus = make_opinion_with_holding["lotus_majority"]
        oracle = make_opinion_with_holding["oracle_majority"]
        left = ComparableGroup(lotus.holdings[7].inputs[:2])
        right = ComparableGroup(
            [oracle.holdings[3].outputs[0], oracle.holdings[3].inputs[0]]
        )
        new = left | right
        text = (
            "that <the Lotus menu command hierarchy> was a "
            "literal element of <Lotus 1-2-3>"
        )
        assert text in new[1].short_string


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
