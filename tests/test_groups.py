import pytest

from nettlesome.comparable import (
    ContextRegister,
    consistent_with,
    contradicts,
    means,
)
from nettlesome.entities import Entity
from nettlesome.groups import ComparableGroup
from nettlesome.predicates import Predicate, Comparison
from nettlesome.statements import Statement


class TestMakeGroup:
    def test_group_from_list(self, make_statement):
        factor_list = [make_statement["crime"], make_statement["shooting"]]
        group = ComparableGroup(factor_list)
        assert isinstance(group, ComparableGroup)
        assert group[1] == make_statement["shooting"]

    def test_make_empty_group(self):
        group = ComparableGroup()
        assert len(group) == 0

    def test_group_from_item(self, make_statement):
        factor = make_statement["shooting"]
        group = ComparableGroup(factor)
        assert isinstance(group, ComparableGroup)
        assert group[0] == make_statement["shooting"]

    def test_make_empty_group(self):
        group = ComparableGroup()
        assert isinstance(group, ComparableGroup)
        assert len(group) == 0

    def test_factorgroup_from_factorgroup(self, make_statement):
        factor_list = [make_statement["crime"], make_statement["shooting"]]
        group = ComparableGroup(factor_list)
        identical_group = ComparableGroup(group)
        assert isinstance(identical_group, ComparableGroup)
        assert identical_group[0] == make_statement["crime"]

    def test_recursive_factors_from_factorgroup(self, make_statement):
        factor_list = [make_statement["crime"], make_statement["shooting"]]
        group = ComparableGroup(factor_list)
        factors = group.recursive_factors
        assert factors["<Alice>"].name == "Alice"

    def test_one_factor_implies_and_has_same_context_as_other(self, make_statement):
        assert make_statement["more"].implies_same_context(
            make_statement["more_meters"]
        )

    def test_drop_implied_factors(self, make_statement):
        group = ComparableGroup([make_statement["more_meters"], make_statement["more"]])
        shorter = group.drop_implied_factors()
        assert len(shorter) == 1
        assert make_statement["more_meters"] in group

    def test_drop_implied_factors_unmatched_context(self):
        """Test that Statements aren't considered redundant because they relate to different entities."""
        left = Statement(
            Comparison(
                "the amount that ${taller}'s height exceeded ${shorter}'s height was",
                sign=">=",
                expression="2 inches",
            ),
            terms=[Entity("Ann"), Entity("Ben")],
        )
        right = Statement(
            Comparison(
                "the amount that ${taller}'s height exceeded ${shorter}'s height was",
                sign=">=",
                expression="2 feet",
            ),
            terms=[Entity("Alice"), Entity("Bob")],
        )
        group = ComparableGroup([left, right])
        shorter = group.drop_implied_factors()
        assert len(shorter) == 2

    def test_make_context_register(self):
        alice = Entity("Alice")
        bob = Entity("Bob")
        craig = Entity("Craig")
        dan = Entity("Dan")

        left = ComparableGroup([alice, bob])
        right = ComparableGroup([craig, dan])

        register = ContextRegister()
        register.insert_pair(alice, craig)

        gen = left._context_registers(right, comparison=means, context=register)
        answer = next(gen)
        assert answer.get("<Bob>").compare_keys(dan)

    def test_get_factor_by_index(self, make_complex_fact):
        alice = Entity("Alice")
        bob = Entity("Bob")
        group = ComparableGroup([alice, bob])
        assert group[1].name == "Bob"

    def test_get_factor_by_name(self, make_complex_fact):
        group = ComparableGroup([make_complex_fact["relevant_murder"]])
        entity = group.get_factor_by_name("Alice")
        assert entity.plural is False


class TestSameFactors:
    def test_group_has_same_factors_as_identical_group(self, make_statement):
        first_group = ComparableGroup(
            [make_statement["crime"], make_statement["shooting"]]
        )
        second_group = ComparableGroup(
            [make_statement["crime"], make_statement["shooting"]]
        )
        assert first_group.has_all_factors_of(second_group)

    def test_group_has_same_factors_as_included_group(self, make_statement):
        first_group = ComparableGroup(
            [
                make_statement["crime"],
                make_statement["shooting"],
                make_statement["murder"],
            ]
        )
        second_group = ComparableGroup(
            [make_statement["crime"], make_statement["murder"]]
        )
        assert first_group.has_all_factors_of(second_group)
        assert not second_group.has_all_factors_of(first_group)

    def test_group_shares_all_factors_with_bigger_group(self, make_statement):
        first_group = ComparableGroup(
            [
                make_statement["crime"],
                make_statement["shooting"],
                make_statement["murder"],
            ]
        )
        second_group = ComparableGroup(
            [make_statement["crime"], make_statement["murder"]]
        )
        assert second_group.shares_all_factors_with(first_group)
        assert not first_group.shares_all_factors_with(second_group)

    def test_group_means_identical_group(self, make_statement):
        first_group = ComparableGroup(
            [make_statement["crime"], make_statement["murder"]]
        )
        second_group = ComparableGroup(
            [make_statement["crime"], make_statement["murder"]]
        )
        assert first_group.means(second_group)
        assert means(first_group, second_group)

    def test_group_does_not_mean_different_group(self, make_statement):
        first_group = ComparableGroup(
            [
                make_statement["crime"],
                make_statement["shooting"],
                make_statement["murder"],
            ]
        )
        second_group = ComparableGroup(
            [make_statement["crime"], make_statement["murder"]]
        )
        assert not first_group.means(second_group)
        assert not second_group.means(first_group)

    def test_register_for_matching_entities(self):
        known = ContextRegister()
        alice = Entity("Alice")
        craig = Entity("Craig")
        known.insert_pair(alice, craig)

        gen = alice._context_registers(other=craig, comparison=means, context=known)
        register = next(gen)
        assert register.get("<Alice>") == craig


class TestImplication:
    def test_factorgroup_implies_none(self, make_statement):
        group = ComparableGroup([make_statement["crime"], make_statement["shooting"]])
        assert group.implies(None)

    def test_factorgroup_implication_of_empty_group(self, make_statement):
        factor_list = [make_statement["crime"], make_statement["shooting"]]
        group = ComparableGroup(factor_list)
        empty_group = ComparableGroup()
        assert group.implies(empty_group)

    def test_explanation_implication_of_factorgroup(self, make_statement):
        """Explanation shows the statements in `left` narrow down the quantity more than `right` does."""
        left = ComparableGroup(
            [make_statement["absent_way_more"], make_statement["less_than_20"]]
        )
        right = ComparableGroup([make_statement["less"], make_statement["absent_more"]])
        explanation = left.explain_implication(right)
        assert "implies" in str(explanation).lower()


class TestContradiction:
    def test_contradiction_of_group(self):
        lived_at = Predicate("$person lived at $residence")
        bob_lived = Statement(lived_at, terms=[Entity("Bob"), Entity("Bob's house")])
        carl_lived = Statement(lived_at, terms=[Entity("Carl"), Entity("Carl's house")])
        distance_long = Comparison(
            "the distance from the center of $city to $residence was",
            sign=">=",
            expression="50 miles",
        )
        statement_long = Statement(
            distance_long, terms=[Entity("Houston"), Entity("Bob's house")]
        )
        distance_short = Comparison(
            "the distance from the center of $city to $residence was",
            sign="<=",
            expression="10 kilometers",
        )
        statement_short = Statement(
            distance_short, terms=[Entity("El Paso"), Entity("Carl's house")]
        )
        left = ComparableGroup([bob_lived, statement_long])
        right = ComparableGroup([carl_lived, statement_short])
        explanation = left.explain_contradiction(right)
        assert explanation["<Houston>"].name == "El Paso"
        assert contradicts(left, right)


class TestAdd:
    def test_add_does_not_consolidate_factors(self, make_statement):
        left = ComparableGroup(make_statement["crime"])
        right = ComparableGroup(make_statement["crime"])
        added = left + right
        assert len(added) == 2
        assert isinstance(added, ComparableGroup)

    def test_add_factor_to_factorgroup(self, make_statement):
        left = ComparableGroup(make_statement["crime"])
        right = make_statement["crime"]
        added = left + right
        assert len(added) == 2
        assert isinstance(added, ComparableGroup)


class TestUnion:
    def test_factors_combined_because_of_implication(self, make_statement):
        left = ComparableGroup(make_statement["more"])
        right = ComparableGroup(make_statement["more_meters"])
        added = left | right
        assert len(added) == 1
        assert "35 foot" in str(added[0])

    def test_union_with_factor_outside_group(self, make_statement):
        left = ComparableGroup(make_statement["more_meters"])
        right = make_statement["more"]
        added = left | right
        assert len(added) == 1
        assert "35 foot" in str(added[0])

    def test_no_contradiction_because_entities_vary(self, make_statement):
        """
        If these Factors were about the same Term, they would contradict
        and no union would be possible.
        """
        left = ComparableGroup(make_statement["no_shooting_entity_order"])
        right = ComparableGroup(make_statement["shooting"])
        combined = left | right
        assert len(combined) == 2

    def test_union_causes_contradiction(self, make_statement):
        """
        Test Factors about the same Term contradict so no union is possible.
        """
        left = ComparableGroup(make_statement["no_shooting"])
        right = ComparableGroup(make_statement["shooting"])
        combined = left | right
        assert combined is None


class TestConsistent:
    predicate_less_specific = Comparison(
        "${vehicle}'s speed was",
        sign="<",
        expression="30 miles per hour",
    )
    predicate_less_general = Comparison(
        "${vehicle}'s speed was",
        sign="<",
        expression="60 miles per hour",
    )
    predicate_more = Comparison(
        "${vehicle}'s speed was",
        sign=">",
        expression="55 miles per hour",
    )
    predicate_farm = Predicate("$person had a farm")
    slower_specific_statement = Statement(
        predicate_less_specific, terms=Entity("the car")
    )
    slower_general_statement = Statement(
        predicate_less_general, terms=Entity("the pickup")
    )
    faster_statement = Statement(predicate_more, terms=Entity("the pickup"))
    farm_statement = Statement(predicate_farm, terms=Entity("Old MacDonald"))

    def test_group_contradicts_single_factor(self):
        group = ComparableGroup([self.slower_specific_statement, self.farm_statement])
        register = ContextRegister()
        register.insert_pair(Entity("the car"), Entity("the pickup"))
        assert group.contradicts(self.faster_statement, context=register)

    def test_one_statement_does_not_contradict_group(self):
        group = ComparableGroup([self.slower_general_statement, self.farm_statement])
        register = ContextRegister()
        register.insert_pair(Entity("the pickup"), Entity("the pickup"))
        assert not self.faster_statement.contradicts(group, context=register)

    def test_group_inconsistent_with_single_factor(self):
        group = ComparableGroup([self.slower_specific_statement, self.farm_statement])
        register = ContextRegister()
        register.insert_pair(Entity("the car"), Entity("the pickup"))
        assert not group.consistent_with(self.faster_statement, context=register)
        assert not consistent_with(group, self.faster_statement, context=register)

    def test_groups_with_one_statement_consistent(self):
        specific_group = ComparableGroup([self.slower_specific_statement])
        general_group = ComparableGroup([self.faster_statement])
        assert specific_group.consistent_with(general_group)
        assert consistent_with(specific_group, general_group)

    def test_group_inconsistent_with_one_statement(self):
        group = ComparableGroup([self.slower_specific_statement, self.farm_statement])
        register = ContextRegister()
        register.insert_pair(Entity("the car"), Entity("the pickup"))
        assert not group.consistent_with(self.faster_statement, context=register)

    def test_one_statement_inconsistent_with_group(self):
        group = ComparableGroup([self.slower_specific_statement, self.farm_statement])
        register = ContextRegister()
        register.insert_pair(Entity("the pickup"), Entity("the car"))
        assert not self.faster_statement.consistent_with(group, context=register)

    def test_one_statement_consistent_with_group(self):
        group = ComparableGroup([self.slower_general_statement, self.farm_statement])
        register = ContextRegister()
        register.insert_pair(Entity("the pickup"), Entity("the pickup"))
        assert self.faster_statement.consistent_with(group, context=register)

    def test_no_contradiction_of_none(self):
        group = ComparableGroup([self.slower_general_statement, self.farm_statement])
        assert not group.contradicts(None)

    def test_consistent_with_none(self):
        group = ComparableGroup([self.slower_general_statement, self.farm_statement])
        assert group.consistent_with(None)

    def test_two_inconsistent_groups(self):
        left = ComparableGroup([self.slower_specific_statement])
        right = ComparableGroup([self.faster_statement])
        context = ContextRegister()
        context.insert_pair(Entity("the car"), Entity("the pickup"))
        assert not left.consistent_with(right, context=context)

    def test_not_internally_consistent_with_context(self, make_statement):
        context = ContextRegister()
        context.insert_pair(Entity("Alice"), Entity("Alice"))
        context.insert_pair(Entity("Bob"), Entity("Bob"))
        group = ComparableGroup(
            [make_statement["shooting"], make_statement["no_shooting"]]
        )
        assert not group.internally_consistent(context=context)

    @pytest.mark.xfail(reason="Always returns True if no context is given.")
    def test_not_internally_consistent(self, make_statement):
        group = ComparableGroup(
            [make_statement["shooting"], make_statement["no_shooting"]]
        )
        assert not group.internally_consistent()

    def test_all_generic_factors_match(self):
        left = ComparableGroup(Entity("Morning Star"))
        right = ComparableGroup(Entity("Evening Star"))
        context = ContextRegister()
        context.insert_pair(left[0], right[0])
        assert left.all_generic_factors_match(right, context=context)

    def test_all_generic_factors_match_in_statement(self):
        predicate = Predicate("the telescope pointed at $object")
        morning = Statement(predicate=predicate, terms=Entity("Morning Star"))
        evening = Statement(predicate=predicate, terms=Entity("Evening Star"))
        left = ComparableGroup(morning)
        right = ComparableGroup(evening)
        context = ContextRegister()
        context.insert_pair(Entity("Morning Star"), Entity("Evening Star"))
        assert left.all_generic_factors_match(right, context=context)
