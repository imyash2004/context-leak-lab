# Wiki.test bot and API policy

Wiki.test welcomes automated access by research tools, bots and scripts, as long as they follow these rules.

## User-Agent
Automated clients should send a descriptive User-Agent with contact information, e.g. `MyBot/1.0 (you@example.org)`. This lets our operators contact you if your client causes problems. Generic User-Agents, such as the defaults sent by HTTP libraries, may be rate-limited or blocked without notice.

## Rate limits
Make requests in series, not in parallel, and keep to about one request per second. Back off when you receive HTTP 429 or 503 responses.

## Content reuse
Article text is available under a free licence. Please link back to the article you used.

## Contact
Operators of high-volume tools should write to the address in the footer before starting.
