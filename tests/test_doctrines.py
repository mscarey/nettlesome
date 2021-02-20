from nettlesome.doctrines import Doctrine
from nettlesome.entities import Entity
from nettlesome.statements import Statement


class TestDoctrine:
    namespaces = Statement(
        "$concept was one honking great idea",
        terms=Entity("namespaces", plural=True),
    )
    with_authority = Doctrine(statement=namespaces, authority=Entity("Tim Peters"))
    no_authority = Doctrine(statement=namespaces, authority=None)

    def test_dictum_string(self):
        assert "<namespaces> were one honking great idea" in str(self.with_authority)

    def test_means_self(self):
        assert self.with_authority.means(self.with_authority)

    def test_not_same_meaning(self):
        assert not self.with_authority.means(self.no_authority)

    def test_not_same_meaning_None_on_left(self):
        assert not self.no_authority.means(self.with_authority)

    def test_implication(self):
        assert self.with_authority.implies(self.no_authority)

    def test_implies_self(self):
        assert self.with_authority.implies(self.with_authority)

    def test_no_implication_no_authority(self):
        assert not self.no_authority.implies(self.with_authority)
