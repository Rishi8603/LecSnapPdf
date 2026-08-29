import cv2
import base64
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def sample_frames(video_path, n=3, max_width=512):
    """
    Extracts n evenly spaced frames from video.
    Returns list of base64 encoded JPEG strings.
    """
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Interior samples at 1/(n+1) .. n/(n+1) of the runtime. Starting at frame 0
    # wasted a sample on the black frame or title card most uploads open with,
    # and the old formula never looked at the final stretch either.
    indices = [int(total_frames * (i + 1) / (n + 1)) for i in range(n)]

    encoded_frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = cap.read()
        if not success:
            continue

        # Deciding "slides vs blackboard vs code" needs layout, not detail.
        # Full 1080p frames were ~190KB of base64 each, making every request a
        # multi-megabyte upload with no gain in classification accuracy.
        height, width = frame.shape[:2]
        if width > max_width:
            scale = max_width / width
            frame = cv2.resize(
                frame,
                (max_width, int(height * scale)),
                interpolation=cv2.INTER_AREA,
            )

        # Encode frame as JPEG → base64
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        b64 = base64.b64encode(buffer).decode("utf-8")
        encoded_frames.append(b64)

    cap.release()
    return encoded_frames


def classify_video(video_path):
    """
    Samples frames and asks Groq vision to classify video type.
    Returns one of: slide, blackboard, scrolling, coding, animated
    """
    print("Sampling frames for classification...")
    # qwen/qwen3.8-27b accepts at most 3 images per request.
    frames = sample_frames(video_path, n=3)

    if not frames:
        print("Could not sample frames, defaulting to slide")
        return "slide"

    # Build image content blocks for Groq
    content = []
    for b64 in frames:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64}"
            }
        })

    content.append({
        "type": "text",
        "text": """Look at these frames from a teaching/lecture video.
Classify it into EXACTLY one of these categories:
- slide: presentation slides, PowerPoint, PDF slides
- blackboard: physical or digital blackboard/whiteboard with handwriting
- scrolling: digital notebook or document being scrolled slowly
- coding: code editor or terminal screen recording
- animated: fast animated explainer video with constant motion

Reply with ONLY the single word category. Nothing else."""
    })

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen/qwen3.8-27b",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 10
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )

    # Classification is advisory — it only picks extraction tuning — so a
    # provider outage degrades to the safe default instead of failing the job.
    # Without this check a 404 (decommissioned model) or 401 (bad key) surfaced
    # as KeyError: 'choices' several lines below, hiding the real cause.
    if response.status_code != 200:
        try:
            detail = response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = response.text[:200]
        print(f"Classifier request failed (HTTP {response.status_code}): {detail}")
        print("Defaulting to slide")
        return "slide"

    result = response.json()

    try:
        video_type = result["choices"][0]["message"]["content"].strip().lower()
    except (KeyError, IndexError, TypeError):
        print(f"Unexpected classifier response: {str(result)[:200]}")
        print("Defaulting to slide")
        return "slide"

    # Qwen-family models may prefix a <think> reasoning block.
    if "</think>" in video_type:
        video_type = video_type.split("</think>")[-1].strip()

    print(f"Classified as: {video_type}")

    # Safety fallback if unexpected response
    valid = ["slide", "blackboard", "scrolling", "coding", "animated"]
    if video_type not in valid:
        print(f"Unexpected classification '{video_type}', defaulting to slide")
        return "slide"

    return video_type


if __name__ == "__main__":
    vtype = classify_video("test2.mp4")
    print(f"Video type: {vtype}")