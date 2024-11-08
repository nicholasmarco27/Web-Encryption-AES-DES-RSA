import base64
import random
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'kelompok14'

# Simplified ElGamal key generation for educational purposes
def generate_elgamal_keys():
    # Small prime and generator for demonstration (NOT SECURE)
    p = 467  # Prime number (in practice, this should be large)
    g = 2    # Generator (primitive root modulo p)
    
    # Private key is a random integer less than p
    private_key = random.randint(2, p - 2)
    
    # Public key is (p, g, g^private_key mod p)
    public_key = (p, g, pow(g, private_key, p))
    
    return public_key, private_key

# Encrypt function that returns Base64 encoded string
def elgamal_encrypt(plaintext, public_key):
    p, g, h = public_key
    encrypted_data = []
    
    for char in plaintext:
        k = random.randint(1, p - 2)  # Random ephemeral key
        c1 = pow(g, k, p)
        c2 = (ord(char) * pow(h, k, p)) % p
        encrypted_data.append((c1, c2))
    
    # Convert pairs to bytes and encode in Base64
    encrypted_bytes = b''.join(c1.to_bytes((c1.bit_length() + 7) // 8, 'big') + c2.to_bytes((c2.bit_length() + 7) // 8, 'big') for c1, c2 in encrypted_data)
    base64_encoded = base64.b64encode(encrypted_bytes).decode('utf-8')
    return base64_encoded

# Decrypt function
def elgamal_decrypt(encrypted_data, public_key, private_key):
    p, g, h = public_key
    encrypted_bytes = base64.b64decode(encrypted_data)
    decrypted_data = ''
    
    # Each character has two parts, c1 and c2
    for i in range(0, len(encrypted_bytes), 4):
        c1 = int.from_bytes(encrypted_bytes[i:i+2], 'big')
        c2 = int.from_bytes(encrypted_bytes[i+2:i+4], 'big')
        s = pow(c1, private_key, p)
        s_inv = pow(s, -1, p)  # Modular inverse of s
        decrypted_char = (c2 * s_inv) % p
        decrypted_data += chr(decrypted_char)
    
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

# Route for checkout with manual ElGamal encryption
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        credit_card = request.form['credit_card']
        expiry_date = request.form['expiry_date']
        cvc = request.form['cvc']
        
        # Encrypt sensitive information manually and encode in Base64
        encrypted_credit_card = elgamal_encrypt(credit_card, public_key)
        encrypted_expiry_date = elgamal_encrypt(expiry_date, public_key)
        encrypted_cvc = elgamal_encrypt(cvc, public_key)
        
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
    return f"<pre>Public Key (p, g, h): {public_key}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
