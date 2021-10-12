""":class:`.Comparable` subclass for things that can be referenced in a Statement."""

from __future__ import annotations
from typing import ClassVar, Dict, Optional, Tuple

from pydantic import BaseModel, Extra, root_validator
from pydantic import ValidationError

from nettlesome.terms import Comparable, ContextRegister, Term


class Entity(Term, BaseModel, extra=Extra.forbid):
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
        more than one thing. Can be checked by a StatementTemplate
        to see whether a verb needs to be made plural.
    """

    name: str = ""
    generic: bool = True
    plural: bool = False
    context_factor_names: ClassVar[Tuple[str, ...]] = ()

    @root_validator(pre=True)
    def validate_type(cls, values) -> Dict:
        name = values.pop("type", None)
        if name and name.lower() != cls.__name__.lower():
            raise ValidationError(f"Expected type {cls.__name__}, not {name}")
        return values

    def __str__(self):
        if self.generic:
            return f"<{self.name}>"
        return self.name

    @property
    def short_string(self):
        """
        Get a short representation of ``self``.

        In Nettlesome, including angle brackets around the representation
        of an object is an indication that the object is generic.
        """
        return str(self)

    def implies(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ) -> bool:
        """
        Test if ``self`` implies ``other``.

        A "generic" Entity implies another Entity even if their names are not
        the same.
        """
        if (
            isinstance(other, Entity)
            and other.generic is False
            and (self.generic or self.name != other.name)
        ):
            return False
        return super().implies(other=other, context=context)

    def means(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ) -> bool:
        """
        Test if ``self`` has the same meaning as ``other``.

        A "generic" Entity has the same meaning as another Entity even if their
        names are not the same.
        """
        if isinstance(other, Entity):
            if self.generic is True:
                return other.generic is True
            return other.generic is False and self.name == other.name

        return super().means(other=other, context=context)
