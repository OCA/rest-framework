First you have to add the auth router to your FastAPI endpoint and the authentication dependency to your app dependencies:

.. code-block:: python

    from odoo.addons.fastapi import dependencies
    from odoo.addons.fastapi_auth_partner.dependencies import (
      auth_partner_authenticated_partner,
    )
    from odoo.addons.fastapi_auth_partner.routers.auth import auth_router

    class FastapiEndpoint(models.Model):
        _inherit = "fastapi.endpoint"

        def _get_fastapi_routers(self):
          if self.app == "myapp":
              return [
                  auth_router,
              ]
          return super()._get_fastapi_routers()
    
        def _get_app_dependencies_overrides(self):
            res = super()._get_app_dependencies_overrides()
            if self.app == "portal":
                res.update(
                    {
                        dependencies.authenticated_partner_impl: auth_partner_authenticated_partner,
                    }
                )
            return res

Next you can manage your authenticable partners and directories in the Odoo interface:

FastAPI > Authentication > Partner

and

FastAPI > Authentication > Directory

Next you must set the directory used for the authentication in the FastAPI endpoint:

FastAPI > FastAPI Endpoint > myapp > Directory

Then you can use the auth router to authenticate your requests:

- POST /auth/register to register a partner
- POST /auth/login to authenticate a partner
- POST /auth/logout to unauthenticate a partner
- POST /auth/validate_email to validate a partner email
- POST /auth/request_reset_password to request a password reset
- POST /auth/set_password to set a new password
- GET /auth/profile to get the partner profile
- GET /auth/impersonate to impersonate a partner
