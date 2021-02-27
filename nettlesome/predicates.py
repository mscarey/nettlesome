r"""
Phrases that contain meanings of :class:`.Statement`\s.

Can contain references to other :class:`.Statement`\s,
to numeric values, to dates, or to quantities (with the use of
the `pint <https://pint.readthedocs.io/en/>`_ library).
"""

from __future__ import annotations

from datetime import date
from itertools import product

from string import Template
from typing import Any, ClassVar, Dict, Iterable, Mapping
from typing import List, Optional, Sequence, Union

from pint import UnitRegistry, Quantity


from nettlesome.comparable import Comparable, FactorSequence
from nettlesome.terms import Term

ureg = UnitRegistry()
Q_ = ureg.Quantity


class StatementTemplate(Template):
    def __init__(self, template: str, make_singular: bool = True) -> None:
        super().__init__(template)
        placeholders = [
            m.group("named") or m.group("braced")
            for m in self.pattern.finditer(self.template)
            if m.group("named") or m.group("braced")
        ]
        self._placeholders = list(dict.fromkeys(placeholders))

        if make_singular:
            self.make_content_singular()

    def __str__(self) -> str:
        return f'StatementTemplate("{self.template}")'

    def make_content_singular(self) -> None:
        """Convert template text for self.context to singular "was"."""
        for placeholder in self.placeholders:
            named_pattern = "$" + placeholder + " were"
            braced_pattern = "${" + placeholder + "} were"
            self.template = self.template.replace(
                named_pattern, "$" + placeholder + " was"
            )
            self.template = self.template.replace(
                braced_pattern, "$" + placeholder + " was"
            )
        return None

    def get_template_with_plurals(self, context: TermSequence) -> str:
        """
        Get a version of self with "was" replaced by "were" for any plural terms.

        Does not modify this object's template attribute.
        """
        result = self.template[:]
        placeholders = self.placeholders
        self._check_number_of_terms(placeholders, context)
        for idx, factor in enumerate(context):
            if factor.__dict__.get("plural") is True:
                named_pattern = "$" + placeholders[idx] + " was"
                braced_pattern = "${" + placeholders[idx] + "} was"
                result = result.replace(
                    named_pattern, "$" + placeholders[idx] + " were"
                )
                result = result.replace(
                    braced_pattern, "$" + placeholders[idx] + " were"
                )
        return result

    @property
    def placeholders(self) -> List[str]:
        return self._placeholders

    def get_term_sequence_from_mapping(
        self, term_mapping: Mapping[str, Comparable]
    ) -> Sequence[Comparable]:
        """Get an ordered list of terms from a mapping of placeholder names to terms."""
        placeholders = self.placeholders
        result = [term_mapping[placeholder] for placeholder in placeholders]
        return FactorSequence(result)

    def _check_number_of_terms(
        self, placeholders: List[str], context: FactorSequence
    ) -> None:
        if len(set(placeholders)) != len(context):
            raise ValueError(
                f"The number of terms passed in 'context' ({len(context)}) must be equal to the "
                f"number of placeholders in the StatementTemplate ({len(placeholders)})."
            )
        return None

    def mapping_placeholder_to_term(
        self, context: FactorSequence
    ) -> Dict[str, Comparable]:
        """
        Get a mapping of template placeholders to context terms.

        :param context:
            a list of context :class:`.factors.Factor`/s, in the same
            order they appear in the template string.
        """
        self._check_number_of_terms(self.placeholders, context)
        return dict(zip(self.placeholders, context))

    def mapping_placeholder_to_term_name(
        self, context: FactorSequence
    ) -> Dict[str, str]:
        """
        Get a mapping of template placeholders to the names of their context terms.

        :param context:
            a list of :class:`~authorityspoke.comparable.Comparable`
            context terms in the same
            order they appear in the template string.
        """
        mapping = self.mapping_placeholder_to_term(context)
        mapping_to_string = {k: v.short_string for k, v in mapping.items()}
        return mapping_to_string

    def substitute_with_plurals(self, context: Iterable[Term]) -> str:
        """
        Update template text with strings representing Comparable terms.

        :param context:
            terms with `.short_string()`
            methods to substitute into template, and optionally with `plural`
            attributes to indicate whether to change the word "was" to "were"

        :returns:
            updated version of template text
        """
        new_content = self.get_template_with_plurals(context=context)
        substitutions = self.mapping_placeholder_to_term_name(context=context)
        new_template = self.__class__(new_content, make_singular=False)
        return new_template.substitute(substitutions)


class Predicate:
    r"""
    A statement about real events or about a legal conclusion.

    Should contain an English-language phrase in the past tense. The past tense
    is used because legal analysis is usually backward-looking,
    determining the legal effect of past acts or past conditions.

    Don't use capitalization or end punctuation to signal the beginning
    or end of the phrase, because the phrase may be used in a
    context where it's only part of a longer sentence.

    If you need to mention the same term more than once in a Predicate,
    use the same placeholder for that term each time. If you later create
    a Fact object using the same Predicate, you will only include each unique
    term once.

        >>> # the template has two placeholders referring to the identical term
        >>> Predicate("$applicant opened a bank account for $applicant and $cosigner")

    Sometimes, a Predicate or Comparison needs to mention two terms that are
    different from each other, but that have interchangeable positions in that
    particular phrase. To convey interchangeability, the template string should
    use identical text for the placeholders for the interchangeable terms,
    except that the different placeholders should each end with a different digit.

        >>> # the template has two placeholders referring to different but interchangeable terms
        >>> Predicate("$relative1 and $relative2 both were members of the same family")

    :param template:
        a clause containing an assertion in English in the past tense, with
        placeholders showing where references to specific terms
        from the case can be inserted to make the clause specific.
        This string must be a valid Python :py:class:`string.Template`\.

    :param truth:
        indicates whether the clause in ``content`` is asserted to be
        true or false. ``None`` indicates an assertion as to "whether"
        the clause is true or false, without specifying which.

    """

    def __init__(self, template: str, truth: Optional[bool] = True):
        """
        Clean up and test validity of attributes.

        If the :attr:`content` sentence is phrased to have a plural
        context term, normalizes it by changing "were" to "was".
        """
        self.template = StatementTemplate(template, make_singular=True)
        self.truth = truth

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(template="{self.template.template}", '
            f"truth={self.truth})"
        )

    @property
    def content(self) -> str:
        return self.template.template

    def content_without_placeholders(self) -> str:
        changes = {p: "{}" for p in self.template.placeholders}
        return self.template.substitute(**changes)

    def _content_with_terms(self, terms: FactorSequence) -> str:
        r"""
        Make a sentence by filling in placeholders with names of Factors.

        :param context:
            terms to be mentioned in the context of
            this Predicate. They do not need to be type :class:`.Entity`

        :returns:
            a sentence created by substituting string representations
            of terms for the placeholders in the content template
        """
        with_plurals = self.template.substitute_with_plurals(terms)

        return with_plurals

    def contradicts(self, other: Any) -> bool:
        r"""
        Test whether ``other`` and ``self`` have contradictory meanings.

        This is determined only by the ``truth`` value, the exact template
        content, and whether the placeholders indicate interchangeable terms.
        """
        if not self._same_meaning_as_true_predicate(other):
            return False

        if self.truth is None or other.truth is None:
            return False

        if self.__class__.__name__ != other.__class__.__name__:
            return False

        return self.truth != other.truth

    def same_content_meaning(self, other: Predicate) -> bool:
        """
        Test if :attr:`~Predicate.content` strings of ``self`` and ``other`` have same meaning.

        This once was used to disregard differences between "was" and "were",
        but that now happens in :meth:`Predicate.__post_init__`.

        :param other:
            another :class:`Predicate` being compared to ``self``

        :returns:
            whether ``self`` and ``other`` have :attr:`~Predicate.content` strings
            similar enough to be considered to have the same meaning.
        """
        return (
            self.content_without_placeholders().lower()
            == other.content_without_placeholders().lower()
        )

    def same_term_positions(self, other: Predicate) -> bool:

        return list(self.term_positions().values()) == list(
            other.term_positions().values()
        )

    def _same_meaning_as_true_predicate(self, other: Predicate) -> bool:
        """
        Test whether ``self`` and ``other`` mean the same if they are both True.
        """
        if not isinstance(other, Predicate):
            raise TypeError(
                f"Type {self.__class__.__name__} can't imply, contradict, or "
                f"have same meaning as type {other.__class__.__name__}"
            )
        if not self.same_content_meaning(other):
            return False

        return self.same_term_positions(other)

    def means(self, other: Any) -> bool:
        """
        Test whether ``self`` and ``other`` have identical meanings.

        To return ``True``, ``other`` can be neither broader nor narrower.
        """

        if not self._same_meaning_as_true_predicate(other):
            return False

        return self.truth == other.truth

    def __gt__(self, other: Predicate) -> bool:
        """
        Test whether ``self`` implies ``other``.

        :returns:
            whether ``self`` implies ``other``, which is ``True``
            if their statements about quantity imply it.
        """
        return self.implies(other)

    def implies(self, other: Any) -> bool:
        """
        Test whether ``self`` implies ``other``.
        """
        if self.truth is None:
            return False
        if not self._same_meaning_as_true_predicate(other):
            return False
        if other.truth is None:
            return True
        return self.truth == other.truth

    def __ge__(self, other: Predicate) -> bool:
        if self.means(other):
            return True
        return self.implies(other)

    def __len__(self):
        """
        Also called the linguistic valency, arity, or adicity.

        :returns:
            the number of entities that can fit in the pairs of brackets
            in the predicate. ``self.expression`` doesn't count as one of these entities,
            even though the place where ``self.expression`` goes in represented by brackets
            in the ``self.content`` string.
        """

        return len(set(self.template.placeholders))

    def negated(self) -> Predicate:
        """Copy ``self``, with the opposite truth value."""
        return Predicate(
            template=self.content,
            truth=not self.truth,
        )

    def term_positions(self):
        """
        Create list of positions that each term could take without changing Predicate's meaning.

        Assumes that if placeholders are the same except for a final digit, that means
        they've been labeled as interchangeable with one another.
        """

        without_duplicates = self.template.placeholders
        result = {p: {i} for i, p in enumerate(without_duplicates)}

        for index, placeholder in enumerate(without_duplicates):
            if placeholder[-1].isdigit:
                for k in result.keys():
                    if k[-1].isdigit() and k[:-1] == placeholder[:-1]:
                        result[k].add(index)
        return result

    def term_index_permutations(self) -> List[List[int]]:
        """Get the arrangements of all this Predicate's terms that preserve the same meaning."""
        product_of_positions = product(*self.term_positions().values())
        without_duplicates = [x for x in product_of_positions if len(set(x)) == len(x)]
        return without_duplicates

    def add_truth_to_content(self, content: str) -> str:
        if self.truth is None:
            truth_prefix = "whether "
        elif self.truth is False:
            truth_prefix = "it was false that "
        else:
            truth_prefix = "that "
        return f"{truth_prefix}{content}"

    def __str__(self):
        return self.add_truth_to_content(self.content)
