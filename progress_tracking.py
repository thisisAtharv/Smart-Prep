import streamlit as st
import pandas as pd
from datetime import datetime
from study_resources import get_database_connection

def show_progress_tracking():
    # Add a back button to return to home or the previous page
    if st.button("← Back to Home"):
        from session_manager import navigate_to
        navigate_to("home")
        
    st.markdown("<h1 class='main-header'>Progress Tracking</h1>", unsafe_allow_html=True)
    
    # Connect to MongoDB (adjust this based on your actual connection logic)
    db, fs = get_database_connection()
    collection = db.test_attempts

    # Get current user's username
    username = st.session_state.get("user_session", "guest")
    
    # Fetch all distinct topics for which the user has attempted tests
    topics = collection.distinct("topic_name", {"username": username})
    
    if not topics:
        st.info("No test attempts found. Start taking tests to see your progress!")
        return

    # Let user select a topic from the dropdown
    selected_topic = st.selectbox("Topics for which you have attempted the test", topics)
    
    # Fetch all test attempts for the selected topic, sorted by timestamp (most recent first)
    attempts = list(collection.find({
        "username": username,
        "topic_name": selected_topic
    }).sort("timestamp", -1))
    
    if not attempts:
        st.info("No test attempts found for this topic. Start taking tests to see your progress!")
        return

    # ---------------- Progress Summary Dashboard ----------------
    total_attempts = len(attempts)
    avg_score = 0
    total_time = 0
    total_questions = 0

    # Data for score over time chart
    chart_data = []
    
    for attempt in attempts:
        # Calculate percentage score for this attempt
        total_q = attempt.get('total_questions', 1)
        score = attempt.get('total_score', 0)
        score_percent = (score / total_q) * 100
        avg_score += score_percent
        
        # Attempt timestamp (assuming stored as a string; adjust parsing as needed)
        timestamp = attempt.get("timestamp", "")
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                dt = datetime.strptime(timestamp, "%Y-%m-%d")
            except Exception:
                dt = datetime.now()
                
        chart_data.append({"Date": dt, "Score (%)": score_percent})
        
        # Sum up time taken for each question in this attempt
        results = attempt.get("results", [])
        for result in results:
            if "time_taken" in result:
                total_time += result["time_taken"]
                total_questions += 1

    avg_score = avg_score / total_attempts if total_attempts > 0 else 0
    avg_time = total_time / total_questions if total_questions > 0 else 0

    st.subheader("Progress Summary Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Attempts", total_attempts)
    col2.metric("Average Score (%)", f"{avg_score:.2f}%")
    col3.metric("Average Time per Question (s)", f"{avg_time:.2f}")

    # ---------------- Visual Analytics: Score Trend ----------------
    st.subheader("Score Trend Over Time")
    df_chart = pd.DataFrame(chart_data)
    df_chart = df_chart.sort_values("Date")
    # Using Streamlit's built-in line chart for quick visualization
    st.line_chart(df_chart.rename(columns={"Date": "index"}).set_index("index"))

    # ---------------- Detailed Statistical Insights ----------------
    st.subheader("Test Attempts Accuracy Overview")
    stats_data = []
    for idx, attempt in enumerate(attempts):
        results = attempt.get("results", [])
        correct = sum(1 for r in results if r.get("is_correct"))
        incorrect = len(results) - correct
        stats_data.append({"Attempt": idx + 1, "Correct": correct, "Incorrect": incorrect})
    df_stats = pd.DataFrame(stats_data)
    # Using bar chart to compare correct vs incorrect counts for each attempt
    st.bar_chart(df_stats.set_index("Attempt"))

    # ---------------- Detailed Results for Each Attempt ----------------
    st.subheader("Detailed Test Attempt Results")
    for attempt in attempts:
        st.markdown(f"### Topic: {attempt.get('topic_name', 'N/A')} (Attempt #{attempt.get('attempt_number', 1)})")
        st.markdown(f"**Date:** {attempt.get('timestamp', 'N/A')}")
        st.markdown(f"**Score:** {attempt.get('total_score', 0)} out of {attempt.get('total_questions', 0)}")
        with st.expander("View Detailed Results"):
            results = attempt.get("results", [])
            for i, result in enumerate(results):
                status_icon = "✅" if result.get("is_correct") else "❌"
                st.markdown(f"**Q{i+1}:** {result.get('question', '')}")
                st.markdown(f"- **Your Answer:** {result.get('user_answer', '')} {status_icon}")
                st.markdown(f"- **Correct Answer:** {result.get('correct_answer', '')}")
                if "time_taken" in result:
                    st.markdown(f"- **Time Taken:** {result['time_taken']} seconds")
        st.markdown("---")
