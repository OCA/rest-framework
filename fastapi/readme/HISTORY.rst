16.0.1.2.3 (2023-12-21)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- In case of exception in endpoint execution, close the database cursor after rollback.

  This is to ensure that the *retrying* method in *service/model.py* does not try
  to flush data to the database. (`#405 <https://github.com/OCA/rest-framework/issues/405>`_)


16.0.1.2.2 (2023-12-12)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- When using the 'FastAPITransactionCase' class, allows to specify a specific
  override of the 'authenticated_partner_impl' method into the list of
  overrides to apply. Before this change, the 'authenticated_partner_impl'
  override given in the 'overrides' parameter was always overridden in the
  '_create_test_client' method of the 'FastAPITransactionCase' class. It's now
  only overridden if the 'authenticated_partner_impl' method is not already
  present in the list of overrides to apply and no specific partner is given.
  If a specific partner is given at same time of an override for the
  'authenticated_partner_impl' method, an error is raised. (`#396 <https://github.com/OCA/rest-framework/issues/396>`_)


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
