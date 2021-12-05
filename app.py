#!/bin/env python3

"""Flask application that returns stock quotes.
Developed for an Eureka code challenge."""

import os

from flask import Flask, request, make_response, Response
from flask_limiter import Limiter
from dotenv import load_dotenv

from eureka_stocks.exceptions import ApplicationException
from eureka_stocks.controller import EurekaStocksController

load_dotenv()

app = Flask(__name__)

API_KEY_HEADER_NAME = 'API_KEY'

APPLICATION_NAME = os.environ.get('APPLICATION_NAME', 'Stocks')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = os.environ.get('FROM_EMAIL')
EXTERNAL_ADDRESS = os.environ.get('EXTERNAL_ADDRESS', 'localhost')
REDIS_URL = os.environ.get('REDISTOGO_URL', 'redis://localhost')
ALPHAVANTAGE_API_KEY = os.environ.get('ALPHAVANTAGE_API_KEY') 

def log_request():
    """Logs generic requests using the default flask logger. Requests are printed to stdout."""
    app.logger.info("SRC: %s, ENDPOINT: %s, ARGS: %s",
                    request.remote_addr, request.path, request.args)


def log_quote_request():
    """Logs quote requests using the default flask logger. Requests are printed to stdout."""
    app.logger.info("SRC: %s, ENDPOINT: %s, KEY: %s, SYMBOL: %s",
                    request.remote_addr, request.path, get_request_api_key(), request.form.get('symbol'))


def get_request_api_key():
    """Returns the API key taken from the request headers."""
    return request.headers.get(API_KEY_HEADER_NAME)


limiter = Limiter(
    app,
    key_func=get_request_api_key,
    default_limits=["2/minute"]
)


applicationController = EurekaStocksController(REDIS_URL,
                                               SENDGRID_API_KEY,
                                               ALPHAVANTAGE_API_KEY,
                                               FROM_EMAIL, EXTERNAL_ADDRESS, APPLICATION_NAME)


@app.before_request
def check_valid_api_key():
    """Verifies that the api key sent in the heder exists in the database.
    It only works for the endpoint that returns stock quotes."""
    if request.path.startswith('/get_stock'):
        key = get_request_api_key()

        if not applicationController.check_key_exists(key):
            return Response('Invalid API_KEY.', status=403, mimetype='text/plain')

    return None


@app.errorhandler(429)
def ratelimit_handler(error):
    """Handles rate limit exceeded errors."""
    return make_response(f"Rate limit exceeded max allowed: {error.description}", 429)


@app.errorhandler(ApplicationException)
def handle_exception(exception):
    """Handles application exceptions."""
    return Response(f"{exception}", status=400, mimetype='text/plain')


@app.route("/")
def hello_world():
    """Health check endpoint."""
    return "Eureka stocks is up and running."


@app.route("/register", methods=['GET'])
def register_user():
    """Registers a new user, it is saved temporarily until the user verifies their
    email address."""

    log_request()

    name = request.args.get('name')
    last_name = request.args.get('last_name')
    email = request.args.get('email')

    applicationController.create_temporary_user(email, name, last_name)
    return Response(f"A validation email has been sent to {email}. " +
                    "Please follow the instructions to get your API key.",
                    status=200, mimetype='text/plain')


@app.route("/validate", methods=['GET'])
def validate_user():
    """Recieves a validation key and stores the corresponding user permanently.
    It also generates an API key for the user and sends it to their registered email."""

    log_request()

    validation_key = request.args.get('id')

    applicationController.validate_and_create_key(validation_key)

    return Response('Your API key has been sent to your email address.', mimetype='text/plain')


@app.route("/get_stock", methods=['POST'])
@limiter.limit("2/minute")
def get_stock():
    """Returns the quotes for the requested symbol."""

    log_quote_request()

    symbol = request.form.get('symbol')

    if not symbol:
        raise ApplicationException("Symbol is required.")

    values = applicationController.get_symbol_quotes(symbol)
    return values


if __name__ == "__main__":
    HOST = '0.0.0.0'
    port = os.environ.get('PORT')
    # Only for debugging while developing
    app.run(host=HOST, debug=True, port=port)
