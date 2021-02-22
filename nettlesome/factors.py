from typing import Optional
from nettlesome.terms import Term


class Factor(Term):
    def __init__(
        self, name: Optional[str] = None, generic: bool = False, absent: bool = False
    ) -> None:
        self.absent = absent
        super().__init__(name=name, generic=generic)
