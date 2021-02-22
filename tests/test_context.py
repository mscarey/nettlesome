import operator

import pytest

from nettlesome.comparable import ContextRegister, means
from nettlesome.entities import Entity
from nettlesome.groups import FactorGroup
from nettlesome.predicates import Predicate
from nettlesome.statements import Statement


class TestContextRegisters:
    bird = Predicate("$bird was a bird")
    paid = Predicate("$employer paid $employee")

    def test_possible_context_without_empty_spaces(self):
        left = Statement(self.bird, terms=Entity("Owl"))
        right = Statement(self.bird, terms=Entity("Owl"))
        contexts = list(left.possible_contexts(right))
        assert len(contexts) == 1
        assert contexts[0].check_match(Entity("Owl"), Entity("Owl"))

    def test_possible_context_different_terms(self):
        left = Statement(self.bird, terms=Entity("Foghorn"))
        right = Statement(self.bird, terms=Entity("Woody"))
        contexts = list(left.possible_contexts(right))
        assert len(contexts) == 1
        assert contexts[0].check_match(Entity("Foghorn"), Entity("Woody"))

    def test_all_possible_contexts_identical_factor(self):
        left = Statement(self.paid, terms=[Entity("Irene"), Entity("Bob")])
        contexts = list(left.possible_contexts(left))
        assert len(contexts) == 2
        assert any(
            context.check_match(Entity("Irene"), Entity("Bob")) for context in contexts
        )

    def test_context_not_equal_to_list(self):
        changes = ContextRegister.from_lists(
            [Entity("Alice")],
            [Entity("Dan")],
        )
        assert changes != [[Entity("Alice")], [Entity("Dan")]]

    def test_cannot_update_context_register_from_lists(self):
        left = Statement(
            "$shooter shot $victim", terms=[Entity("Alice"), Entity("Bob")]
        )
        right = Statement(
            "$shooter shot $victim", terms=[Entity("Craig"), Entity("Dan")]
        )
        update = left.update_context_register(
            right, context=[[Entity("Alice")], [Entity("Craig")]], comparison=means
        )
        with pytest.raises(TypeError):
            next(update)

    def test_limited_possible_contexts_identical_factor(self):
        statement = Statement(self.paid, terms=[Entity("Al"), Entity("Xu")])
        context = ContextRegister()
        context.insert_pair(Entity("Al"), Entity("Xu"))
        contexts = list(statement.possible_contexts(statement, context=context))
        assert len(contexts) == 1
        assert contexts[0].check_match(Entity("Al"), Entity("Xu"))
        assert "Entity(name='Xu', generic=True" in repr(contexts)

    def test_context_register_empty(self, make_complex_fact):
        """
        Yields no context_register because the Term in f1 doesn't imply
        the Fact in f_relevant_murder.
        """
        statement = Statement("$person was a defendant", terms=Entity("Alice"))
        complex_statement = make_complex_fact["relevant_murder"]
        gen = statement._context_registers(complex_statement, operator.ge)
        with pytest.raises(StopIteration):
            next(gen)

    def test_insert_pair_with_wrong_type(self):
        context = ContextRegister()
        with pytest.raises(TypeError):
            context.insert_pair(Entity("Bob"), Predicate("events transpired"))

    def test_failed_match(self):
        context = ContextRegister()
        context.insert_pair(Entity("Bob"), Entity("Alice"))
        assert context.check_match(Entity("Craig"), Entity("Dan")) is False

    def test_context_register_valid(self, make_statement):
        expected = ContextRegister()
        expected.insert_pair(Entity("Alice"), Entity("Bob"))
        generated = next(
            make_statement["no_crime"]._context_registers(
                make_statement["no_crime_entity_order"], operator.le
            )
        )
        assert len(generated) == len(expected)
        assert generated["<Alice>"].name == expected["<Alice>"].name

    def test_import_to_context_register(self, make_statement):

        left = ContextRegister.from_lists(
            keys=[make_statement["shooting"], Entity("Alice")],
            values=[make_statement["shooting_entity_order"], Entity("Bob")],
        )
        right = ContextRegister()
        right.insert_pair(Entity("Bob"), Entity("Alice"))
        assert len(left.merged_with(right)) == 3

    def test_import_to_mapping_no_change(self):
        old_mapping = ContextRegister.from_lists([Entity("Al")], [Entity("Li")])
        new_mapping = ContextRegister.from_lists([Entity("Al")], [Entity("Li")])
        merged = old_mapping.merged_with(new_mapping)
        assert len(merged) == 1
        assert merged["<Al>"].name == "Li"

    def test_import_to_mapping_conflict(self):
        old_mapping = ContextRegister.from_lists([Entity("Al")], [Entity("Li")])
        new_mapping = ContextRegister.from_lists([Entity("Al")], [Entity("Al")])
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
            "$person1 and $person2 met with each other",
            terms=[Entity("Al"), Entity("Ed")],
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
        assert context.check_match(Entity("Bob"), Entity("Bob"))

    def test_likely_context_implication_one_factor(self, make_statement):
        left = make_statement["large_weight"]
        right = make_statement["small_weight"]
        context = next(left.likely_contexts(right))
        assert context.check_match(Entity("Alice"), Entity("Alice"))

    def test_likely_context_two_factors(self, make_statement):
        left = FactorGroup([make_statement["murder"], make_statement["large_weight"]])
        right = make_statement["small_weight_bob"]
        context = next(left.likely_contexts(right))
        assert context.check_match(Entity("Alice"), Entity("Bob"))

    def test_likely_context_two_by_two(self, make_statement):
        left = FactorGroup([make_statement["murder"], make_statement["large_weight"]])
        right = FactorGroup(
            (make_statement["murder_entity_order"], make_statement["small_weight_bob"])
        )
        context = next(left.likely_contexts(right))
        assert context.check_match(Entity("Alice"), Entity("Bob"))

    def test_likely_context_different_terms(self):
        copyright_registered = Statement(
            "$entity registered a copyright covering $work",
            terms=[
                Entity("Lotus Development Corporation"),
                Entity("the Lotus menu command hierarchy"),
            ],
        )
        copyrightable = Statement(
            "$work was copyrightable", terms=Entity("the Lotus menu command hierarchy")
        )
        left = FactorGroup([copyrightable, copyright_registered])
        right = FactorGroup(
            Statement("$work was copyrightable", terms=Entity("the Java API"))
        )
        context = next(left.likely_contexts(right))
        assert (
            context.get_factor(Entity("the Lotus menu command hierarchy")).short_string
            == Entity("the Java API").short_string
        )

    def test_likely_context_from_factor_meaning(self):
        left = Statement(
            "$part provided the means by which users controlled and operated $whole",
            terms=[Entity("the Java API"), Entity("the Java language")],
        )
        right = Statement(
            "$part provided the means by which users controlled and operated $whole",
            terms=[Entity("the Lotus menu command hierarchy"), Entity("Lotus 1-2-3")],
        )
        likely = left._likely_context_from_meaning(right, context=ContextRegister())

        assert (
            likely.get_factor(Entity("the Java API")).short_string
            == Entity("the Lotus menu command hierarchy").short_string
        )

    def test_union_one_generic_not_matched(self):
        """
        Here, both FactorGroups have "fact that <> was a computer program".
        But they each have another generic that can't be matched:
        that <the Java API> was a literal element of <the Java language>
        and
        that <the Lotus menu command hierarchy> provided the means by
        which users controlled and operated <Lotus 1-2-3>

        Tests that Factors from "left" should be keys and Factors from "right" values.
        """
        language_program = Statement(
            "$program was a computer program", terms=Entity("the Java language")
        )
        lotus_program = Statement(
            "$program was a computer program", terms=Entity("Lotus 1-2-3")
        )

        controlled = Statement(
            "$part provided the means by which users controlled and operated $whole",
            terms=[Entity("the Lotus menu command hierarchy"), Entity("Lotus 1-2-3")],
        )
        part = Statement(
            "$part was a literal element of $whole",
            terms=[Entity("the Java API"), Entity("the Java language")],
        )

        left = FactorGroup([lotus_program, controlled])
        right = FactorGroup([language_program, part])

        new = left | right
        text = (
            "that <the Lotus menu command hierarchy> was a "
            "literal element of <Lotus 1-2-3>"
        )
        assert text in new[0].short_string


class TestChangeRegisters:
    def test_reverse_key_and_value_of_register(self):
        left = Entity("Siskel")
        right = Entity("Ebert")

        register = ContextRegister.from_lists([left], [right])

        assert len(register.keys()) == 1
        assert register.get("<Siskel>").name == "Ebert"

        new = register.reversed()
        assert new.get("<Ebert>").name == "Siskel"

    def test_factor_pairs(self):
        register = ContextRegister.from_lists(
            [Entity("apple"), Entity("lemon")], [Entity("pear"), Entity("orange")]
        )
        gen = register.factor_pairs()
        assert next(gen)[0].name == "apple"

    def test_no_iterables_in_register(self):
        left = FactorGroup()
        right = FactorGroup()
        context = ContextRegister()
        with pytest.raises(TypeError):
            context.insert_pair(left, right)
