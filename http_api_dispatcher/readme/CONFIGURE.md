To include the traceback and the description of any error in the responses,
set `dev_mode` in the `http_api` section of the configuration file:

    [http_api]
    dev_mode = True

The `dev_mode` key of the `base_rest` section is honored as well.
Never enable it in production.
