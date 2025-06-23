from flask import Flask, redirect, request, render_template_string
import requests
import json
import time

app = Flask(__name__)

# Set your test credentials here directly
CASHFREE_APP_ID = "TEST10666540f5007316480c6a46b6f404566601"
CASHFREE_SECRET_KEY = "cfsk_ma_test_9bea185d75db4d0bceaa0cce549f021e_5356019f"

@app.route('/')
def index():
    order_id = f"order_{int(time.time())}"
    url = "https://sandbox.cashfree.com/pg/orders"

    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2023-08-01",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "order_id": order_id,
        "order_amount": 100,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": "cust_001",
            "customer_email": "test@example.com",
            "customer_phone": "9999999999"
        },
        "order_meta": {
            "return_url": f"http://localhost:5000/payment_success?order_id={order_id}"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("Cashfree response:", response.status_code, response.text)
        
        if response.status_code == 200:
            data = response.json()
            payment_session_id = data["payment_session_id"]
            
            # Method 1: Direct redirect to Cashfree checkout (simplest)
            checkout_url = f"https://sandbox.cashfree.com/pg/view/sessions/checkout"
            
            # Create a form that auto-submits to Cashfree
            form_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Redirecting to Payment...</title>
            </head>
            <body>
                <div style="text-align: center; margin-top: 50px;">
                    <h3>Redirecting to payment gateway...</h3>
                    <p>Please wait while we redirect you to the payment page.</p>
                </div>
                <form id="redirectForm" action="{checkout_url}" method="post">
                    <input type="hidden" name="payment_session_id" value="{payment_session_id}">
                </form>
                <script>
                    document.getElementById('redirectForm').submit();
                </script>
            </body>
            </html>
            """
            return form_html
            
        else:
            print(f"Error response: {response.status_code} - {response.text}")
            return f"Error creating order: {response.text}", 400
            
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return f"Exception: {str(e)}", 500

@app.route('/payment_success')
def payment_success():
    order_id = request.args.get("order_id")
    
    # Verify the payment status by calling Cashfree's order status API
    if order_id:
        verification_result = verify_payment(order_id)
        if verification_result:
            return f"""
            <h2>Payment Successful!</h2>
            <p>Order ID: {order_id}</p>
            <p>Payment Status: {verification_result.get('order_status', 'Unknown')}</p>
            <p>Amount: ₹{verification_result.get('order_amount', 'Unknown')}</p>
            """
        else:
            return f"Payment verification failed for Order ID: {order_id}"
    else:
        return "No order ID provided"

def verify_payment(order_id):
    """Verify payment status with Cashfree"""
    url = f"https://sandbox.cashfree.com/pg/orders/{order_id}"
    
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2023-08-01",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Payment verification failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception during payment verification: {str(e)}")
        return None

# Alternative route using Cashfree JS SDK (recommended approach)
@app.route('/checkout')
def checkout():
    order_id = f"order_{int(time.time())}"
    url = "https://sandbox.cashfree.com/pg/orders"

    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2023-08-01",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "order_id": order_id,
        "order_amount": 100,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": "cust_001",
            "customer_email": "test@example.com",
            "customer_phone": "9999999999"
        },
        "order_meta": {
            "return_url": f"http://localhost:5000/payment_success?order_id={order_id}"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            payment_session_id = data["payment_session_id"]
            
            # Use Cashfree JS SDK for better integration
            checkout_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Cashfree Checkout</title>
                <script src="https://sdk.cashfree.com/js/v3/cashfree.js"></script>
            </head>
            <body>
                <div style="text-align: center; margin-top: 50px;">
                    <h3>Processing Payment...</h3>
                    <button id="payButton" onclick="initiatePayment()">Pay Now ₹100</button>
                </div>
                
                <script>
                    const cashfree = Cashfree({{
                        mode: "sandbox"
                    }});
                    
                    function initiatePayment() {{
                        const checkoutOptions = {{
                            paymentSessionId: "{payment_session_id}",
                            returnUrl: "http://localhost:5000/payment_success?order_id={order_id}"
                        }};
                        
                        cashfree.checkout(checkoutOptions).then(function(result) {{
                            if (result.error) {{
                                console.error(result.error);
                                alert("Payment failed: " + result.error.message);
                            }}
                        }});
                    }}
                    
                    // Auto-trigger payment
                    setTimeout(initiatePayment, 1000);
                </script>
            </body>
            </html>
            """
            return checkout_html
            
        else:
            return f"Error creating order: {response.text}", 400
            
    except Exception as e:
        return f"Exception: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)