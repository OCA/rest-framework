from extendable_pydantic import ExtendableBaseModel


class StrictExtendableBaseModel(
    ExtendableBaseModel,
    revalidate_instances="always",
    validate_assignment=True,
    extra="forbid",
):
    """
    An ExtendableBaseModel with strict validation.

    By default, Pydantic does not revalidate instances during validation, nor
    when the data is changed. Validation only occurs when the model is created.
    This is not suitable for a REST API, where the data is changed after the
    model is created or the model is created from a partial set of data and
    then updated with more data. This class enforces strict validation by
    forcing the revalidation of instances when the method `model_validate` is
    called and by ensuring that the values assignment is validated.

    The following parameters are added:
    * revalidate_instances="always": model instances are revalidated during validation
    (default is "never")
    * validate_assignment=True: revalidate the model when the data is changed (default is False)
    * extra="forbid": Forbid any extra attributes (default is "ignore")
    """
