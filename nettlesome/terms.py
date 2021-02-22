""":class:`.Comparable` subclass for things that can be referenced in a Statement."""

from __future__ import annotations
from typing import Callable, Iterator, List, Optional

from nettlesome.comparable import Comparable, ContextRegister


class Term(Comparable):
    r"""
    Things that can be referenced in a Statement.

    The name of a Term can replace the placeholder in a StatementTemplate

    :param name:
        An identifier.

    :param generic:
        Determines whether a change in the ``name`` of the
        :class:`Entity` would change the meaning of the
        :class:`.Factor` in which the :class:`Entity` is
        embedded.

    :param plural:
        Specifies whether the :class:`Entity` object refers to
        more than one thing. In other words, whether it would
        be represented by a plural noun.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        generic: bool = True,
    ) -> None:
        self.name = name
        self.generic = generic

    def _borrow_generic_context(self, other: Term) -> Term:
        self_factors = list(self.recursive_factors.values())
        other_factors = list(other.recursive_factors.values())
        changes = ContextRegister()
        for i, factor in enumerate(self_factors):
            if factor.generic:
                changes.insert_pair(factor, other_factors[i])
        return self.new_context(changes)

    def add(
        self, other: Term, context: Optional[ContextRegister] = None
    ) -> Optional[Term]:
        if not isinstance(other, Term):
            raise TypeError
        if self.implies(other, context=context):
            return self
        if other.implies(self, context=context):
            return other._borrow_generic_context(self)
        return None

    def __add__(self, other: Term) -> Optional[Comparable]:
        return self.add(other)
