Changelog
=========
0.3.0 (2021-03-19)
------------------
- add FactorMatch NamedTuples to be listed in Explanation
- remove FactorGroup.comparison method. Instead use implies, contradicts, etc.
- Factor "explanations" methods yield Explanation, not ContextRegister
- add FactorGroup.explanations_implied_by method
- fix bug: shares_all_factors passed without checking all factors
- fix bug: two empty FactorGroups should have same meaning

0.2.2 (2021-03-08)
------------------
- fix: non-generic Entities with different names don't have same meaning

0.2.1 (2021-03-07)
------------------
- fix bug: multiple UnitRegistries conflicted
- fix bug: Comparison.implies(Predicate) should be False
- merge "comparable" module into "terms" module
- fix bug: Comparison >= Predicate should be False

0.2.0 (2021-03-02)
------------------
- create UnitRange, DateRange, and NumberRange classes

0.1.2 (2021-02-26)
------------------
- fix bug: Comparable._context_registers could fail when a Factor's terms could be reordered
- add repr method for TermSequence

0.1.1 (2021-02-23)
------------------
- fix scaling of numbers in FiniteSet when comparing with different physical units

0.1.0 (2021-02-22)
------------------
- Migrate semantic reasoning features from AuthoritySpoke