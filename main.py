import os
import json
import argparse
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from utils import read_text_file, safe_json_loads
from validator import validate_result
from scoring import keyword_coverage_score, final_score, decision_from_score


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
        raise RuntimeError("Rate limit exceeded. Please try again later.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="AI Hiring Copilot - CV vs Job analyzer")
    p.add_argument("--cv", default="sample_cv.txt", help="Path to CV text file")
    p.add_argument("--job", default="sample_job.txt", help="Path to Job description text file")
    p.add_argument("--out", default="", help="Optional output JSON file path")
    p.add_argument("--debug", action="store_true", help="Include debug fields in output")
    return p


def main():
    load_dotenv()
    if "OPENAI_API_KEY" not in os.environ:
        raise RuntimeError("OPENAI_API_KEY is missing. Put it into .env")

    parser = build_parser()
    args = parser.parse_args()

    cv_text = read_text_file(args.cv)
    job_text = read_text_file(args.job)

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    result = analyze(client, cv_text, job_text)

    is_valid, errors = validate_result(result)
    if not is_valid:
        print("Validation errors:")
        for e in errors:
            print("-", e)
        return

    # deterministic score from extracted job keywords
    job_keywords = result.get("job_keywords", [])
    kw_score, kw_debug = keyword_coverage_score(cv_text, job_keywords)

    llm_score = result["match_score"]
    combined = final_score(llm_score, kw_score)
    decision = decision_from_score(combined)

    # enrich result
    result["keyword_coverage_score"] = kw_score
    result["final_score"] = combined
    result["decision"] = decision

    if args.debug:
        result["keyword_coverage_debug"] = kw_debug

    # metadata (helpful for deployment/logging)
    result["_meta"] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "cv_file": args.cv,
        "job_file": args.job,
        "model": "gpt-4o-mini",
    }

    output_text = json.dumps(result, ensure_ascii=False, indent=2)
    print(output_text)

    # optional save
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"\nSaved to: {args.out}")


if __name__ == "__main__":
    main()