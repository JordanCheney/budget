import plaid
import datetime
import os
import twilio.rest

BALANCES_DB_NAME = 'balances.csv'
SAVINGS_DB_NAME = 'savings.csv'
DAILY_BUDGET=10000

def get_current_balances():
    plaid_client_id = os.getenv('PLAID_CLIENT_ID')
    plaid_secret = os.getenv('PLAID_SECRET')
    plaid_env = os.getenv('PLAID_ENV', 'sandbox')

    access_token1 = os.getenv('PLAID_ACCESS_TOKEN1')
    access_token2 = os.getenv('PLAID_ACCESS_TOKEN2')

    access_tokens = [access_token1, access_token2]

    client = plaid.Client(client_id=plaid_client_id,
                          secret=plaid_secret,
                          environment=plaid_env,
                          api_version='2019-05-29')

    balances = []
    for access_token in access_tokens:
        accounts = client.Accounts.balance.get(access_token=access_token)['accounts']

        balances = []
        for account in accounts:
            if account['type'] == 'credit':
                balance = int(account['balances']['current'] * 100) # Convert to cents because floats are stupid
                mask = account['mask']

                balances.append((mask, balance))

    return balances

def create_balances_db():
    with open(BALANCES_DB_NAME, 'w+') as f:
        f.write('Date,Mask,Balance\n')

def create_savings_db():
    with open(SAVINGS_DB_NAME, 'w+') as f:
        f.write('Date,Savings\n')

def get_previous_balances():
    masks = {}
    with open(BALANCES_DB_NAME, 'r') as f:
        f.readline() # Clear header
        for line in f:
            date, mask, balance = line.strip().split(',')
            masks[mask] = int(balance)

    return masks

def get_previous_savings():
    savings = 0
    with open(SAVINGS_DB_NAME, 'r') as f:
        f.readline()
        for line in f: # Get last line
            date, savings = line.strip().split(',')
            savings = int(savings)

    return savings

def get_daily_spend(previous_balances, current_balances):
    spends = {}
    for (mask, current_balance) in current_balances:
        previous_balance = previous_balances.get(mask, 0)
        spends[mask] = current_balance - previous_balance

    return spends

def send_update_message(total_spend, savings, new_savings):
    twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    mobile_number1 = os.getenv('MOBILE_NUMBER1')
    mobile_number2 = os.getenv('MOBILE_NUMBER2')

    dst_numbers = [mobile_number1, mobile_number2]

    message = 'Good morning! Yesterday you spent {0:.2f}.'.format(total_spend / 100)
    if total_spend > DAILY_BUDGET:
        message += ' That is over your daily budget and will decrease your savings by {0:.2f}.'.format((total_spend - DAILY_BUDGET) / 100)
    else:
        message += ' That is less than your daily budget and will increase your savings by {0:.2f}. Good job!'.format((DAILY_BUDGET - total_spend) / 100)

    message += ' Yesterday, you had {0:.2f} in savings. Now you have {1:.2f} in savings.'.format(
        savings / 100,
        new_savings / 100
    )

    client = twilio.rest.Client(twilio_account_sid, twilio_auth_token)

    for dst_number in dst_numbers:
        client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=dst_number
        )

def write_savings(savings):
    with open(SAVINGS_DB_NAME, 'a') as f:
        f.write('{date},{savings}\n'.format(
            date=datetime.datetime.now().strftime('%m/%d/%Y'),
            savings=savings
        ))

def write_balances(balances):
    with open(BALANCES_DB_NAME, 'a') as f:
        for mask, balance in balances:
            f.write('{date},{mask},{balance}\n'.format(
                date=datetime.datetime.now().strftime('%m/%d/%Y'),
                mask=mask,
                balance=balance
            ))

def main():
    if not os.path.exists(BALANCES_DB_NAME):
        create_balances_db()
    if not os.path.exists(SAVINGS_DB_NAME):
        create_savings_db()

    savings = get_previous_savings()

    previous_balances = get_previous_balances()
    current_balances = get_current_balances()
    daily_spend = get_daily_spend(previous_balances, current_balances)

    total_spend = 0
    for mask, spend in daily_spend.items():
        # Arbitrary threshold, greater than 500 should be a monthly payoff of the card,
        # less than that could be a normal return
        if spend < -500:
            continue

        total_spend += spend

    new_savings = savings + (DAILY_BUDGET - total_spend)

    send_update_message(total_spend, savings, new_savings)

    write_savings(new_savings)
    write_balances(current_balances)

if __name__ == '__main__':
    main()

