import random
import time
from flask import Flask, render_template, request, session, redirect, url_for
from math import gcd

app = Flask(__name__)
app.secret_key = 'kelompok14'


def generate_elgamal_keys():
    p = 467  # Small prime for demonstration only 
    g = 2    # Generator
    private_key = random.randint(2, p - 2)
    public_key = (p, g, pow(g, private_key, p))
    return public_key, private_key

# Encrypt function with retry for invertibility issues
def elgamal_encrypt(plaintext, public_key):
    p, g, h = public_key
    encrypted_data = []

    # Start timing encryption
    start_time = time.perf_counter()
    
    for char in plaintext:
        while True:  # Retry if s is not invertible
            k = random.randint(1, p - 2)  # Random ephemeral key
            c1 = pow(g, k, p)
            s = pow(h, k, p)
            if gcd(s, p) == 1:  # Ensure s and p are coprime
                c2 = (ord(char) * s) % p
                encrypted_data.append((c1, c2))
                break
    
    # End timing encryption
    end_time = time.perf_counter()
    encryption_time = end_time - start_time  # Calculate encryption time
    
    return encrypted_data, encryption_time  # Return encrypted data and time

# Decrypt function to handle list of (c1, c2) pairs with modular inverse check
def elgamal_decrypt(encrypted_data, public_key, private_key):
    p, g, h = public_key
    decrypted_data = ''
    
    for c1, c2 in encrypted_data:
        s = pow(c1, private_key, p)
        if gcd(s, p) != 1:  # If s and p are not coprime, skip this decryption step
            raise ValueError("Modular inverse does not exist for this value, decryption failed.")
        s_inv = pow(s, -1, p)  # Modular inverse of s
        decrypted_char = chr((c2 * s_inv) % p)  # Convert back to character
        decrypted_data += decrypted_char  # Append each character to the result string
    
    return decrypted_data

# Generate ElGamal keys
public_key, private_key = generate_elgamal_keys()

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

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        credit_card = request.form['credit_card']  # Capture credit card as plain text
        expiry_date = request.form['expiry_date']
        cvc = request.form['cvc']
        
        # Encrypt expiry_date and cvc, and record encryption times
        encrypted_expiry_date, expiry_date_time = elgamal_encrypt(expiry_date, public_key)
        encrypted_cvc, cvc_time = elgamal_encrypt(cvc, public_key)
        
        # Decrypt the encrypted information
        decrypted_expiry_date = elgamal_decrypt(encrypted_expiry_date, public_key, private_key)
        decrypted_cvc = elgamal_decrypt(encrypted_cvc, public_key, private_key)
        
        # Format encryption times as decimal values with 6 decimal places
        encryption_times = {
            'expiry_date_time': f"{expiry_date_time:.6f}",
            'cvc_time': f"{cvc_time:.6f}"
        }

        # Passing encrypted, decrypted, and other payment info to the template
        return render_template('checkout.html', 
                               encrypted_payment={
                                   'expiry_date': encrypted_expiry_date,
                                   'cvc': encrypted_cvc
                               },
                               decrypted_payment={
                                   'expiry_date': decrypted_expiry_date,
                                   'cvc': decrypted_cvc
                               },
                               encryption_times=encryption_times, 
                               name=name, 
                               address=address, 
                               credit_card=credit_card)  # Pass credit card to template
    
    return render_template('checkout.html')

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('cart'))

# Route to show the public key for reference
@app.route('/show_public_key')
def show_public_key():
    return f"<pre>Public Key (p, g, h): {public_key}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
