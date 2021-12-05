#!/bin/env python3

"""Handles email sending."""

import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import render_template_string

from eureka_stocks.data import User

EMAIL_BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <body style="margin: 0 auto; font-family: Helvetica, sans-serif; color: #333333; text-align: center; max-width: 520px; padding: 0 20px;">
        {}
    </div>
  </body>
</html>
"""

VALIDATION_EMAIL_TEMPLATE = EMAIL_BASE_TEMPLATE.format("""
    <div style="font-size: 16px; text-align: left;">
      <div style="line-height: 150%;">
        <div style="font-size: 20px;">Hi {{ name }},</div>

        <div style="margin: 15px 0;">
          Thanks for creating an {{ application_name }} account. Please verify your email address by clicking the button below.
        </div>

      </div>
      <div>
        <a
          href="{{ validation_url }}"
          style="background:#007bff;
           padding: 9px;
           width: 200px;
           color:#fff;
           text-decoration: none;
           display: inline-block;
           font-weight: bold;
           text-align: center;
           cursor: pointer;
           letter-spacing: 0.5px;
           border-radius: 4px;"
          >Verify email address
        </a>
      </div>
      <div style="line-height: 150%;">
        <div style="color:#828282; margin: 15px 0 75px;">
          - The {{ application_name}} Team
        </div>
      </div>
        """)

KEY_EMAIL_TEMPLATE = EMAIL_BASE_TEMPLATE.format("""
    <div style="font-size: 16px; text-align: left;">
      <div style="line-height: 150%;">
        <div style="font-size: 20px;">Hi {{ name }},</div>

        <div style="margin: 15px 0;">
          Your personal api key for {{ application_name }} is
          <p>
            <bold>{{ api_key }}</bold>
          </p>
        </div>
        <div style="margin: 15px 0;">
          In order to use it, it must be sent in the <bold>API_KEY</bold> header.
        </div>
        <div style="margin: 15px 0;">
        You can request quotes for different symbols with the following url format:
        {{ request_url }}

        And pass the desired symbol in the request body with the format
        symbol=[SYMBOL]

        for example:
        
        symbol=AAPL
        </div>
      </div>
      <div style="line-height: 150%;">
        <div style="color:#828282; margin: 15px 0 75px;">
          - The {{ application_name}} Team
        </div>
      </div>
        """)


class EmailController:
    """Class that handles communication with SendGrid"""

    def __init__(self, sendgrid_api_key,
                 from_email,
                 application_external_address,
                 application_name):
        self.__sendgrid_api_key = sendgrid_api_key
        self.__from_email = from_email
        self.__application_external_address = application_external_address
        self.__application_name = application_name

    def __send_email(self, address, subject, body):
        """Sends an email using Sendgrid's API."""
        logging.debug("Sending email to %s.", address)

        message = Mail(
            from_email=self.__from_email,
            to_emails=address,
            subject=subject,
            html_content=body)

        try:
            sendgrid = SendGridAPIClient(self.__sendgrid_api_key)
            response = sendgrid.send(message)

            logging.debug(response.status_code)
            logging.debug(response.body)
            logging.debug(response.headers)
        except Exception as exception:
            print(exception)

    def send_validation_email(self, validation_key: str, user: User):
        """Sends an email to the user using the Validation template."""
        logging.debug("Sending validation email.")

        validation_url = f"{self.__application_external_address}/validate?id={validation_key}"

        subject = f"{self.__application_name} email validation"

        body = render_template_string(VALIDATION_EMAIL_TEMPLATE,
                                      name=user.name,
                                      application_name=self.__application_name,
                                      validation_url=validation_url)

        self.__send_email(user.email, subject, body)

    def send_api_key_email(self, api_key: str, user: User):
        """Sends an email to the user using the new API key template."""
        logging.debug("Sending api key email.")

        request_example = f"{self.__application_external_address}/get_stock"

        subject = f"{self.__application_name} api key"

        body = render_template_string(KEY_EMAIL_TEMPLATE,
                                      name=user.name,
                                      api_key=api_key,
                                      application_name=self.__application_name,
                                      request_url=request_example)

        self.__send_email(user.email, subject, body)
