from llm.client import generate


def narrate_anomaly(anomaly_result: dict, related_alarms: list[dict],
                     gemini_key: str | None = None, grok_key: str | None = None) -> str:
    """gemini_key / grok_key: the calling user's own keys, passed through explicitly."""
    prompt = f"""You are a telecom NOC assistant. An anomaly detection model flagged the
following alarm as anomalous:

Alarm type: {anomaly_result.get('alarm_type')}
Anomaly score: {anomaly_result.get('score')}

Related recent alarms of the same type: {related_alarms}

In 3-4 short sentences, explain a plausible root cause and suggest one
concrete next troubleshooting step for a network engineer. Be concise
and practical, no headers or markdown."""
    result = generate(prompt, gemini_key=gemini_key, grok_key=grok_key)
    return result["text"]