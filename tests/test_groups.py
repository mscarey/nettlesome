from nettlesome.comparable import (
    ContextRegister,
    consistent_with,
    contradicts,
    means,
)
from nettlesome.terms import Term
from nettlesome.groups import ComparableGroup
from nettlesome.predicates import Predicate, Comparison
from nettlesome.statements import Statement


class TestMakeGroup:
    def test_group_from_list(self, make_statement):
        factor_list = [make_statement["crime"], make_statement["shooting"]]
        group = ComparableGroup(factor_list)
        assert isinstance(group, ComparableGroup)
        assert group[1] == make_statement["shooting"]

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
            terms=[Term("Ann"), Term("Ben")],
        )
        right = Statement(
            Comparison(
                "the amount that ${taller}'s height exceeded ${shorter}'s height was",
                sign=">=",
                expression="2 feet",
            ),
            terms=[Term("Alice"), Term("Bob")],
        )
        group = ComparableGroup([left, right])
        shorter = group.drop_implied_factors()
        assert len(shorter) == 2

    def test_make_context_register(self):
        alice = Term("Alice")
        bob = Term("Bob")
        craig = Term("Craig")
        dan = Term("Dan")

        left = ComparableGroup([alice, bob])
        right = ComparableGroup([craig, dan])

        register = ContextRegister()
        register.insert_pair(alice, craig)

        gen = left._context_registers(right, comparison=means, context=register)
        answer = next(gen)
        assert answer.get("<Bob>").compare_keys(dan)


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
        alice = Term("Alice")
        craig = Term("Craig")
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
        bob_lived = Statement(lived_at, terms=[Term("Bob"), Term("Bob's house")])
        carl_lived = Statement(lived_at, terms=[Term("Carl"), Term("Carl's house")])
        distance_long = Comparison(
            "the distance from the center of $city to $residence was",
            sign=">=",
            expression="50 miles",
        )
        statement_long = Statement(
            distance_long, terms=[Term("Houston"), Term("Bob's house")]
        )
        distance_short = Comparison(
            "the distance from the center of $city to $residence was",
            sign="<=",
            expression="10 kilometers",
        )
        statement_short = Statement(
            distance_short, terms=[Term("El Paso"), Term("Carl's house")]
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
        predicate_less_specific, terms=Term("the car")
    )
    slower_general_statement = Statement(
        predicate_less_general, terms=Term("the pickup")
    )
    faster_statement = Statement(predicate_more, terms=Term("the pickup"))
    farm_statement = Statement(predicate_farm, terms=Term("Old MacDonald"))

    def test_group_contradicts_single_factor(self):
        group = ComparableGroup([self.slower_specific_statement, self.farm_statement])
        register = ContextRegister()
        register.insert_pair(Term("the car"), Term("the pickup"))
        assert group.contradicts(self.faster_statement, context=register)

    def test_one_statement_does_not_contradict_group(self):
        group = ComparableGroup([self.slower_general_statement, self.farm_statement])
        register = ContextRegister()
        register.insert_pair(Term("the pickup"), Term("the pickup"))
        assert not self.faster_statement.contradicts(group, context=register)

    def test_group_inconsistent_with_single_factor(self):
        group = ComparableGroup([self.slower_specific_statement, self.farm_statement])
        register = ContextRegister()
        register.insert_pair(Term("the car"), Term("the pickup"))
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
        register.insert_pair(Term("the car"), Term("the pickup"))
        assert not group.consistent_with(self.faster_statement, context=register)

    def test_one_statement_inconsistent_with_group(self):
        group = ComparableGroup([self.slower_specific_statement, self.farm_statement])
        register = ContextRegister()
        register.insert_pair(Term("the pickup"), Term("the car"))
        assert not self.faster_statement.consistent_with(group, context=register)

    def test_one_statement_consistent_with_group(self):
        group = ComparableGroup([self.slower_general_statement, self.farm_statement])
        register = ContextRegister()
        register.insert_pair(Term("the pickup"), Term("the pickup"))
        assert self.faster_statement.consistent_with(group, context=register)

    def test_no_contradiction_of_none(self):
        group = ComparableGroup([self.slower_general_statement, self.farm_statement])
        assert not group.contradicts(None)

    def test_consistent_with_none(self):
        group = ComparableGroup([self.slower_general_statement, self.farm_statement])
        assert group.consistent_with(None)

    def test_not_internally_consistent(self, make_statement):
        group = ComparableGroup(
            [make_statement["shooting"], make_statement["no_shooting"]]
        )
        assert not group.internally_consistent()