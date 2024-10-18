from flask import Flask, render_template, request, redirect, url_for, session
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Generate RSA keys
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
public_key = private_key.public_key()

# Sample catalog
# Sample catalog with description and image URL
catalog = [
    {'id': 1, 'name': 'Laptop', 'price': 1000, 'description': 'A high-performance laptop for all your needs.', 'image': 'images/lappy.jpg'},
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
    total = sum(item['price'] for item in cart_items)  # Hitung total di server
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
        cart.pop(item_id)  # Hapus item berdasarkan indeksnya
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
        
        # Encrypt credit card number
        encrypted_credit_card = public_key.encrypt(
            credit_card.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Encrypt expiry date
        encrypted_expiry_date = public_key.encrypt(
            expiry_date.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Encrypt CVC (typically not stored long-term)
        encrypted_cvc = public_key.encrypt(
            cvc.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        encrypted_credit_card_b64 = base64.b64encode(encrypted_credit_card).decode()
        encrypted_expiry_date_b64 = base64.b64encode(encrypted_expiry_date).decode()
        encrypted_cvc_b64 = base64.b64encode(encrypted_cvc).decode()
        
        return render_template('checkout.html', 
                               encrypted_payment={
                                   'credit_card': encrypted_credit_card_b64,
                                   'expiry_date': encrypted_expiry_date_b64,
                                   'cvc': encrypted_cvc_b64
                               }, 
                               name=name, address=address)
    
    return render_template('checkout.html')

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('cart'))




if __name__ == '__main__':
    app.run(debug=True)
