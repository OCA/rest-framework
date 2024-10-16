This module adds to the partners the ability to authenticate through directories.

This module does not implement any routing, it only provides the basic mechanisms in a directory for:

  - Registering a partner and sending an welcome email (to validate email address): `_signup`
  - Authenticating a partner: `_login`
  - Validating a partner email using a token: `_validate_email`
  - Impersonating: `_impersonate`, `_impersonating`
  - Resetting the password with a unique token sent by mail: `_request_reset_password`, `_set_password`
  - Sending an invite mail when registering a partner from odoo interface for the partner to enter a password: `_send_invite`, `_set_password`
  
For a routing implementation, see the `fastapi_auth_partner <../fastapi_auth_partner>`_ module.
