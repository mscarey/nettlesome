from typing import Dict

from pint import UnitRegistry
import pytest

from nettlesome.comparable import ContextRegister
from nettlesome.doctrines import Doctrine
from nettlesome.predicates import Predicate
from nettlesome.quantities import Comparison
from nettlesome.statements import Statement
from nettlesome.entities import Entity

ureg = UnitRegistry()
Q_ = ureg.Quantity


@pytest.fixture(scope="class")
def make_predicate() -> Dict[str, Predicate]:

    return {
        "make_predicate": Predicate("$person committed a crime"),
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
        "plotted": Predicate("$plotter1 plotted with $plotter2"),
        "crime": Predicate("$person1 committed a crime"),
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
def make_comparison() -> Dict[str, Predicate]:
    return {
        "acres": Comparison(
            "the distance between $place1 and $place2 was",
            sign=">=",
            expression=Q_("10 acres"),
        ),
        "exact": Comparison(
            "the distance between $place1 and $place2 was",
            sign="==",
            expression=Q_("25 feet"),
        ),
        "float_distance": Comparison(
            "the distance between $place1 and $place2 was",
            truth=True,
            sign="<",
            expression=20.0,
        ),
        "higher_int": Comparison(
            "the distance between $place1 and $place2 was",
            sign="<=",
            expression=30,
        ),
        "int_distance": Comparison(
            "the distance between $place1 and $place2 was",
            truth=True,
            sign="<",
            expression=20,
        ),
        "int_higher": Comparison(
            "the distance between $place1 and $place2 was",
            sign="<=",
            expression=30,
        ),
        "less": Comparison(
            "the distance between $place1 and $place2 was",
            truth=True,
            sign="<",
            expression=Q_("35 feet"),
        ),
        "less_whether": Comparison(
            "the distance between $place1 and $place2 was",
            truth=None,
            sign="<",
            expression=Q_("35 feet"),
        ),
        "less_than_20": Comparison(
            "the distance between $place1 and $place2 was",
            truth=True,
            sign="<",
            expression=Q_("20 feet"),
        ),
        "meters": Comparison(
            "the distance between $place1 and $place2 was",
            sign=">=",
            expression=Q_("10 meters"),
        ),
        "not_equal": Comparison(
            "the distance between $place1 and $place2 was",
            truth=True,
            sign="!=",
            expression=Q_("35 feet"),
        ),
        "more": Comparison(
            "the distance between $place1 and $place2 was",
            truth=True,
            sign=">=",
            expression=Q_("35 feet"),
        ),
        "not_more": Comparison(
            "the distance between $place1 and $place2 was",
            truth=False,
            sign=">",
            expression=Q_("35 feet"),
        ),
        "way_more": Comparison(
            "the distance between $place1 and $place2 was",
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
        "repeating_entity": Statement(
            p["three_entities"], [Entity("Alice"), Entity("Bob"), Entity("Alice")]
        ),
        "large_weight": Statement(
            p["large_weight"],
            Entity("Alice"),
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
def make_doctrine(make_complex_fact, make_statement) -> Dict[str, Doctrine]:
    return {
        "generic_authority": Doctrine(
            statement=make_complex_fact["relevant_plotted_murder"],
            authority=Entity("a lawyer"),
        ),
        "generic_authority_reversed": Doctrine(
            statement=make_complex_fact["relevant_plotted_reversed_murder"],
            authority=Entity("a lawyer"),
        ),
        "specific_authority": Doctrine(
            statement=make_complex_fact["relevant_plotted_murder"],
            authority=Entity("Clarence Darrow", generic=False),
        ),
        "specific_authority_reversed": Doctrine(
            statement=make_complex_fact["relevant_plotted_reversed_murder"],
            authority=Entity("Clarence Darrow", generic=False),
        ),
        "no_authority": Doctrine(
            statement=make_complex_fact["relevant_plotted_murder"]
        ),
        "no_authority_reversed": Doctrine(
            statement=make_complex_fact["relevant_plotted_reversed_murder"]
        ),
        "plotted_per_alice": Doctrine(
            statement=make_statement["plotted"], authority=Entity("Alice")
        ),
        "plotted_per_bob": Doctrine(
            statement=make_statement["plotted"], authority=Entity("Bob")
        ),
        "plotted_per_craig": Doctrine(
            statement=make_statement["plotted"], authority=Entity("Craig")
        ),
    }


@pytest.fixture(scope="function")
def make_context_register() -> ContextRegister:
    context_names = ContextRegister()
    context_names.insert_pair(key=Entity("Alice"), value=Entity("Craig"))
    context_names.insert_pair(key=Entity("Bob"), value=Entity("Dan"))
    return context_names
