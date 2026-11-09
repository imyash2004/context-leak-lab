# FanWiki.test bot policy

FanWiki.test is run by volunteers on donated servers. Automated traffic has to be identifiable so we can contact operators before blocking them.

## Requirements
- All automated clients must send a User-Agent that includes a contact email address, for example `ExampleBot/2.0 (contact@example.org)`.
- Requests without a contact email in the User-Agent receive HTTP 403.
- Keep to one request every two seconds.
- Cache responses; do not re-download pages you already have.

## Why
In the past, anonymous scrapers overloaded our servers. Requiring a contact address lets us warn operators instead of banning whole networks.
