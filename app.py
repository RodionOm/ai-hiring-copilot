import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from utils import safe_json_loads
from validator import validate_result
from scoring import keyword_coverage_score, final_score, decision_from_score


# -----------------------------
# Helpers
# -----------------------------
def analyze(client: OpenAI, cv_text: str, job_text: str) -> dict:
    user_prompt = USER_PROMPT_TEMPLATE.format(cv_text=cv_text, job_text=job_text)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": user_prompt.strip()},
            ],
            temperature=0.2,
        )
        raw = response.choices[0].message.content
        return safe_json_loads(raw)

    except RateLimitError:
        return {"error": "Rate limit exceeded. Please try again later."}


def pretty_badge(decision: str) -> str:
    # simple emoji badges
    if decision == "PROCEED":
        return "✅ PROCEED"
    if decision == "REVIEW":
        return "🟡 REVIEW"
    return "🔴 REJECT"


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="AI Hiring Copilot", page_icon="🤖", layout="wide")
st.title("🤖 AI Hiring Copilot")
st.caption("Analyze a CV against a Job Description using LLM + deterministic keyword coverage scoring.")

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY", "")
if not api_key:
    st.error("OPENAI_API_KEY is missing. Put it into .env and restart the app.")
    st.stop()

client = OpenAI(api_key=api_key)

# Layout: left = inputs, right = output
left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("📥 Inputs")

    cv_text = st.text_area(
        "CV Text",
        height=260,
        placeholder="Paste CV text here...",
    )

    job_text = st.text_area(
        "Job Description Text",
        height=260,
        placeholder="Paste job description here...",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        debug = st.checkbox("Show debug", value=False)
    with col_b:
        run = st.button("Analyze", type="primary", use_container_width=True)

with right:
    st.subheader("📊 Output")

    if run:
        if not cv_text.strip() or not job_text.strip():
            st.warning("Please paste both CV and Job Description text.")
            st.stop()

        with st.spinner("Analyzing..."):
            result = analyze(client, cv_text, job_text)

        # Handle API-level error
        if "error" in result and ("raw" not in result):
            st.error(result["error"])
            st.stop()

        # Validate structure
        is_valid, errors = validate_result(result)
        if not is_valid:
            st.error("Model returned invalid JSON structure.")
            st.write(errors)
            if "raw" in result:
                st.text_area("Raw model output (debug)", result["raw"], height=220)
            st.stop()

        # Deterministic scoring based on job_keywords extracted by LLM
        job_keywords = result.get("job_keywords", [])
        kw_score, kw_debug = keyword_coverage_score(cv_text, job_keywords)

        llm_score = result["match_score"]
        combined = final_score(llm_score, kw_score)
        decision = decision_from_score(combined)

        # enrich (for display/export)
        result["keyword_coverage_score"] = kw_score
        result["final_score"] = combined
        result["decision"] = decision

        # Summary header
        st.markdown(f"### {pretty_badge(decision)}")
        st.metric("Final Score", combined)
        st.columns(2)
        m1, m2 = st.columns(2)
        m1.metric("LLM Match Score", llm_score)
        m2.metric("Keyword Coverage Score", kw_score)

        st.divider()

        # Content sections
        st.markdown("#### 🧾 Summary")
        st.write(result["summary"])

        st.markdown("#### 🧠 Extracted skills")
        st.write(result["extracted_skills"])

        st.markdown("#### 🎯 Job keywords")
        st.write(result["job_keywords"])

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ✅ Strengths")
            st.write(result["strengths"])
        with c2:
            st.markdown("#### ⚠️ Gaps")
            st.write(result["gaps"])

        st.markdown("#### 🗣️ Interview questions")
        for i, q in enumerate(result["interview_questions"], start=1):
            st.write(f"{i}. {q}")

        if debug:
            st.divider()
            st.markdown("#### 🛠 Debug info")
            st.json(kw_debug)

        # Export JSON
        st.divider()
        st.markdown("#### 📤 Export")
        st.download_button(
            label="Download JSON",
            data=json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="analysis_result.json",
            mime="application/json",
            use_container_width=True
        )