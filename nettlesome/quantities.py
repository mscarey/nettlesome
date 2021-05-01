"""Descriptions of quantities."""

from __future__ import annotations

from abc import ABC, abstractproperty
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
    """
    Scale up one interval by multiplying by a scalar.

    Used for converting the units of a UnitRange.
    """
    return Interval(
        start=interval.start * scalar,
        end=interval.end * scalar,
        left_open=interval.left_open,
        right_open=interval.right_open,
    )


def scale_union_of_intervals(
    ranges: sympy.Union, scalar: Union[int, float]
) -> sympy.Union:
    """
    Scale up union of several intervals by multiplying by a scalar.

    Used for converting the units of a UnitRange.
    """
    scaled_intervals = [
        scale_interval(interval=interval, scalar=scalar) for interval in ranges.args
    ]
    return sympy.Union(*scaled_intervals)


def scale_finiteset(elements: FiniteSet, scalar: Union[int, float]) -> FiniteSet:
    """
    Scale up set of finite numbers by multiplying by a scalar.

    Used for converting the units of a UnitRange.
    """
    scaled_intervals = [element * scalar for element in elements.args]
    return FiniteSet(*scaled_intervals)


def scale_ranges(
    ranges: Union[Interval, sympy.Union], scalar: Union[int, float]
) -> Union[Interval, FiniteSet, sympy.Union]:
    """
    Scale up set of interval ranges by multiplying by a scalar.

    Used for converting the units of a UnitRange.
    """
    if isinstance(ranges, Interval):
        return scale_interval(interval=ranges, scalar=scalar)
    if isinstance(ranges, FiniteSet):
        return scale_finiteset(elements=ranges, scalar=scalar)
    return scale_union_of_intervals(ranges=ranges, scalar=scalar)


class QuantityRange(ABC):
    """Base class for ranges that can be assigned to Predicates."""

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

    def __init__(self, sign: str, include_negatives: Optional[bool] = None) -> None:
        """Normalize operator sign and exclude negatives, if needed."""
        if sign in self.normalized_comparisons:
            sign = self.normalized_comparisons[sign]
        if sign not in self.opposite_comparisons.keys():
            raise ValueError(
                f'"sign" string parameter must be one of {self.opposite_comparisons.keys()}.'
            )

        self.sign = sign
        if include_negatives is None:
            include_negatives = bool(self.magnitude < 0)
        self.include_negatives = include_negatives

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(quantity="{self._quantity_string()}", '
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
        return f"{expand[self.sign]} {self._quantity_string()}"

    @property
    def interval(self) -> Union[FiniteSet, Interval, sympy.Union]:
        """Get the range that the Comparison may refer to."""
        if self.sign == "==":
            return FiniteSet(self.magnitude)
        elif ">" in self.sign:
            return Interval(self.magnitude, oo, left_open=bool("=" not in self.sign))
        elif "<" in self.sign:
            return Interval(
                self.lower_bound,
                self.magnitude,
                right_open=bool("=" not in self.sign),
            )
        # self.sign == "!="
        return sympy.Union(
            Interval(self.lower_bound, self.magnitude, right_open=True),
            Interval(self.magnitude, oo, left_open=True),
        )

    @property
    def lower_bound(self):
        """Get lower bound of the range that the Comparison may refer to."""
        return -oo if self.include_negatives else 0

    @abstractproperty
    def magnitude(self) -> Union[int, float]:
        """Get amount of max or minimum of the quantity range, without a unit."""
        pass

    def consistent_dimensionality(self, other: QuantityRange) -> bool:
        """Test if ``other`` has a quantity parameter consistent with ``self``."""
        return isinstance(other, self.__class__)

    def contradicts(self, other: Any) -> bool:
        """Check if self's interval excludes all of other's interval."""
        if not isinstance(other, self.__class__):
            return False
        return self._excludes_quantity_interval(other.interval)

    def implies(self, other: Any) -> bool:
        """Check if self's interval includes all of other's interval."""
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
        """Compare for same meaning."""
        if not isinstance(other, self.__class__):
            return False
        return Eq(self.interval, other.interval)

    def reverse_meaning(self) -> None:
        """
        Change self.sign in place to reverse the range of numbers covered.

            >>> quantity_range = UnitRange(quantity="100 meters", sign=">")
            >>> str(quantity_range)
            'greater than 100 meter'
            >>> quantity_range.reverse_meaning()
            >>> quantity_range.sign
            '<='
            >>> str(quantity_range)
            'no more than 100 meter'
        """
        self.sign = self.opposite_comparisons[self.sign]

    def _quantity_string(self) -> str:
        return ""


class UnitRange(QuantityRange):
    """A range defined relative to a pint Quantity."""

    def __init__(
        self,
        quantity: Union[Quantity, str],
        sign: str = "",
        include_negatives: Optional[bool] = None,
    ) -> None:
        """Set domain as a real number of units."""
        if isinstance(quantity, str):
            quantity = Q_(quantity)
        self.quantity = quantity
        self.domain = S.Reals
        super().__init__(sign=sign, include_negatives=include_negatives)

    @property
    def magnitude(self) -> Union[int, float]:
        """Get magnitude of pint Quantity."""
        super().magnitude  # for the coverage
        return self.quantity.magnitude

    def consistent_dimensionality(self, other: QuantityRange) -> bool:
        """
        Compare dimensionality of Quantities for ``self`` and ``other``.

        For instance, two units representing distance divided by time have
        the same dimensionality, even if one uses feet while the other uses
        meters.

        :param other:
            another QuantityRange with a quantity to compare

        :returns:
            whether the two dimensionalities are the same
        """
        if not isinstance(other, self.__class__):
            return False
        return self.quantity.dimensionality == other.quantity.dimensionality

    def contradicts(self, other: Any) -> bool:
        """Check if ``self``'s quantity range has no overlap with ``other``'s."""
        if not self.consistent_dimensionality(other):
            return False
        other_interval = self.get_unit_converted_interval(other)
        return self._excludes_quantity_interval(other_interval)

    def implies(self, other: Any) -> bool:
        """
        Check if ``self``'s quantity range is a subset of ``other``'s.

        :param other:
            another QuantityRange to compare

        :returns:
            whether ``other`` provides no information about the quantity
            that isn't already provided by ``self``
        """
        if not self.consistent_dimensionality(other):
            return False
        other_interval = self.get_unit_converted_interval(other)
        return self._implies_quantity_interval(other_interval)

    def get_unit_converted_interval(
        self, other: UnitRange
    ) -> Union[Interval, FiniteSet, sympy.Union]:
        """Get ``other``'s interval if it was denominated in ``self``'s units."""
        if not isinstance(other, UnitRange):
            raise TypeError(
                f"Unit coversions only available for type UnitRange, not {other.__class__}."
            )
        if other.quantity.units == self.quantity.units:
            return other.interval
        ratio_of_units = other.quantity.units / self.quantity.units
        return scale_ranges(other.interval, ratio_of_units)

    def means(self, other: Any) -> bool:
        """Whether ``self`` and ``other`` represent the same quantity range."""
        if not self.consistent_dimensionality(other):
            return False
        other_interval = self.get_unit_converted_interval(other)
        if not self.interval.is_subset(other_interval):
            return False
        return other_interval.is_subset(self.interval)

    def _quantity_string(self) -> str:
        return super()._quantity_string() + str(self.quantity)


class DateRange(QuantityRange):
    """A range defined relative to a date."""

    def __init__(
        self,
        quantity: date,
        sign: str = "",
        include_negatives: Optional[bool] = None,
    ) -> None:
        """Set domain as natural numbers."""
        self.quantity = quantity
        self.domain = S.Naturals
        super().__init__(sign=sign, include_negatives=include_negatives)

    @property
    def magnitude(self) -> Union[int, float]:
        """Map dates to integers while preserving the order of the dates."""
        return int(self.quantity.strftime("%Y%m%d"))

    def _quantity_string(self) -> str:
        return str(self.quantity)


class NumberRange(QuantityRange):
    """A range defined relative to an integer or float."""

    def __init__(
        self,
        quantity: Union[int, float],
        sign: str = "",
        include_negatives: Optional[bool] = None,
    ) -> None:
        """Check number type and set domain for number range."""
        if not isinstance(quantity, (int, float)):
            raise TypeError(
                f'"quantity" must be a number (integer or float), '
                f'not "{quantity}", which is type {type(quantity)}.'
            )
        self.quantity = quantity
        self.domain = S.Naturals0 if isinstance(self.quantity, int) else S.Reals
        super().__init__(sign=sign, include_negatives=include_negatives)

    @property
    def magnitude(self) -> Union[int, float]:
        """Return quantity attribute."""
        return self.quantity

    def _quantity_string(self) -> str:
        return str(self.quantity)


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
    Nettlesome will silently modify your statement so it can have
    truth=True with a different sign. In this example, the user’s input
    indicates that it’s false that the weight of marijuana possessed by a defendant
    was more than 10 grams. Nettlesome interprets this to mean it’s
    true that the weight was no more than 10 grams.

        >>> # example comparing a pint Quantity
        >>> drug_comparison_with_upper_bound = Comparison(
        ...     "the weight of marijuana that $defendant possessed was",
        ...     sign=">",
        ...     expression="10 grams",
        ...     truth=False)
        >>> str(drug_comparison_with_upper_bound)
        'that the weight of marijuana that $defendant possessed was no more than 10 gram'

    When the number needed for a Comparison isn’t a physical quantity that can be described
    with the units in the pint library library, you should phrase the text in the template
    string to explain what the number describes. The template string will still need to
    end with the word “was”. The value of the expression parameter should be an integer
    or a floating point number, not a string to be parsed.

        >>> # example comparing an integer
        >>> three_children = Comparison(
        ...     "the number of children in ${taxpayer}'s household was",
        ...     sign="=",
        ...     expression=3)
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
        content: str,
        sign: str = "",
        expression: Union[date, int, float, Quantity] = 0,
        truth: Optional[bool] = True,
        include_negatives: Optional[bool] = None,
        quantity_range: Optional[Union[DateRange, NumberRange, UnitRange]] = None,
    ):
        """
        Clean up and test validity of attributes.

        If the :attr:`content` sentence is phrased to have a plural
        context term, normalizes it by changing "were" to "was".
        """
        super().__init__(content, truth=truth)

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
                self.quantity_range.reverse_meaning()

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
    def interval(self) -> Union[FiniteSet, Interval, sympy.Union]:
        """
        Get the range of numbers covered by the UnitInterval.

        >>> weight=Comparison(
        ...     "the amount of gold $person possessed was",
        ...     sign=">=",
        ...     expression="10 grams")
        >>> weight.interval
        Interval(10, oo)

        """
        return self.quantity_range.interval

    @property
    def quantity(self) -> Union[int, float, Quantity, date]:
        """
        Get the maximum or minimum of the range.

        :returns:
            the number, pint Quantity, or date at the beginning or end of
            the range

            >>> weight=Comparison(
            ...     "the amount of gold $person possessed was",
            ...     sign=">=",
            ...     expression="10 grams")
            >>> weight.quantity
            <Quantity(10, 'gram')>
        """
        return self.quantity_range.quantity

    @property
    def sign(self) -> str:
        """
        Get operator describing the relationship between the quantity and the range.

            >>> weight=Comparison(
            ...     "the amount of gold $person possessed was",
            ...     sign=">=",
            ...     expression="10 grams")
            >>> str(weight.quantity_range)
            'at least 10 gram'
            >>> weight.sign
            '>='
        """
        return self.quantity_range.sign

    def _add_truth_to_content(self, content: str) -> str:
        """Get self's content with a prefix indicating the truth value."""
        content = super()._add_truth_to_content(content)
        return f"{content} {str(self.quantity_range)}"

    def implies(self, other: Any) -> bool:
        r"""
        Check if ``self`` implies ``other``.

        May be based on template text, truth values, and :class:`.QuantityRange`\s.

        >>> small_weight=Comparison(
        ...     "the amount of gold $person possessed was",
        ...     sign=">=",
        ...     expression=Q_("1 gram"))
        >>> large_weight=Comparison(
        ...     "the amount of gold $person possessed was",
        ...     sign=">=",
        ...     expression=Q_("100 kilograms"))
        >>> str(large_weight)
        'that the amount of gold $person possessed was at least 100 kilogram'
        >>> str(small_weight)
        'that the amount of gold $person possessed was at least 1 gram'
        >>> large_weight.implies(small_weight)
        True
        """

        if not super().implies(other):
            return False

        return self.quantity_range.implies(other.quantity_range)

    def means(self, other: Any) -> bool:
        r"""
        Check if ``self`` and ``other`` have identical meanings.

        This method can convert different units to determine whether self and other
        refer to the same :class:`~.quantities.QuantityRange`\.

        >>> volume_in_liters = Comparison(
        ...     "the volume of fuel in the tank was",
        ...     sign="=", expression="10 liters")
        >>> volume_in_milliliters = Comparison(
        ...     "the volume of fuel in the tank was",
        ...     sign="=", expression="10000 milliliters")
        >>> volume_in_liters.means(volume_in_milliliters)
        True
        """
        if not super().means(other):
            return False

        return self.quantity_range.means(other.quantity_range)

    def contradicts(self, other: Any) -> bool:
        r"""
        Check if ``other`` and ``self`` have contradictory meanings.

        If ``self`` and ``other`` have consistent text in the predicate attribute,
        this method looks for a contradiction based on the dimensionality or
        numeric range of the :class:`~.QuantityRange`\s for ``self`` and ``other``.

            >>> earlier = Comparison(
            ...     "the date $dentist became a licensed dentist was",
            ...     sign="<", expression=date(1990, 1, 1))
            >>> later = Comparison(
            ...     "the date $dentist became a licensed dentist was",
            ...     sign=">", expression=date(2010, 1, 1))
            >>> str(earlier)
            'that the date $dentist became a licensed dentist was less than 1990-01-01'
            >>> str(later)
            'that the date $dentist became a licensed dentist was greater than 2010-01-01'
            >>> earlier.contradicts(later)
            True
            >>> later.contradicts(earlier)
            True

        """
        if not self._same_meaning_as_true_predicate(other):
            return False

        if not (self.truth is other.truth is True):
            return False

        return self.quantity_range.contradicts(other.quantity_range)

    def negated(self) -> Comparison:
        """Copy ``self``, with the opposite truth value."""
        return Comparison(
            content=self.content,
            truth=not self.truth,
            sign=self.quantity_range.sign,
            expression=self.quantity_range.quantity,
        )
