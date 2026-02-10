Create a FastAPI endpoint and select the Dynamic app for it.

You can now configure its mounted routers in the Routers field and the authentication
method in the Authentication Method field.

A list of the chosen routers will appear in the Dynamic Routers tab. There you can
configure the routers' options, such as the prefix and the authentication method.

If a router is configured with a prefix, let's say the cart router, it will be mounted
in the app with the prefix unless the authentication method is set, in which case a sub
app will be created for all router with this prefix.
