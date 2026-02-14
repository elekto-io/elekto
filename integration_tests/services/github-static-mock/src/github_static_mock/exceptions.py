from fastapi.exceptions import HTTPException
from starlette import status


class NoUpcomingUserException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No upcoming user configured.'
        )
