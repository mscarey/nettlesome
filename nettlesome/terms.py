""":class:`.Comparable` subclass for things that can be referenced in a Statement."""

from __future__ import annotations
from typing import Callable, Iterator, List, Optional

from nettlesome.comparable import Comparable, ContextRegister


class Term(Comparable):
    r"""
    Things that can be referenced in a Statement.

    The name of a Term can replace the placeholder in a StatementTemplate

    :param name:
        An identifier. An :class:`Entity` with the same ``name``
        is considered to refer to the same specific object, but
        if they have different names but are ``generic`` and are
        otherwise the same, then they're considered to have the
        same meaning and they evaluate equal to one another.

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
        absent: bool = False,
        generic: bool = True,
        plural: bool = False,
    ) -> None:
        self.name = name
        self.absent = absent
        self.generic = generic
        self.plural = plural

    @property
    def short_string(self):
        if self.generic:
            return f"<{self.name}>"
        return self.name

    def __repr__(self) -> str:
        return (
            f'Term(name="{self.name}", absent={self.absent}, '
            f"generic={self.generic}, plural={self.plural})"
        )

    def union(
        self, other: Comparable, context: ContextRegister
    ) -> Optional[Comparable]:
        raise NotImplementedError
