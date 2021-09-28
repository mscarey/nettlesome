"""
Assertions, or Statements associated with speakers or endorsers.
"""

from typing import ClassVar, Optional, Tuple

from pydantic import BaseModel

from nettlesome.entities import Entity
from nettlesome.statements import Statement
from nettlesome.factors import Factor


class Assertion(BaseModel, Factor):
    """A Statement identified with the authority of an Entity."""

    statement: Statement
    authority: Optional[Entity] = None
    name: str = ""
    absent: bool = False
    generic: bool = False
    context_factor_names: ClassVar[Tuple[str, str]] = ("statement", "authority")

    def __str__(self):
        content = f"of {self.statement.short_string}"

        formatted = super().__str__().format(content)
        if self.authority:
            formatted = formatted.replace(
                "the assertion of", f"the assertion, by {self.authority}, of", 1
            )
        return formatted
