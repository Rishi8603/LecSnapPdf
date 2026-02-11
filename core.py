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


def create_pdf():
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

    pdf_path = "output/notes.pdf"

    if os.path.exists(pdf_path):
        os.remove(pdf_path)

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


def main(video_path, interval_seconds):

    if video_path is None:
        print("Video source not available. Exiting.")
        return

    cap = open_video(video_path)
    if cap is None:
        return

    clear_frames_folder()

    frames_to_skip = get_frames_to_skip(cap, interval_seconds)
    extract_frames(cap, frames_to_skip)
    create_pdf()

    cap.release()



