`base_rest` (OCA/rest-framework) has been the foundation of many APIs,
including the Shopfloor apps. Over time it showed some limits:

- it is a monolith: dispatcher, service layer, validation,
  documentation and routing are bound together
  and you cannot use one piece without the others
- services must be `component`s, a second registry
  with its own inheritance and boot lifecycle,
  which is often used only to look up a class by name
- controllers are generated at boot from the services,
  making routing hard to follow and to customize

The `fastapi` stack is a way to go for new standalone APIs,
but moving existing APIs to it means rewriting every service and schema and endpoints are not extendable models.
Plus, it pulls in more external dependencies that for many cases are not needed.

This module is the base of a lighter stack, made of small modules
that can be used separately and extended via standard Odoo inheritance:

- `http_api_dispatcher`: the `http_api` route type (parsing, validation hooks, JSON errors)
  usable by plain Odoo controllers
- `endpoint_spec`: declare endpoints on services, for routes generators
- `http_api_cerberus`: Cerberus validation
- `openapi_doc_base`: API docs from the actual routes
- `endpoint_route_handler` generators: routes computed from the code
  without storing a row per route

Goals:

- simplify the `base_rest` stack without moving to `fastapi`
- keep modules small and reusable
- drop the dependency on `component`, staying highly customizable
  (routing keys per route, `ir.http` hooks per database)
- stay compatible with `base_rest` clients (error format, validation behavior)
  to allow a gradual migration
