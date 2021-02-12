from typing import Any, Dict, List, Text, Tuple

from pint import UnitRegistry
import pytest

from nettlesome.comparable import ContextRegister
from nettlesome.predicates import Predicate, Comparison
from nettlesome.statements import Statement
from nettlesome.terms import Term

ureg = UnitRegistry()
Q_ = ureg.Quantity


@pytest.fixture(scope="class")
def make_predicate() -> Dict[str, Predicate]:

    return {
        "crime": Predicate("$person committed a crime"),
        "murder": Predicate("$shooter murdered $victim"),
        "murder_whether": Predicate("$shooter murdered $victim", truth=None),
        "murder_false": Predicate("$shooter murdered $victim", truth=False),
        "irrelevant": Predicate("$evidence is relevant to show $fact", truth=False),
        "relevant": Predicate("$evidence is relevant to show $fact"),
        "relevant_whether": Predicate(
            "$evidence is relevant to show $fact", truth=None
        ),
        "shooting": Predicate("$shooter shot $victim"),
        "shooting_self": Predicate("$shooter shot $shooter"),
        "no_shooting": Predicate("$shooter shot $victim", truth=False),
        "shooting_whether": Predicate("$shooter shot $victim", truth=None),
        "no_crime": Predicate("$person1 committed a crime", truth=False),
        "three_entities": Predicate("$planner told $intermediary to hire $shooter"),
        "friends": Predicate("$person1 and $person2 were friends"),
        "reliable": Predicate("$evidence was reliable"),
        "no_context": Predicate("context was included", truth=False),
        # Use the irrelevant predicates/factors to make sure they don't affect an outcome.
        "irrelevant_0": Predicate("$person was a clown"),
        "irrelevant_1": Predicate("$person was a bear"),
        "irrelevant_2": Predicate("$place was a circus"),
        "irrelevant_3": Predicate("$person performed at $place"),
    }


@pytest.fixture(scope="class")
def make_comparison() -> Dict[str, Predicate]:
    return {
        "small_weight": Comparison(
            "the amount of gold $person possessed was",
            sign=">=",
            expression=Q_("1 gram"),
        ),
        "large_weight": Comparison(
            "the amount of gold $person possessed was",
            sign=">=",
            expression=Q_("100 kilograms"),
        ),
        "quantity=3": Comparison("The number of mice was", sign="==", expression=3),
        "quantity>=4": Comparison("The number of mice was", sign=">=", expression=4),
        "quantity>5": Comparison("The number of mice was", sign=">", expression=5),
    }


@pytest.fixture(scope="class")
def make_statement(make_predicate, make_entity) -> Dict[str, Statement]:
    p = make_predicate

    return {
        "irrelevant_0": Statement(p["irrelevant_0"], [Term("Craig")]),
        "irrelevant_1": Statement(p["irrelevant_1"], [Term("Dan")]),
        "irrelevant_2": Statement(p["irrelevant_2"], Term("Dan")),
        "irrelevant_3": Statement(p["irrelevant_3"], [Term("Craig"), Term("Dan")]),
        "irrelevant_3_new_context": Statement(
            p["irrelevant_3"], [Term("Craig"), Term("Dan")]
        ),
        "irrelevant_3_context_0": Statement(
            p["irrelevant_3"], [Term("Craig"), Term("Alice")]
        ),
        "crime": Statement(p["crime"], Term("Alice")),
        "no_crime": Statement(p["no_crime"], Term("Alice")),
        "no_crime_entity_order": Statement(p["no_crime"], [Term("Bob")]),
        "murder": Statement(p["murder"], terms=[Term("Alice"), Term("Bob")]),
        "no_murder": Statement(p["murder_false"], terms=[Term("Alice"), Term("Bob")]),
        "murder_entity_swap": Statement(p["murder"], [Term("Bob"), Term("Alice")]),
        "murder_craig": Statement(p["murder"], [Term("Craig"), Term("Dan")]),
        "murder_whether": Statement(
            p["murder_whether"], terms=[Term("Alice"), Term("Bob")]
        ),
        "shooting": Statement(p["shooting"], terms=[Term("Alice"), Term("Bob")]),
        "shooting_self": Statement(p["shooting_self"], terms=[Term("Alice")]),
        "shooting_craig": Statement(p["shooting"], [Term("Craig"), Term("Dan")]),
        "shooting_entity_order": Statement(p["shooting"], [Term("Bob"), Term("Alice")]),
        "no_shooting": Statement(p["no_shooting"]),
        "shooting_whether": Statement(p["shooting_whether"]),
        "no_shooting_entity_order": Statement(
            p["no_shooting"], [Term("Bob"), Term("Alice")]
        ),
        "three_entities": Statement(
            p["three_entities"], [Term("Alice"), Term("Bob"), Term("Craig")]
        ),
        "repeating_entity": Statement(
            p["three_entities"], [Term("Alice"), Term("Bob"), Term("Alice")]
        ),
        "large_weight": Statement(
            p["large_weight"],
            Term("Alice"),
        ),
        "small_weight": Statement(
            p["small_weight"],
            Term("Alice"),
        ),
        "small_weight_bob": Statement(
            p["small_weight"],
            Term("Bob"),
        ),
        "friends": Statement(p["friends"], [Term("Alice"), Term("Bob")]),
        "no_context": Statement(p["no_context"]),
    }


@pytest.fixture(scope="class")
def make_complex_fact(make_predicate, make_factor) -> Dict[str, Statement]:
    p = make_predicate
    f = make_statement

    return {
        "irrelevant_murder": Statement(p["irrelevant"], (f["shooting"], f["murder"])),
        "relevant_murder": Statement(p["relevant"], (f["shooting"], f["murder"])),
        "relevant_murder_swap_entities": Statement(
            p["relevant"], (f["shooting"], f["murder"])
        ),
        "relevant_murder_nested_swap": Statement(
            p["relevant"], (f["shooting_entity_order"], f["murder_entity_swap"])
        ),
        "relevant_murder_whether": Statement(
            p["relevant"], (f["shooting"], f["murder_whether"])
        ),
        "whether_relevant_murder_whether": Statement(
            p["relevant"], (f["shooting_whether"], f["murder_whether"])
        ),
        "relevant_murder_swap": Statement(
            p["relevant"], (f["shooting"], f["murder_entity_swap"])
        ),
        "relevant_murder_craig": Statement(
            p["relevant"], (f["shooting_craig"], f["murder_craig"])
        ),
        "relevant_murder_alice_craig": Statement(
            p["relevant"], (f["shooting"], f["murder_craig"])
        ),
    }


@pytest.fixture(scope="function")
def make_context_register() -> ContextRegister:
    context_names = ContextRegister()
    context_names.insert_pair(key=Term("Alice"), value=Term("Craig"))
    context_names.insert_pair(key=Term("Bob"), value=Term("Dan"))
    return context_names
