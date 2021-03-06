Changelog
=========
dev
------------------
- fix bug: multiple UnitRegistries conflicted
- fix bug: Comparison.implies(Predicate) should be False
- merge `comparable` module into `terms` module
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