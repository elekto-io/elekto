# Static oauth GitHub mock
This project mocks GitHub oauth server's [web application flow](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#web-application-flow).
As this is a static project, codes and tokens are hardcoded. An endpoint is available to set the user data to be 
returned on the next call to the `/user` endpoint. By doing this, a webpage with form input on the mocked user is 
avoided, keeping this simple for automated tests.

WARNING: This is a project for testing purposes only. Nothing about this implementation is secure.

## Running the project
Currently only the Redis cache runs on Docker Compose. This stores the upcoming user's data. Run it with 
`docker compose up`.

The web application itself can be run with `poetry run start` after running `poetry install`.

## Endpoints
### Authorization mechanics
The oauth endpoints mocked facilitate the web application flow. Calls in order are:
1. Call `/system/upcoming-user` to set the next mocked user data.
2. Call `/login/oauth/authorize` to have the application return a response with a code and state.
3. Call `/login/oauth/access_token` to mock exchanging the code for a bearer token.
4. Call `/user` to obtain user data.

## /system/upcoming-user
Example call (using [HTTPie](https://httpie.io/)):

```shell
http "http://localhost:9000/system/upcoming-user" name="John Smith" login=jsmith
```

## /login/oauth/authorize
Authorization requires query parameters: response_type, client_id, scope, state and redirect_uri. The redirect_uri is 
used to redirect the client. The state is included in the redirect URI for further use by the client. The code in the
redirect URI is hardcoded.

```shell
http "http://localhost:9000/login/oauth/authorize?response_type=code&client_id=Ov23liuEhYT3CT9Yh6VA&scope=user%3Alogin%2Cname&state=JQOy3kw1PDiQh662ln4DuTGX20ajwb&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Foauth%2Fgithub%2Fcallback"
```

## /login/oauth/access_token
This endpoint takes a token and returns a bearer token. The bearer token is hardcoded. This endpoint requires 
application/x-www-form-urlencoded data.

```shell
http --form POST "http://localhost:9000/login/oauth/access_token" grant_type=authorization_code code=SplxlOBeZQQYbYS6WxSbIA
```

## /user
Finally, the user endpoint is called. This returns the user's profile data. The `login` and `name` in the response are 
retrieved from Redis and are the values set via the `/system/upcoming-user` endpoint. This endpoint requires an 
Authorization header containing `Bearer `, the token itself is not evaluated. Calling this endpoint without setting an 
upcoming user in cache results in an HTTP400 Bad Request.

```shell
http "http://localhost:9000/user" "Authorization: Bearer gho_xxx"
```
