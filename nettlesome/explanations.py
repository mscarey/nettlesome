"""Objects describing relationships between pairs of Comparables or Opinions."""
from __future__ import annotations

import operator
import textwrap
from typing import Callable, ClassVar, Dict, List, Optional, Tuple

from nettlesome.terms import (
    Comparable,
    ContextRegister,
    means,
    consistent_with,
    contradicts,
)


class Explanation:

    operation_names: ClassVar[Dict[Callable, str]] = {
        operator.ge: "IMPLIES",
        means: "MEANS",
        contradicts: "CONTRADICTS",
        consistent_with: "IS CONSISTENT WITH",
    }

    def __init__(
        self,
        factor_matches: List[Tuple[Comparable, Comparable]],
        context: Optional[ContextRegister] = None,
        operation: Callable = operator.ge,
    ):
        self.factor_matches = factor_matches
        self.context = context or ContextRegister()
        self.operation = operation

    def __str__(self):
        indent = "  "
        relation = self.operation_names[self.operation]
        context_text = f" Because {self.context.reason},\n" if self.context else "\n"
        text = f"EXPLANATION:{context_text}"
        for match in self.factor_matches:
            left = textwrap.indent(str(match[0]), prefix=indent)
            right = textwrap.indent(str(match[1]), prefix=indent)
            match_text = f"{left}\n" f"{relation}\n" f"{right}\n"
            text += match_text
        return text.rstrip("\n")

    def __repr__(self) -> str:
        return f"Explanation(matches={repr(self.factor_matches)}, context={repr(self.context)}), operation={repr(self.operation)})"

    def add_match(self, match=Tuple[Comparable, Comparable]) -> Explanation:
        """Add a pair of compared objects that has been found to satisfy operation, given context."""
        new_matches = self.factor_matches + [match]
        return Explanation(
            factor_matches=new_matches,
            context=self.context,
            operation=self.operation,
        )
