import streamlit as st

def init_session():
    if "page_history" not in st.session_state:
        st.session_state.page_history = []
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"

    # Use the new `st.query_params` method
    query_params = st.query_params

    if "page" in query_params:
        requested_page = query_params["page"]
        if requested_page and requested_page != st.session_state.current_page:
            st.session_state.current_page = requested_page
            st.rerun()  # Ensures the UI updates

import streamlit as st

def navigate_to(page):
    """Handles navigation by updating session state and query parameters."""
    if "page_history" not in st.session_state:
        st.session_state.page_history = []

    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"  # Default page

    # Append previous page to history
    st.session_state.page_history.append(st.session_state.current_page)
    
    # Update current page
    st.session_state.current_page = page

    # ✅ Correct way to update URL query parameters
    st.query_params.update({"page": page})  # This replaces experimental_set_query_params()

    st.rerun()
 # Ensures UI refreshes immediately

def go_back():
    """Handles back navigation."""
    if "page_history" in st.session_state and st.session_state.page_history:
        previous_page = st.session_state.page_history.pop()
        st.session_state.current_page = previous_page

        # ✅ Correct way to update URL query parameters
        st.query_params.update({"page": previous_page})

        st.rerun()
    else:
        st.warning("No previous page found in history!")
def get_current_page():
    return st.session_state.current_page

def clear_navigation():
    """Resets navigation history."""
    st.session_state.page_history = []
    st.query_params.clear()  # Clears the URL parameters
