class MockResponseBase:
    def __init__(self, json, status_code=200):
        self._json = json
        self.status_code = status_code

    def json(self) -> dict:
        return self._json


class MockUserResponse(MockResponseBase):
    ...


class MockTokenResponse(MockResponseBase):
    ...
