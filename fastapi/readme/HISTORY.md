## 17.0.1.0.1 (2024-10-02)

### Bugfixes

- Fix compatibility issues with the latest Odoo version

  From https://github.com/odoo/odoo/commit/cb1d057dcab28cb0b0487244ba99231ee292502e
  the original werkzeug HTTPRequest class has been wrapped in a new class to keep
  under control the attributes developers use. This changes take care of this
  new implementation but also keep compatibility with the old ones. ([#414](https://github.com/OCA/rest-framework/issues/414))


## 16.0.1.2.5 (2024-01-17)

### Bugfixes

- Odoo has done an update and now, it checks domains of ir.rule on creation and
  modification.

  The ir.rule 'Fastapi: Running user rule' uses a field (authenticate*partner_id) that
  comes from the context. This field wasn't always set and this caused an error when
  Odoo checked the domain. So now it is set to *False* by default.
  (`#410 <https://github.com/OCA/rest-framework/issues/410>`*)

## 16.0.1.2.3 (2023-12-21)

### Bugfixes

- In case of exception in endpoint execution, close the database cursor after rollback.

  This is to ensure that the _retrying_ method in _service/model.py_ does not try to
  flush data to the database.
  ([\#405](https://github.com/OCA/rest-framework/issues/405))

## 16.0.1.2.2 (2023-12-12)

### Bugfixes

- When using the 'FastAPITransactionCase' class, allows to specify a specific override
  of the 'authenticated_partner_impl' method into the list of overrides to apply. Before
  this change, the 'authenticated_partner_impl' override given in the 'overrides'
  parameter was always overridden in the '\_create_test_client' method of the
  'FastAPITransactionCase' class. It's now only overridden if the
  'authenticated_partner_impl' method is not already present in the list of overrides to
  apply and no specific partner is given. If a specific partner is given at same time of
  an override for the 'authenticated_partner_impl' method, an error is raised.
  ([\#396](https://github.com/OCA/rest-framework/issues/396))

## 16.0.1.2.1 (2023-11-03)

### Bugfixes

- Fix a typo in the Field declaration of the 'count' attribute of the 'PagedCollection'
  schema.

  Misspelt parameter was triggering a deprecation warning due to recent versions of
  Pydantic seeing it as an arbitrary parameter.
  ([\#389](https://github.com/OCA/rest-framework/issues/389))

## 16.0.1.2.0 (2023-10-13)

### Features

- The field _total_ in the _PagedCollection_ schema is replaced by the field _count_.
  The field _total_ is now deprecated and will be removed in the next major version.
  This change is backward compatible. The json document returned will now contain both
  fields _total_ and _count_ with the same value. In your python code the field _total_,
  if used, will fill the field _count_ with the same value. You are encouraged to use
  the field _count_ instead of _total_ and adapt your code accordingly.
  ([\#380](https://github.com/OCA/rest-framework/issues/380))
