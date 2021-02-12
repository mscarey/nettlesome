from nettlesome.comparable import ContextRegister, means

from nettlesome.explanations import Explanation
from nettlesome.predicates import Predicate
from nettlesome.statements import Statement
from nettlesome.terms import Term


class TestContext:
    sale = Predicate("$seller sold $product to $buyer")
    fact_al = Statement(sale, terms=[Term("Al"), Term("the bull"), Term("Betty")])
    fact_alice = Statement(sale, terms=[Term("Alice"), Term("the cow"), Term("Bob")])

    def test_impossible_register(self):
        context = ContextRegister()
        context.insert_pair(Term("Al"), Term("Bob"))
        answers = self.fact_al.update_context_register(self.fact_alice, context, means)
        assert not any(answers)

    def test_possible_register(self):
        register = ContextRegister()
        register.insert_pair(Term("Al"), Term("Alice"))
        answers = self.fact_al.update_context_register(self.fact_alice, register, means)
        assert Term("the bull").short_string in next(answers).keys()

    def test_explain_consistency(self):
        register = ContextRegister()
        register.insert_pair(Term("Al"), Term("Alice"))
        answers = self.fact_al.explain_consistent_with(self.fact_alice, register)
        explanation = Explanation(
            factor_matches=[(self.fact_al, self.fact_alice)], context=answers
        )
        assert "<the bull> is like <the cow>" in explanation.reason
