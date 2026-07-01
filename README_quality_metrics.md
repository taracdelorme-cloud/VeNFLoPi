# VeNFLoPi Imaging Quality Analysis

Scripts used to compute imaging performance metrics reported in the VeNFLoPi manuscript (Delorme et al., *Scientific Reports*, under revision). These scripts verify signal-to-noise ratio (SNR), illumination uniformity, and frame integrity for videos recorded with the VeNFLoPi system.

---

## Requirements

```bash
pip install opencv-python numpy
brew install ffmpeg  # macOS; for Windows use https://ffmpeg.org/download.html
```

---

## Scripts

### 1. `venflopi_quality_metrics.py`
Computes SNR and illumination uniformity from video files.

**Arguments:**
- `--light` — path to light-condition video
- `--dark` — path to dark/IR-condition video
- `--crop x,y,w,h` — chamber interior crop box in pixels (excludes hardware mounts, cables outside the chamber)
- `--snr_roi x,y,w,h` — fixed background patch for SNR computation, relative to the cropped frame. Pick a small region that stays clean across the recording (no glare, no grid bars, away from where the animal spends time). We used the upper-left corner of the chamber wall.
- `--n_frames` — number of evenly-spaced frames to sample (default: 10; we used 100)

**Metrics reported:**
- **SNR** (dB): mean, median, and trimmed mean (10% trim) across sampled frames, computed on the fixed background ROI using `20 * log10(mean / std)`
- **Illumination uniformity CV%**: coefficient of variation of mean cell intensity across an 8×8 spatial grid within the cropped chamber frame; lower = more uniform

**Exact command used for the manuscript:**
```bash
python venflopi_quality_metrics.py \
  --light "path/to/light_video.mp4" \
  --dark "path/to/dark_video.mp4" \
  --crop 288,14,1344,1052 \
  --snr_roi 40,40,180,150 \
  --n_frames 100
```

**Results reported in manuscript:**

| Condition | SNR (trimmed mean) | Illumination CV% (trimmed mean) |
|-----------|-------------------|----------------------------------|
| Light     | 16.5 dB           | 23.9%                            |
| Dark/IR   | 15.0 dB           | 23.5%                            |

---

### 2. `check_frame_integrity.py`
Verifies no frames were dropped during recording by comparing actual frame counts (via ffprobe) against expected counts (duration × fps). Also compares frame counts across simultaneously-recording cameras.

**Arguments:**
- `--folder` — folder containing .mp4 files to check
- `--files` — individual video files to check (alternative to --folder)
- `--fps` — recording frame rate (default: 30)

**Usage:**
```bash
# Check a folder of videos
python check_frame_integrity.py --folder /path/to/videos --fps 30

# Check specific files
python check_frame_integrity.py \
  --files video1.mp4 video2.mp4 video3.mp4 \
  --fps 30
```

**Results reported in manuscript:**
No dropped frames were detected across any camera or recording file. Inter-camera timing differences were ≤2.7 seconds (light condition) and ≤33 seconds (dark condition), reflecting staggered initialization rather than encoding failures.

---

## Notes on SNR ROI selection

SNR is sensitive to where in the frame you measure. We recommend:
1. Extract a still frame: `ffmpeg -i video.mp4 -ss 00:05:00 -vf "crop=w:h:x:y" -frames:v 1 -update 1 -y frame.png`
2. Open in an image viewer and identify a small region (150×150px or similar) that is consistently background across the recording — no glare, no hardware, minimal animal presence (e.g. upper corner of the chamber wall)
3. Pass those coordinates as `--snr_roi x,y,w,h`

Avoid measuring SNR on the cage floor (grid bars add texture), near light fixtures or IR LEDs (glare), or in regions the animal frequently occupies.
