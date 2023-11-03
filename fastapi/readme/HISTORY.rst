16.0.1.2.1 (2023-11-03)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix a typo in the Field declaration of the 'count' attribute of the 'PagedCollection' schema.

  Misspelt parameter was triggering a deprecation warning due to recent versions of Pydantic seeing it as an arbitrary parameter. (`#389 <https://github.com/OCA/rest-framework/issues/389>`_)


16.0.1.2.0 (2023-10-13)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- The field *total* in the *PagedCollection* schema is replaced by the field *count*.
  The field *total* is now deprecated and will be removed in the next major version.
  This change is backward compatible. The json document returned will now
  contain both fields *total* and *count* with the same value. In your python
  code the field *total*, if used, will fill the field *count* with the same
  value. You are encouraged to use the field *count* instead of *total* and adapt
  your code accordingly. (`#380 <https://github.com/OCA/rest-framework/issues/380>`_)
