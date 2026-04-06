import cv2
import base64
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def sample_frames(video_path, n=5):
    """
    Extracts n evenly spaced frames from video.
    Returns list of base64 encoded JPEG strings.
    """
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = [int(total_frames * i / n) for i in range(n)]

    encoded_frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = cap.read()
        if not success:
            continue

        # Encode frame as JPEG → base64
        _, buffer = cv2.imencode(".jpg", frame)
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
    frames = sample_frames(video_path, n=5)

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
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 10
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload
    )

    result = response.json()
    video_type = result["choices"][0]["message"]["content"].strip().lower()
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