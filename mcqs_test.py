import io
import streamlit as st
import fitz  # PyMuPDF
import time
import re
import random
from datetime import datetime, timedelta
from session_manager import navigate_to  # Import navigation function
from study_resources import get_database_connection
# st.set_page_config(
#     page_title="Online MCQ Test Platform",
#     page_icon="📝",
#     layout="wide"
# )
def extract_topic_from_filename(filename: str) -> str:
    """
    Extracts the topic name from a filename like:
    M-01_IntroductiontoStatisticalMethodsofAnalysis_practicequestions.pdf

    Steps:
    1. Remove the file extension (.pdf).
    2. Replace hyphens with underscores to standardize separators.
    3. Split on underscores.
    4. Confirm the first two segments are "M" and digits (e.g., "01").
    5. Everything from the third segment up to the last segment (which should be 'practicequestions')
       is joined to form the topic.
    """
    # 1. Strip off the .pdf extension
    if filename.lower().endswith(".pdf"):
        filename = filename[:-4]  # Remove last 4 chars (.pdf)

    # 2. Replace hyphens with underscores
    normalized = filename.replace('-', '_')

    # 3. Split on underscores
    parts = normalized.split('_')
    # Example:
    #   "M_01_IntroductiontoStatisticalMethodsofAnalysis_practicequestions"
    #   parts => ["M", "01", "IntroductiontoStatisticalMethodsofAnalysis", "practicequestions"]

    # 4. Basic validation:
    #    - The first part should be "M" (ignoring case).
    #    - The second part should be numeric (the module number).
    #    - The last part is "practicequestions".
    #    - Everything in between is the actual topic name.
    if len(parts) < 4:
        return "Unknown Topic"

    if parts[0].upper() == "M" and parts[-1].lower() == "practicequestions" and parts[1].isdigit():
        # 5. Join all segments from index 2 up to the one before the last
        #    to form the topic name.
        topic_parts = parts[2:-1]  # everything between the module number and 'practicequestions'
        topic = "_".join(topic_parts)  # join them with underscores if needed
        topic = topic.replace('_', ' ')  # convert underscores to spaces
        return topic.title().strip()

    return "Unknown Topic"


def get_attempt_number(db, username: str, topic_name: str) -> int:
    collection = db.test_attempts
    count = collection.count_documents({"username": username, "topic_name": topic_name})
    return count + 1

def store_test_attempt(db, test_data: dict):
    collection = db.test_attempts
    result = collection.insert_one(test_data)
    return result.inserted_id
def initialize_test_session():
    """Ensure all required session state variables are initialized."""
    session_defaults = {
        "test_started": False,
        "mcqs": [],
        "current_index": 0,
        "score": 0,
        "selected_answers": {},
        "results": [],
        "question_timers": {},
        "question_status": {},
        "last_update_time": datetime.now(),
        "all_questions_processed": False,
        "focus_lost": False,
        "focus_confirmed": False,
        "attempt_stored": False
    }
    
    for key, default in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

# Initialize session before accessing any session state variables
initialize_test_session()

st.markdown("""
<style>
    .hidden-button {
        display: none;
    }
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #E5E7EB;
    }
    .question-container {
        color:black;
        background-color: #F9FAFB;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #E5E7EB;
        margin-bottom: 1.5rem;
    }
    .timer-display {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        padding: 0.5rem;
        border-radius: 0.3rem;
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        margin-bottom: 1rem;
    }
    .score-display {
        color:black;
        font-size: 1.8rem;
        text-align: center;
        padding: 1rem;
        background-color: #ECFDF5;
        border-radius: 0.5rem;
        border: 1px solid #A7F3D0;
        margin-top: 2rem;
    }
    .option-text {
        font-size: 1.1rem;
    }
    .test-complete {
        background-color: #F9FAFB;
        padding: 2rem;
        border-radius: 0.5rem;
        border: 1px solid #E5E7EB;
        text-align: center;
    }
    .button-container {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin-top: 1.5rem;
    }
    .stButton>button {
        background-color: #1E40AF;
        color: white;
        padding: 0.5rem 2rem;
    }
    .navigation-panel {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E5E7EB;
        margin-bottom: 1.5rem;
    }
    .nav-button {
        margin: 0.25rem;
        padding: 0.5rem;
        min-width: 2.5rem;
        height: 2.5rem;
        border-radius: 0.3rem;
        font-weight: bold;
        display: inline-block;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
    }
    .nav-button-active {
        background-color: #1E40AF;
        color: white;
        border: 1px solid #1E3A8A;
    }
    .nav-button-completed {
        background-color: #D1FAE5;
        color: #065F46;
        border: 1px solid #A7F3D0;
    }
    .nav-button-expired {
        background-color: #FEE2E2;
        color: #B91C1C;
        border: 1px solid #FECACA;
    }
    .nav-button-pending {
        background-color: #E5E7EB;
        color: #4B5563;
        border: 1px solid #D1D5DB;
    }
</style>
""", unsafe_allow_html=True)
def extract_mcqs_from_pdf(pdf_file):
    pdf_file.seek(0)
    extracted_text = ""
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        for page in doc:
            extracted_text += page.get_text("text") + "\n\n"
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return []
    mcq_pattern = re.compile(
        r'(\d+)\.\s*(.+?)\n'
        r'A\)\s*(.+?)\n'
        r'B\)\s*(.+?)\n'
        r'C\)\s*(.+?)\n'
        r'D\)\s*(.+?)\n'
        r'Answer:\s*([ABCD])',
        re.DOTALL | re.MULTILINE
    )
    mcqs = []
    for match in mcq_pattern.finditer(extracted_text):
        question = match.group(2).strip()
        options = {
            "A": match.group(3).strip(),
            "B": match.group(4).strip(),
            "C": match.group(5).strip(),
            "D": match.group(6).strip(),
        }
        correct_answer = match.group(7).strip()
        mcqs.append({"question": question, "options": options, "answer": correct_answer})
    return mcqs
if "test_started" not in st.session_state:
    st.session_state["test_started"] = False
if "mcqs" not in st.session_state:
    st.session_state["mcqs"] = []
if "current_index" not in st.session_state:
    st.session_state["current_index"] = 0
if "score" not in st.session_state:
    st.session_state["score"] = 0
if "selected_answers" not in st.session_state:
    st.session_state["selected_answers"] = {}
if "results" not in st.session_state:
    st.session_state["results"] = []
if "question_timers" not in st.session_state:
    st.session_state["question_timers"] = {}
if "question_status" not in st.session_state:
    st.session_state["question_status"] = {}
if "last_update_time" not in st.session_state:
    st.session_state["last_update_time"] = datetime.now()
if "all_questions_processed" not in st.session_state:
    st.session_state["all_questions_processed"] = False
def navigate_to_question(question_index):
    if question_index < len(st.session_state["mcqs"]):
        st.session_state["current_index"] = question_index
        st.session_state["last_update_time"] = datetime.now()
def update_timers():
    now = datetime.now()
    elapsed_seconds = (now - st.session_state["last_update_time"]).total_seconds()
    st.session_state["last_update_time"] = now
    current_idx = st.session_state["current_index"]
    if current_idx in st.session_state["question_timers"] and st.session_state["question_timers"][current_idx] > 0:
        st.session_state["question_timers"][current_idx] = max(0, st.session_state["question_timers"][current_idx] - elapsed_seconds)
        if st.session_state["question_timers"][current_idx] <= 0:
            handle_time_up(current_idx)
def handle_time_up(question_index):
    mcqs = st.session_state["mcqs"]
    option_key = f"option_q{question_index}"
    st.session_state["question_status"][question_index] = "expired"
    if option_key in st.session_state and st.session_state[option_key]:
        selected_option = st.session_state[option_key][0]
    else:
        selected_option = "Not answered"
    is_correct = selected_option == mcqs[question_index]["answer"]
    if question_index >= len(st.session_state["results"]):
        st.session_state["results"].append({
            "question": mcqs[question_index]["question"],
            "user_answer": selected_option,
            "correct_answer": mcqs[question_index]["answer"],
            "is_correct": is_correct
        })
    next_index = find_next_available_question(question_index)
    if next_index is not None:
        st.session_state["current_index"] = next_index
        st.session_state["question_status"][next_index] = "active"
    else:
        st.session_state["current_index"] = len(mcqs)
        st.session_state["all_questions_processed"] = True
def find_next_available_question(current_index):
    mcqs = st.session_state["mcqs"]
    for i in range(len(mcqs)):
        status = st.session_state["question_status"].get(i, "pending")
        if status not in ["completed", "expired"] and i != current_index:
            return i
    return None
def reset_session():
    st.session_state["test_started"] = False
    st.session_state["current_index"] = 0
    st.session_state["score"] = 0
    st.session_state["selected_answers"] = {}
    st.session_state["results"] = []
    st.session_state["question_timers"] = {}
    st.session_state["question_status"] = {}
    st.session_state["all_questions_processed"] = False
    st.session_state["focus_lost"] = False
    st.session_state["focus_confirmed"] = False
    st.session_state["mcqs"] = []
    st.session_state["attempt_stored"] = False

def main():
    if "focus_lost" not in st.session_state:
        st.session_state["focus_lost"] = False
    if "focus_confirmed" not in st.session_state:
        st.session_state["focus_confirmed"] = False
    
    # Get database connection at the start of the function
    db, fs = get_database_connection()
    
    if not st.session_state["test_started"]:
        st.markdown("<h1 class='main-header'>📝 Online MCQ Test Platform</h1>", unsafe_allow_html=True)
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("### Upload your PDF containing MCQ questions")
                st.markdown("The PDF should have questions in the format:")
                st.code("""1. What is the capital of France?
A) London
B) Berlin
C) Paris
D) Madrid
Answer: C""")
                st.warning("⚠️ Warning: Switching tabs or applications during the test will be considered cheating and will end your test automatically.", icon="⚠️")
                if "selected_practice_pdf" not in st.session_state or not st.session_state.selected_practice_pdf:
                    st.error("❌ No practice PDF selected. Please go back and select a practice test.")
                    if st.button("🔙 Return to Study Materials", use_container_width=True):
                        reset_session()
                        navigate_to("study_resources")
                        st.rerun()
                else:
                    selected_pdf_data = db.fs.files.find_one({"filename": st.session_state.selected_practice_pdf})

                    if selected_pdf_data:
                        topic_name = extract_topic_from_filename(st.session_state.selected_practice_pdf)
                        st.session_state["test_topic"] = topic_name
                        attempt_number = get_attempt_number(db, st.session_state.get("user_session", "guest"), topic_name)
                        st.session_state["attempt_number"] = attempt_number
                        with st.spinner("Fetching practice questions..."):
                            pdf_data = fs.get(selected_pdf_data["_id"]).read()
                            extracted_mcqs = extract_mcqs_from_pdf(io.BytesIO(pdf_data))
                        
                        if extracted_mcqs:
                            st.success(f"✅ Successfully extracted {len(extracted_mcqs)} questions!")
                            st.session_state["mcqs"] = extracted_mcqs
                            random.shuffle(st.session_state["mcqs"])
                            
                            if st.button("🚀 Start Test", use_container_width=True):
                                # ✅ Reset test-related session variables before starting
                                st.session_state.update({
                                    "test_started": True,
                                    "current_index": 0,
                                    "score": 0,
                                    "selected_answers": {},
                                    "results": [],
                                    "question_timers": {i: 60 for i in range(len(extracted_mcqs))},
                                    "question_status": {i: "pending" for i in range(len(extracted_mcqs))},
                                    "all_questions_processed": False,
                                    "focus_lost": False,
                                    "total_test_start_time": datetime.now(),
                                    "question_start_time": datetime.now()  # Reset the start time for the first question
                                })
                                st.session_state["question_status"][0] = "active"  # ✅ Ensure first question is active
                                st.rerun()

                        else:
                            st.error("❌ No MCQs found in the selected practice PDF.")

    elif st.session_state["focus_lost"]:
        st.markdown("<h1 class='main-header'>⚠️ Test Terminated - Cheating Detected</h1>", unsafe_allow_html=True)
        st.error("Your test has been terminated because you switched tabs or applications during the test, which is against the rules.")
        mcqs = st.session_state["mcqs"]
        for i in range(len(mcqs)):
            if i >= len(st.session_state["results"]):
                st.session_state["results"].append({
                    "question": mcqs[i]["question"],
                    "user_answer": "Not answered",
                    "correct_answer": mcqs[i]["answer"],
                    "is_correct": False,
                    "time_taken": 0  # Add time taken field
                })
        score = sum(1 for result in st.session_state["results"] if result["is_correct"])
        total = len(mcqs)
        percentage = (score / total) * 100 if total > 0 else 0
        st.markdown(f"""
        <div class='score-display' style='background-color: #FEE2E2; border-color: #F87171;'>
            <h2>Your Score: {score} out of {total} ({percentage:.1f}%)</h2>
            <p>Test terminated due to suspicious activity</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start New Test", use_container_width=True):
            reset_session()
            navigate_to("study_resources")
            st.rerun()
    else:
        mcqs = st.session_state["mcqs"]
        current_index = st.session_state["current_index"]
        update_timers()
        if current_index < len(mcqs):
            st.markdown("<h1 class='main-header'>📝 Online MCQ Test</h1>", unsafe_allow_html=True)
            st.markdown("""
            <script>
            document.addEventListener('visibilitychange', function() {
                if (document.visibilityState === 'hidden') {
                    window.parent.postMessage({type: 'focus_lost'}, '*');
                }
            });
            </script>
            """, unsafe_allow_html=True)
            focus_detector = st.empty()
            if focus_detector.checkbox("Focus lost", value=False, key="focus_lost_checkbox", label_visibility="collapsed"):
                st.session_state["focus_lost"] = True
                st.rerun()
            st.markdown("<h3>Question Navigation:</h3>", unsafe_allow_html=True)
            nav_html = "<div class='navigation-panel'>"
            for i in range(len(mcqs)):
                status = st.session_state["question_status"].get(i, "pending")
                remaining_time = int(st.session_state["question_timers"].get(i, 0))
                if i == current_index:
                    button_class = "nav-button nav-button-active"
                    title = f"Current Question - {remaining_time}s left"
                elif status == "completed":
                    button_class = "nav-button nav-button-completed"
                    title = "Answered"
                elif status == "expired":
                    button_class = "nav-button nav-button-expired"
                    title = "Time's up"
                else:
                    button_class = "nav-button nav-button-pending"
                    title = f"{remaining_time}s left"
                if status not in ["completed", "expired"]:
                    nav_html += f"<div class='{button_class}' title='{title}' onclick='document.getElementById(\"nav-btn-{i}\").click()'>{i+1}</div>"
                else:
                    nav_html += f"<div class='{button_class}' title='{title}'>{i+1}</div>"
            nav_html += "</div>"
            st.markdown(nav_html, unsafe_allow_html=True)
            nav_col = st.columns(min(10, len(mcqs)))
            for i in range(len(mcqs)):
                status = st.session_state["question_status"].get(i, "pending")
                if status not in ["completed", "expired"] and i != current_index:
                    with nav_col[i % len(nav_col)]:
                        if st.button(f"{i+1}", key=f"nav-btn-{i}", help=f"Navigate to question {i+1}"):
                            navigate_to_question(i)
            progress_text = f"Question {current_index + 1} of {len(mcqs)}"
            progress_value = (current_index + 1) / len(mcqs)
            st.progress(progress_value)
            st.container().empty()
            col1, col2 = st.columns([3, 1])
            with col1:
                question_data = mcqs[current_index]
                st.markdown(f"""
                <div class='question-container'>
                    <h3>Question {current_index + 1}:</h3>
                    <p style='font-size: 1.2rem;'>{question_data['question']}</p>
                </div>
                """, unsafe_allow_html=True)
                option_key = f"option_q{current_index}"
                options = list(question_data["options"].items())
                default_index = None
                if option_key in st.session_state:
                    selected_option = st.session_state[option_key]
                    if selected_option:
                        for idx, (opt_key, _) in enumerate(options):
                            if opt_key == selected_option[0]:
                                default_index = idx
                                break
                selected_option = st.radio(
                    "Select your answer:",
                    options,
                    format_func=lambda x: f"{x[0]}) {x[1]}",
                    key=option_key,
                    index=default_index,
                    label_visibility="collapsed"
                )
                submit_button = st.button("Submit & Next ▶️", use_container_width=True)
                if submit_button:
                    # Track time taken for the current question
                    time_taken = (datetime.now() - st.session_state.get("question_start_time", datetime.now())).total_seconds()
                    st.session_state["question_start_time"] = datetime.now()  # Reset for next question
    
                    user_answer = selected_option[0] if selected_option else None
                    is_correct = user_answer == question_data["answer"] if user_answer else False
                    
                    # Modify the results to include time taken
                    question_result = {
                        "question": question_data["question"],
                        "user_answer": user_answer if user_answer else "Not answered",
                        "correct_answer": question_data["answer"],
                        "is_correct": is_correct,
                        "time_taken": time_taken  # Add time taken for this question
                    }
                    
                    if current_index >= len(st.session_state["results"]):
                        st.session_state["results"].append(question_result)
                    else:
                        st.session_state["results"][current_index] = question_result
                    
                    if is_correct:
                        st.session_state["score"] += 1
                    st.session_state["question_status"][current_index] = "completed"
                    next_index = find_next_available_question(current_index)
                    if next_index is not None:
                        st.session_state["current_index"] = next_index
                        st.session_state["question_status"][next_index] = "active"
                    else:
                        st.session_state["current_index"] = len(mcqs)
                        st.session_state["all_questions_processed"] = True
                    st.rerun()
            with col2:
                remaining_time = int(st.session_state["question_timers"].get(current_index, 0))
                timer_color = "#1E3A8A" if remaining_time > 10 else "#DC2626"
                st.markdown(f"""
                <div class='timer-display' style='color: {timer_color};'>
                    ⏱️ {remaining_time} seconds
                </div>
                """, unsafe_allow_html=True)
                completed_count = sum(1 for status in st.session_state["question_status"].values() if status in ["completed", "expired"])
                st.markdown(f"**Progress:** {completed_count}/{len(mcqs)} questions")
                st.markdown("**Question Status:**")
                for i in range(len(mcqs)):
                    status = st.session_state["question_status"].get(i, "pending")
                    time_left = int(st.session_state["question_timers"].get(i, 0))
                    if status == "completed":
                        st.markdown(f"- Q{i+1}: ✅ Answered")
                    elif status == "expired":
                        st.markdown(f"- Q{i+1}: ⏱️ Time's up")
                    elif i == current_index:
                        st.markdown(f"- Q{i+1}: 🔍 **Current** ({time_left}s)")
                    else:
                        st.markdown(f"- Q{i+1}: ⏳ Pending ({time_left}s)")
            time.sleep(0.5)
            st.rerun()
        else:
            if current_index >= len(mcqs):  # Test complete branch
                # Ensure that any unanswered questions are marked as "Not answered"
                for i in range(len(mcqs)):
                    if i >= len(st.session_state["results"]):
                        st.session_state["results"].append({
                            "question": mcqs[i]["question"],
                            "user_answer": "Not answered",
                            "correct_answer": mcqs[i]["answer"],
                            "is_correct": False,
                            "time_taken": 0  # Add time taken field
                        })
                
                # Calculate overall score and percentage
                score = sum(1 for result in st.session_state["results"] if result["is_correct"])
                total = len(mcqs)
                percentage = (score / total) * 100 if total > 0 else 0

                # Calculate total test time
                total_test_time = (datetime.now() - st.session_state.get("total_test_start_time", datetime.now())).total_seconds()

                # Only store the attempt if it hasn't been stored yet
                if not st.session_state.get("attempt_stored", False):
                    test_attempt = {
                        "username": st.session_state.get("user_session", "guest"),
                        "topic_name": st.session_state.get("test_topic", "Unknown Topic"),
                        "attempt_number": st.session_state.get("attempt_number", 1),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "total_score": score,
                        "total_questions": total,
                        "total_time_taken": total_test_time,
                        "average_time_per_question": total_test_time / total if total > 0 else 0,
                        "results": st.session_state["results"]
                    }
                    attempt_id = store_test_attempt(db, test_attempt)
                    st.success(f"Test attempt saved with id: {attempt_id}")
                    st.session_state["attempt_stored"] = True  # Set the flag to avoid duplicate storage

                # Display final results
                st.markdown("<h1 class='main-header'>🎉 Test Completed!</h1>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div class='score-display'>
                        <h2>Your Score: {score} out of {total} ({percentage:.1f}%)</h2>
                        <p>{'🏆 Excellent!' if percentage >= 80 else '👍 Good job!' if percentage >= 60 else '📚 Keep practicing!'}</p>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("### Detailed Results")
                for i, result in enumerate(st.session_state["results"]):
                    try:
                        status_icon = "✅" if result.get("is_correct", False) else "❌"
                        with st.expander(f"Question {i+1}: {status_icon}"):
                            st.markdown(f"**Question:** {result.get('question', 'No question text')}")
                            st.markdown(f"**Your Answer:** {result.get('user_answer', 'No answer')}")
                            st.markdown(f"**Correct Answer:** {result.get('correct_answer', 'No correct answer')}")
                            st.markdown(f"**Time Taken:** {result.get('time_taken', 0):.2f} seconds")
                    except Exception as e:
                        st.error(f"Error displaying result for question {i+1}: {e}")
                        st.write(result)
                
                # Display total test time
                st.markdown(f"**Total Test Time:** {total_test_time:.2f} seconds")
                st.markdown(f"**Average Time per Question:** {total_test_time/total:.2f} seconds")
                
                if st.button("Start New Test", use_container_width=True):
                    reset_session()
                    navigate_to("study_resources")
                    st.rerun()
if __name__ == "__main__":
    main()