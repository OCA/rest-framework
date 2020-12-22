This addon provides the basis to develop high level REST APIs for Odoo.

As Odoo becomes one of the central pieces of enterprise IT systems, it often
becomes necessary to set up specialized service interfaces, so existing
systems can interact with Odoo.

While the XML-RPC interface of Odoo comes handy in such situations, it
requires a deep understanding of Odoo’s internal data model. When used
extensively, it creates a strong coupling between Odoo internals and client
systems, therefore increasing maintenance costs.

Once developed, an `OpenApi <https://spec.openapis.org/oas/v3.0.3>`_ documentation
is generated from the source code and available via a
`Swagger UI <https://swagger.io/tools/swagger-ui/>`_ served by your odoo server
at `https://my_odoo_server/api-docs`.
