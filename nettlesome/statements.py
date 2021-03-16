"""Statements, similar to AuthoritySpoke Facts but without a "standard of proof"."""

from copy import deepcopy
import operator

from typing import Dict, Iterator, List, Mapping, Type
from typing import Optional, Sequence, Union

from nettlesome.terms import (
    Comparable,
    Explanation,
    Term,
    TermSequence,
    ContextRegister,
    new_context_helper,
)
from nettlesome.factors import Factor
from nettlesome.formatting import indented, wrapped
from nettlesome.predicates import Predicate
from slugify import slugify


class Statement(Factor):
    r"""An assertion that can be accepted as factual and compared to other Statements."""

    def __init__(
        self,
        predicate: Union[Predicate, str],
        terms: Optional[
            Union[TermSequence, Term, Sequence[Term], Mapping[str, Term]]
        ] = None,
        name: str = "",
        absent: bool = False,
        generic: bool = False,
    ):
        """
        Normalize ``terms`` to initialize Statement.

        :param predicate:
            a natural-language clause with zero or more slots
            to insert ``terms`` that are typically the
            subject and objects of the clause.

        :param terms:
            a series of :class:`~nettlesome.factors.Factor` objects that fill in
            the blank spaces in the ``predicate`` statement.

        :param name:
            an identifier for this object, often used if the object needs
            to be referred to multiple times in the process of composing
            other :class:`~nettlesome.factors.Factor` objects.

        :param absent:
            whether the absence, rather than the presence, of the legal
            fact described above is being asserted.

        :param generic:
            whether this object could be replaced by another generic
            object of the same class without changing the truth of a
            :class:`:class:`~nettlesome.predicates.Predicate`` in
            which it is mentioned.
        """
        terms = terms or TermSequence()

        if isinstance(predicate, str):
            predicate = Predicate(predicate)
        self.predicate = predicate

        if isinstance(terms, Mapping):
            terms = predicate.template.get_term_sequence_from_mapping(terms)

        if not isinstance(terms, TermSequence):
            terms = TermSequence(terms)

        self._terms = terms

        if len(self.terms) != len(self.predicate):
            message = (
                "The number of items in 'terms' must be "
                + f"{len(self.predicate)}, not {len(self.terms)}, "
                + f"to match predicate.context_slots for '{self.predicate.content}'"
            )
            raise ValueError(message)

        if any(not isinstance(s, Comparable) for s in self.terms):
            raise TypeError(
                "Items in the 'terms' parameter should "
                + "be a subclass of Comparable."
            )
        super().__init__(name=name, generic=generic, absent=absent)

    @property
    def short_string(self) -> str:
        """Represent object without line breaks."""
        return str(self)

    @property
    def slug(self) -> str:
        """
        Get a representation of self without whitespace.

        Intended for use as a sympy :class:`~sympy.core.symbol.Symbol`
        """
        terms = [term for term in self.terms if term is not None]
        subject = self.predicate._content_with_terms(terms).removesuffix(" was")
        return slugify(subject)

    @property
    def terms(self) -> TermSequence:
        """Get Terms used to fill placeholders in ``self``'s StatementTemplate."""
        return self._terms

    @property
    def terms_without_nulls(self) -> Sequence[Term]:
        """
        Get Terms that are not None.

        No Terms should be None for the Statement class, so this method is like an
        assertion for type checking.
        """
        return [term for term in self._terms if term is not None]

    @property
    def wrapped_string(self):
        """Wrap text in string representation of ``self``."""
        content = str(self.predicate._content_with_terms(self.terms))
        unwrapped = self.predicate.add_truth_to_content(content)
        text = wrapped(super().__str__().format(unwrapped))
        return text

    @property
    def str_with_concrete_context(self) -> str:
        """
        Identify this Statement more verbosely, specifying which text is a concrete context factor.

        :returns:
            the same as the __str__ method, but with an added "SPECIFIC CONTEXT" section
        """
        text = str(self)
        concrete_context = [
            factor for factor in self.terms_without_nulls if not factor.generic
        ]
        if any(concrete_context) and not self.generic:
            text += "\n" + indented("SPECIFIC CONTEXT:")
            for factor in concrete_context:
                factor_text = indented(factor.wrapped_string, tabs=2)
                text += f"\n{str(factor_text)}"
        return text

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({repr(self.predicate)}, terms={self.terms}"
            f"{', absent=True' if self.absent else ''}{', absent=True' if self.absent else ''})"
        )

    def __str__(self):
        """Create one-line string representation for inclusion in other Facts."""
        content = str(self.predicate._content_with_terms(self.terms))
        unwrapped = self.predicate.add_truth_to_content(content)
        return super().__str__().format(unwrapped)

    @property
    def truth(self) -> Optional[bool]:
        """Access :attr:`~Predicate.truth` attribute."""
        return self.predicate.truth

    def _means_if_concrete(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        if isinstance(other, Statement) and self.predicate.means(other.predicate):
            yield from super()._means_if_concrete(other, context)

    def __len__(self):
        return len(self.generic_factors())

    def _implies_if_concrete(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        """
        Test if ``self`` impliess ``other``, assuming they are not ``generic``.

        :returns:
            whether ``self`` implies ``other`` under the given assumption.
        """
        if isinstance(other, Statement) and self.predicate >= other.predicate:
            yield from super()._implies_if_concrete(other, context)

    def _contradicts_if_present(
        self, other: Comparable, explanation: Explanation
    ) -> Iterator[Explanation]:
        """
        Test if ``self`` contradicts :class:`Fact` ``other`` if neither is ``absent``.

        :returns:
            whether ``self`` and ``other`` can't both be true at
            the same time under the given assumption.
        """
        if isinstance(other, self.__class__) and self.predicate.contradicts(
            other.predicate
        ):
            for context in self._context_registers(
                other, operator.ge, explanation.context
            ):
                yield explanation.with_context(context)

    @new_context_helper
    def new_context(self, changes: Dict[Comparable, Comparable]) -> Comparable:
        """
        Create new :class:`Factor`, replacing keys of ``changes`` with values.

        :returns:
            a version of ``self`` with the new context.
        """
        result = deepcopy(self)
        result._terms = TermSequence(
            [factor.new_context(changes) for factor in self.terms_without_nulls]
        )
        return result

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
            left = [term for term in self._terms if term is not None]
            right = [term for term in term_permutation if term is not None]
            changes = ContextRegister.from_lists(left, right)
            changed_registry = matches.replace_keys(changes)
            if not any(
                changed_registry == returned_dict for returned_dict in already_returned
            ):
                already_returned.append(changed_registry)
                yield changed_registry

    def term_permutations(self) -> Iterator[TermSequence]:
        """Generate permutations of context factors that preserve same meaning."""
        for pattern in self.predicate.term_index_permutations():
            sorted_terms = [x for _, x in sorted(zip(pattern, self.terms))]
            yield TermSequence(sorted_terms)
