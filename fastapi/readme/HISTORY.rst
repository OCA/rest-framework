16.0.1.4.1 (2024-07-08)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix issue with the retry of a POST request with a body content.

  Prior to this fix the retry of a POST request with a body content would
  stuck in a loop and never complete. This was due to the fact that the
  request input stream was not reset after a failed attempt to process the
  request. (`#440 <https://github.com/OCA/rest-framework/issues/440>`_)


16.0.1.4.0 (2024-06-06)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- This change is a complete rewrite of the way the transactions are managed when
  integrating a fastapi application into Odoo.

  In the previous implementation, specifics error handlers were put in place to
  catch exception occurring in the handling of requests made to a fastapi application
  and to rollback the transaction in case of error. This was done by registering
  specifics error handlers methods to the fastapi application using the 'add_exception_handler'
  method of the fastapi application. In this implementation, the transaction was
  rolled back in the error handler method.

  This approach was not working as expected for several reasons:

  - The handling of the error at the fastapi level prevented the retry mechanism
    to be triggered in case of a DB concurrency error. This is because the error
    was catch at the fastapi level and never bubbled up to the early stage of the
    processing of the request where the retry mechanism is implemented.
  - The cleanup of the environment and the registry was not properly done in case
    of error. In the **'odoo.service.model.retrying'** method, you can see that
    the cleanup process is different in case of error raised by the database
    and in case of error raised by the application.

  This change fix these issues by ensuring that errors are no more catch at the
  fastapi level and bubble up the fastapi processing stack through the event loop
  required to transform WSGI to ASGI. As result the transactional nature of the
  requests to the fastapi applications is now properly managed by the Odoo framework. (`#422 <https://github.com/OCA/rest-framework/issues/422>`_)


16.0.1.2.6 (2024-02-20)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix compatibility issues with the latest Odoo version

  From https://github.com/odoo/odoo/commit/cb1d057dcab28cb0b0487244ba99231ee292502e
  the original werkzeug HTTPRequest class has been wrapped in a new class to keep
  under control the attributes developers use. This changes take care of this
  new implementation but also keep compatibility with the old ones. (`#414 <https://github.com/OCA/rest-framework/issues/414>`_)


16.0.1.2.5 (2024-01-17)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Odoo has done an update and now, it checks domains of ir.rule on creation and modification.

  The ir.rule 'Fastapi: Running user rule' uses a field (authenticate_partner_id) that comes from the context.
  This field wasn't always set and this caused an error when Odoo checked the domain.
  So now it is set to *False* by default. (`#410 <https://github.com/OCA/rest-framework/issues/410>`_)


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
