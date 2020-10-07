#!/bin/bash

source "secrets.env"

export PLAID_ENV='development'
export PLAID_PRODUCTS='transactions'
export PLAID_COUNTRY_CODES='US'

python3 app.py
