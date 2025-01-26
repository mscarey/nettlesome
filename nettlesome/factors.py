"""Factors that can be included in FactorGroups."""

from typing import Iterator

from pydantic import BaseModel
from nettlesome.terms import Comparable, Explanation, Term


class Factor(Term, BaseModel):
    r"""
    A thing that can be asserted to be present or absent.

    Factors can be compared as a group by including them
    in :class:`~nettlesome.groups.FactorGroup`\s, unlike
    :class:`~nettlesome.terms.Term`\s that are not Factors.
    """


class AbsenceOf(Comparable, BaseModel):
    """A factor that is not present."""

    generic: bool = False
    absent: Factor

    def __str__(self):
        return f"absence of {str(self.absent)}"

    def _explanations_contradiction(
        self, other: Comparable, explanation: Explanation
    ) -> Iterator[Explanation]:
        if not isinstance(other, Comparable):
            raise TypeError(
                f"{self.__class__} objects may only be compared for "
                + "contradiction with other Factor objects or None."
            )
        if not isinstance(other, self.__class__):
            # No contradiction between absences of any two Comparables
            if isinstance(other, self.absent.__class__):
                explanation_reversed = explanation.with_context(
                    explanation.context.reversed()
                )
                test = other._implies_if_present(self.absent, explanation_reversed)
                for new_explanation in test:
                    yield new_explanation.with_context(
                        new_explanation.context.reversed()
                    )
        elif not isinstance(other, Term):
            explanation_reversed = explanation.reversed_context()
            yield from other._explanations_contradiction(
                self, explanation=explanation_reversed
            )
