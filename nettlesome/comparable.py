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
from typing import List, Optional, Sequence, Tuple, Union

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
    :attr:`~Factor.generic_factors` from the calling object.

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
        changes: Union[Sequence[Comparable], ContextRegister],
        terms_to_replace: Optional[Sequence[Comparable]] = None,
        source: Optional[Comparable] = None,
    ) -> Comparable:

        expanded_changes = convert_changes_to_register(
            factor=factor,
            changes=changes,
            terms_to_replace=terms_to_replace,
            source=source,
        )

        for old, new in expanded_changes.items():
            if factor.short_string == old or factor.__dict__.get("name") == old:
                return new

        return func(factor, expanded_changes)

    return wrapper


def expand_string_from_source(
    term: Union[str, Comparable], source: Comparable
) -> Comparable:
    """Replace ``term`` with the real term it references, if ``term`` is a string reference."""
    if isinstance(term, str):
        result = source.get_factor(term)
    else:
        return term
    if result is None:
        raise ValueError(f'Unable to find replacement term for text "{term}"')
    return result


def convert_changes_to_register(
    factor: Comparable,
    changes: Union[Comparable, ContextRegister, Sequence[Comparable]],
    source: Optional[Comparable],
    terms_to_replace: Optional[Sequence[Comparable]] = None,
) -> ContextRegister:
    """Convert changes to ``factor``, expressed as normal Python objects, to a ContextRegister."""
    if isinstance(changes, ContextRegister):
        return changes
    if not isinstance(changes, Iterable):
        changes = [changes]
    if terms_to_replace:
        for change in changes:
            if not isinstance(change, Comparable):
                raise TypeError(
                    "If 'terms_to_replace' is given, 'changes' must be a list of replacement "
                    f"Terms, but {change} was type {type(change)}."
                )
        if len(terms_to_replace) != len(changes):
            raise ValueError(
                "Cannot create ContextRegister because 'terms_to_replace' is not the same length "
                f"as 'changes'.\nterms_to_replace: ({terms_to_replace})\nchanges: ({changes})"
            )
        return ContextRegister.from_lists(keys=terms_to_replace, values=changes)

    if source:
        changes = [expand_string_from_source(change, source) for change in changes]
    generic_factors = list(factor.generic_factors_by_str().values())
    if len(generic_factors) != len(changes):
        raise ValueError(
            f"Needed {len(generic_factors)} replacements for the "
            + f"items of generic_factors, but {len(changes)} were provided."
        )
    return ContextRegister.from_lists(generic_factors, changes)


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

    generic: bool = False
    absent: bool = False
    name: Optional[str] = None
    plural: bool = False
    context_factor_names: ClassVar[Tuple[str, ...]] = ()

    @property
    def key(self) -> str:
        """Return string representation of self for use as a key in a ContextRegister."""
        return self.short_string

    @property
    def short_string(self) -> str:
        """Return string representation without line breaks."""
        return textwrap.shorten(str(self), width=5000, placeholder="...")

    @property
    def wrapped_string(self) -> str:
        """Return string representation with line breaks."""
        return str(self)

    @property
    def recursive_factors(self) -> Dict[str, Comparable]:
        r"""
        Collect `self`'s :attr:`terms`, and their :attr:`terms`, recursively.

        :returns:
            a :class:`dict` (instead of a :class:`set`,
            to preserve order) of :class:`Factor`\s.
        """
        answers: Dict[str, Comparable] = {self.short_string: self}
        for context in self.terms:
            if context is not None:
                answers.update(context.recursive_factors)
        return answers

    @property
    def terms(self) -> FactorSequence:
        r"""
        Get :class:`Factor`\s used in comparisons with other :class:`Factor`\s.

        :returns:
            a tuple of attributes that are designated as the ``terms``
            for whichever subclass of :class:`Factor` calls this method. These
            can be used for comparing objects using :meth:`consistent_with`
        """
        context: List[Optional[Comparable]] = []
        for factor_name in self.context_factor_names:
            next_factor: Optional[Comparable] = self.__dict__.get(factor_name)
            context.append(next_factor)
        return FactorSequence(context)

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

    def _all_generic_factors_match(
        self, other: Comparable, context: ContextRegister
    ) -> bool:
        if all(
            all(
                context.assigns_same_value_to_key_factor(
                    other=other_register, key_factor=generic
                )
                for generic in self.generic_factors()
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
        self, other: Comparable, relation: Callable, ordering: FactorSequence
    ) -> bool:
        """
        Determine whether one ordering of self's terms matches other's terms.

        Multiple term orderings exist where the terms can be rearranged without
        changing the Fact's meaning.

        For instance, "<Ann> and <Bob> both were members of the same family" has a
        second ordering "<Bob> and <Ann> both were members of the same family".
        """
        for i, self_factor in enumerate(ordering):
            if not (self_factor is other.terms[i] is None):
                if not (self_factor and relation(self_factor, other.terms[i])):
                    return False
        return True

    def _context_registers(
        self,
        other: Optional[Comparable],
        comparison: Callable,
        context: Optional[ContextRegister] = None,
    ) -> Iterator[ContextRegister]:
        r"""
        Search for ways to match :attr:`terms` of ``self`` and ``other``.

        :yields:
            all valid ways to make matches between
            corresponding :class:`Factor`\s.
        """
        if context is None:
            context = ContextRegister()
        if other is None:
            yield context
        elif self.generic or other.generic:
            self_value = context.get(self.key)
            if self_value is None or (self_value.compare_keys(other)):
                yield self._generic_register(other)
        else:
            for term_permutation in self.term_permutations():
                for other_permutation in other.term_permutations():
                    yield from term_permutation.ordered_comparison(
                        other=other_permutation, operation=comparison, context=context
                    )

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
        self, other: Comparable, context: ContextRegister
    ) -> Iterator[ContextRegister]:
        """
        Test if ``self`` would contradict ``other`` if neither was ``absent``.

        The default is to yield nothing where no class-specific method is available.
        """
        yield from iter([])

    def explain_same_meaning(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[ContextRegister]:
        """Get one explanation of why self and other have the same meaning."""
        explanations = self.explanations_same_meaning(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explain_consistent_with(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[ContextRegister]:
        """Get one explanation of why self and other need not contradict."""
        explanations = self.explanations_consistent_with(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explain_contradiction(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[ContextRegister]:
        """Get one explanation of why self and other contradict."""
        explanations = self.explanations_contradiction(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explain_implication(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[ContextRegister]:
        """Get one explanation of why self implies other."""
        explanations = self.explanations_implication(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explain_implied_by(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[ContextRegister]:
        """Get one explanation of why self implies other."""
        explanations = self.explanations_implied_by(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explanations_consistent_with(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        """
        Test whether ``self`` does not contradict ``other``.

        This should only be called after confirming that ``other``
        is not ``None``.

        :returns:
            ``True`` if self and other can't both be true at
            the same time. Otherwise returns ``False``.
        """
        if context is None:
            context = ContextRegister()
        for possible in self.possible_contexts(other, context):
            if not self.contradicts(other, context=possible):
                yield possible

    def explanations_contradiction(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        """
        Test whether ``self`` :meth:`implies` the absence of ``other``.

        This should only be called after confirming that ``other``
        is not ``None``.

        :returns:
            ``True`` if self and other can't both be true at
            the same time. Otherwise returns ``False``.
        """
        context = context or ContextRegister()
        if not isinstance(other, Comparable):
            raise TypeError(
                f"{self.__class__} objects may only be compared for "
                + "contradiction with other Factor objects or None."
            )
        if isinstance(other, self.__class__):
            if not self.__dict__.get("absent"):
                if not other.__dict__.get("absent"):
                    yield from self._contradicts_if_present(other, context)
                else:
                    yield from self._implies_if_present(other, context)
            elif self.__dict__.get("absent"):
                # No contradiction between absences of any two Comparables
                if not other.__dict__.get("absent"):
                    test = other._implies_if_present(self, context.reversed())
                    yield from (register.reversed() for register in test)
        elif isinstance(other, Iterable):
            yield from other.explanations_contradiction(
                self, context=context.reversed()
            )

    def explanations_implication(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        r"""
        Generate :class:`.ContextRegister`\s that cause `self` to imply `other`.

        If self is `absent`, then generate a ContextRegister from other's point
        of view and then swap the keys and values.
        """
        if context is None:
            context = ContextRegister()
        if not isinstance(other, Comparable):
            raise TypeError(
                f"{self.__class__} objects may only be compared for "
                + "implication with other Comparable objects or None."
            )
        if isinstance(other, self.__class__):
            if not self.__dict__.get("absent"):
                if not other.__dict__.get("absent"):
                    yield from self._implies_if_present(other, context)
                else:
                    yield from self._contradicts_if_present(other, context)

            else:
                if other.__dict__.get("absent"):
                    test = other._implies_if_present(self, context.reversed())
                else:
                    test = other._contradicts_if_present(self, context.reversed())
                yield from (register.reversed() for register in test)

    def explanations_implied_by(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        """Get explanations of why self implies other."""
        context = context or ContextRegister()
        yield from (
            register.reversed()
            for register in other.explanations_implication(
                self, context=context.reversed()
            )
        )

    def explanations_same_meaning(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        """Generate ways to match contexts of self and other so they mean the same."""
        if (
            self.__class__ == other.__class__
            and self.generic == other.generic
            and self.absent == other.absent
        ):
            if self.generic:
                yield self._generic_register(other)
            context = context or ContextRegister()
            yield from self._means_if_concrete(other, context)

    def _generic_register(self, other: Comparable) -> ContextRegister:
        register = ContextRegister()
        register.insert_pair(self, other)
        return register

    def _implies_if_present(
        self, other: Comparable, context: ContextRegister
    ) -> Iterator[ContextRegister]:
        """
        Find if ``self`` would imply ``other`` if they aren't absent.

        :returns:
            bool indicating whether ``self`` would imply ``other``,
            under the assumption that neither self nor other has
            the attribute ``absent == True``.
        """
        if isinstance(other, self.__class__):
            if other.generic:
                if context.get_factor(self) is None or (
                    context.get_factor(self) == other
                ):
                    yield self._generic_register(other)
            if not self.generic:
                yield from self._implies_if_concrete(other, context)

    def generic_factors(self) -> List[Comparable]:
        """Get Terms that can be replaced without changing ``self``'s meaning."""
        return list(self.generic_factors_by_str().values())

    def generic_factors_by_str(self) -> Dict[str, Comparable]:
        r"""
        Index Terms that can be replaced without changing ``self``'s meaning.

        :returns:
            a :class:`dict` with the names of ``self``\'s
            generic :class:`.Factor`\s as keys and the :class:`.Factor`\s
            themselves as values.
        """

        if self.generic:
            return {self.short_string: self}
        generics: Dict[str, Comparable] = {}
        for factor in self.terms:
            if factor is not None:
                for generic in factor.generic_factors():
                    generics[generic.short_string] = generic
        return generics

    def get_factor(self, query: str) -> Optional[Comparable]:
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

    def get_factor_by_name(self, name: str) -> Optional[Comparable]:
        """
        Search of ``self`` and ``self``'s attributes for :class:`Factor` with specified ``name``.

        :returns:
            a :class:`Comparable` with the specified ``name`` attribute
            if it exists, otherwise ``None``.
        """
        factors_to_search = self.recursive_factors
        for value in factors_to_search.values():
            if hasattr(value, "name") and value.name == name:
                return value
        return None

    def get_factor_by_str(self, query: str) -> Optional[Comparable]:
        """
        Search of ``self`` and ``self``'s attributes for :class:`Factor` with specified string.

        :returns:
            a :class:`Factor` with the specified string
            if it exists, otherwise ``None``.
        """
        for name, factor in self.recursive_factors.items():
            if name == query:
                return factor
        return None

    def implied_by(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ):
        """Test whether ``other`` implies ``self``."""
        if other is None:
            return False
        return any(
            register is not None
            for register in self.explanations_implied_by(other, context=context)
        )

    def implies(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ) -> bool:
        r"""
        Test whether ``self`` implies ``other``.

        When inherited by :class:`~nettlesome.groups.FactorGroup`\, this method will
        check whether every :class:`~nettlesome.statements.Statement` in ``other``
        is implied by some Statement in ``self``.

            >>> over_100y = Comparison("the distance between $site1 and $site2 was", sign=">", expression="100 yards")
            >>> under_1mi = Comparison("the distance between $site1 and $site2 was", sign="<", expression="1 mile")
            >>> protest_facts = FactorGroup(
            >>>     [Statement(over_100y, terms=[Entity("the political convention"), Entity("the police cordon")]),
            >>>      Statement(under_1mi, terms=[Entity("the police cordon"), Entity("the political convention")])])
            >>> over_50m = Comparison("the distance between $site1 and $site2 was", sign=">", expression="50 meters")
            >>> under_2km = Comparison("the distance between $site1 and $site2 was", sign="<=", expression="2 km")
            >>> speech_zone_facts = FactorGroup(
            >>>     [Statement(over_50m, terms=[Entity("the free speech zone"), Entity("the courthouse")]),
            >>>      Statement(under_2km, terms=[Entity("the free speech zone"), Entity("the courthouse")])])
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
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
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
            yield from self._context_registers(other, operator.ge, context)

    def implies_same_context(self, other) -> bool:
        """Check if self would imply other if their generic terms are matched in order."""
        same_context = ContextRegister()
        for key in self.generic_factors():
            same_context.insert_pair(key, key)
        return self.implies(other, context=same_context)

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
            with the same meaning as ``self``. Not the same as an
            equality comparison with the ``==`` symbol, which simply
            converts ``self``\'s and ``other``\'s fields to tuples
            and compares them.
        """
        if other is None:
            return False
        return any(
            explanation is not None
            for explanation in self.explanations_same_meaning(other, context=context)
        )

    def _means_if_concrete(
        self, other: Comparable, context: Optional[ContextRegister]
    ) -> Iterator[ContextRegister]:
        """
        Test equality based on :attr:`terms`.

        Usually called after a subclasses has injected its own tests
        based on other attributes.

        :returns:
            bool indicating whether ``self`` would equal ``other``,
            under the assumptions that neither ``self`` nor ``other``
            has ``absent=True``, neither has ``generic=True``, and
            ``other`` is an instance of ``self``'s class.
        """
        if self.compare_terms(other, means):
            yield from self._context_registers(other, comparison=means, context=context)

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
            for factor in self.generic_factors()
            if factor.short_string not in context.matches.keys()
        ]
        unused_other = [
            factor
            for factor in other.generic_factors()
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
        gen = self.term_permutations()
        _ = next(gen)  # unchanged permutation
        already_returned: List[ContextRegister] = [matches]

        for term_permutation in gen:
            changes = ContextRegister.from_lists(self.terms, term_permutation)
            changed_registry = matches.replace_keys(changes)
            if not any(
                changed_registry == returned_dict for returned_dict in already_returned
            ):
                already_returned.append(changed_registry)
                yield changed_registry

    def term_permutations(self) -> Iterator[FactorSequence]:
        """Generate permutations of context factors that preserve same meaning."""
        yield self.terms

    def _update_context_from_factors(
        self, other: Comparable, context: ContextRegister
    ) -> Optional[ContextRegister]:
        """
        Update context produce a likely way self corresponds to other.

        It's not guaranteed that by exchanging generic terms in order will
        produce the right updated context.
        """
        incoming = ContextRegister.from_lists(
            keys=self.generic_factors(), values=other.generic_factors()
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
        if not isinstance(context, ContextRegister):
            raise TypeError
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

    def __getitem__(self, item: str) -> Comparable:
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
            f'{key.short_string} {"are" if (key.plural) else "is"} like {value.short_string}'
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
    def matches(self) -> Dict[str, Comparable]:
        """Get names of ``self``'s Terms matched to ``other``'s Terms."""
        return self._matches

    @property
    def reverse_matches(self) -> Dict[str, Comparable]:
        """Get names of ``other``'s Terms matched to ``self``'s Terms."""
        return self._reverse_matches

    @classmethod
    def from_lists(
        cls,
        keys: Union[FactorSequence, Sequence[Comparable]],
        values: Union[FactorSequence, Sequence[Comparable]],
    ) -> ContextRegister:
        """Make new ContextRegister from two lists of Comparables."""
        pairs = zip(keys, values)
        new = cls()
        for pair in pairs:
            new.insert_pair(pair[0], pair[1])
        return new

    def assigns_same_value_to_key_factor(
        self, other: ContextRegister, key_factor: Comparable
    ) -> bool:
        """Check if both ContextRegisters assign same value to the key for this factor."""
        self_value = self.get_factor(key_factor)
        if self_value is None:
            return False
        return self_value.compare_keys(other.get_factor(key_factor))

    def check_match(self, key: Comparable, value: Comparable) -> bool:
        """Test if key and value are in ``matches`` as corresponding to one another."""
        if self.get(key.key) is None:
            return False
        return self[key.key].compare_keys(value)

    def factor_pairs(self) -> Iterator[Tuple[Comparable, Comparable]]:
        """Get pairs of corresponding Comparables."""
        for key, value in self.items():
            yield (self.get_reverse_factor(value), value)

    def get(self, query: str) -> Optional[Comparable]:
        """Get value corresponding to the key named ``query``."""
        return self.matches.get(query)

    def get_factor(self, query: Comparable) -> Optional[Comparable]:
        """Get value corresponding to the key ``query``."""
        return self.get(query.short_string)

    def get_reverse_factor(self, query: Comparable) -> Comparable:
        """Get key corresponding to the value ``query``."""
        return self.reverse_matches[query.short_string]

    def items(self):
        """Get items from ``matches`` mapping."""
        return self.matches.items()

    def keys(self):
        """Get keys from ``matches`` mapping."""
        return self.matches.keys()

    def values(self):
        """Get values from ``matches`` mapping."""
        return self.matches.values()

    def insert_pair(self, key: Comparable, value: Comparable) -> None:
        """Add a pair of corresponding Comparables."""
        for comp in (key, value):
            if not isinstance(comp, Comparable):
                raise TypeError(
                    "'key' and 'value' must both be subclasses of 'Comparable'",
                    f"but {comp} was type {type(comp)}.",
                )
            if isinstance(comp, Iterable):
                raise TypeError("Iterable objects may not be added to ContextRegister")
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
            keys=self.values(), values=self.reverse_matches.values()
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
        for in_key, in_value in incoming_mapping.matches.items():

            if in_value:
                if self_mapping.get(in_key) and not self_mapping[
                    in_key
                ].short_string == (in_value.short_string):
                    logger.debug(
                        f"{in_key} already in mapping with value "
                        + f"{self_mapping.matches[in_key]}, not {in_value}"
                    )
                    return None
                key_as_factor = incoming_mapping.get_reverse_factor(in_value)
                self_mapping.insert_pair(key_as_factor, in_value)
                values_as_keys = [v.short_string for v in self_mapping.values()]
                if values_as_keys.count(in_value.short_string) > 1:
                    logger.debug("%s assigned to two different keys", in_value)
                    return None
        return self_mapping


class FactorSequence(Tuple[Comparable, ...]):
    """A sequence of Comparables that can be compared in order."""

    def __new__(cls, value: Sequence = ()):
        """Convert Sequence of Comparables to a subclass of Tuple."""
        if isinstance(value, Comparable):
            value = (value,)
        return tuple.__new__(FactorSequence, value)

    def ordered_comparison(
        self,
        other: FactorSequence,
        operation: Callable,
        context: Optional[ContextRegister] = None,
    ) -> Iterator[ContextRegister]:
        r"""
        Find ways for a series of pairs of :class:`.Comparable` terms to satisfy a comparison.

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
            factor_pairs: List[Tuple[Optional[Comparable], Optional[Comparable]]],
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
