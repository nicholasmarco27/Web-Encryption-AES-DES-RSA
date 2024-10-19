from flask import Flask, render_template, request, redirect, url_for, flash
from Crypto.Cipher import AES, DES
from Crypto.Util.Padding import pad, unpad
import base64
import os
import bleach

app = Flask(__name__)
app.secret_key = 'crypt0gr4phy_1s_fun_18_42'

# List untuk menyimpan catatan (sebagai pengganti database)
notes = []

# AES 128-bit Encryption
def aes_encrypt(plain_text, key):
    key = key.ljust(16)[:16].encode('utf-8')  # Ensure key is 16 bytes
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    encrypted_data = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))
    result = base64.b64encode(iv + encrypted_data).decode('utf-8')
    return result

# AES 128-bit Decryption
def aes_decrypt(encrypted_text, key):
    key = key.ljust(16)[:16].encode('utf-8')
    encrypted_text = base64.b64decode(encrypted_text)
    iv = encrypted_text[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(encrypted_text[AES.block_size:]), AES.block_size)
    return decrypted_data.decode('utf-8')

# DES Encryption
def des_encrypt(plain_text, key):
    key = key.ljust(8)[:8].encode('utf-8')  # Ensure key is 8 bytes
    cipher = DES.new(key, DES.MODE_CBC)
    iv = cipher.iv
    encrypted_data = cipher.encrypt(pad(plain_text.encode('utf-8'), DES.block_size))
    result = base64.b64encode(iv + encrypted_data).decode('utf-8')
    return result

# DES Decryption
def des_decrypt(encrypted_text, key):
    key = key.ljust(8)[:8].encode('utf-8')
    encrypted_text = base64.b64decode(encrypted_text)
    iv = encrypted_text[:DES.block_size]
    cipher = DES.new(key, DES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(encrypted_text[DES.block_size:]), DES.block_size)
    return decrypted_data.decode('utf-8')

# Route for index page
@app.route('/')
def index():
    return render_template('index.html', notes=notes)

# Route for viewing a note
@app.route('/view_note/<int:note_id>', methods=['GET', 'POST'])
def view_note(note_id):
    note = notes[note_id]  # Ambil catatan berdasarkan ID
    if request.method == 'POST':
        input_password = request.form['password']
        # Cek apakah password yang dimasukkan benar
        if note['importance'] == 'penting':
            decrypted_password = aes_decrypt(note['encrypted_password'], input_password)
        else:
            decrypted_password = des_decrypt(note['encrypted_password'], input_password)

        if decrypted_password == input_password:
            return render_template('view_note.html', note=note, note_id=note_id)
        else:
            flash('Password yang anda masukkan salah, coba lagi.', 'danger')
            return redirect(url_for('view_note', note_id=note_id))  # Redirect untuk menampilkan pesan flash

    return render_template('view_note.html', note=None)


# Route for creating/editing a note
@app.route('/create_note', methods=['GET', 'POST'])
@app.route('/create_note/<int:note_id>', methods=['GET', 'POST'])
def create_note(note_id=None):
    if note_id is not None:
        note = notes[note_id]  # Ambil catatan yang akan diedit
    else:
        note = None

    if request.method == 'POST':
        title = bleach.clean(request.form['title'])
        importance = request.form['importance']
        content = bleach.clean(request.form['content'])
        password = request.form['password']

        # Enkripsi password berdasarkan kepentingan catatan
        if importance == 'penting':
            encrypted_password = aes_encrypt(password, password)
        else:
            encrypted_password = des_encrypt(password, password)

        if note_id is not None:  # Jika kita mengedit catatan yang ada
            # Update catatan yang ada
            notes[note_id] = {
                'title': title,
                'importance': importance,
                'content': content,
                'encrypted_password': encrypted_password,
                'is_locked': True if importance == 'penting' else False
            }
            flash(f"Catatan '{title}' berhasil diperbarui!", "success")
        else:
            # Simpan catatan baru ke list
            notes.append({
                'title': title,
                'importance': importance,
                'content': content,
                'encrypted_password': encrypted_password,
                'is_locked': True if importance == 'penting' else False
            })
            flash(f"Catatan '{title}' berhasil dibuat dan terenkripsi!", "success")

        return redirect(url_for('index'))

    return render_template('create_note.html', note=note)

if __name__ == '__main__':
    app.run(debug=True)
