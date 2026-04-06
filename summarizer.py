import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def get_transcript_for_frame(frame_timestamp, segments, window=30):
    """
    For a frame at timestamp T, collect all transcript text
    spoken within a window around T.
    
    window=30 means: grab text from T-15s to T+15s
    """
    half = window / 2
    relevant = []

    for start, end, text in segments:
        if end >= (frame_timestamp - half) and start <= (frame_timestamp + half):
            relevant.append(text)

    return " ".join(relevant)


def summarize_with_groq(transcript_text):
    """
    Sends transcript segment to Groq, gets back a short concept summary.
    """
    if not transcript_text.strip():
        return None

    if not GROQ_API_KEY:
        raise RuntimeError("AI summary failed: GROQ_API_KEY is missing.")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "You are a study assistant. Given lecture audio transcript, write a concise 2-3 line concept summary a student can read quickly. No bullet points. Plain text only."
            },
            {
                "role": "user",
                "content": f"Transcript: {transcript_text}"
            }
        ],
        "max_tokens": 120
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"AI summary failed: {exc}") from exc

    result = response.json()
    print(result)

    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("AI summary failed: invalid response from summarizer service.") from exc


if __name__ == "__main__":
    # Fake segments to test
    test_segments = [
        (0, 8, "Your body produces 120 million red blood cells per minute."),
        (8, 16, "We produce 5 million pounds of garbage every minute worldwide."),
    ]
    text = get_transcript_for_frame(frame_timestamp=5, segments=test_segments)
    print("Transcript chunk:", text)
    
    summary = summarize_with_groq(text)
    print("Summary:", summary)
