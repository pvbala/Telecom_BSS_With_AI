from llm.client import generate


def summarize_ticket(subject: str, description: str,
                      gemini_key: str | None = None, grok_key: str | None = None) -> str:
    prompt = (f"Summarize this customer support ticket in one sentence.\n"
              f"Subject: {subject}\nDescription: {description}")
    return generate(prompt, gemini_key=gemini_key, grok_key=grok_key)["text"]


def draft_reply(subject: str, description: str,
                 gemini_key: str | None = None, grok_key: str | None = None) -> str:
    prompt = (f"Draft a short, polite customer support reply (3-4 sentences) for this ticket.\n"
              f"Subject: {subject}\nDescription: {description}")
    return generate(prompt, gemini_key=gemini_key, grok_key=grok_key)["text"]