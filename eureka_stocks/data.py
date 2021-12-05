#!/bin/env python3

"""Manages communication with the Redis data store."""

import logging

import redis


class User():
    """"User data class."""

    def __init__(self, email: str, name: str, last_name: str):
        self.email = email
        self.name = name
        self.last_name = last_name


class DataController:
    """Redis communication controller class."""

    def __init__(self, redis_url):
        logging.debug("Connecting to redis in %s.", redis_url)

        self.__redis_client = redis.from_url(redis_url, decode_responses=True)

    def create_user(self, key: str, user: User, expire_time=0) -> str:
        """Creates a new user entry using the key parameter as key,
        an optional expire_time can be provided."""

        self.__redis_client.hset(key, 'email', user.email)
        self.__redis_client.hset(key, 'name', user.name)
        self.__redis_client.hset(key, 'last_name', user.last_name)

        if expire_time > 0:
            self.__redis_client.expire(key, expire_time)

    def add_email(self, email: str, expire_time=0):
        """Adds an email to the database keys, used to validate
        if a user has a pending validation."""
        self.__redis_client.set(email, 1)

        if expire_time > 0:
            self.__redis_client.expire(email, expire_time)

    def find_user(self, key: str) -> User:
        """Retrieves a user form the database."""

        user_data = self.__redis_client.hgetall(key)

        if not user_data:
            return None

        return User(user_data.get('email'), user_data.get('name'), user_data.get('last_name'))

    def delete_key(self, key: str):
        """Deletes a database entry."""
        self.__redis_client.delete(key)

    def check_key_exists(self, key: str) -> bool:
        """Verifies that a key exists in the database."""
        return key and self.__redis_client.exists(key)
