from flask import Flask, render_template, request, redirect
import requests
import uuid
#import os
#from dotenv import load_dotenv

app = Flask(__name__)

# Cashfree test credentials
APP_ID = "TEST10666540f5007316480c6a46b6f404566601"
SECRET_KEY = "cfsk_ma_test_9bea185d75db4d0bceaa0cce549f021e_5356019f"
CASHFREE_API_URL = 'https://sandbox.cashfree.com/pg/links'

SUPABASE_URL = "https://fqupeaniwcakcyklmykb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZxdXBlYW5pd2Nha2N5a2xteWtiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA5NDIxNzIsImV4cCI6MjA2NjUxODE3Mn0.5vdhoQRX2OEWM-CrXvR3sLrQJiIF8vMBscKGMp70rOo"

headers = {
        "x-api-version": "2022-09-01",
        "x-client-id": APP_ID,
        "x-client-secret": SECRET_KEY,
        "Content-Type": "application/json"
    }

@app.route('/')
def home():
    return render_template('seat.html')

@app.route('/pay', methods=['POST'])
def pay():
    #name = request.form['name']
    #email = request.form['email']
    #phone = request.form['phone']
    name="Arya"
    email='maskuaravind29@gmail.com'
    phone='8179326983'
    amount = request.form.get('total_amount')
    
    order_id = str(uuid.uuid4())[:8]  # unique id
    
    payload = {
        "customer_details": {
            "customer_id": name,
            "customer_email": email,
            "customer_phone": phone
        },
        "link_id": order_id,
        "link_amount": float(amount),
        "link_currency": "INR",
        "link_note": "Test Payment",
        "link_purpose": "Product Purchase",
        "link_notify": {
        "send_sms": True,
        "send_email": False
    },
        "link_meta": {
            "return_url": f"http://127.0.0.1:5000/callback?order_id={order_id}",
            "upi_intent": False
        }
    }

    

    response = requests.post(CASHFREE_API_URL, json=payload, headers=headers)
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)

    try:
        response_data = response.json()
        payment_link = response_data.get('payment_link') or response_data.get('link_url')
        print("payment LINK",payment_link)

        if payment_link:
            return redirect(payment_link)
        else:
            return f"<h3>Failed to get payment link</h3><pre>{response_data}</pre>", 500
    except Exception as e:
        return f"<h3>Error processing payment link:</h3><pre>{str(e)}</pre>", 500



@app.route('/callback')
def callback():
    #import requests
    link_id = request.args.get('order_id')  # or 'link_id', depends on what you passed

    status_url = f"https://sandbox.cashfree.com/pg/links/{link_id}"
    response = requests.get(status_url, headers=headers)
    data = response.json()

    print("Payment Verification:", data)

    payment_status = data.get("link_status")  # It will be PAID, UNPAID, etc.

    if payment_status == "PAID":
        return render_template('success.html')
    else:
        return render_template('fail.html')


if __name__ == '__main__':
    app.run(debug=True)
