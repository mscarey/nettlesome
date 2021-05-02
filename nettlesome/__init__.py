"""Nettlesome: Simplified semantic reasoning."""

from .assertions import Assertion
from .entities import Entity
from .groups import FactorGroup
from .predicates import Predicate
from .quantities import Comparison, DateRange, NumberRange, UnitRange
from .spec import make_spec
from .statements import Statement

__version__ = "0.4.0"
