from flask import Flask, render_template, request, jsonify
import requests
import json
import time
import os

app = Flask(__name__)

# Cashfree credentials
CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET_KEY = os.getenv("CASHFREE_SECRET_KEY")
CASHFREE_BASE_URL = "https://sandbox.cashfree.com/pg"

booked_seats = []

@app.route('/')
def home():
    return render_template('seat.html', booked_seats=booked_seats)

@app.route('/create_order', methods=['POST'])
def create_order():
    try:
        # Accept JSON or form input
        data = request.get_json(force=True) or request.form
        print("Incoming create_order data:", data)

        amount = data.get('amount')
        if not amount:
            return jsonify({"error": "Missing amount"}), 400

        headers = {
            "x-client-id": CASHFREE_APP_ID,
            "x-client-secret": CASHFREE_SECRET_KEY,
            "x-api-version": "2022-09-01",
            "Content-Type": "application/json"
        }

        order_id = "order_" + str(request.remote_addr).replace('.', '_') + str(int(time.time()))
        payload = {
            "order_amount": amount,
            "order_currency": "INR",
            "order_id": order_id,
            "customer_details": {
                "customer_id": "cust_001",
                "customer_email": "test@example.com",
                "customer_phone": "9999999999"
            },
            "order_meta": {
                "return_url": f"http://{request.host}/payment_success?order_id={order_id}"
            }
        }

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
    return f"Payment successful! Booking confirmed for Order ID: {order_id}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
