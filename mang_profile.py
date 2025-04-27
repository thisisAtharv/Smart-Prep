import streamlit as st
import sqlite3
from hashlib import sha256
from cryptography.fernet import Fernet
import os

# Assuming the same encryption/decryption functions and key are used
MASTER_KEY = os.environ.get("FERNET_KEY")
cipher = Fernet(MASTER_KEY)

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def decrypt_data(encrypted_data):
    return cipher.decrypt(encrypted_data.encode()).decode()

def encrypt_data(data):
    return cipher.encrypt(data.encode()).decode()

# Connect to the database
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

def show_manage_profile():
    # Import the navigation function
    from session_manager import navigate_to

    # "Back to Home" button (same as in your blog section)
    if st.button("← Back to Home"):
        navigate_to("home")

    # Assume st.session_state.user_session holds the username
    old_username = st.session_state.get('user_session')
    if not old_username:
        st.error("No user session found. Please log in.")
        return

    # Modify the SELECT query to also fetch the stored hashed password
    c.execute("""SELECT username, full_name, email, phone_number, date_of_birth, gender, 
                 state, city, qualification, optional_subject, preparation_stage, target_year, password
                 FROM users WHERE username = ?""", (old_username,))
    user_data = c.fetchone()

    if not user_data:
        st.error("User not found!")
        return

    # Unpack user data (note: the last element is the stored hashed password)
    (username, full_name, encrypted_email, encrypted_phone, date_of_birth, gender,
     state, city, qualification, optional_subject, preparation_stage, target_year, stored_password) = user_data

    # Decrypt email and phone
    email = decrypt_data(encrypted_email)
    phone_number = decrypt_data(encrypted_phone)

    st.title("Manage Your Profile")
    st.write("Review your details below and update where necessary.")

    # Use a form to edit updatable fields
    with st.form("profile_update_form"):
        # Make username an editable field so user can update it
        new_username = st.text_input("Username", value=username)
        st.text_input("Full Name", value=full_name, disabled=True)
        new_email = st.text_input("Email", value=email)
        new_phone = st.text_input("Phone Number", value=phone_number)
        new_preparation_stage = st.selectbox("Preparation Stage", 
                                             ["Beginner", "Intermediate", "Advanced", "Mains Preparation", "Interview"],
                                             index=["Beginner", "Intermediate", "Advanced", "Mains Preparation", "Interview"].index(preparation_stage))
        new_target_year = st.number_input("Target Year", min_value=2024, max_value=2035, step=1, value=target_year)

        st.markdown("### Change Password (Optional)")
        old_password_input = st.text_input("Enter Old Password", type="password")
        new_password_input = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")

        submitted = st.form_submit_button("Update Profile")

    if submitted:
        try:
            # If the user filled in any password field, process the password change logic
            if old_password_input or new_password_input or confirm_new_password:
                # Verify that the old password is provided
                if not old_password_input:
                    st.error("Please enter your old password to change your password.")
                    return
                # Verify the old password matches the stored password
                if hash_password(old_password_input) != stored_password:
                    st.error("The old password you entered is incorrect.")
                    return
                # Check that both new password entries match
                if new_password_input != confirm_new_password:
                    st.error("The new passwords do not match.")
                    return
                # If new password is provided and all checks pass, hash it for storage
                hashed_new_password = hash_password(new_password_input)
                update_password = True
            else:
                update_password = False

            # Prepare update values; update password only if the user wants to change it
            if update_password:
                c.execute("""UPDATE users 
                             SET username = ?, email = ?, password = ?, phone_number = ?, 
                                 preparation_stage = ?, target_year = ?
                             WHERE username = ?""",
                          (new_username, encrypt_data(new_email), hashed_new_password, encrypt_data(new_phone),
                           new_preparation_stage, new_target_year, old_username))
            else:
                c.execute("""UPDATE users 
                             SET username = ?, email = ?, phone_number = ?, 
                                 preparation_stage = ?, target_year = ?
                             WHERE username = ?""",
                          (new_username, encrypt_data(new_email), encrypt_data(new_phone),
                           new_preparation_stage, new_target_year, old_username))
            conn.commit()

            # Update the session state with the new username
            st.session_state.user_session = new_username

            st.success("Profile updated successfully!")
        except Exception as e:
            st.error(f"An error occurred while updating the profile: {e}")
