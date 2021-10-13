"""Base classes for Terms and Factors that can be compared."""

from __future__ import annotations

from abc import ABC
from copy import deepcopy
import functools
from itertools import permutations, zip_longest
import logging
import operator
import textwrap
from typing import Any, Callable, ClassVar, Dict, Iterable, Iterator
from typing import List, NamedTuple, Optional, Sequence, Tuple, Union
from typing import KeysView, ValuesView, ItemsView

from pydantic import BaseModel

logger = logging.getLogger(__name__)


def consistent_with(
    left: Comparable, right: Comparable, context: Optional[ContextRegister] = None
) -> bool:
    """
    Call :meth:`.Factor.consistent_with` as function alias.

    This exists because :func:`Factor._context_registers` needs
    a function rather than a method for the `comparison` variable.

    :returns:
        whether ``other`` is consistent with ``self``.
    """
    context = context or ContextRegister()
    return left.consistent_with(right, context)


def means(left: Comparable, right: Comparable) -> bool:
    """
    Call :meth:`.Factor.means` as function alias.

    This exists because :class:`.Explanation` objects expect
    a function rather than a method

    :returns:
        whether ``other`` is another :class:`Factor` with the same
        meaning as ``self``.
    """
    return left.means(right)


def contradicts(left: Comparable, right: Comparable) -> bool:
    """
    Call :meth:`.Factor.contradicts` as function alias.

    This exists because :class:`.Explanation` objects expect
    a function rather than a method

    :returns:
        whether ``other`` is another :class:`Factor` that can
        contradict ``self``, assuming relevant context factors
    """
    return left.contradicts(right)


def new_context_helper(func: Callable):
    r"""
    Search :class:`.Factor` for generic :class:`.Factor`\s to use in new context.

    Decorators for memoizing generic :class:`.Factor`\s.
    Used when changing an abstract :class:`.Rule` from
    one concrete context to another.

    If a :class:`list` has been passed in rather than a :class:`dict`, uses
    the input as a series of :class:`Factor`\s to replace the
    :attr:`~Factor.generic_terms` from the calling object.

    Also, if ``changes`` contains a replacement for the calling
    object, the decorator returns the replacement and never calls
    the decorated function.

    :param factor:
        a :class:`.Factor` that is having its generic :class:`.Factor`\s
        replaced to change context (for instance, to change to the context
        of a different case involving parties represented by different
        :class:`.Entity` objects).

    :param changes:
        indicates which generic :class:`.Factor`\s within ``factor`` should
        be replaced and what they should be replaced with.

    :returns:
        a new :class:`.Factor` object in the new context.
    """

    @functools.wraps(func)
    def wrapper(
        factor: Comparable,
        changes: ContextMemo,
        terms_to_replace: Optional[Sequence[Term]] = None,
        source: Optional[Term] = None,
    ) -> Comparable:

        expanded_changes = ContextRegister.create(
            changes=changes,
            current=factor,
            incoming=source,
            terms_to_replace=terms_to_replace,
        )

        for old, new in expanded_changes.items():
            if factor.short_string == old or factor.__dict__.get("name") == old:
                return new

        return func(factor, expanded_changes)

    return wrapper


def expand_string_from_source(term: Union[str, Term], source: Comparable) -> Term:
    """Replace ``term`` with the real term it references, if ``term`` is a string reference."""
    if isinstance(term, str):
        result: Optional[Term] = source.get_factor(term)
    else:
        return term
    if result is None:
        raise ValueError(f'Unable to find replacement term for text "{term}"')
    return result


def expand_strings_from_source(
    to_expand: Sequence[Union[str, Term]], source: Optional[Comparable]
) -> List[Term]:
    """Make list of Terms by replacing strings with the real Terms they reference."""
    return [expand_string_from_source(change, source) for change in to_expand]


class Comparable(ABC):
    """
    Objects that can be compared for implication, same meaning, contradiction, and consistency.

    :attr generic:
        Whether the object is referred to in a generic sense. If True, substituting
        this object for another generic object of the same class does not change the
        meaning of other Comparable objects that incorporate this one as a term.

    :attr absent:
        Indicates the absence of the described object. The absence of two
        contradictory objects is not contradictory.

    :attr name:
        An identifier for this object. May be used as a shorthand way of referring to
        this object when replacing another Comparable object's generic terms.

    :attr plural:
        Indicates whether the object refers to multiple things.
    """

    generic: bool
    absent: bool
    context_factor_names: ClassVar[Tuple[str, ...]]

    @property
    def key(self) -> str:
        """Return string representation of self for use as a key in a ContextRegister."""
        return self.short_string

    @property
    def short_string(self) -> str:
        """Summarize self without line breaks."""
        return textwrap.shorten(str(self), width=5000, placeholder="...")

    @property
    def wrapped_string(self) -> str:
        """Return string representation with line breaks."""
        return str(self)

    @property
    def recursive_terms(self) -> Dict[str, Term]:
        r"""
        Collect `self`'s :attr:`terms`, and their :attr:`terms`, recursively.

        :returns:
            a :class:`dict` (instead of a :class:`set`,
            to preserve order) of :class:`Term`\s.
        """
        answers: Dict[str, Term] = {}

        for context in self.term_sequence:
            if context is not None:
                answers.update(context.recursive_terms)
        return answers

    @property
    def term_sequence(self) -> TermSequence:
        r"""
        Get :class:`Factor`\s used in comparisons with other :class:`Factor`\s.

        :returns:
            a tuple of attributes that are designated as the ``terms``
            for whichever subclass of :class:`Factor` calls this method. These
            can be used for comparing objects using :meth:`consistent_with`
        """
        context: List[Optional[Term]] = []
        for factor_name in self.context_factor_names:
            next_factor: Optional[Term] = self.__dict__.get(factor_name)
            context.append(next_factor)
        return TermSequence(context)

    def __ge__(self, other: Optional[Comparable]) -> bool:
        """
        Call :meth:`implies` as an alias.

        :returns:
            bool indicating whether ``self`` implies ``other``
        """
        return bool(self.implies(other))

    def __gt__(self, other: Optional[Comparable]) -> bool:
        """Test whether ``self`` implies ``other`` and ``self`` != ``other``."""
        if other is None:
            return True
        return bool(self.implies(other) and not self.compare_keys(other))

    def __str__(self):
        text = f"the {self.__class__.__name__.lower()}" + " {}"
        if self.generic:
            text = f"<{text}>"
        if self.absent:
            text = "absence of " + text
        return text

    def _all_generic_terms_match(
        self, other: Comparable, context: ContextRegister
    ) -> bool:
        if all(
            all(
                context.assigns_same_value_to_key_factor(
                    other=other_register, key_factor=generic
                )
                for generic in self.generic_terms()
            )
            for other_register in self._context_registers(
                other=other, comparison=means, context=context
            )
        ):
            return True
        return False

    def consistent_with(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ) -> bool:
        """
        Check if self and other can be non-contradictory.

        :returns:
            a bool indicating whether there's at least one way to
            match the :attr:`terms` of ``self`` and ``other``,
            such that they fit the relationship ``comparison``.
        """

        if other is None:
            return True
        return any(
            explanation is not None
            for explanation in self.explanations_consistent_with(other, context)
        )

    def compare_keys(self, other: Optional[Comparable]) -> bool:
        """
        Test if self and other would be considered identical in a ContextRegister.

        May return True even if Python's == operation would return False.

        May return False even if the .means() method would return True because self and other
        have generic terms.
        """
        return other is not None and self.key == other.key

    def compare_terms(self, other: Comparable, relation: Callable) -> bool:
        r"""
        Test if relation holds for corresponding context factors of self and other.

        This doesn't track a persistent :class:`ContextRegister` as it goes
        down the sequence of :class:`Factor` pairs. Perhaps(?) this simpler
        process can weed out :class:`Factor`\s that clearly don't satisfy
        a comparison before moving on to the more costly :class:`Analogy`
        process. Or maybe it's useful for testing.
        """
        orderings = self.term_permutations()
        for ordering in orderings:
            if self.compare_ordering_of_terms(
                other=other, relation=relation, ordering=ordering
            ):
                return True
        return False

    def compare_ordering_of_terms(
        self, other: Comparable, relation: Callable, ordering: TermSequence
    ) -> bool:
        """
        Determine whether one ordering of self's terms matches other's terms.

        Multiple term orderings exist where the terms can be rearranged without
        changing the Fact's meaning.

        For instance, "<Ann> and <Bob> both were members of the same family" has a
        second ordering "<Bob> and <Ann> both were members of the same family".
        """
        for i, self_factor in enumerate(ordering):
            if not (self_factor is other.term_sequence[i] is None):
                if not (self_factor and relation(self_factor, other.term_sequence[i])):
                    return False
        return True

    def _context_registers(
        self,
        other: Optional[Comparable],
        comparison: Callable,
        context: ContextRegister,
    ) -> Iterator[ContextRegister]:
        r"""
        Search for ways to match :attr:`terms` of ``self`` and ``other``.

        :yields:
            all valid ways to make matches between
            corresponding :class:`Factor`\s.
        """
        if other is None:
            yield context
        else:
            already_found: List[ContextRegister] = []
            for term_permutation in self.term_permutations():
                for other_permutation in other.term_permutations():
                    for answer in term_permutation.ordered_comparison(
                        other=other_permutation, operation=comparison, context=context
                    ):
                        if not any(answer.means(entry) for entry in already_found):
                            already_found.append(answer)
                            yield answer

    def contradicts(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ) -> bool:
        """
        Test whether ``self`` implies the absence of ``other``.

        :returns:
            ``True`` if self and other can't both be true at
            the same time. Otherwise returns ``False``.
        """

        if other is None:
            return False
        return any(
            explanation is not None
            for explanation in self.explanations_contradiction(other, context)
        )

    def _contradicts_if_present(
        self, other: Comparable, context: Explanation
    ) -> Iterator[Explanation]:
        """
        Test if ``self`` would contradict ``other`` if neither was ``absent``.

        The default is to yield nothing where no class-specific method is available.
        """
        yield from iter([])

    def explain_same_meaning(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[Explanation]:
        """
        Get one explanation of why self and other have the same meaning.

            >>> from nettlesome import Statement, Entity
            >>> hades_curse = Statement(
            ...    predicate="$deity cursed $target",
            ...    terms=[Entity(name="Hades"), Entity(name="Persephone")])
            >>> aphrodite_curse = Statement(
            ...    predicate="$deity cursed $target",
            ...    terms=[Entity(name="Aphrodite"), Entity(name="Narcissus")])
            >>> print(hades_curse.explain_same_meaning(aphrodite_curse))
            Because <Hades> is like <Aphrodite>, and <Persephone> is like <Narcissus>,
              the statement that <Hades> cursed <Persephone>
            MEANS
              the statement that <Aphrodite> cursed <Narcissus>

        """
        explanations = self.explanations_same_meaning(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explain_consistent_with(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[Explanation]:
        """Get one explanation of why self and other need not contradict."""
        explanations = self.explanations_consistent_with(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explain_contradiction(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[Explanation]:
        r"""
        Get one explanation of why self and other contradict.

        Using the :meth:`~nettlesome.terms.Comparable.explanations_contradiction` method,
        generates one :class:`~nettlesome.terms.Explanation` of how an analogy between the
        generic terms of the two objects can make them contradictory.

        In this example using two :class:`~nettlesome.groups.FactorGroup`\s,
        if the three :class:`~nettlesome.statements.Statement`\s in ``brexit`` were asserted
        about the three :class:`~nettlesome.entities.Entity` terms in ``nafta``,
        there would be an inconsistency as to whether one pair of Entities
        signed a treaty with each other.

        >>> from nettlesome import Statement, Entity, FactorGroup
        >>> nafta = FactorGroup([
        ...     Statement(predicate="$country1 signed a treaty with $country2",
        ...               terms=[Entity(name="Mexico"), Entity(name="USA")]),
        ...     Statement(predicate="$country2 signed a treaty with $country3",
        ...               terms=[Entity(name="USA"), Entity(name="Canada")]),
        ...     Statement(predicate="$country3 signed a treaty with $country1",
        ...           terms=[Entity(name="USA"), Entity(name="Canada")])])
        >>> brexit = FactorGroup([
        ...     Statement(predicate="$country1 signed a treaty with $country2",
        ...               terms=[Entity(name="UK"), Entity(name="European Union")]),
        ...     Statement(predicate="$country2 signed a treaty with $country3",
        ...               terms=[Entity(name="European Union"), Entity(name="Germany")]),
        ...     Statement(predicate="$country3 signed a treaty with $country1",
        ...          terms=[Entity(name="Germany"), Entity(name="UK")], truth=False)])
        >>> print(nafta.explain_contradiction(brexit))
        Because <Mexico> is like <Germany>, and <USA> is like <UK>,
          the statement that <Mexico> signed a treaty with <USA>
        CONTRADICTS
          the statement it was false that <Germany> signed a treaty with <UK>
        """
        explanations = self.explanations_contradiction(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explain_implication(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[Explanation]:
        """Get one explanation of why self implies other."""
        explanations = self.explanations_implication(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explain_implied_by(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[Explanation]:
        """Get one explanation of why self implies other."""
        explanations = self.explanations_implied_by(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def _contexts_consistent_with(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        context = context or ContextRegister()
        for possible in self.possible_contexts(other, context):
            if not self.contradicts(other, context=possible):
                yield possible

    def _explanations_consistent_with(
        self,
        other: Comparable,
        explanation: Explanation,
    ) -> Iterator[Explanation]:

        for new_context in self._contexts_consistent_with(
            other=other, context=explanation.context
        ):
            yield explanation.with_context(new_context)

    def explanations_consistent_with(
        self,
        other: Comparable,
        context: Optional[Union[Explanation, ContextRegister]] = None,
    ) -> Iterator[Explanation]:
        """
        Test whether ``self`` does not contradict ``other``.

        This should only be called after confirming that ``other``
        is not ``None``.

        :returns:
            ``True`` if self and other can't both be true at
            the same time. Otherwise returns ``False``.
        """
        context = context = Explanation.from_context(
            context=context, current=self, incoming=other
        )
        for new in self._explanations_consistent_with(other, explanation=context):
            yield new.with_match(FactorMatch(self, consistent_with, other))

    def _explanations_contradiction(
        self, other: Comparable, explanation: Explanation
    ) -> Iterator[Explanation]:
        if not isinstance(other, Comparable):
            raise TypeError(
                f"{self.__class__} objects may only be compared for "
                + "contradiction with other Factor objects or None."
            )
        if isinstance(other, self.__class__):
            if not self.__dict__.get("absent"):
                if not other.__dict__.get("absent"):
                    yield from self._contradicts_if_present(other, explanation)
                else:
                    yield from self._implies_if_present(other, explanation)
            elif self.__dict__.get("absent"):
                # No contradiction between absences of any two Comparables
                if not other.__dict__.get("absent"):
                    explanation_reversed = explanation.with_context(
                        explanation.context.reversed()
                    )
                    test = other._implies_if_present(self, explanation_reversed)
                    for new_explanation in test:
                        yield new_explanation.with_context(
                            new_explanation.context.reversed()
                        )
        elif not isinstance(other, Term):
            explanation_reversed = explanation.reversed_context()
            yield from other._explanations_contradiction(
                self, explanation=explanation_reversed
            )

    def explanations_contradiction(
        self,
        other: Comparable,
        context: Optional[Union[Explanation, ContextRegister]] = None,
    ) -> Iterator[Explanation]:
        """
        Test whether ``self`` :meth:`implies` the absence of ``other``.

        This should only be called after confirming that ``other``
        is not ``None``.

        :returns:
            ``True`` if self and other can't both be true at
            the same time. Otherwise returns ``False``.
        """
        context = Explanation.from_context(
            context=context, current=self, incoming=other
        )
        for new_explanation in self._explanations_contradiction(
            other=other, explanation=context
        ):
            yield new_explanation.with_match(
                FactorMatch(left=self, operation=contradicts, right=other)
            )

    def _explanations_implication(
        self, other: Comparable, explanation: Explanation
    ) -> Iterator[Explanation]:
        if not isinstance(other, Comparable):
            raise TypeError(
                f"{self.__class__} objects may only be compared for "
                + "implication with other Comparable objects or None."
            )
        if isinstance(other, self.__class__):
            if self.__dict__.get("absent"):
                reversed_explanation = explanation.with_context(
                    explanation.context.reversed()
                )
                if other.__dict__.get("absent"):
                    test = other._implies_if_present(self, reversed_explanation)
                else:
                    test = other._contradicts_if_present(self, reversed_explanation)
                yield from (
                    register.with_context(register.context.reversed())
                    for register in test
                )

            elif not other.__dict__.get("absent"):
                yield from self._implies_if_present(other, explanation)
            else:
                yield from self._contradicts_if_present(other, explanation)

    def explanations_implication(
        self,
        other: Comparable,
        context: Optional[Union[Explanation, ContextRegister]] = None,
    ) -> Iterator[Explanation]:
        r"""
        Generate :class:`.ContextRegister`\s that cause `self` to imply `other`.

        If self is `absent`, then generate a ContextRegister from other's point
        of view and then swap the keys and values.
        """
        context = context = Explanation.from_context(
            context=context, current=self, incoming=other
        )
        for new_explanation in self._explanations_implication(
            other=other, explanation=context
        ):
            yield new_explanation.with_match(
                FactorMatch(left=self, operation=operator.ge, right=other)
            )

    def _explanations_implied_by(
        self, other: Comparable, explanation: Explanation
    ) -> Iterator[Explanation]:
        reversed_explanation = explanation.with_context(explanation.context.reversed())
        for new in other._explanations_implication(
            self, explanation=reversed_explanation
        ):
            yield new.with_context(new.context.reversed())

    def explanations_implied_by(
        self,
        other: Comparable,
        context: Optional[Union[ContextRegister, Explanation]] = None,
    ) -> Iterator[Explanation]:
        """Generate explanations for how other may imply self."""
        context = context = Explanation.from_context(
            context=context, current=self, incoming=other
        )
        for new in self._explanations_implied_by(other=other, explanation=context):
            yield new.with_match(FactorMatch(other, operator.ge, self))

    def _explanations_same_meaning(
        self, other: Comparable, explanation: Explanation
    ) -> Iterator[Explanation]:
        if (
            self.__class__ == other.__class__
            and self.generic == other.generic
            and self.absent == other.absent
        ):
            yield from self._means_if_concrete(other, explanation)

    def explanations_same_meaning(
        self,
        other: Comparable,
        context: Optional[Union[Explanation, ContextRegister]] = None,
    ) -> Iterator[Explanation]:
        """Generate ways to match contexts of self and other so they mean the same."""
        context = context = Explanation.from_context(
            context=context, current=self, incoming=other
        )
        for new in self._explanations_same_meaning(other=other, explanation=context):
            yield new.with_match(FactorMatch(self, means, other))

    def _implies_if_present(
        self, other: Comparable, explanation: Explanation
    ) -> Iterator[Explanation]:
        """
        Find if ``self`` would imply ``other`` if they aren't absent.

        :returns:
            bool indicating whether ``self`` would imply ``other``,
            under the assumption that neither self nor other has
            the attribute ``absent == True``.
        """
        if isinstance(other, self.__class__):
            if not self.generic:
                yield from self._implies_if_concrete(other, explanation)

    def generic_terms(self) -> List[Term]:
        """Get Terms that can be replaced without changing ``self``'s meaning."""
        return list(self.generic_terms_by_str().values())

    def generic_terms_by_str(self) -> Dict[str, Term]:
        r"""
        Index Terms that can be replaced without changing ``self``'s meaning.

        :returns:
            a :class:`dict` with the names of ``self``\'s
            generic :class:`.Factor`\s as keys and the :class:`.Factor`\s
            themselves as values.
        """
        generics: Dict[str, Term] = {}
        for factor in self.term_sequence:
            if factor is not None:
                for generic in factor.generic_terms():
                    generics[generic.short_string] = generic
        return generics

    def get_factor(self, query: str) -> Optional[Term]:
        """
        Search for Comparable with str or name matching query.

        :param query:
            a string that matches the desired Comparable's ``name`` or the
            output of its __str__ method.
        """
        result = self.get_factor_by_str(query)
        if result is None:
            result = self.get_factor_by_name(query)
        return result

    def get_factor_by_name(self, name: str) -> Optional[Term]:
        """
        Search of ``self`` and ``self``'s attributes for :class:`Factor` with specified ``name``.

        :returns:
            a :class:`Comparable` with the specified ``name`` attribute
            if it exists, otherwise ``None``.
        """
        factors_to_search = self.recursive_terms
        for value in factors_to_search.values():
            if hasattr(value, "name") and value.name == name:
                return value
        return None

    def get_factor_by_str(self, query: str) -> Optional[Term]:
        """
        Search of ``self`` and ``self``'s attributes for :class:`Factor` with specified string.

        :returns:
            a :class:`Factor` with the specified string
            if it exists, otherwise ``None``.
        """
        for name, factor in self.recursive_terms.items():
            if name == query:
                return factor
        return None

    def implied_by(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ):
        r"""
        Find whether other implies self.

        :param other:
            a second Comparable to compare with self

        :param context:
            correspondences between :class:`Term`\s in self and other

        :returns:
            whether other implies self.
        """
        if other is None:
            return False
        return any(self.explanations_implied_by(other, context=context))

    def implies(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ) -> bool:
        r"""
        Test whether ``self`` implies ``other``.

        When inherited by :class:`~nettlesome.groups.FactorGroup`\, this method will
        check whether every :class:`~nettlesome.statements.Statement` in ``other``
        is implied by some Statement in ``self``.

            >>> from nettlesome import Entity, Comparison, Statement, FactorGroup
            >>> over_100y = Comparison(content="the distance between $site1 and $site2 was", sign=">", expression="100 yards")
            >>> under_1mi = Comparison(content="the distance between $site1 and $site2 was", sign="<", expression="1 mile")
            >>> protest_facts = FactorGroup(
            ...     [Statement(predicate=over_100y, terms=[Entity(name="the political convention"), Entity(name="the police cordon")]),
            ...      Statement(predicate=under_1mi, terms=[Entity(name="the police cordon"), Entity(name="the political convention")])])
            >>> over_50m = Comparison(content="the distance between $site1 and $site2 was", sign=">", expression="50 meters")
            >>> under_2km = Comparison(content="the distance between $site1 and $site2 was", sign="<=", expression="2 km")
            >>> speech_zone_facts = FactorGroup(
            ...     [Statement(predicate=over_50m, terms=[Entity(name="the free speech zone"), Entity(name="the courthouse")]),
            ...      Statement(predicate=under_2km, terms=[Entity(name="the free speech zone"), Entity(name="the courthouse")])])
            >>> protest_facts.implies(speech_zone_facts)
            True

        """
        if other is None:
            return True
        return any(
            register is not None
            for register in self.explanations_implication(other, context=context)
        )

    def _implies_if_concrete(
        self, other: Comparable, explanation: Explanation
    ) -> Iterator[Explanation]:
        """
        Find if ``self`` would imply ``other`` if they aren't absent or generic.

        Used to test implication based on :attr:`terms`,
        usually after a subclass has injected its own tests
        based on other attributes.

        :returns:
            context assignments where ``self`` would imply ``other``,
            under the assumptions that neither ``self`` nor ``other``
            has ``absent=True``, neither has ``generic=True``, and
            ``other`` is an instance of ``self``'s class.
        """
        if self.compare_terms(other, operator.ge):
            for new_context in self._context_registers(
                other, operator.ge, explanation.context
            ):
                yield explanation.with_context(new_context)

    def implies_same_context(self, other: Comparable) -> bool:
        """Check if self would imply other if their generic terms are matched in order."""
        same_context = self.make_same_context(other)
        return self.implies(other, context=same_context)

    def contradicts_same_context(self, other: Comparable) -> bool:
        """
        Check if self contradicts other if Terms with the same name always match.

        Used to check consistency of FactorGroups.
        """
        same_context = self.make_same_context(other)
        return self.contradicts(other, context=same_context)

    def make_same_context(self, other: Comparable):
        """Make ContextRegister assuming all terms in self correspond to the same terms in other."""
        result = ContextRegister()
        for key in self.generic_terms():
            result.insert_pair(key, key)
        for value in other.generic_terms():
            result.insert_pair(value, value)
        return result

    def likely_contexts(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        r"""
        Generate contexts that match Terms from Factors with corresponding meanings.

        :param other:
            an object being compared to ``self``

        :param context:
            pairs of terms that must remain matched when yielding new contexts

        :yields:
            :class:`.ContextRegister`\s matching all :class:`.Term`\s of ``self``
            and ``other``.
        """

        context = context or ContextRegister()
        same_meaning = self._likely_context_from_meaning(other, context)
        if same_meaning:
            implied = self._likely_context_from_implication(other, same_meaning)
        else:
            implied = self._likely_context_from_implication(other, context)
        if implied:
            yield implied
        if same_meaning:
            yield same_meaning
        yield context

    def _likely_context_from_implication(
        self, other: Comparable, context: ContextRegister
    ) -> Optional[ContextRegister]:
        new_context = None
        if self.implies(other, context=context) or other.implies(
            self, context=context.reversed()
        ):
            new_context = self._update_context_from_factors(other, context)
        if new_context and new_context != context:
            return new_context
        return None

    def _likely_context_from_meaning(
        self, other: Comparable, context: ContextRegister
    ) -> Optional[ContextRegister]:
        new_context = None
        if self.means(other, context=context) or other.means(
            self, context=context.reversed()
        ):
            new_context = self._update_context_from_factors(other, context)
        if new_context and new_context != context:
            return new_context
        return None

    def make_generic(self) -> Comparable:
        """
        Get a copy of ``self`` except ensure ``generic`` is ``True``.

        .. note::
            The new object created with this method will still have all the
            attributes of ``self`` except ``generic=False``.

        :returns: a new object changing ``generic`` to ``True``.
        """
        result = deepcopy(self)
        result.generic = True
        return result

    def means(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ) -> bool:
        r"""
        Test whether ``self`` and ``other`` have identical meanings.

        :returns:
            whether ``other`` is another :class:`Factor`
            with the same meaning as ``self``.

        Not the same as an
        equality comparison with the ``==`` symbol, which simply
        converts ``self``\'s and ``other``\'s fields to tuples
        and compares them.

        >>> from nettlesome import Statement, Entity
        >>> hades_curse = Statement(predicate="$deity cursed $target",
        ...    terms=[Entity(name="Hades"), Entity(name="Persephone")])
        >>> aphrodite_curse = Statement(predicate="$deity cursed $target",
        ...    terms=[Entity(name="Aphrodite"), Entity(name="Narcissus")])
        >>> hades_curse.means(aphrodite_curse)
        True
        """
        if other is None:
            return False
        return any(
            explanation is not None
            for explanation in self.explanations_same_meaning(other, context=context)
        )

    def _means_if_concrete(
        self, other: Comparable, explanation: Explanation
    ) -> Iterator[Explanation]:
        """
        Test equality based on :attr:`terms`.

        Usually called after a subclass has injected its own tests
        based on other attributes.

        :returns:
            bool indicating whether ``self`` would equal ``other``,
            under the assumptions that neither ``self`` nor ``other``
            has ``absent=True``, neither has ``generic=True``, and
            ``other`` is an instance of ``self``'s class.
        """
        if self.compare_terms(other, means):
            for new_context in self._context_registers(
                other, comparison=means, context=explanation.context
            ):
                yield explanation.with_context(new_context)

    @new_context_helper
    def new_context(self, changes: ContextRegister) -> Comparable:
        r"""
        Create new :class:`Comparable`, replacing keys of ``changes`` with values.

        :param changes:
            has :class:`.Comparable`\s to replace as keys, and has
            their replacements as the corresponding values.

        :returns:
            a new :class:`.Comparable` object with the replacements made.
        """
        new_dict = self.own_attributes()
        for name in self.context_factor_names:
            new_dict[name] = self.__dict__[name].new_context(changes)
        return self.__class__(**new_dict)

    def own_attributes(self) -> Dict[str, Any]:
        """
        Return attributes of ``self`` that aren't inherited from another class.

        Used for getting parameters to pass to :meth:`~Factor.__init__`
        when generating a new object.
        """
        return self.__dict__.copy()

    def possible_contexts(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        r"""
        Get permutations of generic Factor assignments not ruled out by the known context.

        :param other:
            another :class:`.Comparable` object with generic :class:`.Factor`\s

        :yields: all possible ContextRegisters linking the two :class:`.Comparable`\s
        """
        context = context or ContextRegister()
        unused_self = [
            factor
            for factor in self.generic_terms()
            if factor.short_string not in context.matches.keys()
        ]
        unused_other = [
            factor
            for factor in other.generic_terms()
            if factor.short_string not in context.reverse_matches.keys()
        ]
        if not (unused_self and unused_other):
            yield context
        else:
            for permutation in permutations(unused_other):
                incoming = ContextRegister()
                for key, value in zip(unused_self, permutation):
                    incoming.insert_pair(key=key, value=value)
                merged_context = context.merged_with(incoming)
                if merged_context:
                    yield merged_context

    def _registers_for_interchangeable_context(
        self, matches: ContextRegister
    ) -> Iterator[ContextRegister]:
        r"""
        Find possible combination of interchangeable :attr:`terms`.

        :yields:
            context registers with every possible combination of
            ``self``\'s and ``other``\'s interchangeable
            :attr:`terms`.
        """
        yield matches

    def term_permutations(self) -> Iterator[TermSequence]:
        """Generate permutations of context factors that preserve same meaning."""
        yield self.term_sequence

    def _update_context_from_factors(
        self, other: Comparable, context: ContextRegister
    ) -> Optional[ContextRegister]:
        """
        Update context produce a likely way self corresponds to other.

        It's not guaranteed that by exchanging generic terms in order will
        produce the right updated context.
        """
        incoming = ContextRegister.from_lists(
            to_replace=self.generic_terms(), replacements=other.generic_terms()
        )
        updated_context = context.merged_with(incoming)
        return updated_context

    def update_context_register(
        self,
        other: Optional[Comparable],
        context: ContextRegister,
        comparison: Callable,
    ) -> Iterator[ContextRegister]:
        r"""
        Find ways to update ``self_mapping`` to allow relationship ``comparison``.

        :param other:
            another :class:`Comparable` being compared to ``self``

        :param register:
            keys representing :class:`Comparable`\s from ``self``'s context and
            values representing :class:`Comparable`\s in ``other``'s context.

        :param comparison:
            a function defining the comparison that must be ``True``
            between ``self`` and ``other``. Could be :meth:`Comparable.means` or
            :meth:`Comparable.__ge__`.

        :yields:
            every way that ``self_mapping`` can be updated to be consistent
            with ``self`` and ``other`` having the relationship
            ``comparison``.
        """
        if other and not isinstance(other, Comparable):
            raise TypeError
        context = context or ContextRegister()
        for incoming_register in self._context_registers(
            other, comparison, context=context
        ):
            for new_register_variation in self._registers_for_interchangeable_context(
                incoming_register
            ):
                register_or_none = context.merged_with(new_register_variation)
                if register_or_none is not None:
                    yield register_or_none


class ContextRegister:
    r"""
    A mapping of corresponding :class:`Factor`\s from two different contexts.

    When :class:`Factor`\s are matched in a ContextRegister, it indicates
    that their relationship can be described by a comparison function
    like :func:`means`, :meth:`Factor.implies`, or :meth:`Factor.consistent_with`\.
    """

    def __init__(self):
        """Index Comparables on each side by names of Comparables on the other side."""
        self._matches = {}
        self._reverse_matches = {}

    def __getitem__(self, item: str) -> Term:
        return self.matches[item]

    def __len__(self):
        return len(self.matches)

    def __repr__(self) -> str:
        return "ContextRegister({})".format(self._matches.__repr__())

    def __str__(self) -> str:
        return f"ContextRegister({self.reason})"

    @property
    def reason(self) -> str:
        """Make statement matching analagous context factors of self and other."""
        similies = [
            f'{key.short_string} {"are" if (key.__dict__.get("plural")) else "is"} like {value.short_string}'
            for key, value in self.factor_pairs()
        ]
        if len(similies) > 1:
            similies[-2:] = [", and ".join(similies[-2:])]
        return ", ".join(similies)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.matches == other.matches

    @property
    def matches(self) -> Dict[str, Term]:
        """Get names of ``self``'s Terms matched to ``other``'s Terms."""
        return self._matches

    @property
    def reverse_matches(self) -> Dict[str, Term]:
        """Get names of ``other``'s Terms matched to ``self``'s Terms."""
        return self._reverse_matches

    @classmethod
    def _from_lists(
        cls,
        to_replace: Sequence[Term],
        replacements: Sequence[Term],
    ) -> ContextRegister:
        pairs = zip(to_replace, replacements)
        new = cls()
        for pair in pairs:
            new.insert_pair(pair[0], pair[1])
        return new

    @classmethod
    def from_lists(
        cls,
        to_replace: Sequence[Union[Term, str]],
        replacements: Sequence[Union[Term, str]],
        current: Optional[Comparable] = None,
        incoming: Optional[Comparable] = None,
    ) -> ContextRegister:
        """Make new ContextRegister from two lists of Comparables."""
        terms_to_replace = expand_strings_from_source(
            to_expand=to_replace, source=current
        )
        term_replacements = expand_strings_from_source(
            to_expand=replacements, source=incoming
        )
        return cls._from_lists(
            to_replace=terms_to_replace[: len(term_replacements)],
            replacements=term_replacements[: len(terms_to_replace)],
        )

    @classmethod
    def from_changes_and_current(
        cls,
        changes: Sequence[Union[str, Term]],
        current: Comparable,
        incoming: Optional[Comparable] = None,
    ):
        """Make new ContextRegister from a list of replacement generic Terms."""
        changes = expand_strings_from_source(to_expand=changes, source=incoming)
        generic_terms = list(current.generic_terms_by_str().values())
        if len(generic_terms) != len(changes):
            raise ValueError(
                f"Needed {len(generic_terms)} replacements for the "
                + f"items of generic_terms, but {len(changes)} were provided."
            )
        return cls._from_lists(to_replace=generic_terms, replacements=changes)

    @classmethod
    def create(
        cls,
        changes: ContextMemo,
        current: Optional[Comparable] = None,
        incoming: Optional[Comparable] = None,
        terms_to_replace: Optional[Sequence[Term]] = None,
    ) -> ContextRegister:
        """Convert changes to ``factor``, expressed as built-in Python objects, to a ContextRegister."""
        if isinstance(changes, ContextRegister):
            return changes
        if isinstance(changes, Dict):
            return cls.from_lists(
                to_replace=list(changes),
                replacements=list(changes.values()),
                current=current,
                incoming=incoming,
            )
        if (
            len(changes) == 2
            and all(not isinstance(change, str) for change in changes)
            and all(isinstance(change, Sequence) for change in changes)
        ):
            return cls.from_lists(
                to_replace=changes[0],
                replacements=changes[1],
                current=current,
                incoming=incoming,
            )
        if terms_to_replace:
            return cls.from_lists(
                to_replace=terms_to_replace,
                replacements=changes,
                current=current,
                incoming=incoming,
            )
        if not current:
            raise ValueError(
                "If terms to replace are not provided in the 'changes' attribute "
                "or the 'terms_to_replace' attribue, "
                "then a 'current' object must be provided."
            )
        return cls.from_changes_and_current(
            current=current, changes=changes, incoming=incoming
        )

    def assigns_same_value_to_key_factor(
        self, other: ContextRegister, key_factor: Comparable
    ) -> bool:
        """Check if both ContextRegisters assign same value to the key for this factor."""
        self_value = self.get_factor(key_factor)
        if self_value is None:
            return False
        return self_value.compare_keys(other.get_factor(key_factor))

    def check_match(self, key: Term, value: Term) -> bool:
        """Test if key and value are in ``matches`` as corresponding to one another."""
        if self.get(key.key) is None:
            return False
        return self[key.key].compare_keys(value)

    def factor_pairs(self) -> Iterator[Tuple[Term, Term]]:
        """Get pairs of corresponding Comparables."""
        for value in self.values():
            yield (self.reverse_matches[value.key], value)

    def means(self, other: ContextRegister) -> bool:
        """Determine if self and other have the same Factor matches."""
        if not isinstance(other, ContextRegister):
            return False
        for key, value in self.factor_pairs():
            if not other.check_match(key=key, value=value):
                return False
        return True

    def get(self, query: str) -> Optional[Comparable]:
        """Get value corresponding to the key named ``query``."""
        return self.matches.get(query)

    def get_factor(self, query: Comparable) -> Optional[Comparable]:
        """Get value corresponding to the key ``query``."""
        return self.get(query.short_string)

    def get_reverse_factor(self, query: Term) -> Optional[Term]:
        """Get key corresponding to the value ``query``."""
        return self.reverse_matches.get(query.short_string)

    def items(self) -> ItemsView:
        """Get items from ``matches`` mapping."""
        return self.matches.items()

    def keys(self) -> KeysView:
        """Get keys from ``matches`` mapping."""
        return self.matches.keys()

    def values(self) -> ValuesView:
        """Get values from ``matches`` mapping."""
        return self.matches.values()

    def check_insert_pair(self, key: Term, value: Term) -> None:
        """Raise exception if a pair of corresponding Terms can't be added to register."""
        for comp in (key, value):
            if not isinstance(comp, Term):
                raise TypeError(
                    "'key' and 'value' must both be subclasses of 'Term'",
                    f"but {comp} was type {type(comp)}.",
                )
        found_value = self.get_factor(key)
        if found_value and not self.check_match(key, value):
            raise KeyError(
                f"{key.key} already in mapping with value "
                + f"{found_value.key}, not {value.key}"
            )
        found_key = self.get_reverse_factor(value)
        if found_key and not self.check_match(key, value):
            raise KeyError(
                f"{value.key} already in mapping with key "
                + f"{found_key.key}, not {key.key}"
            )

    def insert_pair(self, key: Term, value: Term) -> None:
        """Add a pair of corresponding Comparables."""
        self.check_insert_pair(key=key, value=value)

        self._matches[key.short_string] = value
        self._reverse_matches[value.short_string] = key

    def replace_keys(self, replacements: ContextRegister) -> ContextRegister:
        """
        Construct new :class:`ContextRegister` by replacing keys.

        Used when making permutations of the key orders because some are interchangeable.

        e.g. in "Amy and Bob were married" the order of "Amy" and "Bob" is interchangeable.
        """

        result = ContextRegister()
        for key, value in self.matches.items():
            replacement = replacements[key]
            result.insert_pair(key=replacement, value=value)

        return result

    def reversed(self):
        """Swap keys for values and vice versa."""
        return ContextRegister.from_lists(
            to_replace=self.values(), replacements=self.reverse_matches.values()
        )

    def merged_with(
        self, incoming_mapping: ContextRegister
    ) -> Optional[ContextRegister]:
        r"""
        Create a new merged :class:`ContextRegister`\.

        :param incoming_mapping:
            an incoming mapping of :class:`Factor`\s
            from ``self`` to :class:`Factor`\s.

        :returns:
            ``None`` if the same :class:`Factor` in one mapping
            appears to match to two different :class:`Factor`\s in the other.
            Otherwise returns an updated :class:`ContextRegister` of matches.
        """
        self_mapping = deepcopy(self)
        for in_key, in_value in incoming_mapping.factor_pairs():
            try:
                self_mapping.insert_pair(key=in_key, value=in_value)
            except KeyError:
                return None

        return self_mapping


class FactorMatch(NamedTuple):
    """A pair of corresponding Factors, with the operation that they can satisfy."""

    left: Comparable
    operation: Callable
    right: Comparable

    operation_names: ClassVar[Dict[Callable, str]] = {
        operator.ge: "IMPLIES",
        means: "MEANS",
        contradicts: "CONTRADICTS",
        consistent_with: "IS CONSISTENT WITH",
    }

    @property
    def short_string(self) -> str:
        """Summarize self without line breaks."""
        relation = self.operation_names[self.operation]
        return f"{self.left.short_string} {relation} {self.right.short_string}"

    @property
    def key(self) -> str:
        """Make a key for storing the FactorMatch in a dict."""
        return self.short_string

    def __str__(self):
        relation = self.operation_names[self.operation]
        indent = "  "
        left = textwrap.indent(str(self.left), prefix=indent)
        right = textwrap.indent(str(self.right), prefix=indent)
        return f"{left}\n" f"{relation}\n" f"{right}\n"


class Explanation:
    """Explanation of how a comparison method between Comparables can succeed."""

    def __init__(
        self,
        reasons: List[FactorMatch],
        context: Optional[ContextRegister] = None,
        operation: Callable = operator.ge,
    ):
        """Set pairs of corresponding Factors as "reasons", and corresponding generic Terms as "context"."""
        self.reasons = reasons
        self.context = context or ContextRegister()
        if not isinstance(self.context, ContextRegister):
            raise TypeError(
                f"context attribute of Explanation must be type ContextRegister, not {type(self.context)}"
            )
        self.operation = operation

    def __str__(self):
        context_text = f"Because {self.context.reason},\n" if self.context else "\n"
        match_texts = [str(match) for match in self.reasons]
        if len(match_texts) > 1:
            match_texts[-2] = match_texts[-2].rstrip("\n") + ", and\n"
        for line in match_texts:
            context_text += line
        return context_text.rstrip("\n")

    def __repr__(self) -> str:
        return f"Explanation(reasons={repr(self.reasons)}, context={repr(self.context)}), operation={repr(self.operation)})"

    @property
    def short_string(self) -> str:
        """Summarize self without line breaks."""
        context_text = f"Because {self.context.reason}, " if self.context else ""
        match_texts = [match.short_string for match in self.reasons]
        if len(match_texts) > 1:
            match_texts[-2:] = [f"{match_texts[-2]}, and {match_texts[-1]}"]
        context_text += ", ".join(match_texts)
        return context_text

    @classmethod
    def from_context(
        cls,
        context: Optional[Union[ContextMemo, Explanation]] = None,
        current: Optional[Comparable] = None,
        incoming: Optional[Comparable] = None,
    ) -> Explanation:
        """Return new Explanation with self as context but no reasons."""
        if isinstance(context, Explanation):
            return context
        if not context:
            context = ContextRegister()
        elif not isinstance(context, ContextRegister):
            context = ContextRegister.create(
                changes=context, current=current, incoming=incoming
            )
        return Explanation(reasons=[], context=context or ContextRegister())

    def means(self, other: Explanation) -> bool:
        """Test if both Explanations have the same context and reasons."""
        if not isinstance(other, Explanation):
            return False
        if not self.context.means(other.context):
            return False
        if len(self.reasons) != len(other.reasons):
            return False
        return not any(
            all(other_reason.key != reason.key for other_reason in other.reasons)
            for reason in self.reasons
        )

    def operate(self, left: Comparable, right: Comparable) -> Iterator[Explanation]:
        """Generate further explanations for applying self.operation to a new Factor pair."""
        if self.operation == operator.ge:
            yield from left.explanations_implication(right, self)
        elif self.operation == means:
            yield from left.explanations_same_meaning(right, self)
        elif self.operation == contradicts:
            yield from left.explanations_contradiction(right, self)
        elif self.operation == consistent_with:
            yield from left.explanations_consistent_with(right, self)
        else:
            raise ValueError(
                f"Can't apply self.operation '{self.operation}' as function."
            )

    def reversed_context(self) -> Explanation:
        """Make new copy of self, swapping keys and values of context."""
        return self.with_context(self.context.reversed())

    def with_match(self, match: FactorMatch) -> Explanation:
        """Add a pair of compared objects that has been found to satisfy operation, given context."""
        new_matches = self.reasons + [match]
        return Explanation(
            reasons=new_matches,
            context=self.context,
            operation=self.operation,
        )

    def with_context(self, context: ContextRegister) -> Explanation:
        """Make new copy of self, replacing context."""
        return Explanation(
            reasons=self.reasons,
            context=context,
            operation=self.operation,
        )


class Term(Comparable):
    r"""
    Things that can be referenced in a Statement.

    The name of a Term can replace the placeholder in
    a :class:`~nettlesome.predicates.StatementTemplate`\.
    """

    def _borrow_generic_context(self, other: Term) -> Term:
        self_factors = list(self.recursive_terms.values())
        other_factors = list(other.recursive_terms.values())
        changes = ContextRegister()
        for i, factor in enumerate(self_factors):
            if factor.generic:
                changes.insert_pair(factor, other_factors[i])
        return self.new_context(changes)

    def __bool__(self) -> bool:
        return True

    def add(
        self, other: Term, context: Optional[ContextRegister] = None
    ) -> Optional[Term]:
        """
        Get a term that combines the meaning of self and other, if possible.

        :param other:
            another Term

        :returns:
            the Term that implies the other, with self's context.
            If neither returns the other, returns None.
        """
        if not isinstance(other, Term):
            raise TypeError
        if self.implies(other, context=context):
            return self
        if other.implies(self, context=context):
            return other._borrow_generic_context(self)
        return None

    def __add__(self, other: Term) -> Optional[Comparable]:
        return self.add(other)

    def explanations_consistent_with(
        self,
        other: Comparable,
        context: Optional[Union[ContextRegister, Explanation]] = None,
    ) -> Iterator[Explanation]:
        """Get Term assignments resulting in no contradiction between self and other."""
        context = Explanation.from_context(
            context=context, current=self, incoming=other
        )
        if not isinstance(other, Term):
            yield from other.explanations_consistent_with(
                self, context.reversed_context()
            )
        else:
            yield from super().explanations_consistent_with(
                other=other, context=context
            )

    def _context_registers(
        self,
        other: Optional[Comparable],
        comparison: Callable,
        context: Optional[ContextRegister] = None,
    ) -> Iterator[ContextRegister]:
        if context is None:
            context = ContextRegister()
        if other is None:
            yield context
        elif isinstance(other, Term) and (self.generic or other.generic):
            self_value = context.get(self.key)
            if self_value is None or (self_value.compare_keys(other)):
                yield self._generic_register(other)
        else:
            yield from super()._context_registers(other, comparison, context=context)

    def _explanations_same_meaning(
        self, other: Comparable, explanation: Explanation
    ) -> Iterator[Explanation]:
        if (
            isinstance(other, Term)
            and self.__class__ == other.__class__
            and self.generic
            and other.generic
            and self.absent == other.absent
        ):
            generic_context = self._generic_register(other)
            new_context = explanation.context.merged_with(generic_context)
            if new_context:
                yield explanation.with_context(new_context)
        yield from super()._explanations_same_meaning(other, explanation)

    def _implies_if_present(
        self, other: Comparable, explanation: Explanation
    ) -> Iterator[Explanation]:
        if (
            isinstance(other, self.__class__)
            and other.generic
            and (
                explanation.context.get_factor(self) is None
                or (explanation.context.get_factor(self) == other)
            )
        ):
            new_context = self._generic_register(other)
            yield explanation.with_context(new_context)
        yield from super()._implies_if_present(other, explanation)

    def _generic_register(self, other: Term) -> ContextRegister:
        register = ContextRegister()
        register.insert_pair(self, other)
        return register

    def generic_terms_by_str(self) -> Dict[str, Term]:
        """Get all generic Terms found in this Term, indexed by their string keys."""
        if self.generic:
            return {self.key: self}
        return super().generic_terms_by_str()

    @property
    def recursive_terms(self) -> Dict[str, Term]:
        r"""
        Collect `self`'s :attr:`terms`, and their :attr:`terms`, recursively.

        :returns:
            a :class:`dict` (instead of a :class:`set`,
            to preserve order) of :class:`Term`\s.
        """
        answers = super().recursive_terms
        answers[self.key] = self
        return answers


class DuplicateTermError(Exception):
    """Error indicating a TermSequence contains the same Term more than once."""

    pass


class TermSequence(Tuple[Optional[Term], ...]):
    """A sequence of Terms that can be compared in order."""

    def __new__(cls, value: Union[Term, Sequence[Optional[Term]]] = ()):
        """Convert Sequence of Terms to a subclass of Tuple."""
        if isinstance(value, Term):
            value = (value,)
        cls.validate_terms(value)
        return tuple.__new__(TermSequence, value)

    @classmethod
    def validate_terms(cls, terms: Sequence[Optional[Term]]) -> None:
        seen: List[str] = []
        for term in terms:
            if term is not None:
                if not isinstance(term, Term):
                    raise TypeError(
                        f"'{term}' cannot be included in TermSequence because it is not type Term."
                    )
                if term.key in seen:
                    raise DuplicateTermError(
                        f"Term '{term}' may not appear more than once in TermSequence. "
                        "If you need to refer to the same term more than once in a Predicate, "
                        "please use the same placeholder text instead of including the "
                        "Term in the TermSequence more than once. If more than one distinct "
                        "Term shares the same key text, please change one of them."
                    )
                seen.append(term.key)
        return None

    def ordered_comparison(
        self,
        other: TermSequence,
        operation: Callable,
        context: Optional[ContextRegister] = None,
    ) -> Iterator[ContextRegister]:
        r"""
        Find ways for a series of pairs of :class:`.Terms` terms to satisfy a comparison.

        :param context:
            keys representing terms in ``self`` and
            values representing terms in ``other``. The
            keys and values have been found in corresponding positions
            in ``self`` and ``other``.

        :yields:
            every way that ``matches`` can be updated to be consistent
            with each element of ``self.need_matches`` having the relationship
            ``self.comparison`` with the item at the corresponding index of
            ``self.available``.
        """

        def update_register(
            register: ContextRegister,
            factor_pairs: List[Tuple[Optional[Term], Optional[Term]]],
            i: int = 0,
        ):
            """
            Recursively search through Factor pairs trying out context assignments.

            This has the potential to take a long time to fail if the problem is
            unsatisfiable. It will reduce risk to check that every :class:`Factor` pair
            is satisfiable before checking that they're all satisfiable together.
            """
            if i == len(factor_pairs):
                yield register
            else:
                left, right = factor_pairs[i]
                if left is not None or right is None:
                    if left is None:
                        yield from update_register(
                            register, factor_pairs=factor_pairs, i=i + 1
                        )
                    else:
                        new_mapping_choices: List[ContextRegister] = []
                        for incoming_register in left.update_context_register(
                            right, register, operation
                        ):
                            if incoming_register not in new_mapping_choices:
                                new_mapping_choices.append(incoming_register)
                                yield from update_register(
                                    incoming_register,
                                    factor_pairs=factor_pairs,
                                    i=i + 1,
                                )

        context = context or ContextRegister()
        ordered_pairs = list(zip_longest(self, other))
        yield from update_register(register=context, factor_pairs=ordered_pairs)


# Type annotation of formats for describing the context of a comparison
# between two Factors. All of these can be converted to a ContextRegister
# using information from the Factors being compared.
ContextMemo = Union[
    ContextRegister,
    List[Union[str, Term]],
    Tuple[List[Union[str, Term]], List[Union[str, Term]]],
    Dict[str, Union[str, Term]],
]
