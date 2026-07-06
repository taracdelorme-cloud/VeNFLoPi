import argparse
import re
import cv2
import numpy as np


# ---------- VIDEO METRICS ----------

def sample_frames(video_path, n_frames=10, crop=None):
    """
    Grab n_frames evenly spaced grayscale frames from a video.
    crop: (x, y, w, h) in pixels. If provided, each frame is cropped to this
    box (e.g. the chamber interior) before being returned.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video: {video_path}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        raise ValueError(f"Video has no readable frames: {video_path}")

    idxs = np.linspace(0, total - 1, num=min(n_frames, total), dtype=int)
    frames = []
    for idx in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if ok:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if crop is not None:
                x, y, w, h = crop
                gray = gray[y:y + h, x:x + w]
            frames.append(gray)
    cap.release()
    if not frames:
        raise ValueError(f"No frames could be read from {video_path}")
    return frames


def compute_snr(frames, roi, trim_pct=10):
    """
    SNR per frame on a fixed background ROI, summarized across frames using
    mean, median, and a trimmed mean (more robust to occasional bad frames).

    roi: (x, y, w, h) in pixels -- REQUIRED. Pick this by eye from a still
    frame: a small patch that is consistently background across the
    recording (no glare, no grid bars, no mouse) e.g. a top corner.
    """
    snrs = []
    x, y, rw, rh = roi
    for frame in frames:
        patch = frame[y:y + rh, x:x + rw].astype(np.float64)
        mean = patch.mean()
        std = patch.std()
        if std == 0:
            continue
        snr_db = 20 * np.log10(mean / std)
        snrs.append(snr_db)

    snrs = np.array(snrs)
    sorted_snrs = np.sort(snrs)
    n_trim = int(len(sorted_snrs) * (trim_pct / 100) / 2)
    trimmed = sorted_snrs[n_trim:-n_trim] if n_trim > 0 else sorted_snrs

    return {
        "mean": float(np.mean(snrs)),
        "median": float(np.median(snrs)),
        "std": float(np.std(snrs)),
        "trimmed_mean": float(np.mean(trimmed)),
        "n": len(snrs),
    }


def compute_illumination_uniformity(frames, grid=(8, 8), trim_pct=10):
    """
    Coefficient of variation (%) of mean cell intensity across a grid,
    summarized across frames using mean, median, and trimmed mean.
    Lower CV% = more uniform illumination.
    """
    cvs = []
    gx, gy = grid
    for frame in frames:
        h, w = frame.shape
        cell_h, cell_w = h // gy, w // gx
        cell_means = []
        for i in range(gy):
            for j in range(gx):
                cell = frame[i * cell_h:(i + 1) * cell_h, j * cell_w:(j + 1) * cell_w]
                if cell.size > 0:
                    cell_means.append(cell.mean())
        cell_means = np.array(cell_means)
        cv_pct = (cell_means.std() / cell_means.mean()) * 100
        cvs.append(cv_pct)

    cvs = np.array(cvs)
    sorted_cvs = np.sort(cvs)
    n_trim = int(len(sorted_cvs) * (trim_pct / 100) / 2)
    trimmed = sorted_cvs[n_trim:-n_trim] if n_trim > 0 else sorted_cvs

    return {
        "mean": float(np.mean(cvs)),
        "median": float(np.median(cvs)),
        "std": float(np.std(cvs)),
        "trimmed_mean": float(np.mean(trimmed)),
        "n": len(cvs),
    }


def analyze_video(label, path, n_frames=10, crop=None, snr_roi=None):
    print(f"\n--- {label} video: {path} ---")
    if crop:
        print(f"  Cropping to chamber ROI: x={crop[0]}, y={crop[1]}, w={crop[2]}, h={crop[3]}")
    if snr_roi:
        print(f"  Using fixed SNR background patch: x={snr_roi[0]}, y={snr_roi[1]}, w={snr_roi[2]}, h={snr_roi[3]}")
    frames = sample_frames(path, n_frames=n_frames, crop=crop)

    snr = compute_snr(frames, roi=snr_roi)
    cv = compute_illumination_uniformity(frames)

    print(f"  SNR (n={snr['n']} frames): mean={snr['mean']:.2f} dB, "
          f"median={snr['median']:.2f} dB, trimmed_mean={snr['trimmed_mean']:.2f} dB, "
          f"std={snr['std']:.2f}")
    print(f"  Illumination CV (n={cv['n']} frames): mean={cv['mean']:.2f}%, "
          f"median={cv['median']:.2f}%, trimmed_mean={cv['trimmed_mean']:.2f}%, "
          f"std={cv['std']:.2f}")

    return {"snr": snr, "cv": cv}


# ---------- OBS LOG PARSING ----------

def parse_obs_log(log_path):
    """
    Parses an OBS Studio log file for total frames encoded and dropped frames.
    """
    with open(log_path, "r", errors="ignore") as f:
        text = f.read()

    results = {}

    patterns = {
        "encoding_lag": r"skipped frames due to encoding lag:\s*(\d+)/(\d+)\s*\(([\d.]+)%\)",
        "rendering_lag": r"lagged frames due to rendering lag:\s*(\d+)/(\d+)\s*\(([\d.]+)%\)",
        "output_dropped": r"frames? dropped:\s*(\d+)\s*\(([\d.]+)%\)",
    }

    for key, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            results[key] = m.groups()

    if not results:
        print("  WARNING: No standard frame-drop lines found. "
              "Search the log manually for 'skipped' or 'lagged' or 'dropped'.")
    else:
        print("\n--- OBS log frame drop summary ---")
        for key, vals in results.items():
            print(f"  {key}: {vals}")

    return results


# ---------- MAIN ----------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VeNFLoPi imaging quality metrics")
    parser.add_argument("--light", required=False, help="Path to light-condition video")
    parser.add_argument("--dark", required=False, help="Path to dark/IR-condition video")
    parser.add_argument("--obslog", required=False, help="Path to OBS log file (.txt)")
    parser.add_argument("--n_frames", type=int, default=10, help="Number of frames to sample per video")
    parser.add_argument("--crop", required=False, default=None,
                         help="Chamber crop box as 'x,y,w,h' in pixels, e.g. --crop 200,100,800,700. "
                              "Use the same crop for both light and dark videos if the camera position is fixed.")
    parser.add_argument("--snr_roi", required=True,
                         help="Fixed background patch for SNR as 'x,y,w,h' in pixels (coordinates are "
                              "relative to the CROPPED frame if --crop is used). Pick a small region that "
                              "stays clean (no glare/grid/mouse) across the recording, e.g. a top corner. "
                              "e.g. --snr_roi 40,40,180,150")
    args = parser.parse_args()

    crop = None
    if args.crop:
        try:
            crop = tuple(int(v.strip()) for v in args.crop.split(","))
            if len(crop) != 4:
                raise ValueError
        except ValueError:
            raise SystemExit("--crop must be in the form x,y,w,h e.g. --crop 200,100,800,700")

    try:
        snr_roi = tuple(int(v.strip()) for v in args.snr_roi.split(","))
        if len(snr_roi) != 4:
            raise ValueError
    except ValueError:
        raise SystemExit("--snr_roi must be in the form x,y,w,h e.g. --snr_roi 40,40,180,150")

    results = {}

    if args.light:
        results["light"] = analyze_video("Light", args.light, n_frames=args.n_frames, crop=crop, snr_roi=snr_roi)
    if args.dark:
        results["dark"] = analyze_video("Dark/IR", args.dark, n_frames=args.n_frames, crop=crop, snr_roi=snr_roi)
    if args.obslog:
        parse_obs_log(args.obslog)

    if results:
        print("\n=== SUMMARY ===")
        for cond, vals in results.items():
            print(f"{cond}: SNR trimmed_mean={vals['snr']['trimmed_mean']:.2f} dB, "
                  f"Illumination CV trimmed_mean={vals['cv']['trimmed_mean']:.2f}%")
