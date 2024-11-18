import random
import time
import tracemalloc  # Import tracemalloc for memory usage tracking
from flask import Flask, render_template, request, session, redirect, url_for
from math import gcd
import json
from markupsafe import Markup

# Define the escapejs filter
def escapejs(value):
    if isinstance(value, (dict, list)):
        value = json.dumps(value)  # Convert Python dict or list to JSON string
    return Markup(value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\'", "\\\'").replace("\n", "\\n")
                .replace("\r", "\\r").replace("\t", "\\t"))


app = Flask(__name__)
app.secret_key = 'kelompok14'
# Register the filter in Flask
app.jinja_env.filters['escapejs'] = escapejs


def generate_elgamal_keys():
    p = 467  # Small prime for demonstration only 
    g = 2    # Generator
    private_key = random.randint(2, p - 2)
    public_key = (p, g, pow(g, private_key, p))
    return public_key, private_key

# Encrypt function with retry for invertibility issues and memory usage tracking
def elgamal_encrypt(plaintext, public_key):
    p, g, h = public_key
    encrypted_data = []

    # Start timing and memory tracking
    tracemalloc.start()
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
    
    # End timing and memory tracking
    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    encryption_time = end_time - start_time  # Calculate encryption time
    memory_used = peak - current  # Peak memory used during the process

    return encrypted_data, encryption_time, memory_used

# Decrypt function to handle list of (c1, c2) pairs with modular inverse check and memory tracking
def elgamal_decrypt(encrypted_data, public_key, private_key):
    p, g, h = public_key
    decrypted_data = ''
    
    # Start memory tracking
    tracemalloc.start()
    
    for c1, c2 in encrypted_data:
        s = pow(c1, private_key, p)
        if gcd(s, p) != 1:  # If s and p are not coprime, skip this decryption step
            raise ValueError("Modular inverse does not exist for this value, decryption failed.")
        s_inv = pow(s, -1, p)  # Modular inverse of s
        decrypted_char = chr((c2 * s_inv) % p)  # Convert back to character
        decrypted_data += decrypted_char  # Append each character to the result string

    # Capture memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    memory_used = peak - current  # Peak memory used during the process

    return decrypted_data, memory_used

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
        
        # Encrypt expiry_date and cvc, and record encryption times and memory usage
        encrypted_expiry_date, expiry_date_time, expiry_date_memory = elgamal_encrypt(expiry_date, public_key)
        encrypted_cvc, cvc_time, cvc_memory = elgamal_encrypt(cvc, public_key)
        
        # Decrypt the encrypted information
        decrypted_expiry_date, expiry_date_memory_used = elgamal_decrypt(encrypted_expiry_date, public_key, private_key)
        decrypted_cvc, cvc_memory_used = elgamal_decrypt(encrypted_cvc, public_key, private_key)
        
        # Format memory usage and encryption times as decimal values with 6 decimal places
        encryption_details = {
            'expiry_date_time': f"{expiry_date_time:.6f}",
            'cvc_time': f"{cvc_time:.6f}",
            'expiry_date_memory': f"{expiry_date_memory / 1024:.2f} KB",
            'cvc_memory': f"{cvc_memory / 1024:.2f} KB",
            'expiry_date_memory_used': f"{expiry_date_memory_used / 1024:.2f} KB",
            'cvc_memory_used': f"{cvc_memory_used / 1024:.2f} KB"
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
                               encryption_details=encryption_details, 
                               name=name, 
                               address=address, 
                               credit_card=credit_card)  # Pass credit card to template
    
    return render_template('checkout.html')

@app.route('/performance')
def performance():
    trials = 10
    encryption_times = []
    decryption_times = []
    encryption_memories = []
    decryption_memories = []

    sample_data = "TestData"  # Sample plaintext for encryption and decryption

    for _ in range(trials):
        # Encryption Performance
        encrypted_data, encryption_time, encryption_memory = elgamal_encrypt(sample_data, public_key)
        encryption_times.append(encryption_time)
        encryption_memories.append(encryption_memory / 1024)  # Convert memory usage to KB

        # Decryption Performance
        _, decryption_memory = elgamal_decrypt(encrypted_data, public_key, private_key)
        decryption_times.append(encryption_time)  # Decryption time can be calculated here if required
        decryption_memories.append(decryption_memory / 1024)  # Convert memory usage to KB

    # Average Results
    avg_encryption_time = sum(encryption_times) / trials
    avg_decryption_time = sum(decryption_times) / trials
    avg_encryption_memory = sum(encryption_memories) / trials
    avg_decryption_memory = sum(decryption_memories) / trials

    # Data to Pass to Template
    performance_data = {
        "encryption_times": encryption_times,
        "decryption_times": decryption_times,
        "encryption_memories": encryption_memories,
        "decryption_memories": decryption_memories,
        "avg_encryption_time": avg_encryption_time,
        "avg_decryption_time": avg_decryption_time,
        "avg_encryption_memory": avg_encryption_memory,
        "avg_decryption_memory": avg_decryption_memory,
    }

    return render_template('performance.html', performance_data=performance_data)

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
