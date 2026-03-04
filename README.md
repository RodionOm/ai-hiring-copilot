# AI Hiring Copilot

AI Hiring Copilot is a small AI-powered tool that analyzes a CV against a job description.

The system combines:

- LLM analysis (OpenAI)
- keyword matching
- rule-based scoring

The output is a structured hiring report.

---

# Features

- CV vs Job analysis
- skill extraction
- strengths and gaps detection
- interview questions generation
- hybrid scoring system

---

# Example Output

```json
{
  "summary": "AI-focused student with Python and ML experience",
  "match_score": 85,
  "keyword_coverage_score": 80,
  "final_score": 84,
  "decision": "PROCEED"
}