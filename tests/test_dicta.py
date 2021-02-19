from nettlesome.dicta import Dictum
from nettlesome.entities import Entity
from nettlesome.statements import Statement


class TestDicta:
    def test_dictum_string(self):
        statement = Statement(
            "$concept was one honking great idea",
            terms=Entity("namespaces", plural=True),
        )
        dictum = Dictum(statement=statement, authority=Entity("Tim Peters"))
        assert "<namespaces> were one honking great idea" in str(dictum)
