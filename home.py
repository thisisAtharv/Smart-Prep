
import streamlit as st
import sqlite3
from hashlib import sha256
import requests
import os
import json
import random
from openai import OpenAI
from datetime import date
# Set up the page configuration
st.set_page_config(page_title="Smart Prep", layout="wide")
from session_manager import init_session, navigate_to, go_back
init_session()
from study_resources import show_study_resources_dashboard
from blog_section import show_blog_section
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from mang_profile import show_manage_profile

load_dotenv()
MASTER_KEY = os.environ.get("FERNET_KEY")
cipher = Fernet(MASTER_KEY)

# Database connection
conn = sqlite3.connect("users.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (id INTEGER PRIMARY KEY, 
              full_name TEXT NOT NULL,
              username TEXT UNIQUE NOT NULL,
              email TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              phone_number TEXT,
              date_of_birth DATE,
              gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
              state TEXT,
              city TEXT,
              qualification TEXT,
              optional_subject TEXT,
              preparation_stage TEXT CHECK(preparation_stage IN 
                ('Beginner', 'Intermediate', 'Advanced', 'Mains Preparation', 'Interview')),
              target_year INTEGER,
              registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'show_fact_modal' not in st.session_state:
    st.session_state.show_fact_modal = False
if 'current_fact' not in st.session_state:
    st.session_state.current_fact = {"type": "", "content": ""}

def encrypt_data(data):
    """Encrypts data using Fernet encryption."""
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    """Decrypts data using Fernet decryption."""
    return cipher.decrypt(encrypted_data.encode()).decode()
# Authentication functions
def hash_password(password):
    return sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    hashed_pwd = hash_password(password)
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pwd))
    return c.fetchone()

def register_user(username, full_name, email, password, phone_number, date_of_birth, gender, state, city, qualification, optional_subject, preparation_stage, target_year):
    try:
        hashed_pwd = hash_password(password)
        encrypted_email = encrypt_data(email)  
        encrypted_phone = encrypt_data(phone_number)
        encrypted_dob = encrypt_data(str(date_of_birth))

        c.execute('''INSERT INTO users 
                     (username, full_name, email, password, phone_number, date_of_birth, gender, state, city, qualification, optional_subject, preparation_stage, target_year)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                  (username, full_name, encrypted_email, hashed_pwd, encrypted_phone, encrypted_dob, gender, state, city, qualification, optional_subject, preparation_stage, target_year))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
# Initialize OpenAI Client
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def fetch_historical_fact():
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert historian specializing in Indian history. Provide real, verified historical facts about India."},
                {"role": "user", "content": "Give me a real and verified historical fact about India in the format 'Year: Event'. Avoid any unrelated, fake, or humorous facts."}
            ]
        )

        if response.choices:
            return response.choices[0].message.content
        return "Unable to fetch historical fact. Please try again later."

    except Exception as e:
        if "insufficient_quota" in str(e):
            return "Did you know? India was the first country to mine diamonds as early as the 4th century BC."
        return f"Error fetching historical fact: {str(e)}"



def fetch_social_fact():
    api_urls = [
        "https://www.boredapi.com/api/activity/",  # Social activity suggestions
        "https://uselessfacts.jsph.pl/random.json?language=en"  # Fun & random facts
    ]
    for url in api_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "boredapi" in url:  # If using Bored API
                    return f"Try this social activity: {data.get('activity', 'No activity found')}"
                elif "uselessfacts" in url:  # If using Useless Facts API
                    return data.get('text', "Unable to fetch social fact at this time.")
        except:
            continue  # Try the next API if one fails
    
    return "The average person spends over 2 hours per day on social media."

def fetch_political_fact():
    api_urls = [
        "https://api.quotable.io/random",  # Political quotes
        "https://opentdb.com/api.php?amount=1&category=24&type=multiple"  # Political trivia
    ]
    
    for url in api_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "quotable" in url:  # If using Quotable API
                    return f"\"{data.get('content', '')}\" - {data.get('author', 'Unknown')}"
                elif "opentdb" in url:  # If using Open Trivia DB API
                    return data['results'][0]['question']
        except:
            continue  # Try the next API if one fails
    
    return "Politics has shaped nations for centuries, with countless debates and revolutions."

# Custom CSS
st.markdown("""
    <style>
        .main-title {
            font-size: 48px;
            font-weight: bold;
            color: #2C3E50;
            margin-bottom: 20px;
        }
        .subtitle {
            font-size: 24px;
            color: #666;
            margin-bottom: 30px;
        }
        .hero-section {
            padding: 60px 0;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            margin-bottom: 40px;
        }
        .feature-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            height: 100%;
            margin-bottom: 20px;
        }
        .feature-icon {
            font-size: 36px;
            margin-bottom: 15px;
        }
        .feature-title {
            font-size: 20px;
            font-weight: bold;
            color: #2C3E50;
            margin-bottom: 10px;
        }
        .section-title {
            font-size: 32px;
            font-weight: bold;
            color: #2C3E50;
            margin: 40px 0 20px 0;
            padding-left: 20px;
            border-left: 5px solid #0056D2;
        }
        .auth-form {
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stButton > button {
            background-color: #0056D2;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 10px 20px;
        }
        .nav-link {
            color: #2C3E50;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        .nav-link:hover {
            background-color: #f8f9fa;
        }
        .resource-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            height: 100%;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

def show_navbar():
    with st.container():
        cols = st.columns([2, 1, 1, 1, 1])  # Adjusted columns to remove extra spacing

        with cols[0]:
            st.markdown("### Smart Prep")  # ✅ Title appears only once

        # ✅ Hide "Back" button on homepage, show it on other pages
        if st.session_state.get("current_page", "home") != "home":
            with cols[1]:
                if st.button("← Back", key="back_btn"):
                    go_back()
        with cols[3]:
            if st.button("Manage Profile", key="manage_profile_btn"):
                navigate_to("manage_profile")

        # ✅ Show "Logout" button ONLY if the user is logged in
        with cols[4]:
            if st.session_state.get('logged_in', False):
                if st.button("Logout", key="logout_btn_navbar"):
                    st.session_state.logged_in = False
                    st.session_state.current_page = "login"
                    st.rerun()


def show_hero_section():
    st.markdown(
    '''
    <style>
        .hero-section {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            color: #2E86C1;
            padding: 20px;
            background-color: #F4F6F7;
            border-radius: 10px;
        }
    </style>
    <div class="hero-section">
        <h2>Get Your Brain In Gear!</h2>
    </div>
    ''', 
    unsafe_allow_html=True
)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown('<div class="main-title">Welcome to Smart Prep</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Your comprehensive platform for exam preparation</div>', unsafe_allow_html=True)

def show_resources_section():
    st.markdown('<div class="section-title">📖 Study Resources</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Study Materials", key="study_materials_btn", use_container_width=True):
            navigate_to("study_resources")
            
        st.markdown("""
            <div class="resource-card"  style="color: black;">
                <h3>📚 Study Materials</h3>
                <ul>
                    <li>Comprehensive study guides</li>
                    <li>Practice question banks</li>
                    <li>Video lectures</li>
                    <li>PDF resources</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("Blog Section", key="blog_section_btn", use_container_width=True):
            navigate_to("blog_section")
        
        st.markdown("""
            <div class="resource-card" style="color: black;">
                <h3>📝 Blog Section</h3>
                <ul>
                    <li>Educational blogs</li>
                    <li>Study tips</li>
                    <li>Exam insights</li>
                    <li>Community discussions</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="resource-card" style="color: black;">
                <h3>🎥 Video Content</h3>
                <ul>
                    <li>Expert lectures</li>
                    <li>Concept explanations</li>
                    <li>Problem-solving sessions</li>
                    <li>Strategy discussions</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
def show_facts_insights_section():
    st.markdown('<div class="section-title" >📌 Facts & Insights</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    facts_data = [
        {
            "icon": "📜",
            "title": "Historical Facts",
            "description": "Explore key events and milestones that shaped our world.",
            "key": "historical"
        },
        {
            "icon": "👥",
            "title": "Social Facts",
            "description": "Understand society, culture, and demographic trends.",
            "key": "social"
        },
        {
            "icon": "⚖️",
            "title": "Political Facts",
            "description": "Stay updated with political systems and governance.",
            "key": "political"
        }
    ]
    
    columns = [col1, col2, col3]
    for col, fact in zip(columns, facts_data):
        with col:
            st.markdown(f"""
                <div class="feature-card"  style="color: black;">
                    <div class="feature-icon">{fact['icon']}</div>
                    <div class="feature-title">{fact['title']}</div>
                    <p>{fact['description']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Show {fact['title']}", key=f"btn_{fact['key']}"):
                fact_content = None
                if fact['key'] == 'historical':
                    fact_content = fetch_historical_fact()
                elif fact['key'] == 'social':
                    fact_content = fetch_social_fact()
                elif fact['key'] == 'political':
                    fact_content = fetch_political_fact()
                
                with st.expander(f"{fact['title']} - Click to view", expanded=True):
                    st.markdown(f"""
                        <div style="background-color: #f8f9fa; color: black; padding: 15px; border-radius: 5px; border-left: 5px solid #0056D2;">
                            <p style="font-style: italic;">{fact_content}</p>
                        </div>
                    """, unsafe_allow_html=True)

def show_courses_section():
    st.markdown('<div class="section-title">🎓 Courses</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    courses = [
        ("Prelims Preparation", "Comprehensive course for preliminary examination"),
        ("Mains Strategy", "In-depth preparation for main examination"),
        ("Interview Guidance", "Expert tips and mock interviews")
    ]
    
    for i, (title, desc) in enumerate(courses):
        with [col1, col2, col3][i]:
            st.markdown(f"""
                <div class="feature-card"  style="color: black;">
                    <div class="feature-title">{title}</div>
                    <p>{desc}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Use Streamlit's button to capture clicks
            if st.button(f"Enroll {title}", key=f"enroll_{i}"):
                st.success(f"Enrolled in {title} successfully!")


def show_assessments_section():
    st.markdown('<div class="section-title">📝 Assessments</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="feature-card"  style="color: black;">
                <div class="feature-title">Practice Tests</div>
                <ul>
                    <li>Daily quizzes</li>
                    <li>Subject-wise tests</li>
                    <li>Full-length mock exams</li>
                    <li>Performance analytics</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="feature-card"  style="color: black;">
                <div class="feature-title">Progress Tracking</div>
                <ul>
                    <li>Detailed performance reports</li>
                    <li>Strength and weakness analysis</li>
                    <li>Personalized recommendations</li>
                    <li>Improvement metrics</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Progress Tracking", key="progress_tracking_btn"):
            navigate_to("progress_tracking")


def show_login_page():
    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown('<div class="main-title" style="text-align: center;">Login to Smart Prep</div>', unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                if submit:
                    if username and password:
                        user = authenticate_user(username, password)
                        if user:
                            st.success("Login successful!")
                            st.session_state.logged_in = True
                            st.session_state['user_session'] = username
                            st.session_state.user_session = username
                            # st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials!")
                    else:
                        st.warning("Please fill in all fields!")
            
            st.markdown("---")
            st.write("Don't have an account?")
            if st.button("Register",key="next_btn_5",):
               navigate_to("register")
def is_username_available(username):
    c.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    return c.fetchone() is None

def show_register_page():
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="main-title" style="text-align: center;">Register for Smart Prep</div>', unsafe_allow_html=True)

            with st.form("register_form", clear_on_submit=True):
                # Basic Details
                username = st.text_input("Username")
                
                # Check username availability dynamically
                if username:
                    if not is_username_available(username):
                        st.warning("⚠️ Username is already taken! Please choose another.")
                        username_valid = False
                    else:
                        st.success("✅ Username available!")
                        username_valid = True
                else:
                    username_valid = False

                full_name = st.text_input("Full Name")
                email = st.text_input("Email")
                phone_number = st.text_input("Phone Number")
                today = date.today()
                max_dob = date(today.year - 21, today.month, today.day)  # Minimum age 21
                min_dob = date(today.year - 32, today.month, today.day)  # Maximum age 32
                date_of_birth = st.date_input("Date of Birth", min_value=min_dob, max_value=max_dob)
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                
                # Location & Qualification
                state = st.text_input("State")
                city = st.text_input("City")
                qualification = st.text_input("Qualification")

                # UPSC Specific Fields
                optional_subject = st.text_input("Optional Subject")
                preparation_stage = st.selectbox("Preparation Stage", 
                                                 ["Beginner", "Intermediate", "Advanced", "Mains Preparation", "Interview"])
                target_year = st.number_input("Target Year", min_value=today.year, max_value=2035, step=1)

                # Passwords
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")

                # Submit Button (Disabled if username is invalid)
                submit = st.form_submit_button("Register", disabled=username_valid)

                # Registration Logic
                if submit:
                    if (
                        full_name and email and phone_number and date_of_birth and gender and
                        state and city and qualification and optional_subject and
                        preparation_stage and target_year and password and confirm_password
                    ):
                        if password == confirm_password:
                            if register_user(
                                username, full_name, email, password, phone_number,
                                str(date_of_birth), gender, state, city, qualification,
                                optional_subject, preparation_stage, target_year
                            ):
                                st.success("✅ Registration successful! Please login.")
                                st.session_state.current_page = "login"
                                st.rerun()
                            else:
                                st.error("⚠️ Email already registered! Try logging in.")
                        else:
                            st.error("❗ Passwords don't match!")
                    else:
                        st.warning("⚠️ Please fill in all required fields!")

            st.markdown("---")
            st.write("Already have an account?")
            
            # Navigation to Login
            if st.button("Login", key="next_btn_6"):
                navigate_to("login")


# Continuing from where we left off in show_main_app():

def show_main_app():
    current_page = st.session_state.get("current_page", "home")
    
    # Render navbar only if not in blog_section or mcqs_test or manage_profile
    if current_page not in ["blog_section", "mcqs_test", "manage_profile", "progress_tracking"]:
        show_navbar()
    
    # Render the appropriate page based on current_page
    if current_page == "blog_section":
        show_blog_section()
    elif current_page == "study_resources":
        show_study_resources_dashboard()
    elif current_page == "mcqs_test":
        from mcqs_test import main
        main()
    elif current_page == "manage_profile":
        show_manage_profile()
    elif current_page == "progress_tracking":
        from progress_tracking import show_progress_tracking
        show_progress_tracking()
    else:
        show_hero_section()
        show_resources_section()
        show_facts_insights_section()
        show_courses_section()
        show_assessments_section()

def main():
    init_session()  # Ensure session is initialized

    # Show authentication pages only if not logged in
    if not st.session_state.get('logged_in', False):
        if st.session_state.current_page == "register":
            show_register_page()
        else:
            show_login_page()
        return  # Exit if not logged in

    # Show navbar only once after login
    if "navbar_displayed" not in st.session_state:
        st.session_state.navbar_displayed = True

    current_page = st.session_state.get("current_page", "home")

    if current_page == "study_resources":
        show_study_resources_dashboard()
    else:
        show_main_app()  # Default to home or based on current_page

if __name__ == "__main__":
    main()