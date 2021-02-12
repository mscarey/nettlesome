from typing import Any, Dict, List, Text, Tuple

from pint import UnitRegistry
import pytest

from nettlesome.comparable import ContextRegister
from nettlesome.predicates import Predicate, Comparison
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


@pytest.fixture(scope="function")
def make_context_register() -> ContextRegister:
    context_names = ContextRegister()
    context_names.insert_pair(key=Term("Alice"), value=Term("Craig"))
    context_names.insert_pair(key=Term("Bob"), value=Term("Dan"))
    return context_names
