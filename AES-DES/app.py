from flask import Flask, render_template, request, redirect, url_for, flash
import base64
import os
import bleach

app = Flask(__name__)
app.secret_key = 'crypt0gr4phy_1s_fun_18_42'

# List to store notes (acting as a placeholder for a database)
notes = []

# Simplified AES 128-bit Encryption (Educational Use Only)
def aes_encrypt_manual(plain_text, key):
    plain_text = plain_text.ljust(16)[:16]  # Pad to 16 bytes
    key = key.ljust(16)[:16].encode('utf-8')  # Ensure key is 16 bytes
    iv = os.urandom(16)
    encrypted = b''

    for i in range(16):
        encrypted += bytes([plain_text.encode('utf-8')[i] ^ key[i] ^ iv[i]])  # XOR with key and IV

    # Combine IV and ciphertext
    return base64.b64encode(iv + encrypted).decode('utf-8')

# Simplified AES 128-bit Decryption (Educational Use Only)
def aes_decrypt_manual(encrypted_text, key):
    key = key.ljust(16)[:16].encode('utf-8')  # Ensure key is 16 bytes
    encrypted_data = base64.b64decode(encrypted_text)
    iv = encrypted_data[:16]
    encrypted_text = encrypted_data[16:]
    decrypted = b''

    for i in range(16):
        decrypted += bytes([encrypted_text[i] ^ key[i] ^ iv[i]])  # Reverse XOR

    return decrypted.decode('utf-8').rstrip()  # Remove padding

# Simplified DES 64-bit Encryption (Educational Use Only)
def des_encrypt_manual(plain_text, key):
    plain_text = plain_text.ljust(8)[:8]  # Pad to 8 bytes
    key = key.ljust(8)[:8].encode('utf-8')  # Ensure key is 8 bytes
    iv = os.urandom(8)
    encrypted = b''

    for i in range(8):
        encrypted += bytes([plain_text.encode('utf-8')[i] ^ key[i] ^ iv[i]])  # XOR with key and IV

    # Combine IV and ciphertext
    return base64.b64encode(iv + encrypted).decode('utf-8')

# Simplified DES 64-bit Decryption (Educational Use Only)
def des_decrypt_manual(encrypted_text, key):
    key = key.ljust(8)[:8].encode('utf-8')  # Ensure key is 8 bytes
    encrypted_data = base64.b64decode(encrypted_text)
    iv = encrypted_data[:8]
    encrypted_text = encrypted_data[8:]
    decrypted = b''

    for i in range(8):
        decrypted += bytes([encrypted_text[i] ^ key[i] ^ iv[i]])  # Reverse XOR

    return decrypted.decode('utf-8').rstrip()  # Remove padding

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
    note = notes[note_id]  # Get note by ID
    show_note_content = False  # Control whether content is displayed
    edit_mode = False  # Control edit mode

    if request.method == 'POST':
        if 'password' in request.form:  # Password verification
            input_password = request.form['password']
            reversed_key = input_password[::-1]  # Reverse password for use as key

            # Check if the entered password is correct
            if note['importance'] == 'penting':
                try:
                    decrypted_password = aes_decrypt_manual(note['encrypted_password'], reversed_key)
                except:
                    decrypted_password = None
            else:
                try:
                    decrypted_password = des_decrypt_manual(note['encrypted_password'], reversed_key)
                except:
                    decrypted_password = None

            if decrypted_password == input_password:
                show_note_content = True  # Display content if password is correct
                edit_mode = True  # Enter edit mode
            else:
                flash('Incorrect password, please try again.', 'danger')

        elif 'content' in request.form:  # Save note changes
            new_content = request.form['content']
            note['content'] = bleach.clean(new_content)  # Update note with new content
            flash('Note updated successfully!', 'success')
            return redirect(url_for('view_note', note_id=note_id))  # Redirect after saving

    return render_template('view_note.html', note=note, show_note_content=show_note_content, edit_mode=edit_mode)


# Route for creating/editing a note
@app.route('/create_note', methods=['GET', 'POST'])
@app.route('/create_note/<int:note_id>', methods=['GET', 'POST'])
def create_note(note_id=None):
    if note_id is not None:
        note = notes[note_id]  # Get note to edit
    else:
        note = None

    if request.method == 'POST':
        title = bleach.clean(request.form['title'])
        importance = request.form['importance']
        content = bleach.clean(request.form['content'])
        password = request.form['password']

        reversed_key = password[::-1]  # Reverse password for use as key

        # Encrypt password based on note importance
        if importance == 'penting':
            encrypted_password = aes_encrypt_manual(password, reversed_key)
        else:
            encrypted_password = des_encrypt_manual(password, reversed_key)

        if note_id is not None:  # Editing existing note
            notes[note_id] = {
                'title': title,
                'importance': importance,
                'content': content,
                'encrypted_password': encrypted_password,
                'is_locked': True if importance == 'penting' else False
            }
            flash(f"Note '{title}' updated successfully!", "success")
        else:
            notes.append({
                'title': title,
                'importance': importance,
                'content': content,
                'encrypted_password': encrypted_password,
                'is_locked': True if importance == 'penting' else False
            })
            flash(f"Note '{title}' created and encrypted!", "success")

        # Redirect to main page after saving note
        return redirect(url_for('notes_by_category', category='all'))  # Redirect to 'All' category

    return render_template('create_note.html', note=note)


if __name__ == '__main__':
    app.run(debug=True)
