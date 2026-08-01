from llm.client import generate


def summarize_ticket(subject: str, description: str) -> str:
    prompt = (f"Summarize this customer support ticket in one sentence.\n"
              f"Subject: {subject}\nDescription: {description}")
    return generate(prompt)["text"]


def draft_reply(subject: str, description: str) -> str:
    prompt = (f"Draft a short, polite customer support reply (3-4 sentences) for this ticket.\n"
              f"Subject: {subject}\nDescription: {description}")
    return generate(prompt)["text"]
