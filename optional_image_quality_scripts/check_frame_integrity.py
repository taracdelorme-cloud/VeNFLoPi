import argparse
import subprocess
import os
import glob


def get_frame_count(filepath):
    """Use ffprobe to count actual video packets (frames) in a file."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-count_packets",
        "-show_entries", "stream=nb_read_packets",
        "-of", "csv=p=0",
        filepath
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip()
    if not output or not output.isdigit():
        return None
    return int(output)


def get_duration_seconds(filepath):
    """Use ffprobe to get video duration in seconds."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=duration",
        "-of", "csv=p=0",
        filepath
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip()
    try:
        return float(output)
    except ValueError:
        return None


def analyze_files(filepaths, fps):
    results = []
    print(f"\n{'File':<55} {'Actual':>10} {'Duration':>12} {'Expected':>10} {'Dropped':>10} {'Drop%':>8}")
    print("-" * 110)

    for fp in filepaths:
        name = os.path.basename(fp)
        actual = get_frame_count(fp)
        duration = get_duration_seconds(fp)

        if actual is None:
            print(f"{name:<55} {'ERROR reading file':>10}")
            continue

        if duration is not None:
            expected = round(duration * fps)
            dropped = expected - actual
            drop_pct = (dropped / expected * 100) if expected > 0 else 0
        else:
            expected = actual  # can't compute independently
            dropped = 0
            drop_pct = 0.0

        h = int(actual // fps // 3600)
        m = int((actual // fps % 3600) // 60)
        s = (actual / fps) % 60

        print(f"{name:<55} {actual:>10} {h:02d}:{m:02d}:{s:05.2f} {expected:>10} {dropped:>10} {drop_pct:>7.3f}%")
        results.append({"file": name, "actual": actual, "expected": expected, "dropped": dropped})

    # Cross-camera comparison
    if len(results) > 1:
        actuals = [r["actual"] for r in results]
        max_diff = max(actuals) - min(actuals)
        print(f"\n--- Cross-camera comparison ---")
        print(f"  Max frames: {max(actuals)}, Min frames: {min(actuals)}")
        print(f"  Difference: {max_diff} frames ({max_diff/fps:.1f} seconds)")
        if max_diff / fps < 5:
            print(f"  ✓ All cameras within 5 seconds of each other — consistent recording")
        else:
            print(f"  ⚠ Cameras differ by >{max_diff/fps:.1f} seconds — check for staggered start/stop")

    total_dropped = sum(r["dropped"] for r in results)
    print(f"\n=== TOTAL DROPPED FRAMES ACROSS ALL FILES: {total_dropped} ===")
    if total_dropped == 0:
        print("✓ No dropped frames detected.")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VeNFLoPi frame integrity checker")
    parser.add_argument("--folder", required=False, help="Folder containing .mp4 files to check")
    parser.add_argument("--files", nargs="+", required=False, help="Individual video files to check")
    parser.add_argument("--fps", type=float, default=30, help="Recording frame rate (default: 30)")
    args = parser.parse_args()

    filepaths = []
    if args.folder:
        filepaths = sorted(glob.glob(os.path.join(args.folder, "*.mp4")))
        if not filepaths:
            raise SystemExit(f"No .mp4 files found in {args.folder}")
    elif args.files:
        filepaths = args.files
    else:
        raise SystemExit("Provide either --folder or --files")

    analyze_files(filepaths, fps=args.fps)
