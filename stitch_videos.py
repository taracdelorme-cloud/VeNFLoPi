import os
import cv2
from datetime import datetime

# Parent directory containing one subfolder per recording session.
# Each subfolder is expected to contain timestamped .mp4 video files.
parent_dir = r"F:\24hIVSA_saline_withdrawal_11.2025_TD\24hIVSA_saline_withdrawal_1-6_11.2025_TD"

# Threshold for detecting and skipping near-black frames
# (mean grayscale intensity below this value will be ignored)
black_frame_threshold = 10

# Timestamp text appearance (grayscale video)
font_scale = 0.8
font_color = 255          # white in grayscale
thickness = 2
line_height = 20          # vertical spacing between characters
x_pos = 10                # left margin for timestamp text
bottom_margin = 10        # distance from bottom of frame

# Helper function
def get_datetime_from_filename(filename):
    """
    Extract datetime from filename formatted as:
    YYYY-MM-DD HH-MM-SS.mp4

    If parsing fails, return datetime.min so files
    are sorted to the beginning.
    """
    try:
        name = os.path.splitext(filename)[0]
        return datetime.strptime(name, '%Y-%m-%d %H-%M-%S')
    except ValueError:
        return datetime.min

# Main loop: process each subfolder in parent_dir
for folder_name in os.listdir(parent_dir):

    video_folder = os.path.join(parent_dir, folder_name)

    # Skip non-directory items
    if not os.path.isdir(video_folder):
        continue

    print(f"\n=== Processing folder: {folder_name} ===")

    # Output video will be saved INSIDE the current subfolder
    output_file = f"{folder_name}_stitched_output.mp4"
    out_path = os.path.join(video_folder, output_file)

# Step 1: Collect all valid .mp4 files
  videos = [
        f for f in os.listdir(video_folder)
        if f.endswith(".mp4") and not f.startswith("._")  # ignore hidden/system files
    ]

    if not videos:
        print("  No videos found — skipping.")
        continue

    # Sort videos chronologically using timestamp in filename
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

# Step 3: Initialize VideoWriter (grayscale output)
   fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(
        out_path,
        fourcc,
        fps,
        (width, height),
        isColor=False  # output is grayscale
    )

# Step 4: Stitch videos together
   for video in videos:
        video_path = os.path.join(video_folder, video)
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"  Could not open {video}")
            continue

        # Timestamp text derived directly from filename
        timestamp_text = os.path.splitext(video)[0]
        print(f"  Processing: {video}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Skip black or near-black frames
            if gray.mean() < black_frame_threshold:
                continue

            # Draw vertical timestamp along bottom-left edge
            for i, char in enumerate(timestamp_text):
                y_pos = height - bottom_margin - i * line_height
                cv2.putText(
                    gray,
                    char,
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