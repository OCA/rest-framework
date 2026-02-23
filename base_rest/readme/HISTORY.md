## 16.0.1.0.2 (2023-10-07)

**Features**

- Add support for oauth2 security scheme in the Swagger UI. If your
  openapi specification contains a security scheme of type oauth2, the
  Swagger UI will display a login button in the top right corner. In
  order to finalize the login process, a redirect URL must be provided
  when initializing the Swagger UI. The Swagger UI is now initialized
  with a oauth2RedirectUrl option that references a oauth2-redirect.html
  file provided by the swagger-ui lib and served by the current addon.
  ([\#379](https://github.com/OCA/rest-framework/issues/379))

## 12.0.2.0.1

- validator\_...() methods can now return a cerberus `Validator` object
  instead of a schema dictionnary, for additional flexibility (e.g.
  allowing validator options such as `allow_unknown`).

## 12.0.2.0.0

- Licence changed from AGPL-3 to LGPL-3

## 12.0.1.0.1

- Fix issue when rendering the jsonapi documentation if no documentation
  is provided on a method part of the REST api.

## 12.0.1.0.0

First official version. The addon has been incubated into the
[Shopinvader repository](https://github.com/akretion/odoo-shopinvader)
from Akretion. For more information you need to look at the git log.
