"""Factors that can be included in FactorGroups."""

from typing import Optional
from nettlesome.terms import Term


class Factor(Term):
    r"""
    A thing that can be asserted to be present or absent.

    Factors can be compared as a group by including them
    in :class:`~nettlesome.groups.FactorGroup`\s, unlike
    :class:`~nettlesome.term.Term`\s that are not Factors.
    """

    def __init__(
        self, name: Optional[str] = None, generic: bool = False, absent: bool = False
    ) -> None:
        """Add "absent" attribute to Term's attributes."""
        self.absent = absent
        super().__init__(name=name, generic=generic)
