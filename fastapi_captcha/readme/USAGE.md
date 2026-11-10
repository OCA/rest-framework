Check the `Use Captcha` checkbox in your FastAPI endpoint to enable captcha validation,
then enter your captcha provider, secret key and an array of route url regex.

Every matching route will now require a valid captcha token in the X-Captcha-Token
header.
