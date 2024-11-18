from flask import Flask, render_template, request, redirect, url_for, flash
import base64
import os
import bleach

app = Flask(__name__)
app.secret_key = 'crypt0gr4phy_1s_fun_18_42'

# List to store notes (acting as a placeholder for a database)
notes = []

import base64
import os

# AES Encryption
def aes_encrypt_manual(plain_text, key):
    # Ensure text is padded to 16 bytes (AES block size)
    padding_len = 16 - len(plain_text) % 16
    plain_text = plain_text + chr(padding_len) * padding_len  # Pad text to make it a multiple of 16
    key = key.ljust(16)[:16].encode('utf-8')  # Ensure key is 16 bytes
    iv = os.urandom(16)
    encrypted = b''

    for i in range(len(plain_text)):
        encrypted += bytes([ord(plain_text[i]) ^ key[i % 16] ^ iv[i % 16]])

    # Combine IV and ciphertext and encode to base64
    return base64.b64encode(iv + encrypted).decode('utf-8')

# AES Decryption
def aes_decrypt_manual(encrypted_text, key):
    key = key.ljust(16)[:16].encode('utf-8')  # Ensure key is 16 bytes
    encrypted_data = base64.b64decode(encrypted_text)
    iv = encrypted_data[:16]
    encrypted_text = encrypted_data[16:]
    decrypted = b''

    for i in range(len(encrypted_text)):
        decrypted += bytes([encrypted_text[i] ^ key[i % 16] ^ iv[i % 16]])

    decrypted = decrypted.decode('utf-8')

    # Remove PKCS7 padding
    padding_len = ord(decrypted[-1])  # Get padding length
    return decrypted[:-padding_len]  # Remove padding

# DES Encryption
def des_encrypt_manual(plain_text, key):
    # Ensure text is padded to 8 bytes (DES block size)
    padding_len = 8 - len(plain_text) % 8
    plain_text = plain_text + chr(padding_len) * padding_len  # Pad text to make it a multiple of 8
    key = key.ljust(8)[:8].encode('utf-8')  # Ensure key is 8 bytes
    iv = os.urandom(8)
    encrypted = b''

    for i in range(len(plain_text)):
        encrypted += bytes([ord(plain_text[i]) ^ key[i % 8] ^ iv[i % 8]])

    # Combine IV and ciphertext and encode to base64
    return base64.b64encode(iv + encrypted).decode('utf-8')

# DES Decryption
def des_decrypt_manual(encrypted_text, key):
    key = key.ljust(8)[:8].encode('utf-8')  # Ensure key is 8 bytes
    encrypted_data = base64.b64decode(encrypted_text)
    iv = encrypted_data[:8]
    encrypted_text = encrypted_data[8:]
    decrypted = b''

    for i in range(len(encrypted_text)):
        decrypted += bytes([encrypted_text[i] ^ key[i % 8] ^ iv[i % 8]])

    decrypted = decrypted.decode('utf-8')

    # Remove PKCS7 padding
    padding_len = ord(decrypted[-1])  # Get padding length
    return decrypted[:-padding_len]  # Remove padding

@app.route('/')
@app.route('/category/<category>')
def notes_by_category(category='all'):  # Default category is 'all'
    if category == 'all':
        filtered_notes = notes
    else:
        filtered_notes = [note for note in notes if note['importance'] == category]
    
    return render_template('index.html', notes=filtered_notes, selected_category=category)


# Route for index page
@app.route('/')
def index():
    return render_template('index.html', notes=notes)

# Route for viewing a note
@app.route('/view_note/<int:note_id>', methods=['GET', 'POST'])
def view_note(note_id):
    note = notes[note_id]
    show_note_content = False
    edit_mode = False
    decrypted_content = None
    decrypted_password = None  # Initialize decrypted_password here

    if request.method == 'POST':
        if 'password' in request.form:
            input_password = request.form['password']
            reversed_key = input_password[::-1]

            if note['importance'] == 'penting':
                decrypted_password = aes_decrypt_manual(note['encrypted_password'], reversed_key)
                decrypted_content = aes_decrypt_manual(note['encrypted_content'], reversed_key)
            else:
                decrypted_password = des_decrypt_manual(note['encrypted_password'], reversed_key)
                decrypted_content = des_decrypt_manual(note['encrypted_content'], reversed_key)

            if decrypted_password == input_password:
                show_note_content = True
                edit_mode = True
            else:
                flash('Incorrect password, please try again.', 'danger')
                # After flashing, ensure that the view_note page is rendered again
                return render_template(
                    'view_note.html', 
                    note=note, 
                    decrypted_password=decrypted_password,
                    decrypted_content=decrypted_content, 
                    show_note_content=show_note_content, 
                    edit_mode=edit_mode
                )

        elif 'content' in request.form:
            new_content = request.form['content']
            note['content'] = bleach.clean(new_content)
            flash('Note updated successfully!', 'success')
            return redirect(url_for('view_note', note_id=note_id))

    return render_template(
        'view_note.html', 
        note=note, 
        decrypted_password=decrypted_password,
        decrypted_content=decrypted_content, 
        show_note_content=show_note_content, 
        edit_mode=edit_mode
    )

# Route for creating/editing a note
@app.route('/create_note', methods=['GET', 'POST'])
@app.route('/create_note/<int:note_id>', methods=['GET', 'POST'])
def create_note(note_id=None):
    if note_id is not None:
        note = notes[note_id]
    else:
        note = None

    if request.method == 'POST':
        title = bleach.clean(request.form['title'])
        importance = request.form['importance']
        content = request.form['content']
        password = request.form['password']

        reversed_key = password[::-1]

        # Encrypt password and content based on importance
        if importance == 'penting':
            encrypted_password = aes_encrypt_manual(password, reversed_key)
            encrypted_content = aes_encrypt_manual(content, reversed_key)
        else:
            encrypted_password = des_encrypt_manual(password, reversed_key)
            encrypted_content = des_encrypt_manual(content, reversed_key)

        if note_id is not None:
            notes[note_id] = {
                'title': title,
                'importance': importance,
                'encrypted_content': encrypted_content,
                'encrypted_password': encrypted_password,
                'is_locked': True if importance == 'penting' else False
            }
            flash(f"Note '{title}' updated successfully!", "success")
        else:
            notes.append({
                'title': title,
                'importance': importance,
                'encrypted_content': encrypted_content,
                'encrypted_password': encrypted_password,
                'is_locked': True if importance == 'penting' else False
            })
            flash(f"Note '{title}' created and encrypted!", "success")

        return redirect(url_for('notes_by_category', category='all'))

    return render_template('create_note.html', note=note)

# Route for deleting a note
@app.route('/delete_note/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    if 0 <= note_id < len(notes):  # Ensure note_id is within the range of the notes list
        notes.pop(note_id)  # Remove the note from the list
        flash('Note deleted successfully', 'success')
    else:
        flash('Note not found', 'danger')
    return redirect(url_for('notes_by_category', category='all'))

if __name__ == '__main__':
    app.run(debug=True)
