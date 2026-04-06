import assemblyai as aai
import os
from dotenv import load_dotenv

load_dotenv()

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")


def transcribe_video(video_path):
    config = aai.TranscriptionConfig(
        speech_models=["universal-2"],
        language_code="en" 
    )

    transcriber = aai.Transcriber(config=config)

    print("Uploading and transcribing audio (using Universal-2)...")
    try:
        transcript = transcriber.transcribe(video_path)
    except Exception as exc:
        raise RuntimeError(f"Transcription service failed: {exc}") from exc

    if transcript.status == aai.TranscriptStatus.error:
        print("Transcription failed:", transcript.error)
        raise RuntimeError(f"Transcription failed: {transcript.error}")
    

    segments = []
    for sentence in transcript.get_sentences():
        start = sentence.start / 1000
        end = sentence.end / 1000
        segments.append((start, end, sentence.text))

    if not segments:
        raise RuntimeError("Transcription failed: no transcript sentences were returned.")

    return segments


if __name__ == "__main__":
    segments = transcribe_video("test.mp4")
    for start, end, text in segments:
        print(f"[{int(start)}s - {int(end)}s]: {text}")
