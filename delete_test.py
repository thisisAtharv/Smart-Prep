import streamlit as st
from study_resources import get_database_connection

def delete_test_records_for_user(username: str):
    db, fs = get_database_connection()
    collection = db.test_attempts

    # Count the test records for the provided username
    record_count = collection.count_documents({"username": username})
    st.info(f"Found {record_count} test record(s) for user '{username}'.")

    # Provide a confirmation checkbox before deletion
    confirm = st.checkbox("I confirm that I want to delete all test records for this user", key="confirm_delete")
    if confirm:
        if st.button("Delete All Test Records", key="delete_records_btn"):
            result = collection.delete_many({"username": username})
            st.success(f"Deleted {result.deleted_count} test record(s) for user '{username}'.")
    else:
        st.warning("Check the box above to confirm deletion.")

def show_delete_records_page():
    st.markdown("<h1 class='main-header'>Delete Test Records</h1>", unsafe_allow_html=True)
    
    # Input box to enter the username
    username = st.text_input("Enter username to delete records:", "")
    
    if username:
        delete_test_records_for_user(username)
    
    # Navigation back to home
    if st.button("← Back to Home"):
        from session_manager import navigate_to
        navigate_to("home")

if __name__ == "__main__":
    show_delete_records_page()
