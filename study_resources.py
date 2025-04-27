import streamlit as st
import base64
import io
from pymongo import MongoClient
import gridfs
import math
from session_manager import init_session, navigate_to, go_back


# MongoDB Connection Settings
MONGO_URI = "mongodb://localhost:27017/"  # Replace with your MongoDB connection string
DB_NAME = "study_resources"

# Connect to MongoDB
@st.cache_resource
def get_database_connection():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    fs = gridfs.GridFS(db)
    return db, fs

def init_study_resources():
    init_session()  # Initialize main session first
    if 'current_subject' not in st.session_state:
        st.session_state.current_subject = None
    if 'current_subsection' not in st.session_state:
        st.session_state.current_subsection = None
    if 'show_study_materials' not in st.session_state:
        st.session_state.show_study_materials = False
    if 'selected_pdf' not in st.session_state:
        st.session_state.selected_pdf = None
    if 'show_fullscreen_pdf' not in st.session_state:
        st.session_state.show_fullscreen_pdf = False

# Subjects data structure
SUBJECTS_DATA = {
    "History": {
        "icon": "📜",
        "subsections": [
            "Prehistoric and Protohistoric Periods",
            "Harappan Civilization",
            "Vedic Age and Iron Age developments",
            "Intellectual and Religious Developments",
            "Mahajanapadas, Mauryas, and Empires",
            "Science, Technology, and Gender Studies",
        ]
    },
    "Geography": {
        "icon": "🌍",
        "subsections": [
            "Quantitative Technique",
            "Resource Geography",
            "Geographical Thought",
            "Environmental Geography",
            "Urban Geography",
            "Remote Sensing, GIS and GPS",
            "Geomorphology",
            "Climatology",
            "Geography of Natural Hazards and Disaster Management",
            "Geography of Water Resources"
        ]
    },
    "Political Science": {
        "icon": "🏛️",
        "subsections": [
            "Indian Politics- I",
        "Indian Politics- II ",
        "Comparative Politics",
        "International Relations Theory and Politics",
        "Public Policy, Governance and Indian Administration",
        "Foreign policy of India",
        "Political Theory and Thought: Western and Indian Traditions"
        ]
    },
    "Economics": {
        "icon": "💰",
        "subsections": [
            "Quantitative Methods I (Mathematical Methods)",
            "Quantitative Methods II (Statistical Methods)",
            "Fundamentals Of Microeconomic Theory",
            "Basic Macroeconomics",
            "Advanced Microeconomics",
            "Advanced Macroeconomics",
            "Theory Of Public Finance",
            "Economic Planning In India: Overview & Challenges",
            "Public Finance And Policy In India",
            "Sectoral Growth In India",
            "Money And Banking",
            "Economics Of Growth And Development - I",
            "International Economics",
            "Economics Of Growth And Development - II",
            "Environment Economics"
        ]
    },
    "Science & Technology": {
        "icon": "🔬",
        "subsections": [
            "Space & Defense Technology",
            "Biotechnology & Nanotechnology",
            "IT & Artificial Intelligence",
            "Environmental Science"
        ]
    },
    "Environment & Ecology": {
        "icon": "🌿",
        "subsections": [
            "Climate Change & Global Initiatives",
            "Biodiversity & Wildlife Conservation",
            "Pollution & Sustainable Development"
        ]
    },
    "Legal Studies": {
        "icon": "⚖️",
        "subsections": [
            "Ethical Theories & Philosophies",
            "Public Administration Ethics",
            "Case Studies on Ethics"
        ]
    },
    "Electronic Science": {
        "icon": "🔌",
        "subsections": [
            "Communication System",
            "Digital Electronics- I",
            "Digital Electronics- II",
            "C & C++ Programming",
            "Electrodynamics & Microwaves",
            "Microprocessors & Microcontrollers",
            "Optoelectronics",
            "Power Electronics",
            "VHDL &amp; Verilog- Testing &amp; Verification"
        ]
    }
}

# Custom CSS for styling
st.markdown("""
    <style>
        .dashboard-sidebar {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            height: 100%;
            min-height: calc(100vh - 100px);
        }
        .subject-header {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .content-area {
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            min-height: 500px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .resources-container {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 8px;
            border: 1px solid #eaeaea;
        }
        .pdf-container {
            margin-top: 15px;
            padding: 10px;
            background-color: white;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .pdf-list-item {
            display: flex;
            align-items: center;
            padding: 10px 15px;
            margin-bottom: 8px;
            background-color: white;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            transition: all 0.2s ease;
        }
        .pdf-list-item:hover {
            background-color: #f0f7ff;
            border-color: #b3d7ff;
            cursor: pointer;
        }
        .pdf-icon {
            margin-right: 15px;
            color: #2196F3;
            font-size: 24px;
        }
        .pdf-title {
            font-weight: 500;
            color: #333;
        }
        .fullscreen-pdf {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 9999;
            background-color: rgba(0,0,0,0.9);
            padding: 20px;
            box-sizing: border-box;
        }
        .fullscreen-close {
            position: absolute;
            top: 20px;
            right: 20px;
            color: white;
            background-color: #f44336;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            font-size: 20px;
            cursor: pointer;
            z-index: 10000;
        }
        .fullscreen-pdf iframe {
            width: 100%;
            height: calc(100% - 60px);
            border: none;
        }
        .stButton {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

def init_study_resources():
    init_session()  # Initialize main session first
    if 'current_subject' not in st.session_state:
        st.session_state.current_subject = None
    if 'current_subsection' not in st.session_state:
        st.session_state.current_subsection = None
    if 'show_study_materials' not in st.session_state:
        st.session_state.show_study_materials = False
    if 'selected_pdf' not in st.session_state:
        st.session_state.selected_pdf = None
    if 'show_fullscreen_pdf' not in st.session_state:
        st.session_state.show_fullscreen_pdf = False
    if 'current_pdf_section' not in st.session_state:
        st.session_state.current_pdf_section = 0

def fetch_practice_pdfs(subject, subsection):
    """Fetch all practice question PDFs for the selected subsection from MongoDB."""
    db, fs = get_database_connection()
    
    practice_pdfs = db.fs.files.find({
        "metadata.subject": subject,
        "metadata.topic": subsection,
        "filename": {"$regex": "practicequestions\\.pdf$"}  # Fetch only PDFs ending with 'practicequestions.pdf'
    })

    return list(practice_pdfs)  # Convert cursor to a list

def display_pdf_list(subject, subsection):
    """Display the PDF list view with pagination (10 PDFs per page)"""
    db, fs = get_database_connection()
    
    if 'current_pdf_section' not in st.session_state:
        st.session_state.current_pdf_section = 0
    
    st.markdown("### 📚 Study Materials")
    
    try:
        # Query MongoDB for PDFs in the current folder, excluding practice questions
        pdf_files_cursor = db.fs.files.find({
            "metadata.subject": subject,
            "metadata.topic": subsection,
            "filename": {"$not": {"$regex": "practicequestions\\.pdf$"}}  # Exclude PDFs ending with 'practicequestions.pdf'
        })
        
        pdf_files_list = list(pdf_files_cursor)
        
        if pdf_files_list:
            total_pdfs = len(pdf_files_list)
            total_pages = math.ceil(total_pdfs / 10)  # Calculate total pages
            
            current_page = st.session_state.current_pdf_section  # Current page
            start_idx = current_page * 10
            end_idx = min(start_idx + 10, total_pdfs)
            
            # Display PDF list
            for i in range(start_idx, end_idx):
                pdf_file = pdf_files_list[i]
                file_name = pdf_file["filename"]
                
                col1, col2 = st.columns([10, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="pdf-list-item">
                        <div class="pdf-icon">📄</div>
                        <div class="pdf-title">{file_name}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("View", key=f"pdf-btn-{i}"):
                        st.session_state.selected_pdf = file_name
                        st.session_state.show_fullscreen_pdf = True
                        st.rerun()

            # Updated pagination controls with consistent sizing
            st.markdown("""
            <style>
            .pagination-container {
                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 20px;
                gap: 10px;
            }
            .arrow-container {
                width: 40px;
                height: 38px;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .page-button {
                display: inline-flex;
                justify-content: center;
                align-items: center;
                padding: 8px 16px;
                margin: 0;
                background-color: #0d6efd;
                color: white;
                text-align: center;
                text-decoration: none;
                cursor: pointer;
                min-width: 40px;
                height: 38px;
                width: 40px;
                border-radius: 4px;
                border: none;
                font-weight: bold;
            }
            .page-number {
                color: #0d6efd;
                font-weight: bold;
                font-size: 1.1rem;
            }
            .page-button:hover {
                background-color: #0b5ed7;
            }
            .page-button.disabled {
                background-color: #6c757d;
                cursor: not-allowed;
                opacity: 0.6;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Create clean pagination with just left arrow, page number, and right arrow
            col_left, col_center, col_right = st.columns([1, 1, 1])
            
            with col_left:
                # Instead of conditionally showing different elements, always show a button
                # but make it disabled when needed
                if current_page > 0:
                    if st.button("←", key="prev_page", use_container_width=True):
                        st.session_state.current_pdf_section -= 1
                        st.rerun()
                else:
                    # Use st.button with disabled=True to keep consistent sizing
                    st.button("←", key="prev_page", use_container_width=True, disabled=True)
            
            with col_center:
                st.markdown(f"""
                <div style="text-align: center;">
                    <span class="page-number">{current_page + 1}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col_right:
                if current_page < total_pages - 1:
                    if st.button("→", key="next_page", use_container_width=True):
                        st.session_state.current_pdf_section += 1
                        st.rerun()
                else:
                    # Use st.button with disabled=True to keep consistent sizing
                    st.button("→", key="next_page", use_container_width=True, disabled=True)

        else:
            st.warning("No PDFs found for this subject and subsection.")
    
    except Exception as e:
        st.error(f"Error accessing MongoDB: {str(e)}")
def display_fullscreen_pdf():
    """Display a PDF in fullscreen mode with a fixed close button."""
    db, fs = get_database_connection()
    
    try:
        # Get the file from MongoDB
        file_metadata = db.fs.files.find_one({
            "filename": st.session_state.selected_pdf,
            "metadata.subject": st.session_state.current_subject,
            "metadata.topic": st.session_state.current_subsection
        })
        
        if file_metadata:
            # Create a layout with columns for the close button
            col1, col2, col3 = st.columns([1, 8, 1])
            
            # Place the close button in the right column
            with col3:
                if st.button("✖ Close PDF", key="close_fullscreen_pdf_btn"):
                    st.session_state.show_fullscreen_pdf = False
                    st.rerun()
                    return
            
            # Retrieve the file data
            pdf_data = fs.get(file_metadata["_id"]).read()
            pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")
            
            # Display PDF with HTML (without JavaScript)
            pdf_viewer = f"""
            <div style="padding: 10px 0; height: 90vh;">
                <iframe src="data:application/pdf;base64,{pdf_base64} " width="100%" height="100% " 
                style="border: none; display: block;"></iframe>
                
            </div>
            """
            
            # Display the PDF content
            st.markdown(pdf_viewer, unsafe_allow_html=True)
            
            # Add another close button at the bottom for convenience

        else:
            st.warning("PDF not found in database.")
            if st.button("Go Back", key="close_warning"):
                st.session_state.show_fullscreen_pdf = False
                st.rerun()
    
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")
        if st.button("Close Viewer", key="close_error_btn"):
            st.session_state.show_fullscreen_pdf = False
            st.rerun()
def show_study_resources_dashboard():
    init_study_resources()  # Initialize study resources session
    
    # Handle fullscreen PDF view
    if st.session_state.show_fullscreen_pdf and st.session_state.selected_pdf:
        display_fullscreen_pdf()
        return  # Return early to show only the fullscreen PDF
    
    st.markdown('<div class="section-title">📚 Study Resources Dashboard</div>', unsafe_allow_html=True)
    
    if st.button("← Back to Home"):
        navigate_to("home")
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 3])
    
    # Sidebar with subjects
    with col1:
        st.markdown('<div class="dashboard-sidebar">', unsafe_allow_html=True)
        st.markdown("### Subjects")
        
        for subject, data in SUBJECTS_DATA.items():
            with st.expander(f"{data['icon']} {subject}", expanded=(st.session_state.current_subject == subject)):
                for subsection in data['subsections']:
                    if st.button(subsection, key=f"subsection_{subject}_{subsection}", use_container_width=True):
                        st.session_state.current_subject = subject
                        st.session_state.current_subsection = subsection
                        st.session_state.show_study_materials = False  # Ensure materials don't show automatically
                        st.rerun()

        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Content area
    with col2:
        st.markdown('<div class="content-area">', unsafe_allow_html=True)
        
        if st.session_state.current_subject and st.session_state.current_subsection:
            st.markdown(f"## {st.session_state.current_subject}")
            st.markdown(f"### {st.session_state.current_subsection}")
            
            # Content type selection buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📚 Study Materials", use_container_width=True):
                    st.session_state.show_study_materials = not st.session_state.show_study_materials
                    st.session_state.show_practice_questions = False  # Ensure practice questions are hidden
                    st.rerun()

            with col2:
                if st.button("🎥 Video Lectures", use_container_width=True):
                    st.session_state.show_study_materials = False
                    st.session_state.show_practice_questions = False
                    st.info("Video lectures functionality coming soon!")

            with col3:
                if st.button("📝 Practice Questions", use_container_width=True):
                    st.session_state.show_study_materials = False  # Hide study materials
                    st.session_state.show_practice_questions = True
                    st.rerun()

            # Ensure session state is initialized
            if "show_practice_questions" not in st.session_state:
                st.session_state.show_practice_questions = False
            
            # Show content based on selection
            if st.session_state.show_study_materials:
                st.markdown('<div class="resources-container">', unsafe_allow_html=True)
                display_pdf_list(st.session_state.current_subject, st.session_state.current_subsection)
                st.markdown('</div>', unsafe_allow_html=True)
            if st.session_state.show_practice_questions:
                st.markdown('<div class="resources-container">', unsafe_allow_html=True)
                st.markdown("### 📝 Practice Question PDFs")

                practice_pdfs = fetch_practice_pdfs(st.session_state.current_subject, st.session_state.current_subsection)
                
                if practice_pdfs:
                    selected_practice_pdf = st.selectbox("📜 Select a Practice Question PDF", 
                                                        [pdf["filename"] for pdf in practice_pdfs])

                    if st.button("Start Practice Test 🚀", use_container_width=True):
                        if selected_practice_pdf:
                            st.session_state["selected_practice_pdf"] = selected_practice_pdf  # ✅ Ensure the session variable is stored
                            st.session_state["test_initialized"] = False  # ✅ Reset test state
                            navigate_to("mcqs_test")  # Redirect to MCQs Test page
                            st.rerun()
                        else:
                            st.warning("⚠️ Please select a practice question PDF before starting the test.")

                else:
                    st.warning("No practice question PDFs available for this subsection.")

                st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state.current_subject:
            st.markdown(f"## {st.session_state.current_subject}")
            st.markdown("Please select a subsection from the sidebar to view its content.")
        else:
            st.markdown("## Welcome to Study Resources")
            st.markdown("Please select a subject from the sidebar to get started.")
            
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    st.error("This is a module and should not be run directly. Please run home.py instead.")