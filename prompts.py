# prompts.py

SYSTEM_PROMPT = """
You are an AI hiring assistant.
Return STRICT JSON only. No markdown, no code fences, no extra text.
If you are unsure, still return valid JSON that matches the schema.
"""

USER_PROMPT_TEMPLATE = """
Analyze the following candidate CV against the job description.

Return JSON with keys:
- summary (string, 3-5 sentences)
- extracted_skills (list of strings)
- - job_keywords (list of 10-15 strings). Each item MUST be a concrete skill/tool/tech/task noun phrase (e.g., "Python", "API integration", "Zapier/Make", "LLM workflow", "prompt engineering", "data analysis"). 
Do NOT include generic words like "familiarity", "basic knowledge", "intern", "role".
- match_score (integer 0..100)
- strengths (list of strings)
- gaps (list of strings)
- interview_questions (list of exactly 5 strings)

IMPORTANT:
- Output MUST be valid JSON.
- Do NOT include any additional keys.
- Do NOT include markdown.

CV:
{cv_text}

JOB DESCRIPTION:
{job_text}
"""