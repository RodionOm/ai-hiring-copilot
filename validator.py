from typing import Any, Dict, List, Tuple

REQUIRED_KEYS = [
    "summary",
    "extracted_skills",
    "job_keywords",
    "match_score",
    "strengths",
    "gaps",
    "interview_questions",
]

def validate_result(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    # защита на случай если data вообще не dict
    if not isinstance(data, dict):
        return False, ["Result must be a dictionary (parsed JSON)."]

    # если safe_json_loads вернул ошибку
    if "error" in data and "raw" in data:
        return False, [data["error"]]

    errors: List[str] = []

    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"Missing required key: {key}")
            continue

        if key == "summary":
            if not isinstance(data[key], str):
                errors.append("Key 'summary' must be a string.")

        elif key in ["extracted_skills", "job_keywords", "strengths", "gaps"]:
            if not isinstance(data[key], list) or not all(isinstance(item, str) for item in data[key]):
                errors.append(f"Key '{key}' must be a list of strings.")

            # job_keywords должен быть 10-15
            if key == "job_keywords" and isinstance(data[key], list):
                if not (10 <= len(data[key]) <= 15):
                    errors.append("Key 'job_keywords' must contain 10-15 strings.")

        elif key == "match_score":
            if not isinstance(data[key], int) or not (0 <= data[key] <= 100):
                errors.append("Key 'match_score' must be an integer between 0 and 100.")

        elif key == "interview_questions":
            if (
                not isinstance(data[key], list)
                or len(data[key]) != 5
                or not all(isinstance(item, str) for item in data[key])
            ):
                errors.append("Key 'interview_questions' must be a list of exactly 5 strings.")

    return (len(errors) == 0, errors)