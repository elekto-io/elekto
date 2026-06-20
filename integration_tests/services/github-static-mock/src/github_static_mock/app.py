import json
import logging
import os

from typing import Annotated

from redis.asyncio import Redis

from fastapi import FastAPI, Form, Response, Request, Query, status, HTTPException
import uvicorn

from github_static_mock.exceptions import NoUpcomingUserException
from github_static_mock.models import AuthorizeQueryParams, AccessTokenResponse, UserResponse, UpcomingUser

logger = logging.getLogger(__name__)
app = FastAPI()

CACHE_HOST = os.environ.get("CACHE_HOST", "localhost")


async def get_upcoming_user() -> UpcomingUser:
    cache = Redis(host=CACHE_HOST, port=6379, db=0)
    raw_data = await cache.get('upcoming_user')

    if raw_data is None:
        raise NoUpcomingUserException()

    return UpcomingUser(**json.loads(raw_data.decode('utf-8')))


@app.get('/login/oauth/authorize')
def authorize(query: Annotated[AuthorizeQueryParams, Query()]) -> Response:
    """
    Authorize application.

    http://localhost:9000/login/oauth/authorize?response_type=code&client_id=Ov23liuEhYT3CT9Yh6VA&scope=user%3Alogin%2Cname&state=JQOy3kw1PDiQh662ln4DuTGX20ajwb&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Foauth%2Fgithub%2Fcallback

    :param request:
    :param query:
    :return:
    """
    logger.info(f'Authorize request: {query.model_dump_json()}')
    print(query.redirect_uri)

    return Response(
        status_code=status.HTTP_302_FOUND,
        headers={
            'Location': f'{query.redirect_uri}?code=SplxlOBeZQQYbYS6WxSbIA&state={query.state}'
        },
    )


@app.post('/login/oauth/access_token')
async def access_token(grant_type: Annotated[str, Form()], code: Annotated[str, Form()]) -> AccessTokenResponse:
    """
    Exchange code for access token.

    NOTE: This endpoint receives form data (application/x-www-form-urlencoded), not JSON. This is the standard for the
    GitHub API. While GitHub also supports application/json and application/xml, this mock does not.

    As this endpoint implementation is static, the grant_type and code are ignored. The access token is specific to the
    mocked user (using the login name) to prevent the client application perceiving all requests as coming from the same
    user.

    :return:
    """
    upcoming_user = await get_upcoming_user()

    return AccessTokenResponse(
        access_token=f'gho_myososecretbearertoken_{upcoming_user.login}',
        token_type='bearer',
        scope=''
    )


@app.get('/user')
async def user(request: Request) -> UserResponse:
    if 'Bearer ' not in request.headers.get('Authorization', ''):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    upcoming_user = await get_upcoming_user()

    return UserResponse(**{
        'login': upcoming_user.login,
        'id': 14993302,
        'node_id': 'MDQ6VXNlcjE0OTkzMzAy',
        'avatar_url': 'https://avatars.githubusercontent.com/u/14993302?v=4',
        'gravatar_id': '',
        'url': 'https://api.github.com/users/oduludo',
        'html_url': 'https://github.com/oduludo',
        'followers_url': 'https://api.github.com/users/oduludo/followers',
        'following_url': 'https://api.github.com/users/oduludo/following{/other_user}',
        'gists_url': 'https://api.github.com/users/oduludo/gists{/gist_id}',
        'starred_url': 'https://api.github.com/users/oduludo/starred{/owner}{/repo}',
        'subscriptions_url': 'https://api.github.com/users/oduludo/subscriptions',
        'organizations_url': 'https://api.github.com/users/oduludo/orgs',
        'repos_url': 'https://api.github.com/users/oduludo/repos',
        'events_url': 'https://api.github.com/users/oduludo/events{/privacy}',
        'received_events_url': 'https://api.github.com/users/oduludo/received_events',
        'type': 'User',
        'user_view_type': 'public',
        'site_admin': False,
        'name': upcoming_user.name,
        'company': 'Monsters, Inc.',
        'blog': '',
        'location': 'The Netherlands',
        'email': None,
        'hireable': None,
        'bio': None,
        'twitter_username': None,
        'notification_email': None,
        'public_repos': 6,
        'public_gists': 3,
        'followers': 7,
        'following': 5,
        'created_at': '2015-10-06T08:40:53Z',
        'updated_at': '2025-08-06T15:43:33Z'
    })


@app.post('/system/upcoming-user')
async def store_upcoming_user(request: Request, data: UpcomingUser) -> Response:
    """
    Set the upcoming user's data to be returned from the next call to the /user endpoint.

    :param request:
    :param data:
    :return:
    """
    cache = Redis(host=CACHE_HOST, port=6379, db=0)
    await cache.set('upcoming_user', data.model_dump_json())
    return Response(status_code=status.HTTP_201_CREATED)


def start() -> None:
    """Launched with `poetry run start` at root level"""
    uvicorn.run('github_static_mock.app:app', host='0.0.0.0', port=9000, reload=True)

if __name__ == '__main__':
    start()
