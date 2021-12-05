#!/bin/env python3

""""Manages communication with AlphaVantage API."""

import logging
import requests

from eureka_stocks.exceptions import ApplicationException

OPEN_KEY = '1. open'
HIGH_KEY = '2. high'
LOW_KEY = '3. low'
CLOSE_KEY = '4. close'


class AlphaVantageController:
    """Handles communication with Alpha Vantage API"""

    def __init__(self, api_key: str):
        self.__api_key = api_key

    def __query_alphavantage(self, symbol: str) -> dict:
        """Sends requests to AV to requets the last 100 data points for a symbol.

        Values are returned in a dictionary. Only the time series data is returned.
        """

        try:
            payload = {'function': 'TIME_SERIES_DAILY',
                       'outputsize': 'compact',
                       'apikey': self.__api_key
                       }

            payload['symbol'] = symbol

            request = requests.get(
                'https://www.alphavantage.co/query', params=payload)

            json_response = request.json()

            if 'Error Message' in json_response.keys():
                raise ApplicationException(
                    f"Error retrieving data: {json_response['Error Message']}")
            return json_response['Time Series (Daily)']
        except Exception as exception:
            logging.exception(
                'Error retrieving data from AlphaVantage.')
            raise ApplicationException(exception) from exception

    def get_symbol_quotes(self, symbol: str) -> dict:
        """Returns the open, close, higher, lower, and the last 2 days
         variation for a single symbol.

        Values are returned in a dictionary.
        The variation is returned in absolute value in the two_day_variation field and in
        percentage in the two_day_variation_pct field.
        """
        values = self.__query_alphavantage(symbol)

        # In python 3.7+ dict keys keep their insertion order,
        # so because alphavantage returns the latest day's data first,
        # converting the dict keys to a list and getting the first one
        # is guaranteed to return the last days key.
        value_keys = list(values.keys())

        latest_day = value_keys[0]
        previous_day = value_keys[1]

        last = values[latest_day]
        prev = values[previous_day]

        last_close = float(last[CLOSE_KEY])
        prev_close = float(prev[CLOSE_KEY])
        variation = last_close - prev_close
        variation_pct = ((last_close - prev_close) / prev_close) * 100

        response = {
            'open': float(last[OPEN_KEY]),
            'close': float(last[CLOSE_KEY]),
            'high': float(last[HIGH_KEY]),
            'low': float(last[LOW_KEY]),
            'two_day_variation': variation,
            'two_day_variation_pct': variation_pct
        }

        return response
