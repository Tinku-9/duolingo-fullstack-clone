import re
from datetime import date, timedelta


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold()).rstrip(".!?¿¡ ")


def validate_answer(exercise_type: str, public: dict, answer: dict) -> None:
    if len(str(answer)) > 5000:
        raise ValueError("Answer is too long")
    if exercise_type == "multiple_choice":
        if answer.get("option_id") not in {x["id"] for x in public["options"]}:
            raise ValueError("Choose one of the supplied options")
    elif exercise_type == "word_bank":
        tokens = answer.get("token_ids")
        available = {x["id"] for x in public["tokens"]}
        if not isinstance(tokens, list) or not tokens or not all(isinstance(x, str) and x in available for x in tokens) or len(set(tokens)) != len(tokens):
            raise ValueError("Select supplied word tokens once each")
    elif exercise_type == "match_pairs":
        pairs = answer.get("pairs")
        left = {x["id"] for x in public["left"]}
        right = {x["id"] for x in public["right"]}
        if not isinstance(pairs, dict) or set(pairs) != left or not all(isinstance(x, str) and x in right for x in pairs.values()) or len(set(pairs.values())) != len(right):
            raise ValueError("Match every supplied word exactly once")
    elif not isinstance(answer.get("text"), str) or not answer["text"].strip():
        raise ValueError("Enter an answer")


def grade(exercise_type: str, public: dict, expected: dict, submitted: dict) -> bool:
    if exercise_type == "multiple_choice":
        return submitted.get("option_id") == expected["option_id"]
    if exercise_type == "word_bank":
        return submitted.get("token_ids") == expected["token_ids"]
    if exercise_type == "match_pairs":
        return submitted.get("pairs") == expected["pairs"]
    if exercise_type in {"fill_blank", "type_answer"}:
        text = submitted.get("text")
        return isinstance(text, str) and normalize(text) in {normalize(x) for x in expected["accepted"]}
    raise ValueError("Unsupported exercise type")


def correction(exercise_type: str, public: dict, expected: dict) -> str:
    if exercise_type == "multiple_choice":
        return next(x["text"] for x in public["options"] if x["id"] == expected["option_id"])
    if exercise_type == "word_bank":
        tokens = {x["id"]: x["text"] for x in public["tokens"]}
        return " ".join(tokens[x] for x in expected["token_ids"])
    if exercise_type == "match_pairs":
        left = {x["id"]: x["text"] for x in public["left"]}
        right = {x["id"]: x["text"] for x in public["right"]}
        return "; ".join(f"{left[a]} = {right[b]}" for a, b in expected["pairs"].items())
    return expected["accepted"][0]


def current_streak(active_dates: set[date], today: date) -> int:
    cursor = today if today in active_dates else today - timedelta(days=1)
    streak = 0
    while cursor in active_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
