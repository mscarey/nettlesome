from nettlesome.comparable import ContextRegister
import operator

import pytest

from nettlesome.predicates import Predicate
from nettlesome.entities import Entity
from nettlesome.statements import Statement


class TestMakeEntities:
    def test_conversion_to_generic(self):
        jon = Entity("Jon Doe", generic=False)
        generic = jon.make_generic()
        assert generic.generic is True

    def test_context_register(self):
        """
        There will be a match because both object are :class:`.Term`.
        """
        left = Entity("peanut butter")
        right = Entity("jelly")
        update = left._context_registers(right, operator.ge)
        assert any(register is not None for register in update)

        update = left._context_registers(right, operator.le)
        expected = ContextRegister()
        expected.insert_pair(left, right)
        assert any(register == expected for register in update)

    def test_new_context(self):

        changes = ContextRegister.from_lists(
            [Entity("Death Star 3"), Entity("Kylo Ren")],
            [Entity("Death Star 1"), Entity("Darth Vader")],
        )
        place = Entity("Death Star 3")
        assert place.new_context(changes) == changes.get_factor(place)


class TestSameMeaning:
    def test_equality_generic_entities(self):
        left = Entity("Bert")
        right = Entity("Ernie")
        assert left.means(right)
        assert not left == right

    def test_entity_does_not_mean_statement(self):
        entity = Entity("Bob")
        statement = Statement("$person loves ice cream", terms=entity)
        assert not entity.means(statement)
        assert not statement.means(entity)


class TestImplication:
    def test_implication_of_generic_entity(self):
        assert Entity("Specific Bob", generic=False) > Entity("Clara")

    def test_generic_entity_does_not_imply_specific_and_different(self):
        assert not Entity("Clara") > Entity("Specific Bob", generic=False)

    def test_generic_entity_does_not_imply_specific_and_same(self):
        assert not Entity("Clara") > Entity("Clara", generic=False)

    def test_same_entity_not_ge(self):
        assert not Entity("Clara") > Entity("Clara")

    def test_implies_concrete_with_same_name(self):
        concrete = Entity("Bob", generic=False)
        other = Entity("Bob", generic=False)
        assert concrete.implies(other)
        assert concrete >= other
        assert not concrete > other

    def test_implication_concrete_with_different_name(self):
        concrete = Entity("Bob", generic=False)
        generic = Entity("Barb")
        assert concrete.implies(generic)
        assert concrete > generic
        assert concrete >= generic

    def test_entity_does_not_imply_statement(self):
        entity = Entity("Bob")
        statement = Statement("$person loves ice cream", terms=entity)
        assert not entity.implies(statement)
        assert not statement.implies(entity)
        assert not entity >= statement
        assert not statement >= entity
        assert not entity > statement
        assert not statement > entity


class TestContradiction:
    def test_error_contradiction_with_non_factor(self):
        with pytest.raises(TypeError):
            assert Entity("Al").contradicts(Predicate("any text"))

    def test_no_contradiction_of_other_entity(self):
        assert not Entity("Al").contradicts(Entity("Ed"))
        assert not Entity("Al").contradicts(Statement("any text"))


class TestAdd:
    def test_union_not_valid_alias(self):
        with pytest.raises(TypeError):
            Entity("Al") | Entity("Ed")

    def test_add_generic(self):
        new = Entity("Al") + Entity("Ed")
        assert new.name == "Al"

    def test_no_adding_string(self):
        with pytest.raises(TypeError):
            Entity("Al") + "Ed"

    def test_add_generic_and_specific(self):
        new = Entity("Al") + Entity("Mister Ed", generic=False)
        assert new.name == "Mister Ed"

    def test_two_specifics_will_not_add(self):
        new = Entity("Inimitable", generic=False) + Entity("Original", generic=False)
        assert new is None

    def test_two_specifics_with_same_name_will_add(self):
        new = Entity("Identical", generic=False) + Entity("Identical", generic=False)
        assert new.name == "Identical"
