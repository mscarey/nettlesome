from nettlesome.entities import Entity
from nettlesome.statements import Statement
from nettlesome.factors import Factor


class Dictum(Factor):
    def __init__(
        self,
        authority: Entity,
        statement: Statement,
        name: str = "",
        absent: bool = False,
        generic: bool = False,
    ) -> None:
        self.authority = authority
        self.statement = statement
        super().__init__(name=name, absent=absent, generic=generic)

    def __str__(self):
        content = f"{self.statement.short_string}, according to {self.authority}"
        return super().__str__().format(content)
