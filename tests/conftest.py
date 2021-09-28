from typing import Dict

import pytest

from nettlesome.terms import ContextRegister
from nettlesome.assertions import Assertion
from nettlesome.predicates import Predicate
from nettlesome.quantities import Comparison, Q_
from nettlesome.statements import Statement
from nettlesome.entities import Entity


@pytest.fixture(scope="class")
def make_predicate() -> Dict[str, Predicate]:

    return {
        "make_predicate": Predicate(content="$person committed a crime"),
        "murder": Predicate(content="$shooter murdered $victim"),
        "murder_whether": Predicate(content="$shooter murdered $victim", truth=None),
        "murder_false": Predicate(content="$shooter murdered $victim", truth=False),
        "irrelevant": Predicate(
            content="$evidence is relevant to show $fact", truth=False
        ),
        "relevant": Predicate(content="$evidence is relevant to show $fact"),
        "relevant_whether": Predicate(
            content="$evidence is relevant to show $fact", truth=None
        ),
        "shooting": Predicate(content="$shooter shot $victim"),
        "shooting_self": Predicate(content="$shooter shot $shooter"),
        "no_shooting": Predicate(content="$shooter shot $victim", truth=False),
        "shooting_whether": Predicate(content="$shooter shot $victim", truth=None),
        "plotted": Predicate(content="$plotter1 plotted with $plotter2"),
        "crime": Predicate(content="$person1 committed a crime"),
        "no_crime": Predicate(content="$person1 committed a crime", truth=False),
        "three_entities": Predicate(
            content="$planner told $intermediary to hire $shooter"
        ),
        "friends": Predicate(content="$person1 and $person2 were friends"),
        "reliable": Predicate(content="$evidence was reliable"),
        "no_context": Predicate(content="context was included", truth=False),
        # Use the irrelevant predicates/factors to make sure they don't affect an outcome.
        "irrelevant_0": Predicate(content="$person was a clown"),
        "irrelevant_1": Predicate(content="$person was a bear"),
        "irrelevant_2": Predicate(content="$place was a circus"),
        "irrelevant_3": Predicate(content="$person performed at $place"),
    }


@pytest.fixture(scope="class")
def make_comparison() -> Dict[str, Predicate]:
    return {
        "small_weight": Comparison(
            content="the amount of gold $person possessed was",
            sign=">=",
            expression=Q_("1 gram"),
        ),
        "large_weight": Comparison(
            content="the amount of gold $person possessed was",
            sign=">=",
            expression=Q_("100 kilograms"),
        ),
        "quantity=3": Comparison(
            content="The number of mice was", sign="==", expression=3
        ),
        "quantity>=4": Comparison(
            content="The number of mice was", sign=">=", expression=4
        ),
        "quantity>5": Comparison(
            content="The number of mice was", sign=">", expression=5
        ),
        "acres": Comparison(
            content="the distance between $place1 and $place2 was",
            sign=">=",
            expression=Q_("10 acres"),
        ),
        "exact": Comparison(
            content="the distance between $place1 and $place2 was",
            sign="==",
            expression=Q_("25 feet"),
        ),
        "float_distance": Comparison(
            content="the distance between $place1 and $place2 was",
            truth=True,
            sign="<",
            expression=20.0,
        ),
        "higher_int": Comparison(
            content="the distance between $place1 and $place2 was",
            sign="<=",
            expression=30,
        ),
        "int_distance": Comparison(
            content="the distance between $place1 and $place2 was",
            truth=True,
            sign="<",
            expression=20,
        ),
        "int_higher": Comparison(
            content="the distance between $place1 and $place2 was",
            sign="<=",
            expression=30,
        ),
        "less": Comparison(
            content="the distance between $place1 and $place2 was",
            truth=True,
            sign="<",
            expression=Q_("35 feet"),
        ),
        "less_whether": Comparison(
            content="the distance between $place1 and $place2 was",
            truth=None,
            sign="<",
            expression=Q_("35 feet"),
        ),
        "less_than_20": Comparison(
            content="the distance between $place1 and $place2 was",
            truth=True,
            sign="<",
            expression=Q_("20 feet"),
        ),
        "meters": Comparison(
            content="the distance between $place1 and $place2 was",
            sign=">=",
            expression=Q_("10 meters"),
        ),
        "not_equal": Comparison(
            content="the distance between $place1 and $place2 was",
            truth=True,
            sign="!=",
            expression=Q_("35 feet"),
        ),
        "more": Comparison(
            content="the distance between $place1 and $place2 was",
            truth=True,
            sign=">=",
            expression=Q_("35 feet"),
        ),
        "not_more": Comparison(
            content="the distance between $place1 and $place2 was",
            truth=False,
            sign=">",
            expression=Q_("35 feet"),
        ),
        "way_more": Comparison(
            content="the distance between $place1 and $place2 was",
            truth=True,
            sign=">=",
            expression=Q_("30 miles"),
        ),
    }


@pytest.fixture(scope="class")
def make_statement(make_predicate, make_comparison) -> Dict[str, Statement]:
    p = make_predicate
    c = make_comparison
    return {
        "irrelevant_0": Statement(p["irrelevant_0"], [Entity("Craig")]),
        "irrelevant_1": Statement(p["irrelevant_1"], [Entity("Dan")]),
        "irrelevant_2": Statement(p["irrelevant_2"], Entity("Dan")),
        "irrelevant_3": Statement(
            p["irrelevant_3"], [Entity("Craig"), Entity("circus")]
        ),
        "irrelevant_3_new_context": Statement(
            p["irrelevant_3"], [Entity("Craig"), Entity("Dan")]
        ),
        "irrelevant_3_context_0": Statement(
            p["irrelevant_3"], [Entity("Craig"), Entity("Alice")]
        ),
        "crime": Statement(p["crime"], Entity("Alice")),
        "crime_bob": Statement(p["crime"], Entity("Bob")),
        "crime_craig": Statement(p["crime"], Entity("Craig")),
        "crime_generic": Statement(p["crime"], Entity("Alice"), generic=True),
        "crime_specific_person": Statement(p["crime"], Entity("Alice", generic=False)),
        "absent_no_crime": Statement(p["no_crime"], Entity("Alice"), absent=True),
        "no_crime": Statement(p["no_crime"], Entity("Alice")),
        "no_crime_entity_order": Statement(p["no_crime"], [Entity("Bob")]),
        "murder": Statement(p["murder"], terms=[Entity("Alice"), Entity("Bob")]),
        "murder_false": Statement(
            p["murder_false"], terms=[Entity("Alice"), Entity("Bob")]
        ),
        "murder_entity_order": Statement(p["murder"], [Entity("Bob"), Entity("Alice")]),
        "murder_craig": Statement(p["murder"], [Entity("Craig"), Entity("Dan")]),
        "murder_whether": Statement(
            p["murder_whether"], terms=[Entity("Alice"), Entity("Bob")]
        ),
        "shooting": Statement(p["shooting"], terms=[Entity("Alice"), Entity("Bob")]),
        "shooting_self": Statement(p["shooting_self"], terms=[Entity("Alice")]),
        "shooting_craig": Statement(p["shooting"], [Entity("Craig"), Entity("Dan")]),
        "shooting_entity_order": Statement(
            p["shooting"], [Entity("Bob"), Entity("Alice")]
        ),
        "no_shooting": Statement(
            p["no_shooting"], terms=[Entity("Alice"), Entity("Bob")]
        ),
        "shooting_whether": Statement(
            p["shooting_whether"], terms=[Entity("Alice"), Entity("Bob")]
        ),
        "no_shooting_entity_order": Statement(
            p["no_shooting"], [Entity("Bob"), Entity("Alice")]
        ),
        "plotted": Statement(p["plotted"], [Entity("Alice"), Entity("Craig")]),
        "plotted_reversed": Statement(p["plotted"], [Entity("Alice"), Entity("Craig")]),
        "three_entities": Statement(
            p["three_entities"], [Entity("Alice"), Entity("Bob"), Entity("Craig")]
        ),
        "large_weight": Statement(
            p["large_weight"],
            Entity("Alice"),
        ),
        "large_weight_craig": Statement(
            p["large_weight"],
            Entity("Craig"),
        ),
        "small_weight": Statement(
            p["small_weight"],
            Entity("Alice"),
        ),
        "small_weight_bob": Statement(
            p["small_weight"],
            Entity("Bob"),
        ),
        "friends": Statement(p["friends"], [Entity("Alice"), Entity("Bob")]),
        "no_context": Statement(p["no_context"]),
        "exact": Statement(
            c["exact"], terms=[Entity("San Francisco"), Entity("Oakland")]
        ),
        "less": Statement(
            c["less"], terms=[Entity("San Francisco"), Entity("Oakland")]
        ),
        "less_than_20": Statement(
            c["less_than_20"], terms=[Entity("San Francisco"), Entity("Oakland")]
        ),
        "less_whether": Statement(
            c["less_whether"], terms=[Entity("San Francisco"), Entity("Oakland")]
        ),
        "more": Statement(
            c["more"], terms=[Entity("San Francisco"), Entity("Oakland")]
        ),
        "more_atlanta": Statement(
            c["more"], terms=[Entity("Atlanta"), Entity("Marietta")]
        ),
        "more_meters": Statement(
            c["meters"], terms=[Entity("San Francisco"), Entity("Oakland")]
        ),
        "not_more": Statement(
            c["not_more"], terms=[Entity("San Francisco"), Entity("Oakland")]
        ),
        "float_distance": Statement(
            c["float_distance"], terms=[Entity("San Francisco"), Entity("Oakland")]
        ),
        "int_distance": Statement(
            c["int_distance"], terms=[Entity("San Francisco"), Entity("Oakland")]
        ),
        "higher_int": Statement(
            c["higher_int"], terms=[Entity("San Francisco"), Entity("Oakland")]
        ),
        "way_more": Statement(
            c["way_more"], terms=[Entity("San Francisco"), Entity("Oakland")]
        ),
        "absent_less": Statement(
            c["less"], terms=[Entity("San Francisco"), Entity("Oakland")], absent=True
        ),
        "absent_more": Statement(
            c["more"], terms=[Entity("San Francisco"), Entity("Oakland")], absent=True
        ),
        "absent_way_more": Statement(
            c["way_more"],
            terms=[Entity("San Francisco"), Entity("Oakland")],
            absent=True,
        ),
    }


@pytest.fixture(scope="class")
def make_complex_fact(make_predicate, make_statement) -> Dict[str, Statement]:
    p = make_predicate
    f = make_statement

    return {
        "irrelevant_murder": Statement(p["irrelevant"], (f["shooting"], f["murder"])),
        "relevant_murder": Statement(p["relevant"], (f["shooting"], f["murder"])),
        "relevant_murder_swap_entities": Statement(
            p["relevant"], (f["shooting"], f["murder"])
        ),
        "relevant_murder_nested_swap": Statement(
            p["relevant"], (f["shooting_entity_order"], f["murder_entity_order"])
        ),
        "relevant_murder_whether": Statement(
            p["relevant"], (f["shooting"], f["murder_whether"])
        ),
        "whether_relevant_murder_whether": Statement(
            p["relevant"], (f["shooting_whether"], f["murder_whether"])
        ),
        "relevant_murder_swap": Statement(
            p["relevant"], (f["shooting"], f["murder_entity_order"])
        ),
        "relevant_murder_craig": Statement(
            p["relevant"], (f["shooting_craig"], f["murder_craig"])
        ),
        "relevant_murder_alice_craig": Statement(
            p["relevant"], (f["shooting"], f["murder_craig"])
        ),
        "relevant_plotted_murder": Statement(
            p["relevant"], (f["plotted"], f["murder"])
        ),
        "relevant_plotted_reversed_murder": Statement(
            p["relevant"], (f["plotted_reversed"], f["murder"])
        ),
    }


@pytest.fixture(scope="class")
def make_assertion(make_complex_fact, make_statement) -> Dict[str, Assertion]:
    return {
        "generic_authority": Assertion(
            statement=make_complex_fact["relevant_plotted_murder"],
            authority=Entity("a lawyer"),
        ),
        "generic_authority_reversed": Assertion(
            statement=make_complex_fact["relevant_plotted_reversed_murder"],
            authority=Entity("a lawyer"),
        ),
        "specific_authority": Assertion(
            statement=make_complex_fact["relevant_plotted_murder"],
            authority=Entity("Clarence Darrow", generic=False),
        ),
        "specific_authority_reversed": Assertion(
            statement=make_complex_fact["relevant_plotted_reversed_murder"],
            authority=Entity("Clarence Darrow", generic=False),
        ),
        "no_authority": Assertion(
            statement=make_complex_fact["relevant_plotted_murder"]
        ),
        "no_authority_reversed": Assertion(
            statement=make_complex_fact["relevant_plotted_reversed_murder"]
        ),
        "plotted_per_alice": Assertion(
            statement=make_statement["plotted"], authority=Entity("Alice")
        ),
        "plotted_per_bob": Assertion(
            statement=make_statement["plotted"], authority=Entity("Bob")
        ),
        "plotted_per_craig": Assertion(
            statement=make_statement["plotted"], authority=Entity("Craig")
        ),
    }


@pytest.fixture(scope="function")
def make_context_register() -> ContextRegister:
    context_names = ContextRegister()
    context_names.insert_pair(key=Entity("Alice"), value=Entity("Craig"))
    context_names.insert_pair(key=Entity("Bob"), value=Entity("Dan"))
    return context_names
