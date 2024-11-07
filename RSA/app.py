import base64
import random
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'kelompok14'

# Simplified RSA key generation for educational purposes
def generate_rsa_keys():
    # Simple prime numbers for demonstration (NOT SECURE)
    p = 61
    q = 53
    n = p * q
    phi = (p - 1) * (q - 1)
    
    # Choose e (Public exponent) that is coprime with phi
    e = 17  # A common choice for e
    
    # Compute d (Private exponent)
    d = pow(e, -1, phi)
    
    return (e, n), (d, n)

# Encrypt function that returns Base64 encoded string
def rsa_encrypt(plaintext, public_key):
    e, n = public_key
    encrypted_data = [pow(ord(char), e, n) for char in plaintext]
    
    # Convert each encrypted integer to bytes and then encode in Base64
    encrypted_bytes = b''.join(enc_val.to_bytes((enc_val.bit_length() + 7) // 8, 'big') for enc_val in encrypted_data)
    base64_encoded = base64.b64encode(encrypted_bytes).decode('utf-8')
    return base64_encoded

# Decrypt function
def rsa_decrypt(encrypted_data, private_key):
    d, n = private_key
    # Decrypt each character
    decrypted_data = ''.join(chr(pow(char, d, n)) for char in encrypted_data)
    return decrypted_data

# Generate RSA keys
public_key, private_key = generate_rsa_keys()

# Sample catalog with description and image URL
catalog = [
    {'id': 1, 'name': 'Laptop', 'price': 1000, 'description': 'A high-performance laptop.', 'image': 'images/lappy.jpg'},
    {'id': 2, 'name': 'Monitor', 'price': 250, 'description': 'FHD 100% S-RGB 144 Hz Gaming Monitor.', 'image': 'images/monitor.jpg'},
    {'id': 3, 'name': 'Smartphone', 'price': 600, 'description': 'A smartphone with all the latest features.', 'image': 'images/phone.jpg'},
    {'id': 4, 'name': 'Headphones', 'price': 150, 'description': 'Noise-cancelling headphones for clear sound.', 'image': 'images/headphones.jpeg'},
    {'id': 5, 'name': 'Keyboard', 'price': 150, 'description': 'Gaming Keyboard.', 'image': 'images/keyboard.jpg'},
    {'id': 6, 'name': 'Mouse', 'price': 120, 'description': 'Gaming Mouse.', 'image': 'images/mouse.jpg'}
]

# Route for home/catalog page
@app.route('/')
def index():
    return render_template('index.html', catalog=catalog)

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total = sum(item['price'] for item in cart_items)  # Calculate total in server
    return render_template('cart.html', cart=cart_items, total=total)

# Add item to cart
@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    cart = session.get('cart', [])
    item = next((x for x in catalog if x['id'] == item_id), None)
    if item:
        cart.append(item)
        session['cart'] = cart
    return '', 204  # Empty response for AJAX

@app.route('/cart_count')
def cart_count():
    cart = session.get('cart', [])
    return {'count': len(cart)}

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    cart = session.get('cart', [])
    if item_id < len(cart):
        cart.pop(item_id)  # Remove item by index
        session['cart'] = cart
    return redirect(url_for('cart'))

# Route for checkout with manual RSA encryption
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        credit_card = request.form['credit_card']
        expiry_date = request.form['expiry_date']
        cvc = request.form['cvc']
        
        # Encrypt sensitive information manually and encode in Base64
        encrypted_credit_card = rsa_encrypt(credit_card, public_key)
        encrypted_expiry_date = rsa_encrypt(expiry_date, public_key)
        encrypted_cvc = rsa_encrypt(cvc, public_key)
        
        return render_template('checkout.html', 
                               encrypted_payment={
                                   'credit_card': encrypted_credit_card,
                                   'expiry_date': encrypted_expiry_date,
                                   'cvc': encrypted_cvc
                               }, 
                               name=name, address=address)
    
    return render_template('checkout.html')

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('cart'))

# Route to show the public key for reference
@app.route('/show_public_key')
def show_public_key():
    # Display public key in a readable format
    return f"<pre>Public Key (e, n): {public_key}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
