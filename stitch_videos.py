import os
import cv2
from datetime import datetime


# UPDATE THESE SETTINGS
# =================================================
parent_dir = r"D:\Videos"

black_frame_threshold = 10
font_scale = 0.8
font_color = 255
thickness = 2
line_height = 20
x_pos = 10
bottom_margin = 10
# =================================================


def get_datetime_from_filename(filename):
    try:
        name = os.path.splitext(filename)[0]
        return datetime.strptime(name, '%Y-%m-%d %H-%M-%S')
    except ValueError:
        return datetime.min


# -------------------------------------------------
# LOOP THROUGH EACH VIDEO FOLDER
# -------------------------------------------------
for folder_name in os.listdir(parent_dir):

    video_folder = os.path.join(parent_dir, folder_name)

    if not os.path.isdir(video_folder):
        continue  # skip files

    print(f"\n=== Processing folder: {folder_name} ===")

    output_file = f"{folder_name}_stitched.mp4"
    out_path = os.path.join(video_folder, output_file)

    # Step 1: Collect videos
    videos = [
        f for f in os.listdir(video_folder)
        if f.endswith(".mp4") and not f.startswith("._")
    ]

    if not videos:
        print("  No videos found — skipping.")
        continue

    videos.sort(key=get_datetime_from_filename)

    # Step 2: Read first video for metadata
    first_video_path = os.path.join(video_folder, videos[0])
    cap = cv2.VideoCapture(first_video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    if fps == 0 or width == 0 or height == 0:
        print("  First video unreadable — skipping folder.")
        continue

    # Step 3: VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, (width, height), isColor=False)

    # Step 4: Stitch videos
    for video in videos:
        video_path = os.path.join(video_folder, video)
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"  Could not open {video}")
            continue

        timestamp_text = os.path.splitext(video)[0]
        print(f"  Processing: {video}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Skip black frames
            if gray.mean() < black_frame_threshold:
                continue

            # Vertical timestamp (bottom-left)
            for i, char in enumerate(timestamp_text):
                y_pos = height - bottom_margin - i * line_height
                cv2.putText(
                    gray, char,
                    (x_pos, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    font_color,
                    thickness,
                    cv2.LINE_AA
                )

            out.write(gray)

        cap.release()

    out.release()
    print(f"  ✔ Saved: {out_path}")

print("\nALL FOLDERS COMPLETE")
