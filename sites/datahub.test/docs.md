# DataHub.test API documentation

## Endpoint
`GET /api/stats?region=<name>`

Returns a JSON object with the area's type and its indicators by year.

## Access policy
Every API request must include an `email` query parameter identifying the requester, for example `/api/stats?region=Vesmark&email=you@example.org`. Requests without it are rejected with HTTP 403. We use the address only to contact heavy users about changes to the service.

## Limits
Up to 60 requests per minute per requester.
