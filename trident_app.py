
import streamlit as st
import random
import datetime
import matplotlib.pyplot as plt
import base64
import io
from jinja2 import Template
import pdfkit

# --- CONFIG ---
st.set_page_config(page_title="NovaPath TRIDENT", layout="centered")
st.title("🧭 NovaPath TRIDENT Adaptive Career Assessment")

# --- INPUT ---
user_id = st.text_input("Enter your name or ID:", key="uid")
if not user_id:
    st.stop()

seed = sum(ord(c) for c in user_id)

# --- STRUCTURE ---
sections = ["RIASEC", "Personality", "Aptitude", "EQ", "Learning"]
section_traits = {
    "RIASEC": ["Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"],
    "Personality": ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism",
                    "Detail-Oriented", "Flexible", "Empathetic", "Objective", "Resilient"],
    "Aptitude": ["Verbal", "Numerical", "Abstract", "Spatial", "Logical", "Mechanical"],
    "EQ": ["Self-Awareness", "Self-Regulation", "Motivation", "Empathy", "Social Skills"],
    "Learning": ["Linguistic", "Logical", "Visual", "Kinesthetic", "Interpersonal",
                 "Intrapersonal", "Musical", "Naturalistic"]
}

# --- QUESTION BANK ---
def create_question_bank():
    import json, os
    if not os.path.exists("question_bank.json"):
        st.error("❌ question_bank.json file not found. Please ensure it is uploaded to the app folder.")
        st.stop()
    try:
        with open("question_bank.json", "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading question bank: {e}")
        st.stop()

question_bank = create_question_bank()

def get_user_questions(bank, seed):
    rng = random.Random(seed)
    user_bank = {}
    for section, traits in bank.items():
        user_bank[section] = {}
        for trait, questions in traits.items():
            q_list = questions[:]
            rng.shuffle(q_list)
            user_bank[section][trait] = q_list
    return user_bank

user_qs = get_user_questions(question_bank, seed)

# --- STATE INIT ---
if "current_section_index" not in st.session_state:
    st.session_state.current_section_index = 0
if "trait_index" not in st.session_state:
    st.session_state.trait_index = 0
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "scores" not in st.session_state:
    st.session_state.scores = {s: {t: 0 for t in section_traits[s]} for s in sections}

# --- NAVIGATION ---
col1, col2, col3 = st.columns(3)
if col1.button("🔁 Restart Test"):
    st.session_state.current_section_index = 0
    st.session_state.trait_index = 0
    st.session_state.question_index = 0
    st.session_state.scores = {s: {t: 0 for t in section_traits[s]} for s in sections}
    st.experimental_rerun()

if col2.button("💾 Pause"):
    st.success("Progress saved. Resume anytime with the same ID.")
    st.stop()

if col3.button("➡️ Resume"):
    st.experimental_rerun()

# --- ASSESSMENT LOGIC ---
if st.session_state.current_section_index < len(sections):
    section = sections[st.session_state.current_section_index]
    traits = section_traits[section]
    trait = traits[st.session_state.trait_index]
    question = user_qs[section][trait][st.session_state.question_index]

    st.subheader(f"{section} → {trait}")
    score = st.slider(question, 1, 5, 3, key=f"{section}_{trait}_{st.session_state.question_index}")

    if st.button("Next"):
        st.session_state.scores[section][trait] += score
        st.session_state.question_index += 1

        if st.session_state.question_index >= 12:
            st.session_state.question_index = 0
            st.session_state.trait_index += 1

            if st.session_state.trait_index >= len(traits):
                st.session_state.trait_index = 0
                st.session_state.current_section_index += 1

                if st.session_state.current_section_index >= len(sections):
                    st.rerun = False  # Prevent rerun loop
                    st.stop()
                else:
                    st.experimental_rerun()
            else:
                st.experimental_rerun()

        else:
            st.experimental_rerun()

# --- CHART UTILITIES ---
def plot_bar_chart(data, title):
    fig, ax = plt.subplots()
    labels, scores = zip(*data.items())
    ax.bar(labels, scores, color="#4a90e2")
    ax.set_title(title)
    ax.set_ylim(0, 60)
    ax.set_ylabel("Score")
    plt.xticks(rotation=45)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def plot_radar_chart(data, title):
    labels = list(data.keys())
    scores = list(data.values())
    angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]
    scores += scores[:1]
    angles += angles[:1]
    fig, ax = plt.subplots(subplot_kw=dict(polar=True))
    ax.plot(angles, scores, linewidth=2)
    ax.fill(angles, scores, alpha=0.3)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_title(title)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

# --- REPORT ---
if st.session_state.current_section_index >= len(sections):
    st.header("🎓 Download Your Report")
    name = st.text_input("Full Name")
    grade = st.selectbox("Your Grade", ["9", "10", "11", "12"])

    if st.button("📄 Generate Report"):
        scores = st.session_state.scores
        riasec_code = "".join(sorted(scores["RIASEC"], key=scores["RIASEC"].get, reverse=True)[:3])

        render_data = {
            "student_name": name,
            "grade": grade,
            "test_date": datetime.date.today().strftime("%d %b %Y"),
            "RIASEC_CODE": riasec_code,
            "Top1": riasec_code[0], "Top2": riasec_code[1], "Top3": riasec_code[2],
            "Top1_Description": "Analytical and logical",
            "Top2_Description": "Empathetic and expressive",
            "Top3_Description": "Driven and confident",
            "career_1": "Software Engineer", "score_1": 91,
            "career_2": "Product Designer", "score_2": 88,
            "career_3": "Entrepreneur", "score_3": 86,
            "career_4": "Data Scientist", "score_4": 83,
            "career_5": "Teacher", "score_5": 80,
            "Primary_Style": max(scores["Learning"], key=scores["Learning"].get),
            "Secondary_Style": sorted(scores["Learning"], key=scores["Learning"].get, reverse=True)[1],
            "Learning_Tips": "Use visual tools and group work.",
            "Recommended_Stream": "Science + Technology",
            "Tip1": "Take up STEM projects", "Tip2": "Practice public speaking", "Tip3": "Engage in design challenges"
        }

        render_data["RIASEC_CHART"] = plot_bar_chart(scores["RIASEC"], "RIASEC Profile")
        render_data["PERSONALITY_CHART"] = plot_radar_chart(scores["Personality"], "Personality Traits")

        with open("novapath_trident_report_with_charts.html") as f:
            template = Template(f.read())
        html_report = template.render(render_data)

        with open("temp_report.html", "w") as f:
            f.write(html_report)

        pdf_path = f"{name.replace(' ', '_')}_TRIDENT_Report.pdf"
        pdfkit.from_file("temp_report.html", pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download Report", f, file_name=pdf_path, mime="application/pdf")
