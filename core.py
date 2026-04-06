import cv2              
import os              
from PIL import Image   


def open_video(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Video open nahi ho raha")
        return None

    print("Video successfully opened")
    return cap


def get_frames_to_skip(cap, interval_seconds):
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames_to_skip = int(fps * interval_seconds)

    
    if frames_to_skip <= 0:
      frames_to_skip = 1

    print("FPS:", fps)
    print("Frames to skip:", frames_to_skip)

    return frames_to_skip


def extract_frames(cap, frames_to_skip):
    os.makedirs("frames", exist_ok=True)

    frame_count = 0
    saved_count = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        if frame_count % frames_to_skip == 0:
            timestamp_seconds = frame_count / cap.get(cv2.CAP_PROP_FPS)
            timestamp_text = format_timestamp(timestamp_seconds)

            # OpenCV text overlay
            cv2.putText(
                frame,
                f"Time: {timestamp_text}",
                (20, frame.shape[0] - 20),   # bottom-left
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),             # white
                2,
                cv2.LINE_AA
            )

            filename = f"frames/frame_{saved_count}.jpg"
            cv2.imwrite(filename, frame)
            saved_count += 1


        frame_count += 1
        if frame_count % (frames_to_skip * 10) == 0:
          print(f"Processed {frame_count} frames...")


    print("Total frames read:", frame_count)
    print("Total frames saved:", saved_count)


def create_pdf(job_id="default"):
    os.makedirs("output", exist_ok=True)

    image_files = sorted(os.listdir("frames"), key=lambda x: int(x.split("_")[1].split(".")[0]))

    if not image_files:
        print("No frames extracted. PDF not created.")
        return

    images = []

    for img_file in image_files:
        img_path = os.path.join("frames", img_file)
        img = Image.open(img_path).convert("RGB")
        images.append(img)

    pdf_path = f"output/{job_id}.pdf"

    images[0].save(
        pdf_path,
        save_all=True,
        append_images=images[1:]
    )

    print("PDF generated at", pdf_path)

def get_interval_from_user():
    while True:
        user_input = input("Enter interval in seconds (e.g. 10): ")

        try:
            interval = int(user_input)

            if interval <= 0:
                print("Please enter a number greater than 0.")
                continue

            return interval

        except ValueError:
            print("Invalid input. Please enter a number.")

def clear_frames_folder():
    if not os.path.exists("frames"):
        return

    for file in os.listdir("frames"):
        file_path = os.path.join("frames", file)
        os.remove(file_path)

    print("Frames folder cleared")

def get_youtube_url():
    url = input("Enter YouTube video URL: ").strip()
    return url

import subprocess #python se terminal command chalane ke liye

def download_youtube_video(url):
    os.makedirs("input", exist_ok=True)
    output_path = "input/lecture.mp4"

    
    if os.path.exists(output_path):
        os.remove(output_path)

    command = [
        "yt-dlp",
        "--force-overwrites",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", output_path,
        url
    ]

    print("\n Downloading video from YouTube...")
    try:
        subprocess.run(command, check=True)
        if not os.path.exists(output_path):
            print("Download completed but output file not found.")
            return None
        print("Download completed successfully")
        return output_path
    except subprocess.CalledProcessError:
        print("Error while downloading video")
        return None

def get_video_source():
    print("\nChoose video source:")
    print("1. Local video file")
    print("2. YouTube URL")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        path = input("Enter local video path: ").strip()
        return path

    elif choice == "2":
        url = input("Enter YouTube URL: ").strip()
        return download_youtube_video(url)

    else:
        print("Invalid choice")
        return None

def format_timestamp(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def main(video_path, interval_seconds, job_id="default"):

    if video_path is None:
        print("Video source not available. Exiting.")
        return

    cap = open_video(video_path)
    if cap is None:
        return

    clear_frames_folder()

    frames_to_skip = get_frames_to_skip(cap, interval_seconds)
    extract_frames(cap, frames_to_skip)
    create_pdf(job_id)

    cap.release()



def save_frames_as_pdf(frames, job_id="default"):
    """
    frames: list of (timestamp_seconds, PIL_image) tuples
    coming directly from smart_extractor.py
    """
    os.makedirs("output", exist_ok=True)

    images = []

    for timestamp, pil_img in frames:
        # Convert PIL to RGB (safety)
        img = pil_img.convert("RGB")
        # Force JPEG compatibility for PIL's PDF writer
        import io
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        img = Image.open(buffer)
        img.load()

        # Stamp timestamp on the image using PIL (no OpenCV needed here)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        label = f"Time: {format_timestamp(timestamp)}"
        draw.text((20, img.height - 30), label, fill=(255, 255, 255))

        images.append(img)

    if not images:
        print("No frames to save.")
        return

    pdf_path = f"output/{job_id}.pdf"

    images[0].save(
        pdf_path,
        save_all=True,
        append_images=images[1:]
    )

    print(f"Smart PDF generated with {len(images)} frames at {pdf_path}")



def smart_pipeline(video_path, job_id="default", progress_store=None, summary_position="right"):
    from classifier import classify_video
    from router import route_extraction
    from transcriber import transcribe_video
    from summarizer import get_transcript_for_frame, summarize_with_groq
    from layout import create_frame_with_summary

    def update(msg):
        print(msg)
        if progress_store is not None:
            progress_store[job_id] = msg

    update("Classifying video type...")
    video_type = classify_video(video_path)

    update(f"Detected: {video_type} - extracting frames...")
    frames = route_extraction(video_path, video_type)

    update(f"{len(frames)} frames captured - transcribing audio...")
    segments = transcribe_video(video_path)

    update("Generating AI summaries...")
    os.makedirs("output", exist_ok=True)
    images = []

    for timestamp, pil_img in frames:
        transcript_chunk = get_transcript_for_frame(timestamp, segments)
        summary = summarize_with_groq(transcript_chunk)
        final_image = create_frame_with_summary(
            pil_img,
            summary or "",
            timestamp,
            summary_position,
        )

        import io
        buffer = io.BytesIO()
        final_image.save(buffer, format="JPEG")
        buffer.seek(0)
        final_image = Image.open(buffer)
        final_image.load()

        images.append(final_image)

    update("Building PDF...")
    pdf_path = f"output/{job_id}.pdf"

    if not images:
        update("No frames found. PDF not created.")
        return

    images[0].save(
        pdf_path,
        save_all=True,
        append_images=images[1:]
    )

    update("DONE")
    print(f"Done. PDF saved at {pdf_path} with {len(images)} pages.")
