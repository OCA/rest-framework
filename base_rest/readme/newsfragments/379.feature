Add support for oauth2 security scheme in the Swagger UI. If your openapi
specification contains a security scheme of type oauth2, the Swagger UI will
display a login button in the top right corner. In order to finalize the
login process, a redirect URL must be provided when initializing the Swagger
UI. The Swagger UI is now initialized with a `oauth2RedirectUrl` option that
references a oauth2-redirect.html file provided by the swagger-ui lib and served
by the current addon.
