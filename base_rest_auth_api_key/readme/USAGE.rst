To get the proper documentation in the Swagger UI, you will need to define
where the API key is read from. For instance by creating an abstract component
that will serve as base for all services using the authentication method:

.. code-block:: python
  from odoo.addons.component.core import AbstractComponent
  class BaseApiKeyService(AbstractComponent):
      _inherit = 'base.rest.service'
      _name = 'base.rest.auth_apikey.service'

      def _get_openapi_default_parameters(self):
          defaults = super()._get_openapi_default_parameters()
          defaults.extend(
              [
                  {
                      "name": "API-KEY",
                      "in": "header",
                      "description": "Auth API key "
                      "(Only used when authenticated by API key)",
                      "required": False,
                      "schema": {"type": "string"},
                      "style": "simple",
                  },
              ]
          )
          return defaults
