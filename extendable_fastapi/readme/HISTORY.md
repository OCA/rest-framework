## 16.0.2.1.1 (2023-11-07)

**Bugfixes**

- Fix registry corruption when running tests difined in a class
  inheriting of the *FastAPITransactionCase* class if an error occurs in
  the *setUpClass* after the call to super().
  ([\#392](https://github.com/OCA/rest-framework/issues/392))

## 16.0.2.1.0 (2023-10-13)

**Features**

- - New base schemas: *PagedCollection*. This schema is used to define
    the the structure of a paged collection of resources. This schema is
    similar to the ones defined in the Odoo's **fastapi** addon but
    works as/with extendable models.
  - The *StrictExtendableBaseModel* has been moved to the
    *extendable_pydantic* python lib. You should consider to import it
    from there.
    ([\#380](https://github.com/OCA/rest-framework/issues/380))
