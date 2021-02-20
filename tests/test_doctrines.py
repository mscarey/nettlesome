from nettlesome.doctrines import Doctrine
from nettlesome.entities import Entity
from nettlesome.statements import Statement


class TestDoctrine:
    namespaces = Statement(
        "$concept was one honking great idea",
        terms=Entity("namespaces", plural=True),
    )
    generic_authority = Doctrine(statement=namespaces, authority=Entity("Twitter user"))
    specific_authority = Doctrine(
        statement=namespaces, authority=Entity("Tim Peters", generic=False)
    )
    no_authority = Doctrine(statement=namespaces, authority=None)

    def test_dictum_string(self):
        assert "<namespaces> were one honking great idea" in str(self.generic_authority)

    def test_means_self(self):
        assert self.generic_authority.means(self.generic_authority)

    def test_means_self_with_no_authority(self):
        assert self.no_authority.means(self.no_authority)

    def test_means_self_with_specific_authority(self):
        assert self.specific_authority.means(self.specific_authority)

    def test_not_same_meaning(self):
        assert not self.generic_authority.means(self.no_authority)

    def test_not_same_meaning_None_on_left(self):
        assert not self.no_authority.means(self.generic_authority)

    def test_not_same_meaning_specific_entity(self):
        assert not self.specific_authority.means(self.no_authority)

    def test_not_same_meaning_None_on_left_specific_entity(self):
        assert not self.no_authority.means(self.specific_authority)

    def test_no_authority_implies_none(self):
        assert self.no_authority.implies(self.no_authority)

    def test_generic_authority_implies_none(self):
        assert self.generic_authority.implies(self.no_authority)

    def test_no_implication_of_specific(self):
        assert not self.generic_authority.implies(self.specific_authority)

    def test_implication_by_specific(self):
        assert self.specific_authority.implies(self.generic_authority)

    def test_no_implication_of_specific_by_none(self):
        assert not self.no_authority.implies(self.specific_authority)

    def test_implication_of_none_by_specific(self):
        assert self.specific_authority.implies(self.no_authority)

    def test_implies_self(self):
        assert self.generic_authority.implies(self.generic_authority)

    def test_no_implication_no_authority(self):
        assert not self.no_authority.implies(self.generic_authority)
