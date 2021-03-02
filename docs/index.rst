.. Nettlesome documentation master file, created by
   sphinx-quickstart on Mon Feb 22 21:37:12 2021.

==========================================
Nettlesome: Simplified Semantic Reasoning
==========================================

Release v\. |release|.

`Nettlesome <https://github.com/mscarey/nettlesome>`_ is a Python
library defining a limited grammar of natural-language statements
that can be compared programmatically for implication or contradiction.

Nettlesome is intended for use where there is a limited schema of statements
that can be used to annotate a dataset with categories, numbers, quantities,
and dates. One example of such a schema is
the `National Information Exchange Model <https://github.com/NIEM/NIEM-Releases/tree/niem-5.0>`_.

Although Nettlesome was designed to be used for legal annotations in
the `AuthoritySpoke <https://github.com/mscarey/AuthoritySpoke>`_ library,
Nettlesome itself doesn't depend on any legal concepts or specialized knowledge.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. toctree::
    :maxdepth: 2
    :caption: Guides

    guides/intro.rst

.. toctree::
    :maxdepth: 1
    :caption: API Reference

    api/comparable.rst
    api/terms.rst
    api/factors.rst
    api/entities.rst
    api/predicates.rst
    api/comparisons.rst
    api/quantities.rst
    api/statements.rst
    api/doctrines.rst
    api/explanations.rst
    api/groups.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
