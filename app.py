from flask import Flask, render_template, request, jsonify
import requests
import json
import time
import os
import uuid

app = Flask(__name__)

# Cashfree credentials
CASHFREE_APP_ID = os.environ.get("CASHFREE_APP_ID")
CASHFREE_SECRET_KEY = os.environ.get("CASHFREE_SECRET_KEY")
CASHFREE_BASE_URL = "https://sandbox.cashfree.com/pg"

print("CASHFREE_APP_ID:", CASHFREE_APP_ID)
print("CASHFREE_SECRET_KEY:", CASHFREE_SECRET_KEY[:10] + "..." if CASHFREE_SECRET_KEY else None)

# In-memory storage for booked seats (use database in production)
booked_seats = []

@app.route('/')
def home():
    return render_template('seat.html', booked_seats=booked_seats)

@app.route('/create_order', methods=['POST'])
def create_order():
    print("create_order route hit")
    try:
        data = request.get_json(force=True) or request.form
        print("Incoming create_order data:", data)

        amount = data.get('amount')
        seats = data.get('seats', [])
        
        if not amount:
            return jsonify({"error": "Missing amount"}), 400
        
        if not seats:
            return jsonify({"error": "No seats selected"}), 400

        # Check if any selected seats are already booked
        conflicting_seats = [seat for seat in seats if seat in booked_seats]
        if conflicting_seats:
            return jsonify({"error": f"Seats {conflicting_seats} are already booked"}), 400

        url = f"{CASHFREE_BASE_URL}/orders"
        headers = {
            "x-client-id": CASHFREE_APP_ID,
            "x-client-secret": CASHFREE_SECRET_KEY,
            "x-api-version": "2025-01-01",  # Updated to latest version
            "Content-Type": "application/json"
        }

        # Generate unique order_id
        order_id = "order_" + str(uuid.uuid4()).replace('-', '_')[:20]
        
        payload = {
            "order_id": order_id,  # Added required order_id
            "order_amount": float(amount),
            "order_currency": "INR",
            "customer_details": {
                "customer_id": "cust_" + str(int(time.time())),
                "customer_email": "test@example.com",
                "customer_phone": "9999999999"
            },
            "order_meta": {
                "return_url": f"https://cash-1rwc.onrender.com/payment_success?order_id={order_id}&seats={','.join(map(str, seats))}"
            },
            "order_note": f"Seat booking for seats: {', '.join(map(str, seats))}"
        }

        response = requests.post(url, headers=headers, json=payload)
        print("Response code:", response.status_code)
        print("Response body:", response.text)

        if response.status_code == 200:
            res_data = response.json()
            payment_session_id = res_data.get("payment_session_id")
            if payment_session_id:
                checkout_link = f"https://sandbox.cashfree.com/pg/checkout?payment_session_id={payment_session_id}"
                return jsonify({
                    "checkout_link": checkout_link,
                    "order_id": order_id,
                    "payment_session_id": payment_session_id
                })
            else:
                return jsonify({"error": "No payment_session_id returned"}), 400
        else:
            error_data = response.json() if response.content else {}
            return jsonify({
                "error": "Cashfree order creation failed", 
                "details": error_data.get("message", response.text)
            }), 400

    except Exception as e:
        print("Exception:", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/payment_success')
def payment_success():
    order_id = request.args.get("order_id")
    seats_param = request.args.get("seats")
    
    if not order_id:
        return "Error: Missing order ID", 400
    
    # Verify payment status with Cashfree
    try:
        url = f"{CASHFREE_BASE_URL}/orders/{order_id}"
        headers = {
            "x-client-id": CASHFREE_APP_ID,
            "x-client-secret": CASHFREE_SECRET_KEY,
            "x-api-version": "2025-01-01"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            order_data = response.json()
            order_status = order_data.get("order_status")
            
            if order_status == "PAID":
                # Payment successful, book the seats
                if seats_param:
                    seats = [int(seat) for seat in seats_param.split(',')]
                    # Add seats to booked_seats (avoid duplicates)
                    for seat in seats:
                        if seat not in booked_seats:
                            booked_seats.append(seat)
                    
                    return f"""
                    <html>
                    <head><title>Payment Successful</title></head>
                    <body>
                        <h1>Payment Successful!</h1>
                        <p>Booking confirmed for Order ID: {order_id}</p>
                        <p>Seats booked: {', '.join(map(str, seats))}</p>
                        <p>Total amount: ₹{order_data.get('order_amount', 'N/A')}</p>
                        <a href="/">Book more seats</a>
                    </body>
                    </html>
                    """
                else:
                    return f"Payment successful! Booking confirmed for Order ID: {order_id}"
            else:
                return f"Payment not completed. Order status: {order_status}. Please try again."
        else:
            return f"Error verifying payment status. Please contact support with Order ID: {order_id}"
            
    except Exception as e:
        print(f"Error verifying payment: {e}")
        return f"Error verifying payment. Please contact support with Order ID: {order_id}"

@app.route('/check_order_status/<order_id>')
def check_order_status(order_id):
    """API endpoint to check order status"""
    try:
        url = f"{CASHFREE_BASE_URL}/orders/{order_id}"
        headers = {
            "x-client-id": CASHFREE_APP_ID,
            "x-client-secret": CASHFREE_SECRET_KEY,
            "x-api-version": "2025-01-01"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to fetch order status"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_booked_seats')
def get_booked_seats():
    """API endpoint to get currently booked seats"""
    return jsonify({"booked_seats": booked_seats})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)