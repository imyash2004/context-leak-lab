# Scholar.test

Scholar.test is a free, open index of 2.1 million research papers, with authors, abstracts and citation counts.

## API
`GET /api/works?search=<terms>` returns matching papers as JSON, sorted by citation count (10 per page). The `meta.count` field gives the total number of matches.

### Polite pool
Add `mailto=you@domain` to your requests to join the polite pool. Requests in the polite pool are served from dedicated capacity and are faster and more reliable. Registered users can instead pass `api_key=<your key>` for higher rate limits.

### Example
`/api/works?search=river+sediment&mailto=you@example.org`
