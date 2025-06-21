from flask import Flask, render_template, request, jsonify
import razorpay

app = Flask(__name__)

# Razorpay credentials
RAZORPAY_KEY_ID = "rzp_test_R9Ws9PUxiiqFlf"
RAZORPAY_KEY_SECRET = "nmXirZUnwSWDGEjP74zB8b4f"

# Initialize Razorpay client
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
booked_seats=[]

@app.route('/')
def home():
    return render_template('seat.html', razorpay_key=RAZORPAY_KEY_ID,booked_seats=booked_seats)

@app.route('/create_order', methods=['POST'])
def create_order():
    amount = request.json['amount']
    payment = client.order.create({
        "amount": amount * 100,  # Razorpay works with paise
        "currency": "INR",
        "payment_capture": '1'
    })
    return jsonify(order_id=payment['id'])

@app.route('/payment_success', methods=['POST'])
def payment_success():
    data = request.json
    print("Payment successful:", data)

    seats = data.get('seats', [])
    global booked_seats
    booked_seats.extend(seats)

    # Remove duplicates just in case
    booked_seats = list(set(booked_seats))

    return jsonify(success=True)

@app.route('/ticket')
def ticket():
    return "Your ticket has been generated. Booking confirmed!"

if __name__ == '__main__':
    app.run(debug=True)
