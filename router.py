from smart_extractor import extract_unique_frames


def route_extraction(video_path, video_type):
    """
    Based on video type, applies the correct frame extraction strategy.
    Returns list of (timestamp, PIL_image) tuples.
    """
    print(f"Routing strategy for: {video_type}")

    if video_type == "slide":
        # Standard perceptual hash dedup
        return extract_unique_frames(video_path, threshold=25, cooldown=3)

    elif video_type == "blackboard":
        # Lower threshold — captures smaller changes (writing builds up slowly)
        return extract_unique_frames(video_path, threshold=15, cooldown=5)

    elif video_type == "scrolling":
        # Higher cooldown — avoid capturing every scroll tick
        return extract_unique_frames(video_path, threshold=20, cooldown=8)

    elif video_type == "coding":
        # Crop center region before hashing (ignore webcam corner)
        return extract_unique_frames(video_path, threshold=20, cooldown=5, crop_center=True)

    elif video_type == "animated":
        # Animated = no smart detection possible, fall back to interval
        return extract_unique_frames(video_path, threshold=30, cooldown=10)

    else:
        # Unknown — safe default
        return extract_unique_frames(video_path, threshold=25, cooldown=3)
    

if __name__ == "__main__":
  frames = route_extraction("test2.mp4", "blackboard")
  print(f"Extracted {len(frames)} frames")