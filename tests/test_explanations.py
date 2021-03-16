import operator

from nettlesome.terms import ContextRegister, contradicts, means
from nettlesome.predicates import Predicate
from nettlesome.quantities import Comparison
from nettlesome.statements import Statement
from nettlesome.entities import Entity
from nettlesome.groups import FactorGroup


class TestContext:
    sale = Predicate("$seller sold $product to $buyer")
    fact_al = Statement(sale, terms=[Entity("Al"), Entity("the bull"), Entity("Betty")])
    fact_alice = Statement(
        sale, terms=[Entity("Alice"), Entity("the cow"), Entity("Bob")]
    )

    def test_impossible_register(self):
        context = ContextRegister()
        context.insert_pair(Entity("Al"), Entity("Bob"))
        answers = self.fact_al.update_context_register(self.fact_alice, context, means)
        assert not any(answers)

    def test_possible_register(self):
        register = ContextRegister()
        register.insert_pair(Entity("Al"), Entity("Alice"))
        answers = self.fact_al.update_context_register(self.fact_alice, register, means)
        assert Entity("the bull").short_string in next(answers).keys()

    def test_explain_consistency(self):
        register = ContextRegister()
        register.insert_pair(Entity("Al"), Entity("Alice"))
        explanation = self.fact_al.explain_consistent_with(self.fact_alice, register)

        assert "<the bull> is like <the cow>" in explanation.context.reason
        assert "terms=(Entity(name='Al'" in repr(explanation)


class TestContinuedExplanation:
    def test_implication_and_contradiction(self):
        lived_at = Predicate("$person lived at $residence")
        bob_lived = Statement(lived_at, terms=[Entity("Bob"), Entity("Bob's house")])
        carl_lived = Statement(lived_at, terms=[Entity("Carl"), Entity("Carl's house")])
        explanation = bob_lived.explain_implication(carl_lived)

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

        left = FactorGroup(statement_long)
        right = FactorGroup(statement_short)
        new_explanation = left.explain_contradiction(right, context=explanation)

        expected = "the statement that <bob> lived at <bob's house>"
        assert new_explanation.factor_matches[0].left.key.lower() == expected
        assert new_explanation.factor_matches[0].operation == operator.ge

        part = "from the center of <houston> to <bob's house> was at least 50 mile"
        assert part in new_explanation.factor_matches[1].left.key.lower()
        assert new_explanation.factor_matches[1].operation == contradicts

    def test_two_implying_groups(self, make_statement):
        left_weight = FactorGroup(make_statement["large_weight"])
        right_weight = FactorGroup(make_statement["small_weight"])
        explanation = left_weight.explain_implication(right_weight)
        left_more = FactorGroup(make_statement["way_more"])
        right_more = FactorGroup(make_statement["more"])
        new = left_more.explain_implication(right_more, context=explanation)
        assert len(new.factor_matches) == 2
        assert new.factor_matches[0].operation == operator.ge
        assert new.factor_matches[1].operation == operator.ge

    def test_consistent_and_same_meaning(self, make_statement):
        left_weight = FactorGroup(make_statement["small_weight_bob"])
        right_weight = FactorGroup(make_statement["large_weight"])
        explanation = left_weight.explain_consistent_with(right_weight)
        new_explanation = make_statement["crime_bob"].explain_same_meaning(
            make_statement["crime"], context=explanation
        )
        assert "Because <Bob> is like <Alice>" in str(new_explanation)
        assert "FactorGroup([" not in str(new_explanation)

    def test_same_meaning_factors_not_grouped(self, make_statement):
        left_weight = make_statement["small_weight_bob"]
        right_weight = make_statement["large_weight"]
        explanation = left_weight.explain_consistent_with(right_weight)
        new = FactorGroup(make_statement["crime_bob"]).explain_same_meaning(
            FactorGroup(make_statement["crime"]), context=explanation
        )
        assert "Because <Bob> is like <Alice>" in str(new)
        assert new.factor_matches[1].operation == means
        assert "was at least 100 kilogram, and the statement" in new.short_string

    def test_means_to_contradicts(self, make_statement):
        explanation = make_statement["crime"].explain_same_meaning(
            make_statement["crime_bob"]
        )
        left = FactorGroup([make_statement["shooting_craig"], make_statement["less"]])
        right = FactorGroup([make_statement["murder_craig"], make_statement["more"]])
        new = left.explain_contradiction(right, context=explanation)
        assert len(new.factor_matches) == 2
        assert new.factor_matches[1].operation == contradicts
