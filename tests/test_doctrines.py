import pytest

from nettlesome.comparable import ContextRegister
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

    def test_new_context(self):
        context = ContextRegister()
        context.insert_pair(Entity("Twitter user"), Entity("Python Software Foundation", generic=False))
        new = self.generic_authority.new_context(context)
        assert "according to the entity Python" in str(new)

class TestInterchangeable:
    identical = Statement(
        "$god1 was identical with $god2",
        terms=[Entity("Dionysus"), Entity("Osiris")],
    )
    generic_authority = Doctrine(statement=identical, authority=Entity("a historian"))
    specific_authority = Doctrine(
        statement=identical, authority=Entity("Herodotus", generic=False)
    )
    no_authority = Doctrine(statement=identical, authority=None)


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

    def test_same_because_interchangeable(self, make_doctrine):
        assert make_doctrine["plotted_per_alice"].means(make_doctrine["plotted_per_craig"])
        assert make_doctrine["plotted_per_craig"].means(make_doctrine["plotted_per_alice"])

    def test_different_because_not_interchangeable(self, make_doctrine):
        assert not make_doctrine["plotted_per_alice"].means(make_doctrine["plotted_per_bob"])
        assert not make_doctrine["plotted_per_bob"].means(make_doctrine["plotted_per_alice"])

class TestComplex:

    @pytest.mark.parametrize(
        "left, right, expected",
        [("generic", "generic", True),
        ("no", "no", True),
        ("specific", "specific", True),
        ("generic", "specific", False),
        ("specific", "generic", False),
        ("specific", "no", False),
        ]
    )
    def test_doctrines_same_meaning(self, make_doctrine, left, right, expected):
        assert make_doctrine[f"{left}_authority"].means(make_doctrine[f"{right}_authority"]) is expected
        assert make_doctrine[f"{left}_authority_reversed"].means(make_doctrine[f"{right}_authority"]) is expected
        assert make_doctrine[f"{left}_authority"].means(make_doctrine[f"{right}_authority_reversed"]) is expected
        assert make_doctrine[f"{left}_authority_reversed"].means(make_doctrine[f"{right}_authority_reversed"]) is expected

    @pytest.mark.parametrize(
        "left, right, expected",
        [("no", "no", True),
        ("no", "generic", False),
        ("no", "specific", False),
        ("generic", "generic", True),
        ("generic", "no", True),
        ("generic", "specific", False),
        ("specific", "specific", True),
        ("specific", "generic", True),
        ("specific", "no", True),
        ]
    )
    def test_doctrines_imply(self, make_doctrine, left, right, expected):
        assert make_doctrine[f"{left}_authority"].implies(make_doctrine[f"{right}_authority"]) is expected
        assert make_doctrine[f"{left}_authority_reversed"].implies(make_doctrine[f"{right}_authority"]) is expected
        assert make_doctrine[f"{left}_authority"].implies(make_doctrine[f"{right}_authority_reversed"]) is expected
        assert make_doctrine[f"{left}_authority_reversed"].implies(make_doctrine[f"{right}_authority_reversed"]) is expected
