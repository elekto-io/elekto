import requests

from .models import User


class GithubMockUtilityClient:
    def __init__(self, host: str):
        self.host = host

    def store_upcoming_user(self, user: User) -> None:
        """
        Set user data for the next mocked Github login.

        IRL users would log in at Github and then return to Elekto with a code. Elekto uses the code to get data for
        that authenticated user. Our tests mock the Github part, causing the code to not point to a particular user. To
        make up for this, we can set fake user data in the mock server. The next user lookup populates the 'name' and
        'login' fields with the fake data we sent in using the /system/upcoming-user call.

        Args:
            user: The User object to set mock data from.

        Returns: None

        """
        resp = requests.post(f'{self.host}/system/upcoming-user', json=user.to_dict())

        if resp.status_code != 201:
            raise Exception(resp.text)
