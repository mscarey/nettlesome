"""Statements, similar to AuthoritySpoke Facts but without a "standard of proof"."""


from copy import deepcopy
import operator

from typing import ClassVar, Dict, Iterator, List, Mapping
from typing import Optional, Self, Sequence, Tuple, Union

from pydantic import (
    BaseModel,
    validator,
    field_validator,
    model_validator,
    root_validator,
)
from slugify import slugify

from nettlesome.terms import (
    Comparable,
    Explanation,
    Term,
    TermSequence,
    ContextRegister,
    new_context_helper,
)
from nettlesome.entities import Entity
from nettlesome.factors import Factor
from nettlesome.formatting import indented, wrapped
from nettlesome.predicates import Predicate
from nettlesome.quantities import Comparison


class Statement(Factor, BaseModel):
    r"""
    An assertion that can be accepted as factual and compared to other Statements.

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

    :param truth:
        a new "truth" attribute for the "predicate", if needed.
    """

    predicate: Union[Predicate, Comparison]
    terms: List[Union[Entity, "Statement", "Assertion"]]
    name: str = ""
    absent: bool = False
    generic: bool = False

    @model_validator(mode="before")
    def move_truth_to_predicate(cls, values):
        if isinstance(values.get("predicate"), str):
            values["predicate"] = Predicate(content=values["predicate"])
        if "truth" in values:
            values["predicate"].truth = values["truth"]
            del values["truth"]
        if isinstance(values.get("terms"), Mapping):
            values["terms"] = values[
                "predicate"
            ].template.get_term_sequence_from_mapping(values["terms"])
        if not values.get("terms"):
            values["terms"] = []
        elif isinstance(values.get("terms"), Term):
            values["terms"] = [values["terms"]]
        return values

    @field_validator("terms")
    @classmethod
    def validate_terms(cls, v):
        """Normalize ``terms`` to initialize Statement."""

        # make TermSequence for validation, then ignore it
        TermSequence.validate_terms(v)
        return v

    @model_validator(mode="after")
    def validate_terms_for_predicate(self) -> Self:
        if self.predicate and len(self.terms) != len(self.predicate):
            message = (
                "The number of items in 'terms' must be "
                + f"{len(self.predicate)}, not {len(self.terms)}, "
                + f"to match predicate.context_slots for '{self.predicate}'"
            )
            raise ValueError(message)
        return self

    @property
    def term_sequence(self) -> TermSequence:
        """Return a TermSequence of the terms in this Statement."""
        return TermSequence(self.terms)

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
    def terms_without_nulls(self) -> Sequence[Term]:
        """
        Get Terms that are not None.

        No Terms should be None for the Statement class, so this method is like an
        assertion for type checking.
        """
        return [term for term in self.terms if term is not None]

    @property
    def wrapped_string(self):
        """Wrap text in string representation of ``self``."""
        content = str(self.predicate._content_with_terms(self.terms))
        unwrapped = self.predicate._add_truth_to_content(content)
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

    def __str__(self):
        """Create one-line string representation for inclusion in other Facts."""
        content = str(self.predicate._content_with_terms(self.terms))
        unwrapped = self.predicate._add_truth_to_content(content)
        return super().__str__().format(unwrapped)

    @property
    def truth(self) -> Optional[bool]:
        """Access :attr:`~Predicate.truth` attribute."""
        return self.predicate.truth

    def _means_if_concrete(
        self, other: Comparable, context: Explanation
    ) -> Iterator[Explanation]:
        if isinstance(other, Statement) and self.predicate.means(other.predicate):
            yield from super()._means_if_concrete(other, context)

    def __len__(self):
        return len(self.generic_terms())

    def _implies_if_concrete(
        self, other: Comparable, context: Explanation
    ) -> Iterator[Explanation]:
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
        new_terms = TermSequence(
            [factor.new_context(changes) for factor in self.terms_without_nulls]
        )
        result.terms = list(new_terms)
        return result

    def _registers_for_interchangeable_context(
        self, matches: ContextRegister
    ) -> Iterator[ContextRegister]:
        r"""
        Find possible combination of interchangeable :attr:`terms`.

        :param matches:
            matching Terms between self and other

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
            left = [term for term in self.terms if term is not None]
            right = [term for term in term_permutation if term is not None]
            changes = ContextRegister.from_lists(left, right)
            changed_registry = matches.replace_keys(changes)
            if all(
                changed_registry != returned_dict for returned_dict in already_returned
            ):
                already_returned.append(changed_registry)
                yield changed_registry

    def term_permutations(self) -> Iterator[TermSequence]:
        """Generate permutations of context factors that preserve same meaning."""
        for pattern in self.predicate.term_index_permutations():
            sorted_terms = [x for _, x in sorted(zip(pattern, self.terms))]
            yield TermSequence(sorted_terms)


class Assertion(Factor, BaseModel):
    """A Statement identified with the authority of a speaker or endorser."""

    statement: "Statement"
    authority: Optional[Entity] = None
    name: str = ""
    absent: bool = False
    generic: bool = False
    context_factor_names: ClassVar[Tuple[str, ...]] = ("statement", "authority")

    def base_string(self):
        text = f"the {self.__class__.__name__.lower()}" + " {}"
        if self.generic:
            text = f"<{text}>"
        if self.absent:
            text = "absence of " + text
        return text

    def __str__(self):
        content = f"of {self.statement.short_string}"

        formatted = self.base_string().format(content)
        if self.authority:
            formatted = formatted.replace(
                "the assertion of", f"the assertion, by {self.authority}, of", 1
            )
        return formatted


Statement.model_rebuild()
Assertion.model_rebuild()
