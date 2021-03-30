"""
Doctrines, or Statements associated with speakers or endorsers.

There may be a better class name than "Doctrine".
"""

from typing import Optional

from nettlesome.entities import Entity
from nettlesome.statements import Statement
from nettlesome.factors import Factor


class Doctrine(Factor):
    """A Statement identified with the authority of an Entity."""

    context_factor_names = ("statement", "authority")

    def __init__(
        self,
        statement: Statement,
        authority: Optional[Entity] = None,
        name: str = "",
        absent: bool = False,
        generic: bool = False,
    ) -> None:
        """Identify Entity's endorsement of a Statement."""
        self.authority = authority
        self.statement = statement
        super().__init__(name=name, absent=absent, generic=generic)

    def __str__(self):
        content = f"{self.statement.short_string}"
        if self.authority:
            content += f", according to {self.authority}"
        return super().__str__().format(content)
