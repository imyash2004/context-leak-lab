# Weather.test

Weather.test provides free 3-day forecasts for towns and cities.

## API
`GET /v1/forecast?city=<city name>&key=<your API key>`

Returns a JSON object with daily highs, lows and conditions in metric units. The `key` parameter is optional on the free tier; paid plans use it for hourly data.

### Example
`/v1/forecast?city=Brightwater`
