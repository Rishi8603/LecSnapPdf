import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# One summary call per slide means N sequential requests to the same host.
# requests.post() opens a fresh TCP+TLS connection every time, and the handshake
# to Groq measured ~21s here against ~0.3s of actual inference — so a 27-slide
# lecture spent ~10 minutes on handshakes alone. A Session keeps one connection
# alive, so only the first call pays that cost.
_session = requests.Session()


def get_transcript_for_frame(frame_timestamp, segments, next_timestamp=None, min_span=8):
    """
    Collect the transcript spoken while a captured frame was actually on screen.

    The span for a frame is [frame_timestamp, next_timestamp) — the moment the
    next unique frame was captured is exactly the moment this slide left the
    screen. The last frame has no successor, so it runs to the end of the
    transcript.

    A sentence counts as relevant when it *overlaps* the span, not only when it
    sits entirely inside it: a sentence chopped in half at a slide boundary is
    useless to the summarizer, so a little duplication between neighbouring
    slides is the cheaper trade.

    Slides captured back-to-back (the extractor allows gaps as small as its
    cooldown) would otherwise produce a span too short to summarize, so spans
    are floored at min_span seconds.
    """
    if not segments:
        return ""

    span_start = frame_timestamp

    if next_timestamp is not None:
        span_end = next_timestamp
    else:
        span_end = max(end for _, end, _ in segments)

    if span_end - span_start < min_span:
        span_end = span_start + min_span

    relevant = [
        text
        for start, end, text in segments
        if end > span_start and start < span_end
    ]

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
        "model": "qwen/qwen3.8-27b",
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

    # One summary call per slide, so a lecture with many slides walks straight
    # into the free tier's 8000 tokens/minute cap. Groq's 429 states exactly how
    # long to wait, so honour it rather than failing the whole job.
    for attempt in range(3):
        try:
            response = _session.post(
                GROQ_URL,
                headers=headers,
                json=payload,
                timeout=60,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"AI summary failed: {exc}") from exc

        if response.status_code != 429 or attempt == 2:
            break

        wait = response.headers.get("retry-after")
        if wait is None:
            match = re.search(r"try again in ([\d.]+)s", response.text)
            wait = match.group(1) if match else "5"
        wait = float(wait) + 0.5
        print(f"Rate limited by Groq, waiting {wait:.1f}s (attempt {attempt + 1}/3)")
        time.sleep(wait)

    try:
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"AI summary failed: {exc}") from exc

    result = response.json()

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
