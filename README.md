# eureka-stocks

This is a Stock Market Data application.

It allows users to register and get a personal API key to retrieve stock quotes.

The workflow is the following:

1. User registers by sending their information in a GET request with the following format:
   > https://eureka-stocks.herokuapp.com/register?email=EMAIL=NAME&last_name=LAST_NAME

   for example:

   > https://eureka-stocks.herokuapp.com/register?email=ramiroperezosan@gmail.com&name=ramiro&last_name=perez

1. A validation key is sent to the user by email. Users must validate their account by clicking on the link, or making a GET request to the server with the following format:
   > https://eureka-stocks.herokuapp.com//validate?id=KEY

   for example:

   > https://eureka-stocks.herokuapp.com//validate?id=18e0c89d-45b9-4bf0-8559-ca3846748d74

1. When the validation is complete, an API key is generated and sent to the users' email.
   With the KEY, the user is able to query the API and retrieve stock quotes.
   Queries to that endpoint must use the POST verb, contain the API key in the "API_KEY" HTTP header and carry the symbol in the request body, using standard http __form formatting__ with the "symbol" variable name, for example

   > symbol=AAPL

   The API has a rate limiter that only allows 2 requests per minute per key.

   The response is a JSON object with the following format:

   ```javascript
   {
    "close": 4131.7762,
    "high": 4202.1086,
    "low": 4105.6243,
    "open": 4196.9508,
    "two_day_variation": -64.46529999999984,
    "two_day_variation_pct": -1.5362628676161714
   }
   ```

   where two_day_variation and two_day_variation_pct are the price change in the last 2 days in absolute and percentual format.


Example requests and responses using the command line httpie utility:

```
$ http "https://eureka-stocks.herokuapp.com/register?email=ramiroperezosan@gmail.com&name=ramiro&last_name=perez"

A validation email has been sent to ramiroperezosan@gmail.com. Please follow the instructions to get your API key.

$ http "https://eureka-stocks.herokuapp.com//validate?id=18e0c89d-45b9-4bf0-8559-ca3846748d74"

Your API key has been sent to your email address.

$ http -f POST "https://eureka-stocks.herokuapp.com/get_stock" API_KEY:86d6ca2c-5f44-46fb-adef-2de830c696f4 symbol=ggal

{
    "close": 9.17,
    "high": 9.54,
    "low": 9.0,
    "open": 9.54,
    "two_day_variation": -0.35999999999999943,
    "two_day_variation_pct": -3.7775445960125857
}
```


## Running the application

The application can be executed locally with the included docker-compose.yml file by creating the __.env-docker__ file using __dotenv-sample__ as source (just renaming it and setting the SendGrid api key works) and running:

> $ docker-compose -f docker-compose.yml build

> $ docker-compose -f docker-compose.yml up

## Other considerations

* The application is developed in Python, using the Flask framework. It uses Redis as data storage, the flask rate limiting add on, Flask-Limiter and the SendGrid module to send emails through their service.
* The application is hosted in Heroku, and can be accessed in the url https://eureka-stocks.herokuapp.com

* Requests are logged using python's standard logging to stdout.

  Regular request logs look like this (in the Heroku logs):
  > 2021-12-06T02:43:02.175598+00:00 app[web.1]: INFO:app:SRC: 10.1.36.147, ENDPOINT: /validate, ARGS: ImmutableMultiDict([('id', '18e0c89d-45b9-4bf0-8559-ca3846748d74')])

  And stock requests like this:
  > 2021-12-06T02:49:35.771400+00:00 app[web.1]: INFO:app:SRC: 10.1.39.26, ENDPOINT: /get_stock, KEY: 9be24a42-5ee8-48f2-b890-ebf83a0abfc5, SYMBOL: ethusdt

