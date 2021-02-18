from nettlesome.comparable import ContextRegister
import operator

import pytest

from nettlesome.predicates import Predicate
from nettlesome.terms import Term
from nettlesome.statements import Statement


class TestMakeEntities:
    def test_conversion_to_generic(self):
        jon = Term("Jon Doe", generic=False)
        generic = jon.make_generic()
        assert generic.generic is True

    def test_context_register(self):
        """
        There will be a match because both object are :class:`.Term`.
        """
        left = Term("peanut butter")
        right = Term("jelly")
        update = left._context_registers(right, operator.ge)
        assert any(register is not None for register in update)

        update = left._context_registers(right, operator.le)
        expected = ContextRegister()
        expected.insert_pair(left, right)
        assert any(register == expected for register in update)

    def test_new_context(self):

        changes = ContextRegister.from_lists(
            [Term("Death Star 3"), Term("Kylo Ren")],
            [Term("Death Star 1"), Term("Darth Vader")],
        )
        place = Term("Death Star 3")
        assert place.new_context(changes) == changes.get_factor(place)


class TestSameMeaning:
    def test_equality_generic_entities(self):
        left = Term("Bert")
        right = Term("Ernie")
        assert left.means(right)
        assert not left == right

    def test_entity_does_not_mean_statement(self):
        entity = Term("Bob")
        statement = Statement("$person loves ice cream", terms=entity)
        assert not entity.means(statement)
        assert not statement.means(entity)


class TestImplication:
    def test_implication_of_generic_entity(self):
        assert Term("Specific Bob", generic=False) > Term("Clara")

    def test_generic_entity_does_not_imply_specific_and_different(self):
        assert not Term("Clara") > Term("Specific Bob", generic=False)

    def test_generic_entity_does_not_imply_specific_and_same(self):
        assert not Term("Clara") > Term("Clara", generic=False)

    def test_same_entity_not_ge(self):
        assert not Term("Clara") > Term("Clara")

    def test_implies_concrete_with_same_name(self):
        concrete = Term("Bob", generic=False)
        other = Term("Bob", generic=False)
        assert concrete.implies(other)
        assert concrete >= other
        assert not concrete > other

    def test_implication_concrete_with_different_name(self):
        concrete = Term("Bob", generic=False)
        generic = Term("Barb")
        assert concrete.implies(generic)
        assert concrete > generic
        assert concrete >= generic

    def test_entity_does_not_imply_statement(self):
        entity = Term("Bob")
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
            assert Term("Al").contradicts(Predicate("any text"))

    def test_no_contradiction_of_other_entity(self):
        assert not Term("Al").contradicts(Term("Ed"))
        assert not Term("Al").contradicts(Statement("any text"))


class TestUnion:
    def test_union_of_terms(self):
        with pytest.raises(NotImplementedError):
            Term("Al") | Term("Ed")