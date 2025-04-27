import base64
import io
import streamlit as st
from pymongo import MongoClient
from bson.binary import Binary
import gridfs
import gc
import copy

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "study_resources"

@st.cache_resource
def get_database_connection():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    fs = gridfs.GridFS(db)
    return db, fs

db, fs = get_database_connection()

subjects = {
    "Geography": [
        "Quantitative Technique",
        "Resource Geography",
        "Geographical Thought",
        "Environmental Geography",
        "Urban Geography",
        "Remote Sensing, GIS and GPS",
        "Geomorphology",
        "Climatology",
        "Geography of Natural Hazards and Disaster Management",
        "Geography of Water Resources",
    ],
    "History": [
        "Prehistoric and Protohistoric Periods",
        "Harappan Civilization",
        "Vedic Age and Iron Age developments",
        "Intellectual and Religious Developments",
        "Mahajanapadas, Mauryas, and Empires",
        "Science, Technology, and Gender Studies",
    ],
    "Political Science":[
        "Indian Politics- I",
        "Indian Politics- II ",
        "Comparative Politics",
        "International Relations Theory and Politics",
        "Public Policy, Governance and Indian Administration",
        "Foreign policy of India",
        "Political Theory and Thought: Western and Indian Traditions",
    ],
    "Economics": [
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
}

st.title("📚 Study Resource Manager")

if "selected_subject" not in st.session_state:
    st.session_state.selected_subject = list(subjects.keys())[0]
if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = subjects[st.session_state.selected_subject][0]
if "selected_pdf" not in st.session_state:
    st.session_state.selected_pdf = None

selected_subject = st.selectbox(
    "📖 Select Subject", 
    list(subjects.keys()),
    index=list(subjects.keys()).index(st.session_state.selected_subject)
)

if selected_subject != st.session_state.selected_subject:
    st.session_state.selected_subject = selected_subject
    st.session_state.selected_topic = subjects[selected_subject][0]
    st.session_state.selected_pdf = None

selected_topic = st.selectbox(
    "📂 Select Topic", 
    subjects[selected_subject],
    index=subjects[selected_subject].index(st.session_state.selected_topic) 
    if st.session_state.selected_topic in subjects[selected_subject] 
    else 0
)

if selected_topic != st.session_state.selected_topic:
    st.session_state.selected_topic = selected_topic
    st.session_state.selected_pdf = None

folder_path = f"{selected_subject}/{selected_topic}"

st.subheader(f"📂 Upload PDFs to **{selected_topic}**")

uploaded_files = st.file_uploader("📤 Upload PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            file_name = uploaded_file.name
            with io.BytesIO() as buffer:
                buffer.write(uploaded_file.getvalue())
                buffer.seek(0)
                file_data = buffer.read()
            
            existing_file = db.fs.files.find_one({
                "filename": file_name,
                "metadata.subject": selected_subject,
                "metadata.topic": selected_topic
            })
            
            if existing_file:
                fs.delete(existing_file["_id"])
            
            file_id = fs.put(
                file_data,
                filename=file_name,
                metadata={
                    "subject": selected_subject,
                    "topic": selected_topic,
                    "path": folder_path
                }
            )
            del file_data
            st.success(f"✅ **{file_name}** has been uploaded!")
        except Exception as e:
            st.error(f"Error uploading file: {str(e)}")
    gc.collect()

st.subheader(f"📄 PDFs in **{selected_topic}**")

try:
    pdf_files_cursor = db.fs.files.find({
        "metadata.subject": selected_subject,
        "metadata.topic": selected_topic
    })
    
    pdf_files_list = list(pdf_files_cursor)
    pdf_files = [file["filename"] for file in pdf_files_list]
    
    if pdf_files:
        selected_index = 0
        if st.session_state.selected_pdf in pdf_files:
            selected_index = pdf_files.index(st.session_state.selected_pdf)
        
        selected_pdf = st.selectbox("📜 Select a PDF to View or Delete", pdf_files, index=selected_index)
        
        st.session_state.selected_pdf = selected_pdf
        
        file_metadata = db.fs.files.find_one({
            "filename": selected_pdf,
            "metadata.subject": selected_subject,
            "metadata.topic": selected_topic
        })
        
        if file_metadata:
            try:
                pdf_data = fs.get(file_metadata["_id"]).read()
                pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")
                
                st.download_button(
                    "⬇️ Download PDF", 
                    pdf_data, 
                    file_name=selected_pdf, 
                    mime="application/pdf"
                )
                
                st.markdown(
                    f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="700" height="500"></iframe>',
                    unsafe_allow_html=True,
                )
                
                if st.button("🗑️ Delete PDF"):
                    try:
                        fs.delete(file_metadata["_id"])
                        st.warning(f"🚮 **{selected_pdf}** has been deleted!")
                        st.session_state.selected_pdf = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting file: {str(e)}")
                        
                del pdf_data
                del pdf_base64
                
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
        else:
            st.error("File metadata found but file could not be retrieved.")
    else:
        st.info("📌 No PDFs uploaded yet.")
except Exception as e:
    st.error(f"Error accessing MongoDB: {str(e)}")

pdf_files_cursor = db.fs.files.find({
    "metadata.subject": selected_subject,
    "metadata.topic": selected_topic,
    "metadata.linked_pdf": {"$exists": False}
})

pdf_files_list = list(pdf_files_cursor)
pdf_files = [file["filename"] for file in pdf_files_list]

if pdf_files:
    formatted_pdf_names = {pdf: pdf.replace(".pdf", "") for pdf in pdf_files}
    
    st.subheader("📝 Upload Practice Questions")
    selected_study_pdf = st.selectbox(
        "📌 Select the topic for which you want to upload the practice test",
        list(formatted_pdf_names.values())
    )
    
    selected_study_pdf_filename = [
        k for k, v in formatted_pdf_names.items() if v == selected_study_pdf
    ][0]
    
    practice_filename = f"{selected_study_pdf}_practicequestions.pdf"
    
    existing_practice_file = db.fs.files.find_one({
        "filename": practice_filename,
        "metadata.subject": selected_subject,
        "metadata.topic": selected_topic
    })
    
    practice_question_file = st.file_uploader(
        "Upload Practice Question PDF", type=["pdf"], key="practice_uploader"
    )
    
    if practice_question_file:
        try:
            with io.BytesIO() as buffer:
                buffer.write(practice_question_file.getvalue())
                buffer.seek(0)
                practice_file_data = buffer.read()
    
            if existing_practice_file:
                fs.delete(existing_practice_file["_id"])
    
            file_id = fs.put(
                practice_file_data,
                filename=practice_filename,
                metadata={
                    "subject": selected_subject,
                    "topic": selected_topic,
                    "linked_pdf": selected_study_pdf_filename,
                    "path": folder_path,
                    "is_practice": True
                }
            )
    
            st.success(f"✅ Practice questions for **{selected_study_pdf}** have been uploaded!")
    
        except Exception as e:
            st.error(f"Error uploading practice questions: {str(e)}")
    
    if existing_practice_file:
        st.subheader(f"📜 Practice Questions for **{selected_study_pdf}**")
    
        try:
            practice_file_data = fs.get(existing_practice_file["_id"]).read()
            practice_base64 = base64.b64encode(practice_file_data).decode("utf-8")
    
            st.download_button(
                "⬇️ Download Practice Questions", 
                practice_file_data, 
                file_name=practice_filename, 
                mime="application/pdf"
            )
    
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{practice_base64}" width="700" height="500"></iframe>',
                unsafe_allow_html=True,
            )
    
            if st.button("🗑️ Delete Practice Questions"):
                try:
                    fs.delete(existing_practice_file["_id"])
                    st.warning(f"🚮 Practice questions for **{selected_study_pdf}** have been deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting practice questions: {str(e)}")
    
        except Exception as e:
            st.error(f"Error retrieving practice questions file: {str(e)}")

gc.collect()