from http import HTTPStatus
from aws_lambda_powertools.event_handler.exceptions import ServiceError


class InvalidParameterError(ServiceError):
    """
    Raised when the request includes a non-allowed value
    """

    def __init__(self, message: str) -> None:
        super().__init__(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, msg=message)
