# Budget

Budget is a python script that queries linked credit cards to track daily spending, compares spending against
a daily budget, and tracks long term savings. It was created because I couldn't find any application that
does this.

## Financial Information

Budget stores your daily spending and savings information in plain-text CSV files. This is personal information and should be treated with care! Run budget in an environment you control access to.

## Secrets

Budget uses Plaid to link with your bank and Twilio to send text messages. You must create a `secrets.env` file in the project root with account information for both services. The file should look like

    export PLAID_CLIENT_ID=<>
    export PLAID_SECRET=<>
    export TWILIO_ACCOUNT_SID=<>
    export TWILIO_AUTH_TOKEN=<>
    export TWILIO_PHONE_NUMBER=<>
    export MOBILE_NUMBER1=<>

## Linking bank accounts

Linked banked accounts are managed within your plaid account. To link an account, run the flask app in server/ open your web browser and use you financial institution credentials to link the account. Account information is never stored outside of Plaid
