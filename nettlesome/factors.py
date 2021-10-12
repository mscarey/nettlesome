"""Factors that can be included in FactorGroups."""

from nettlesome.terms import Term


class Factor(Term):
    r"""
    A thing that can be asserted to be present or absent.

    Factors can be compared as a group by including them
    in :class:`~nettlesome.groups.FactorGroup`\s, unlike
    :class:`~nettlesome.term.Term`\s that are not Factors.
    """
