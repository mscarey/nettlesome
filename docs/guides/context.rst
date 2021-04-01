.. _Comparisons with Context:

Comparisons with Context
========================

In **Nettlesome**, logical comparisons
between :class:`~nettlesome.statements.Statement`\s and other
:class:`~nettlesome.factors.Factor`\s can depend on whether
the :class:`~nettlesome.terms.Term`\s of the
:class:`~nettlesome.statements.Statement`\s are considered
analagous to one another. In the example below, the two phrases can be
considered to have the same meaning because the Terms of each Statement
can be “matched” to one another.

    >>> from nettlesome import Statement, Entity
    >>> hades_curse = Statement("$deity cursed $target",
    ...     terms=[Entity("Hades"), Entity("Persephone")])
    >>> aphrodite_curse = Statement("$deity cursed $target",
    ...     terms=[Entity("Aphrodite"), Entity("Narcissus")])
    >>> print(aphrodite_curse)
    the statement that <Aphrodite> cursed <Narcissus>

The :meth:`~nettlesome.terms.Comparable.means` method is used to determine
whether two :class:`~nettlesome.statements.Statement`\s have the same meaning.

    >>> hades_curse.means(aphrodite_curse)
    True

The :meth:`~nettlesome.terms.Comparable.explain_same_meaning` method
generates an :class:`~nettlesome.terms.Explanation`
explaining why the two Statements can be considered to have the
same meaning.

    >>> print(hades_curse.explain_same_meaning(aphrodite_curse))
    Because <Hades> is like <Aphrodite>, and <Persephone> is like <Narcissus>,
      the statement that <Hades> cursed <Persephone>
    MEANS
      the statement that <Aphrodite> cursed <Narcissus>


Formatting Contexts for Comparison Methods
------------------------------------------

But what if the two :class:`~nettlesome.statements.Statement`\s need to be
compared in a context where it
has been established that Hades is more comparable to Narcissus, not to
Aphrodite? That changes the meaning of the second Statement and
indicates that the two Statements don’t have the same meaning. To add
that context information in Nettlesome, use the ``context``
parameter of the :meth:`~nettlesome.terms.Comparable.means` method.
One input format for the ``context``
parameter is a :py:class:`tuple` of two :py:class:`list`\s, with the first List containing Terms
from the Statement on the left, and the second List containing the
corresponding :class:`~nettlesome.terms.Term`\s from the
Statement on the right. (This means that
the two lists will need to be the same length.) In this example, there’s
a one-item List containing Hades, matched to a one-item List containing
Narcissus. The value returned by
the :meth:`~nettlesome.terms.Comparable.means` method is now ``False``
instead of ``True``.

    >>> hades_curse.means(aphrodite_curse, context=([Entity("Hades")], [Entity("Narcissus")]))
    False

Maybe it seems more natural to use a Python :py:class:`dict`\, instead
of a :py:class:`tuple` of
two Lists, to match pairs of corresponding Terms.
(A Python :py:class:`dict` is a mapping of keys to values.)
A :py:class:`dict` can be used for the ``context``
parameter, but there’s a complication: a :class:`nettlesome.entities.Entity` is not a
valid :py:class:`dict` key in Python. Here’s the error message you'll see
if you try to use an :class:`~nettlesome.entities.Entity` directly
as a :py:class:`dict` key,
and then try to retrieve the value stored under that key.

    >>> myths = {Entity("Hades"): Entity("Narcissus")}
    >>> myths[Entity("Hades")]

::

    ---------------------------------------------------------------------------

    KeyError                                  Traceback (most recent call last)

    <ipython-input-5-75ea1b988416> in <module>
          1 myths = {Entity("Hades"): Entity("Narcissus")}
    ----> 2 myths[Entity("Hades")]


    KeyError: Entity(name="Hades", generic=True, plural=False)


So instead of passing in the :class:`~nettlesome.entities.Entity` itself
as a :py:class:`dict` key, we’ll pass in the :meth:`~nettlesome.terms.Comparable.key`
property of the Entity.

    >>> hades_curse.means(
    ...     aphrodite_curse,
    ...     context=({Entity("Hades").key: Entity("Narcissus")}))
    False

Finally, we might want to skip identifying any Terms from the left
:class:`~nettlesome.statements.Statement`\, and instead provide
one :py:class:`list` with matching :class:`~nettlesome.terms.Term`\s for all of
the left :class:`~nettlesome.statements.Statement`\'s
:meth:`~nettlesome.terms.Comparable.generic_terms`\. To understand this, let’s see
what the Statement’s :meth:`~nettlesome.terms.Comparable.generic_terms` are. As
mentioned in the :ref:`Generic Terms` section of the :ref:`Introduction to Nettlesome`
tutorial, generic Terms are Terms used as an
example or stand-in for a broader category, so that a different generic
Term can be substituted without changing the meaning of the Statement.

    >>> hades_curse.generic_terms()
    [Entity(name="Hades", generic=True, plural=False),
     Entity(name="Persephone", generic=True, plural=False)]

This time, we’ll provide the correct Entities that match to the Entities
of ``hades_curse``, so the :meth:`~nettlesome.terms.Comparable.means` method
will return ``True``.

    >>> hades_curse.means(
    ...     aphrodite_curse,
    ...     context=([Entity("Aphrodite"), Entity("Narcissus")]))
    True

Comparing FactorGroups in Context
---------------------------------

Like :class:`~nettlesome.statements.Statement`\s, :class:`~nettlesome.groups.FactorGroup`\s
can be compared to one another using the
:meth:`~nettlesome.terms.Comparable.implies`, :meth:`~nettlesome.terms.Comparable.means`\,
:meth:`~nettlesome.groups.FactorGroup.contradicts`\, and
:meth:`~nettlesome.groups.FactorGroup.consistent_with` methods. In
this example, the ``nafta`` :class:`~nettlesome.groups.FactorGroup` describes
three countries all making bilateral agreements with one another.
The ``brexit`` :class:`~nettlesome.groups.FactorGroup`
describes one country making treaties with two other countries that do
not make a treaty with each other. These two FactorGroups are considered
to “contradict” one another, because if the Statements in ``brexit``
were asserted about the parties in ``nafta``, there would be a conflict
about whether one pair of Entities signed a treaty with each other.

    >>> from nettlesome import FactorGroup
    >>> nafta = FactorGroup([
    ...     Statement("$country1 signed a treaty with $country2",
    ...               terms=[Entity("Mexico"), Entity("USA")]),
    ...     Statement("$country2 signed a treaty with $country3",
    ...               terms=[Entity("USA"), Entity("Canada")]),
    ...     Statement("$country3 signed a treaty with $country1",
    ...           terms=[Entity("USA"), Entity("Canada")])])
    >>> brexit = FactorGroup([
    ...     Statement("$country1 signed a treaty with $country2",
    ...               terms=[Entity("UK"), Entity("European Union")]),
    ...     Statement("$country2 signed a treaty with $country3",
    ...               terms=[Entity("European Union"), Entity("Germany")]),
    ...     Statement("$country3 signed a treaty with $country1",
    ...          terms=[Entity("Germany"), Entity("UK")], truth=False)])
    >>> nafta.contradicts(brexit)
    True

The :meth:`~nettlesome.terms.Comparable.explain_contradiction` method
will generate one :class:`~nettlesome.terms.Explanation` of how
an analogy between the generic terms of the
two :class:`~nettlesome.groups.FactorGroup`\s can make them contradictory.

    >>> print(nafta.explain_contradiction(brexit))
    Because <Mexico> is like <Germany>, and <USA> is like <UK>,
      the statement that <Mexico> signed a treaty with <USA>
    CONTRADICTS
      the statement it was false that <Germany> signed a treaty with <UK>

The :meth:`~nettlesome.groups.FactorGroup.explanations_contradiction` method
(with the plural “explanations” instead of “explain”) returns a generator
that will yield all available :class:`~nettlesome.terms.Explanation`\s of
how to cause a contradiction. In this case it generates four Explanations.

    >>> all_explanations = list(nafta.explanations_contradiction(brexit))
    >>> len(all_explanations)
    4

By adding a context parameter to the method that compares the
:class:`~nettlesome.groups.FactorGroup`\s for contradiction, we can narrow
down how nettlesome discovers analogies between
the :class:`~nettlesome.entities.Entity` objects. The result is that
nettlesome finds only two Explanations of how a contradiction can exist.

    >>> explanations_usa_like_uk = list(nafta.explanations_contradiction(brexit, context=([Entity("USA")], [Entity("UK")])))
    >>> len(explanations_usa_like_uk)
    2

Here are the two :class:`~nettlesome.terms.Explanation`\s for how a contradiction
can exist if the :class:`~nettlesome.entities.Entity` “USA” in ``left`` is considered
analagous to the Entity “UK” in ``right``.

    >>> print(explanations_usa_like_uk[0])
    Because <USA> is like <UK>, and <Mexico> is like <Germany>,
      the statement that <Mexico> signed a treaty with <USA>
    CONTRADICTS
      the statement it was false that <Germany> signed a treaty with <UK>
    >>> print(explanations_usa_like_uk[1])
    Because <USA> is like <UK>, and <Canada> is like <Germany>,
      the statement that <USA> signed a treaty with <Canada>
    CONTRADICTS
      the statement it was false that <Germany> signed a treaty with <UK>
