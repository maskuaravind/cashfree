from flask import Flask, render_template, request, jsonify
import requests
import json
import time

app = Flask(__name__)

# Cashfree credentials (LIVE keys)
CASHFREE_APP_ID = "TEST10666540f5007316480c6a46b6f404566601"
CASHFREE_SECRET_KEY = "cfsk_ma_test_57e0cbd4b9e148da4cbd007b59336dc8_c9b8cc84"
CASHFREE_BASE_URL = "https://sandbox.cashfree.com/pg"

booked_seats = []

@app.route('/')
def home():
    return render_template('seat.html', booked_seats=booked_seats)

@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    amount = data['amount']

    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2022-09-01",
        "Content-Type": "application/json"
    }

    payload = {
        "order_amount": amount,
        "order_currency": "INR",
        "order_id": "order_" + str(request.remote_addr).replace('.', '_') + str(int(time.time())),
        "customer_details": {
            "customer_id": "cust_001",
            "customer_email": "test@example.com",
            "customer_phone": "9999999999"
        },
        "order_meta": {
            "return_url": "https://fair-chicken-battle.loca.lt/payment_success?order_id={order_id}"
        }
    }

    try:
        response = requests.post(f"{CASHFREE_BASE_URL}/orders", headers=headers, data=json.dumps(payload))
        print("Response code:", response.status_code)
        print("Response body:", response.text)

        if response.status_code == 200:
            res_data = response.json()
            session_id = res_data.get("payment_session_id")
            if session_id:
                payment_link = f"https://payments.cashfree.com/pg/checkout?payment_session_id={session_id}"
                return jsonify(payment_link=payment_link)
            else:
                return jsonify({"error": "No session_id returned from Cashfree"}), 400
        else:
            return jsonify({"error": "Cashfree order creation failed"}), 400

    except Exception as e:
        print("Exception:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route('/payment_success')
def payment_success():
    order_id = request.args.get("order_id")
    # In real app: verify order status via Cashfree API
    return "Payment successful! Booking confirmed."

if __name__ == '__main__':
    app.run(debug=True)
