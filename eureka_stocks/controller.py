#!/bin/env python3

"""Main application controller."""

import threading
import uuid
import re
import logging

from eureka_stocks.alphavantage import AlphaVantageController
from eureka_stocks.exceptions import ApplicationException
from eureka_stocks.data import DataController, User
from eureka_stocks.mail import EmailController


EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
DEFAULT_KEY_EXPIRE_TIME = 600


class EurekaStocksController:
    """Main application controller class."""

    def __init__(self,
                 redis_url,
                 sendgrid_api_key,
                 alpha_vantage_api_key,
                 from_email,
                 external_address,
                 application_name):
        self.__data_controller = DataController(redis_url)

        self.__email_controller = EmailController(sendgrid_api_key,
                                                  from_email,
                                                  external_address,
                                                  application_name)

        self.__alpha_vantage_controller = AlphaVantageController(
            alpha_vantage_api_key)

        self.__locks = {}
        self.__locks_lock = threading.Lock()

    def __get_lock(self, key):
        with self.__locks_lock:
            if key not in self.__locks:
                self.__locks[key] = threading.Lock()

            return self.__locks[key]

    def create_temporary_user(self, email, name, last_name):
        """Creates a user with an expiry time of 10 minutes.

        Create a user and sends the validation key by email. If the user is not validated in
        the next 10 minutes, it is removed from the database and must register again to
        get an API key.
        """

        if not name or not last_name or not email:
            raise ApplicationException(
                'Required fields: name, last_name, email.')

        if not re.fullmatch(EMAIL_REGEX, email):
            raise ApplicationException(f'Invalid email address: {email}.')

        try:
            if self.check_key_exists(email):
                raise ApplicationException(
                    'User is already registered or has a pending validation.')

            self.__data_controller.add_email(
                email, expire_time=DEFAULT_KEY_EXPIRE_TIME)

            validation_key = str(uuid.uuid4())

            new_user = User(email, name, last_name)
            self.__data_controller.create_user(
                validation_key, new_user, expire_time=DEFAULT_KEY_EXPIRE_TIME)

            self.__email_controller.send_validation_email(
                validation_key, new_user)
        except Exception as exception:
            logging.exception('Error creating user.')
            raise ApplicationException(
                f'Error creating user: {exception}') from exception

    def validate_and_create_key(self, validation_key):
        """Recieves a validation key that means that the user can be validated.

        A new API key is generated and sent by email to the user.
        Validated users are copied from their temporary location to a permanent one
        using their API key as database key.
        """

        if not validation_key:
            raise ApplicationException("Validation key required.")

        with self.__get_lock(validation_key):
            user = self.__data_controller.find_user(validation_key)

            if not user:
                raise ApplicationException("Validation key not found.")

            new_api_key = str(uuid.uuid4())

            self.__data_controller.create_user(new_api_key, user)

            self.__email_controller.send_api_key_email(new_api_key, user)

            self.__data_controller.delete_key(validation_key)

            # Delete the email and re-add it without expire time so
            # the same email cannot be used more than once.
            self.__data_controller.delete_key(user.email)

            self.__data_controller.add_email(
                user.email)

    def check_key_exists(self, api_key: str) -> bool:
        """Verifies that a key exists in the database."""
        return self.__data_controller.check_key_exists(api_key)

    def get_symbol_quotes(self, symbol: str) -> dict:
        """Returns the last day's data for a stock symbol in a dictionary."""
        try:
            return self.__alpha_vantage_controller.get_symbol_quotes(symbol)
        except Exception as exception:
            logging.exception('Error retrieving quotes.')
            raise ApplicationException(exception) from exception
