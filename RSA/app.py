import base64
import random
from flask import Flask, render_template, request, redirect, url_for, session
import time
import tracemalloc  # Import for memory tracking

app = Flask(__name__)
app.secret_key = 'kelompok14'

def generate_rsa_keys():
    p = 61
    q = 53
    n = p * q
    phi = (p - 1) * (q - 1)
    
    # Choose e (Public exponent) that is coprime with phi
    e = 17  # A common choice for e
    
    # Compute d (Private exponent)
    d = pow(e, -1, phi)
    
    return (e, n), (d, n)
 

def rsa_encrypt(plaintext, public_key):
    e, n = public_key
    tracemalloc.start()  # Start memory tracking
    start_time = time.perf_counter()
    
    # Encrypt each character as a separate integer
    encrypted_data = [pow(ord(char), e, n) for char in plaintext]
    
    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()  # Stop memory tracking
    
    encryption_time = end_time - start_time
    memory_used = peak - current  # Peak memory usage during encryption
    
    # Return the list of encrypted integers, time, and memory usage
    return encrypted_data, encryption_time, memory_used

def rsa_decrypt(encrypted_data, private_key):
    d, n = private_key
    tracemalloc.start()  # Start memory tracking
    
    # Decrypt each integer and convert back to characters
    decrypted_data = ''.join(chr(pow(char, d, n)) for char in encrypted_data)
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()  # Stop memory tracking
    
    memory_used = peak - current  # Peak memory usage during decryption
    return decrypted_data, memory_used


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

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        credit_card = request.form['credit_card']
        expiry_date = request.form['expiry_date']
        cvc = request.form['cvc']
        
        # Encrypt with RSA and measure encryption time and memory
        encrypted_credit_card_rsa, credit_card_time_rsa, credit_card_memory_rsa = rsa_encrypt(credit_card, public_key)
        encrypted_expiry_date_rsa, expiry_date_time_rsa, expiry_date_memory_rsa = rsa_encrypt(expiry_date, public_key)
        encrypted_cvc_rsa, cvc_time_rsa, cvc_memory_rsa = rsa_encrypt(cvc, public_key)
        
        # Decrypt the encrypted information to verify and measure memory
        decrypted_credit_card_rsa, credit_card_memory_used = rsa_decrypt(encrypted_credit_card_rsa, private_key)
        decrypted_expiry_date_rsa, expiry_date_memory_used = rsa_decrypt(encrypted_expiry_date_rsa, private_key)
        decrypted_cvc_rsa, cvc_memory_used = rsa_decrypt(encrypted_cvc_rsa, private_key)
        
        # Format encryption and memory usage as decimal values
        encryption_details_rsa = {
            'credit_card_time': f"{credit_card_time_rsa:.6f} seconds",
            'credit_card_memory': f"{credit_card_memory_rsa / 1024:.2f} KB",
            'expiry_date_time': f"{expiry_date_time_rsa:.6f} seconds",
            'expiry_date_memory': f"{expiry_date_memory_rsa / 1024:.2f} KB",
            'cvc_time': f"{cvc_time_rsa:.6f} seconds",
            'cvc_memory': f"{cvc_memory_rsa / 1024:.2f} KB",
        }

        # Pass encrypted data, decrypted data, and encryption times/memory to the template
        return render_template('checkout.html', 
                               encrypted_payment_rsa={
                                   'credit_card': encrypted_credit_card_rsa,
                                   'expiry_date': encrypted_expiry_date_rsa,
                                   'cvc': encrypted_cvc_rsa
                               },
                               decrypted_payment_rsa={
                                   'credit_card': decrypted_credit_card_rsa,
                                   'expiry_date': decrypted_expiry_date_rsa,
                                   'cvc': decrypted_cvc_rsa
                               },
                               encryption_details_rsa=encryption_details_rsa, 
                               name=name, address=address)
    
    return render_template('checkout.html')

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('cart'))

# Route to show the public key for reference
@app.route('/show_public_key')
def show_public_key():
    return f"<pre>Public Key (e, n): {public_key}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
