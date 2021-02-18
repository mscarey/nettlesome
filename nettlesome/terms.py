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

    def __repr__(self) -> str:
        return f'Term(name="{self.name}", generic={self.generic})'
