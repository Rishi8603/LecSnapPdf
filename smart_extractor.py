import cv2
import imagehash
from PIL import Image

def frame_to_pil(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def extract_unique_frames(video_path, threshold=25, cooldown=3, crop_center=False):
    cap = cv2.VideoCapture(video_path)

    unique_frames = []
    last_hash = None
    last_timestamp = -1
    frame_index = 0
    fps = cap.get(cv2.CAP_PROP_FPS)

    while True:
        success, frame = cap.read()
        if not success:
            break

        if frame_index % int(fps) != 0:
            frame_index += 1
            continue

        pil_img = frame_to_pil(frame)

        if crop_center:
            # Crop center 70% of frame — ignores webcam corners
            w, h = pil_img.size
            left = int(w * 0.15)
            right = int(w * 0.85)
            top = int(h * 0.1)
            bottom = int(h * 0.9)
            hash_img = pil_img.crop((left, top, right, bottom))
        else:
            hash_img = pil_img

        current_hash = imagehash.phash(hash_img)
        timestamp = round(frame_index / fps, 2)

        if last_hash is None:
            unique_frames.append((timestamp, pil_img))
            last_hash = current_hash
            last_timestamp = timestamp
        else:
            distance = current_hash - last_hash

            if distance > threshold and (timestamp - last_timestamp) >= cooldown:
                unique_frames.append((timestamp, pil_img))
                last_hash = current_hash
                last_timestamp = timestamp

        frame_index += 1

    cap.release()
    return unique_frames