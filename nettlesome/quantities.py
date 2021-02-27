from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, ClassVar, Dict, Optional, Union

from pint import UnitRegistry, Quantity
import sympy
from sympy import Eq, Interval, oo, S
from sympy.sets import EmptySet, FiniteSet

from nettlesome.predicates import Predicate


ureg = UnitRegistry()
Q_ = ureg.Quantity


def scale_interval(interval: Interval, scalar: Union[int, float]) -> Interval:
    result = Interval(
        start=interval.start * scalar,
        end=interval.end * scalar,
        left_open=interval.left_open,
        right_open=interval.right_open,
    )
    return result


def scale_union_of_intervals(
    ranges: sympy.Union, scalar: Union[int, float]
) -> sympy.Union:
    scaled_intervals = [
        scale_interval(interval=interval, scalar=scalar) for interval in ranges.args
    ]
    result = sympy.Union(*scaled_intervals)
    return result


def scale_finiteset(elements: FiniteSet, scalar: Union[int, float]) -> FiniteSet:
    scaled_intervals = [element * scalar for element in elements.args]
    result = FiniteSet(*scaled_intervals)
    return result


def scale_ranges(
    ranges: Union[Interval, sympy.Union], scalar: Union[int, float]
) -> Union[Interval, FiniteSet, sympy.Union]:
    if isinstance(ranges, Interval):
        return scale_interval(interval=ranges, scalar=scalar)
    if isinstance(ranges, FiniteSet):
        return scale_finiteset(elements=ranges, scalar=scalar)
    return scale_union_of_intervals(ranges=ranges, scalar=scalar)


class QuantityRange(ABC):

    opposite_comparisons: ClassVar[Dict[str, str]] = {
        ">=": "<",
        "==": "!=",
        "!=": "=",
        "<=": ">",
        "==": "!=",
        "<>": "=",
        ">": "<=",
        "<": ">=",
    }
    normalized_comparisons: ClassVar[Dict[str, str]] = {"=": "==", "<>": "!="}

    def __init__(
        self, sign: str = "", include_negatives: Optional[bool] = None
    ) -> None:
        if sign in self.normalized_comparisons:
            sign = self.normalized_comparisons[sign]
        if sign not in self.opposite_comparisons.keys():
            raise ValueError(
                f'"sign" string parameter must be one of {self.opposite_comparisons.keys()}.'
            )

        self.sign = sign
        if include_negatives is None:
            include_negatives = bool(self.magnitude() < 0)
        self.include_negatives = include_negatives

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(quantity="{self.quantity}", '
            f'sign="{self.sign}", include_negatives={self.include_negatives})'
        )

    def __str__(self) -> str:
        return self.expression_comparison()

    def expression_comparison(self) -> str:
        """
        Convert text to a comparison with a quantity.

        :returns:
            string representation of a comparison with a
            quantity, which can include units due to the
            `pint <pint.readthedocs.io>`_  library.
        """

        expand = {
            "==": "exactly equal to",
            "=": "exactly equal to",
            "!=": "not equal to",
            "<>": "not equal to",
            ">": "greater than",
            "<": "less than",
            ">=": "at least",
            "<=": "no more than",
        }
        return f"{expand[self.sign]} {self.quantity}"

    @property
    def interval(self) -> Union[FiniteSet, Interval, sympy.Union]:
        if self.sign == "==":
            return FiniteSet(self.magnitude())
        elif ">" in self.sign:
            return Interval(self.magnitude(), oo, left_open=bool("=" not in self.sign))
        elif "<" in self.sign:
            return Interval(
                self.lower_bound,
                self.magnitude(),
                right_open=bool("=" not in self.sign),
            )
        # self.sign == "!="
        return sympy.Union(
            Interval(self.lower_bound, self.magnitude(), right_open=True),
            Interval(self.magnitude(), oo, left_open=True),
        )

    @property
    def lower_bound(self):
        """The lower bound of the range that the Comparison may refer to."""
        return -oo if self.include_negatives else 0

    @abstractmethod
    def magnitude(self) -> Union[int, float]:
        pass

    def consistent_dimensionality(self, other: QuantityRange) -> bool:
        """Test if ``other`` has a quantity parameter consistent with ``self``."""
        return isinstance(other, self.__class__)

    def contradicts(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._excludes_quantity_interval(other.interval)

    def implies(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._implies_quantity_interval(other.interval)

    def _excludes_quantity_interval(
        self, other_interval: Union[sympy.Union, Interval, FiniteSet]
    ) -> bool:
        """Test if quantity ranges in self and other are non-overlapping."""
        combined_interval = self.interval.intersect(other_interval)
        return combined_interval == EmptySet

    def _implies_quantity_interval(
        self, other_interval: Union[sympy.Union, Interval, FiniteSet]
    ) -> bool:
        """Test if the range of quantities mentioned in self is a subset of other's."""

        combined_interval = self.interval.intersect(other_interval)
        return self.interval.is_subset(combined_interval)

    def means(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return Eq(self.interval, other.interval)

    def opposite_meaning(self) -> None:
        self.sign = self.opposite_comparisons[self.sign]


class UnitRange(QuantityRange):
    def __init__(
        self,
        quantity: Quantity,
        sign: Optional[str] = None,
        include_negatives: Optional[bool] = None,
    ) -> None:
        self.quantity = quantity
        self.domain = S.Reals
        super().__init__(sign=sign, include_negatives=include_negatives)

    def magnitude(self) -> Union[int, float]:
        return self.quantity.magnitude

    def consistent_dimensionality(self, other: QuantityRange) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.quantity.dimensionality == other.quantity.dimensionality

    def contradicts(self, other: Any) -> bool:
        if not self.consistent_dimensionality(other):
            return False
        other_interval = self.get_unit_converted_interval(other)
        return self._excludes_quantity_interval(other_interval)

    def implies(self, other: Any) -> bool:
        if not self.consistent_dimensionality(other):
            return False
        other_interval = self.get_unit_converted_interval(other)
        return self._implies_quantity_interval(other_interval)

    def get_unit_converted_interval(
        self, other: UnitRange
    ) -> Union[Interval, FiniteSet, sympy.Union]:
        if not isinstance(other, UnitRange):
            raise TypeError(
                f"Unit coversions only available for type UnitRange, not {other.__class__}."
            )
        if other.quantity.units != self.quantity.units:
            ratio_of_units = other.quantity.units / self.quantity.units
            other_interval = scale_ranges(other.interval, ratio_of_units)
        else:
            other_interval = other.interval
        return other_interval

    def means(self, other: Any) -> bool:
        if not self.consistent_dimensionality(other):
            return False
        other_interval = self.get_unit_converted_interval(other)
        if not self.interval.is_subset(other_interval):
            return False
        return other_interval.is_subset(self.interval)


class DateRange(QuantityRange):
    def __init__(
        self,
        quantity: date,
        sign: Optional[str] = None,
        include_negatives: Optional[bool] = None,
    ) -> None:
        self.quantity = quantity
        self.domain = S.Naturals
        super().__init__(sign=sign, include_negatives=include_negatives)

    def magnitude(self) -> Union[int, float]:
        return int(self.quantity.strftime("%Y%m%d"))


class NumberRange(QuantityRange):
    def __init__(
        self,
        quantity: Union[int, float],
        sign: Optional[str] = None,
        include_negatives: Optional[bool] = None,
    ) -> None:
        if not isinstance(quantity, (int, float)):
            raise TypeError(
                f'"quantity" must be a number (integer or float), '
                f'not "{quantity}", which is type {type(quantity)}.'
            )
        self.quantity = quantity
        if isinstance(self.quantity, int):
            self.domain = S.Naturals0
        else:
            self.domain = S.Reals
        super().__init__(sign=sign, include_negatives=include_negatives)

    def magnitude(self) -> Union[int, float]:
        return self.quantity


class Comparison(Predicate):
    r"""
    A Predicate that compares a described quantity to a constant.

    The Comparison class extends the concept of a Predicate.
    A Comparison still contains a truth value and a template string,
    but that template should be used to identify a quantity that will
    be compared to an expression using a sign such as an equal sign
    or a greater-than sign. This expression must be a constant: either
    an integer, a floating point number, or a physical quantity expressed
    in units that can be parsed using the pint library.

    To encourage consistent phrasing, the template string in every
    Comparison object must end with the word “was”.

    If you phrase a Comparison with an inequality sign using truth=False,
    AuthoritySpoke will silently modify your statement so it can have
    truth=True with a different sign. In this example, the user’s input
    indicates that it’s false that the weight of marijuana possessed by a defendant
    was more than 10 grams. AuthoritySpoke interprets this to mean it’s
    true that the weight was no more than 10 grams.

        >>> # example comparing a pint Quantity
        >>> drug_comparison_with_upper_bound = Comparison(
        >>>     "the weight of marijuana that $defendant possessed was",
        >>>     sign=">",
        >>>     expression="10 grams",
        >>>     truth=False)
        >>> str(drug_comparison_with_upper_bound)
        'that the weight of marijuana that $defendant possessed was no more than 10 gram'

    When the number needed for a Comparison isn’t a physical quantity that can be described
    with the units in the pint library library, you should phrase the text in the template
    string to explain what the number describes. The template string will still need to
    end with the word “was”. The value of the expression parameter should be an integer
    or a floating point number, not a string to be parsed.

        >>> # example comparing an integer
        >>> three_children = Comparison(
        >>>     "the number of children in ${taxpayer}'s household was",
        >>>     sign="=",
        >>>     expression=3)
        >>> str(three_children)
        "that the number of children in ${taxpayer}'s household was exactly equal to 3"

    :param sign:
        A string representing an equality or inequality sign like ``==``,
        ``>``, or ``<=``. Used to indicate that the clause ends with a
        comparison to some quantity. Should be defined if and only if a
        ``quantity`` is defined. Even though "=" is the default, it's
        the least useful, because courts almost always state rules that
        are intended to apply to quantities above or below some threshold.

    :param quantity:
        a Python number object or :class:`ureg.Quantity` from the
        `pint library <https://pint.readthedocs.io/>`_. Comparisons to
        quantities can be used to determine whether :class:`Predicate`\s
        imply or contradict each other. A single :class:`Predicate`
        may contain no more than one ``sign`` and one ``quantity``.
    """

    def __init__(
        self,
        template: str,
        sign: Optional[str] = None,
        expression: Union[date, int, float, Quantity] = 0,
        truth: Optional[bool] = True,
        include_negatives: Optional[bool] = None,
        quantity_range: Union[DateRange, NumberRange, UnitRange, None] = None,
    ):
        """
        Clean up and test validity of attributes.

        If the :attr:`content` sentence is phrased to have a plural
        context term, normalizes it by changing "were" to "was".
        """
        super().__init__(template, truth=truth)

        if quantity_range:
            self.quantity_range = quantity_range
        else:
            quantity = self.read_quantity(expression)
            if isinstance(quantity, date):
                self.quantity_range = DateRange(
                    sign=sign,
                    quantity=quantity,
                    include_negatives=include_negatives,
                )
            elif isinstance(quantity, Quantity):
                self.quantity_range = UnitRange(
                    sign=sign,
                    quantity=quantity,
                    include_negatives=include_negatives,
                )
            else:
                self.quantity_range = NumberRange(
                    sign=sign,
                    quantity=quantity,
                    include_negatives=include_negatives,
                )

            if self.truth is False:
                self.truth = True
                self.quantity_range.opposite_meaning()

        if not self.content.endswith("was"):
            raise ValueError(
                "A Comparison's template string must end "
                "with the word 'was' to signal the comparison with the quantity. "
                f"The word 'was' is not the end of the string '{self.template.template}'."
            )

    def __repr__(self):
        result = super().__repr__()
        return result.rstrip(")") + f", quantity_range={repr(self.quantity_range)})"

    @classmethod
    def read_quantity(
        cls, value: Union[date, float, int, str]
    ) -> Union[date, float, int, Quantity]:
        r"""
        Create numeric expression from text for Comparison class.

        This expression can be a datetime.date, an int, a float, or a
        pint quantity. (See `pint
        tutorial <https://pint.readthedocs.io/en/16.1/tutorial.html>`_)

        :param quantity:
            an object to be interpreted as the ``expression`` field
            of a :class:`~authorityspoke.predicate.Comparison`
        :returns:
            a Python number object or a :class:`pint.Quantity`
            object created with :class:`pint.UnitRegistry`.
        """
        if isinstance(value, (int, float, Quantity, date)):
            return value
        quantity = value.strip()

        try:
            result = date.fromisoformat(value)
            return result
        except ValueError:
            pass

        if quantity.isdigit():
            return int(quantity)
        float_parts = quantity.split(".")
        if len(float_parts) == 2 and all(
            substring.isnumeric() for substring in float_parts
        ):
            return float(quantity)
        return Q_(quantity)

    @property
    def interval(self) -> [Interval, sympy.Union, EmptySet]:
        return self.quantity_range.interval

    @property
    def quantity(self) -> Union[int, float, Quantity, date]:
        return self.quantity_range.quantity

    @property
    def sign(self) -> str:
        return self.quantity_range.sign

    def add_truth_to_content(self, content: str) -> str:
        content = super().add_truth_to_content(content)
        return f"{content} {str(self.quantity_range)}"

    def implies(self, other: Any) -> bool:

        if not super().implies(other):
            return False

        return self.quantity_range.implies(other.quantity_range)

    def means(self, other: Any) -> bool:

        if not super().means(other):
            return False

        return self.quantity_range.means(other.quantity_range)

    def contradicts(self, other: Any) -> bool:
        """
        Test whether ``other`` and ``self`` have contradictory meanings.

        If the checks in the Predicate class find no contradiction, this
        method looks for a contradiction in the dimensionality detected by the
        ``pint`` library, or in the possible ranges for each Comparison's
        numeric ``expression``.
        """
        if not self._same_meaning_as_true_predicate(other):
            return False

        if not isinstance(other, self.__class__):
            return False

        if not (self.truth is other.truth is True):
            return False

        return self.quantity_range.contradicts(other.quantity_range)

    def negated(self) -> Comparison:
        """Copy ``self``, with the opposite truth value."""
        return Comparison(
            template=self.content,
            truth=not self.truth,
            sign=self.quantity_range.sign,
            expression=self.quantity_range.quantity,
        )
