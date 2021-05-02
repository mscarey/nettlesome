"""
Assertions, or Statements associated with speakers or endorsers.
"""

from typing import Optional

from nettlesome.entities import Entity
from nettlesome.statements import Statement
from nettlesome.factors import Factor


class Assertion(Factor):
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
        content = f"of {self.statement.short_string}"

        formatted = super().__str__().format(content)
        if self.authority:
            formatted = formatted.replace(
                "the assertion of", f"the assertion, by {self.authority}, of", 1
            )
        return formatted
