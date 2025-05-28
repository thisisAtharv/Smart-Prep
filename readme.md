# Smart Prep

Smart Prep is an interactive, centralized platform designed to streamline competitive exam preparation—initially tailored for UPSC aspirants. It integrates categorized study materials, real-time current‑affairs updates, self‑assessment tools, and a community‑driven blog section, all within a lightweight web interface built on Streamlit. Smart Prep enhances learning efficiency by aggregating resources, delivering bite‑sized facts, and tracking progress to help aspirants stay organized and focused. citeturn0file0

---

## Features

- **User‑Friendly Dashboard**: Intuitive, responsive web interface with secure login and personalized home view. citeturn0file1
- **Categorized Study Resources**: Concise notes and PDFs organized by subject and topic for structured self‑study. citeturn0file1
- **Blog Section**: Aspirants can read, create, and manage posts on preparation strategies, syllabus updates, and motivational stories. citeturn0file0
- **MCQs & Quizzes**: Topic‑wise multiple‑choice questions and timed tests with instant feedback and performance summaries. citeturn0file1
- **Daily Facts & Insights**: Bite‑sized data points covering history, geography, science, and current affairs to boost retention. citeturn0file0
- **Real‑Time Updates**: Automated fetching of current affairs, exam notifications, and syllabus changes from trusted sources. citeturn0file0
- **Progress Tracking**: Visual analytics of quiz scores, completed topics, and learning trends over time. citeturn0file0

---

## Technology Stack

- **Frontend & Backend**: Python 3, Streamlit
- **Databases**:
  - MongoDB for unstructured content (blogs, current affairs).
  - SQLite for structured data (user profiles, quiz records, progress logs). citeturn0file0
- **Environment**:
  - VS Code (development)
  - Requirements managed via `requirements.txt`

---

## Project Structure

```plain
smart-prep/
├── __pycache__/
├── img_content/
├── .env
├── .gitignore
├── blog_section.py
├── delete_test.py
├── home.py
├── mang_profile.py
├── mcqs_test.py
├── progress_tracking.py
├── readme.md
├── resources_adder.py
├── session_manager.py
├── study_resources.py
├── testing.py
├── users.db
```

---

## System Architecture

Smart Prep follows a layered design:

1. **Presentation Layer** (Streamlit UI) – Handles user interactions and displays content.
2. **Application Layer** (Python Logic) – Implements business rules: authentication, content retrieval, and quiz evaluation.
3. **Data Layer** (MongoDB & SQLite) – Stores unstructured and structured data respectively.

Components communicate via lightweight API calls and internal module imports, ensuring modularity and scalability. citeturn0file1

---

## Workflow

1. **User Login** → Authenticate and initialize session.  
2. **Dashboard** → Personalized view with quick links to resources, quizzes, blogs, and facts.  
3. **Resource Access** → Browse organized study materials or enter quizzes.  
4. **Engagement** → Read/write blogs; view daily facts; attempt MCQs.  
5. **Progress Analytics** → Review performance trends and refine study path.

---

## Objectives

- Centralize all UPSC preparation resources in one platform.  
- Deliver up‑to‑date current affairs and examination notifications.  
- Facilitate active learning through quizzes, insights, and blogs.  
- Provide personalized progress tracking and recommendations.  
- Scale to support additional competitive exams (MPSC, GATE, banking). citeturn0file0

---

## Installation & Usage

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Itz-Om17/Smart-Prep
   cd smart-prep
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Databases**:
   - Ensure MongoDB is running; update connection URI in `modules/blog_section.py`.  
   - SQLite database will be initialized automatically on first run.

5. **Run the application**:
   ```bash
   streamlit run modules/home.py
   ```

6. **Access in browser** at `http://localhost:8501`.

---



