Introduction to Nettlesome
==========================

Nettlesome is a Python library that lets you use readable English
phrases as semantic tags for your data. Once you’ve created tags,
Nettlesome can automate the process of comparing the tags to determine
whether they have the *same meaning*, whether one tag *implies* another,
whether one tag *contradicts* another, or whether one tag is *consistent
with* another.

This tutorial will show you how to use some of Nettlesome’s basic
classes: :class:`~nettlesome.predicates.Predicate`,
:class:`~nettlesome.statements.Statement`, and :class:`~nettlesome.quantities.Comparison`.

"Predicates" as descriptors
------------------------------

A :class:`~nettlesome.predicates.Predicate` should contain an
English-language phrase in the past tense. The use of the past
tense reflects Nettlesome’s original use case of legal
analysis, which is usually backward-looking, determining the legal
effect of past acts or past conditions.

To create a useful :class:`~nettlesome.predicates.Predicate`\, you might
remember from grade school that
in a simple sentence the “subject” and any “objects” are typically
nouns, while the “predicate” is a verb phrase that describes an action
or relationship of those nouns. In Nettlesome you can consider marking the
subject and object nouns as "terms" that should be represented by placeholders
in the :class:`~nettlesome.predicates.Predicate`\'s template string. Generally,
concepts that are part of your data model are good choices to designate
as "terms", while other nouns that aren’t relevant enough to be part
of your data model don’t need to be terms.

For instance, this example might be a good :class:`~nettlesome.predicates.Predicate`
for a data model about determining whether an individual is an owner or
employee of a company:

    >>> from nettlesome import Predicate
    >>> account_for_company = Predicate("$applicant opened a bank account for $company")

Because ``$applicant`` and ``$company`` are marked as placeholders for
:class:`~nettlesome.terms.Term`\s, you’ll be able to add more data about
those entities later. But
notice that the words “bank account” haven't been replaced by a placeholder.
That means you won’t be able to link this :class:`~nettlesome.predicates.Predicate`
to a :class:`~nettlesome.terms.Term` representing the bank account. That should be
okay as long as your data model
doesn't need to include specific details about bank accounts.

Predicates also have a ``truth`` attribute that can be used to establish
that one Predicate ``contradicts`` another.

    >>> no_account_for_company = Predicate(
    >>>     "$applicant opened a bank account for $company",
    >>>     truth=False)
    >>> str(no_account_for_company)
    'it was false that $applicant opened a bank account for $company'

The ``truth`` attribute will become more significant as we build up to
create more complex objects.

Formatting predicates
~~~~~~~~~~~~~~~~~~~~~

Placeholders for terms in a :class:`~nettlesome.predicates.Predicate` should
be marked up using
the placeholder syntax for a :class:`string.Template`, which is a part of the
Python standard library.

The placeholders you choose always need to ``$start_with_a_dollar_sign``
and they need to be valid Python identifiers, which means they can’t
contain spaces. If a placeholder needs to be adjacent to a
non-whitespace character, you also need to
``${wrap_it_in_curly_braces}``.

Don’t use capitalization or end punctuation to signal the beginning or
end of the phrase in a :class:`~nettlesome.predicates.Predicate`\,
because the phrase may be used in a
context where it’s only part of a longer sentence.

The use of different placeholders doesn’t
cause :class:`~nettlesome.predicates.Predicate`\s to be considered to have
different meanings. The example below demonstrates this using
the :meth:`~nettlesome.predicates.Predicate.means` method, which tests
whether two Nettlesome objects have the same meaning.

    >>> account_for_partnership = Predicate("$applicant opened a bank account for $partnership")
    >>> account_for_company.means(account_for_partnership)
    True

If you need to mention the same term more than once
in a :class:`~nettlesome.predicates.Predicate`\, use
the same placeholder for that term each time. If you later create a
:class:`~nettlesome.statements.Statement` object using the
same :class:`~nettlesome.predicates.Predicate`\, you will only include each
unique :class:`~nettlesome.terms.Term` once, in the order they first appear.

In this example, a :class:`~nettlesome.predicates.Predicate`\'s template has
two placeholders referring to the identical :class:`~nettlesome.terms.Term`\.
Even though the rest  of the text is the same, the
reuse of the same :class:`~nettlesome.terms.Term` means that
the :class:`~nettlesome.predicates.Predicate` has a different meaning.

    >>> account_for_self = Predicate("$applicant opened a bank account for $applicant")
    >>> account_for_self.means(account_for_company)
    False

Linking predicates to entities
------------------------------

Basically, a :class:`~nettlesome.statements.Statement` is
a :class:`~nettlesome.predicates.Predicate` plus
the :class:`~nettlesome.terms.Term`\s that need to be included to
make the :class:`~nettlesome.statements.Statement` a complete phrase.

    >>> from nettlesome import Statement, Entity
    >>> statement = Statement(
    >>>     predicate=account_for_company,
    >>>     terms=[Entity("Sarah"), Entity("Acme Corporation")])
    >>> str(statement)
    'the statement that <Sarah> opened a bank account for <Acme Corporation>'

An :class:`~nettlesome.entities.Entity` is a :class:`~nettlesome.terms.Term`
representing a person or thing. If you’re lucky
enough to be able to run effective Named Entity Recognition techniques
on your dataset, you may already have good candidates for the
:class:`~nettlesome.entities.Entity` objects that should be included in
your :class:`~nettlesome.statements.Statement`\s. The data
model of an :class:`~nettlesome.entities.Entity` in Nettlesome includes
just a ``name`` attribute, an attribute indicating whether
the :class:`~nettlesome.entities.Entity` should be considered
``generic``, and a ``plural`` attribute mainly used to determine whether
the word “was” after the :class:`~nettlesome.entities.Entity` should be
replaced with “were”.

    >>> not_at_school = Predicate("$group were at school", truth=False)
    >>> plural_statement = Statement(not_at_school, terms=Entity("the students", plural=True))
    >>> str(plural_statement)
    'the statement it was false that <the students> were at school'    singular_statement = Statement(not_at_school, terms=Entity("Lee", plural=False))
    >>> str(singular_statement)
    'the statement it was false that <Lee> was at school'


The ``generic`` attribute is more subtle than the ``plural`` attribute.
A :class:`~nettlesome.terms.Term` should be marked as ``generic`` if
it’s really being used as a
stand-in for a broader category. For instance, in ``singular_statement``
above, the fact that ``<Lee>`` is generic indicates that
the :class:`~nettlesome.statements.Statement`
isn’t really about a specific incident when Lee was not at school.
Instead, it’s more about the concept of someone not being at school. In
Nettlesome, when angle brackets appear around the string representation
of an object, that’s an indication that the object is generic.

If two :class:`~nettlesome.statements.Statement`\s have different
generic :class:`~nettlesome.terms.Term`\s but they’re otherwise the
same, they’re still considered to have the same meaning as one another.
That’s the case even if one of the :class:`~nettlesome.terms.Term`\s is
plural while the other is singular.

    >>> plural_statement.means(singular_statement)
    True



However, sometimes you need to label an Entity as being somehow sui
generis, so that Statements about that Entity aren’t really applicable
to other, generic Entities. In that case, you can set the Entity’s
``generic`` attribute to False and it’ll no longer be found to have the
same meaning as generic Entities.

.. code:: ipython3

    harry_statement = Statement(not_at_school, terms=Entity("Harry Potter", generic=False))
    harry_statement.means(singular_statement)




.. parsed-literal::

    False



By default, Entities are generic and Statements are not generic. Both of
these defaults can be changed when you create instances of the
respective classes.

Comparing quantitative statements
---------------------------------

The Comparison class extends the concept of a Predicate. A Comparison
still contains a truth value and a template string, but that template
should be used to identify a quantity that will be compared to an
expression using a sign such as an equal sign or a greater-than sign.
This expression must be a constant: either an integer, a floating point
number, or a physical quantity expressed in units that can be parsed
using the pint library.

.. code:: ipython3

    from nettlesome import Comparison

    weight_in_pounds = Comparison("the weight of ${driver}'s vehicle was", sign=">", expression="26000 pounds")
    pounds_statement = Statement(weight_in_pounds, terms=Entity("Alice"))
    str(pounds_statement)




.. parsed-literal::

    "the statement that the weight of <Alice>'s vehicle was greater than 26000 pound"



Statements including Comparisons will handle unit conversions when
applying operations like ``implies`` or ``contradicts``.

.. code:: ipython3

    weight_in_kilos = Comparison("the weight of ${driver}'s vehicle was", sign="<=", expression="3000 kilograms")
    kilos_statement = Statement(weight_in_kilos, terms=Entity("Alice"))
    str(kilos_statement)




.. parsed-literal::

    "the statement that the weight of <Alice>'s vehicle was no more than 3000 kilogram"



.. code:: ipython3

    pounds_statement.contradicts(kilos_statement)




.. parsed-literal::

    True



Formatting comparisons
~~~~~~~~~~~~~~~~~~~~~~

To encourage consistent phrasing, the template string in every
Comparison object must end with the word “was”.

If you phrase a Comparison with an inequality sign using
``truth=False``, Nettlesome will silently modify your statement so it
can have ``truth=True`` with a different sign. In this example, the
user’s input indicates that it’s false that the weight of marijuana
possessed by a defendant was an ounce or more. Nettlesome interprets
this to mean it’s true that the weight was less than one ounce.

.. code:: ipython3

    drug_comparison_with_upper_bound = Comparison(
       "the weight of marijuana that $defendant possessed was",
        sign=">=",
        expression="1 ounce",
        truth=False)
    str(drug_comparison_with_upper_bound)




.. parsed-literal::

    'that the weight of marijuana that $defendant possessed was less than 1 ounce'



When the number needed for a Comparison isn’t a physical quantity that
can be described with the units in the pint library library, you should
phrase the text in the template string to explain what the number
describes. The template string will still need to end with the word
“was”. The value of the expression parameter should be an integer or a
floating point number, not a string to be parsed.

.. code:: ipython3

    three_children = Comparison(
        "the number of children in ${taxpayer}'s household was",
        sign="=",
        expression=3)
    str(three_children)




.. parsed-literal::

    "that the number of children in ${taxpayer}'s household was exactly equal to 3"



Comparing groups of statements
---------------------------------

You can also check to see whether a set of Statements, taken as a group,
implies another Statement or group of Statements.

Here, the use of placeholders that are identical except for a digit on
the end indicates to Nettlesome that the positions of those Terms should
be considered interchangeable. (In this example, if ``site1`` is a
certain distance away from ``site2``, then ``site2`` must also be the
same distance away from ``site1``.)

.. code:: ipython3

    from nettlesome import FactorGroup

    more_than_100_yards = Comparison("the distance between $site1 and $site2 was", sign=">", expression="100 yards")
    less_than_1_mile = Comparison("the distance between $site1 and $site2 was", sign="<", expression="1 mile")

    protest_facts = FactorGroup(
        [Statement(more_than_100_yards, terms=[Entity("the political convention"), Entity("the police cordon")]),
         Statement(less_than_1_mile, terms=[Entity("the police cordon"), Entity("the political convention")])]
    )
    str(protest_facts)




.. parsed-literal::

    "FactorGroup(['the statement that the distance between <the political convention> and <the police cordon> was greater than 100 yard', 'the statement that the distance between <the police cordon> and <the political convention> was less than 1 mile'])"



.. code:: ipython3

    more_than_50_meters = Comparison("the distance between $site1 and $site2 was", sign=">", expression="50 meters")
    less_than_2_km = Comparison("the distance between $site1 and $site2 was", sign="<=", expression="2 km")

    speech_zone_facts = FactorGroup(
        [Statement(more_than_50_meters, terms=[Entity("the free speech zone"), Entity("the courthouse")]),
         Statement(less_than_2_km, terms=[Entity("the free speech zone"), Entity("the courthouse")])]
    )
    protest_facts.implies(speech_zone_facts)




.. parsed-literal::

    True


