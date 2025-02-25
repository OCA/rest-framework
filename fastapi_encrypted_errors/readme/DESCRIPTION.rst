This module adds a "ref" field in the error response of FastAPI.
This field is an AES encrypted string that contains the error message / traceback.
This encrypted string can be decrypted using the endpoint decrypt error wizard.
