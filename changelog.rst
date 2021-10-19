Changelog
=========
0.6.0 (2021-10-19)
------------------
- replace NumberRange with IntRange and FloatRange
- replace Marshmallow serializers with Pydantic
- Entity and Predicate models don't allow extra fields
- add equal sign as default value for QuantityRange sign
- fix bug: bool(Term) returned False if the Term's "length" was 0
- remove custom reprs that can be replaced by Pydantic BaseModel repr

0.5.1 (2021-05-20)
------------------
- internally_consistent raises ValueError identifying contradiction

0.5.0 (2021-05-02)
------------------
- change Doctrine class name to Assertion
- change Predicate param name from template to content
- add Marshmallow schemas
- add APISpec for documenting Marshmallow schemas

0.4.0 (2021-04-08)
------------------
- Fact constructor accepts truth param
- allow alternate methods to specify context for .implies()
- add string expansion to ContextRegister.from_lists
- all Explanation.from_context calls expand strings
- disallow repeated Terms in TermSequence
- fix bug: _context_registers method yielded same ContextRegister repeatedly
- add DuplicateTermError
- fix bug: FactorGroup.union used duplicative TermSequence
- ContextRegister.from_lists works with unequal length lists
- add contradicts_same_context method
- add repr method for subclasses of Comparable to inherit

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