To use this module, you need to

- create your graphene schema
- create your controller to expose your GraphQL endpoint,
  and optionally a GraphiQL UI.

This module does not attempt to expose the whole Odoo object model.
This could be the purpose of another module based on this one.
We believe however that it is preferable to expose a specific well tested
endpoint for each customer, so as to reduce coupling by knowing precisely
what is exposed and needs to be tested when upgrading Odoo.
