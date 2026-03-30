# VeNFLoPi

(unpublished)
Versatile Night/Day Framework for Longitudinal Pi-based Imaging
Open-source Raspberry Pi camera platform for behavioral neuroscience experiments.

Tara C. Delorme, Mackenzie C. Gamble, Ryan W. Logan

Overview

VeNFLoPi is an open-source Raspberry Pi–based video acquisition system designed for long-term behavioral recordings under both light and dark conditions.

The system combines:

Raspberry Pi 4 computers
HDMI-connected Arducam cameras
Custom infrared (IR) illumination
Centralized recording using OBS Studio

This architecture enables high-resolution, high-frame-rate behavioral video acquisition with real-time monitoring and reliable long-duration recordings.

VeNFLoPi was developed to support machine-learning–based behavioral analysis, including:
DeepLabCut
SimBA
SLEAP
other pose-estimation workflows
As well as LabGym

The system produces videos that are immediately compatible with downstream behavioral analysis pipelines.

Key Features
Low-cost and scalable open-source camera platform
Continuous recording across light and dark cycles
High-frame-rate acquisition
Infrared illumination for nocturnal recordings
Wide-angle fisheye camera support
Real-time multi-camera monitoring using OBS
Automated video stitching and preprocessing
Flexible mounting using 3D-printed camera arms

Host Computer

records video using OBS Studio
manages file storage and backups
allows multi-camera monitoring

This approach avoids storage and processing limitations associated with recording directly on the Raspberry Pi.

Installation
1. Download the VeNFLoPi system image:

VeNFLoPi.img

from this repository.

2. Flash the MicroSD Card

Install Raspberry Pi Imager:
https://www.raspberrypi.com/software/

Steps:

Open Raspberry Pi Imager
Select Use Custom Image
Choose VeNFLoPi.img
Select the MicroSD card
Flash and verify

Insert the MicroSD card into the Raspberry Pi.

3. Assemble Hardware

Connect:

Raspberry Pi 4
Arducam camera via CSI ribbon cable
IR illumination module
HDMI output to capture card
USB-C power supply
Squid button for safe shutdown

Optional:

fisheye M12 lens
extended ribbon cable
3D-printed camera mounts

3D-printed components:

https://www.thingiverse.com/gloverlab/designs

Video Acquisition

Video recording is performed on a host computer using OBS Studio.

Install OBS:

https://obsproject.com/

Recommended recording settings:

Resolution: 1920 x 1080
Frame rate: 60 FPS
Format: MKV
Auto-remux to MP4

Multi-camera setups use OBS Scene Collections.

Optional plugin:

Advanced Scene Switcher

This allows automated recording schedules (e.g., alternating recording blocks during 24-hour experiments).

Video Processing

This repository includes a script:

stitch_videos.py

Functions:

merges segmented recordings
converts frames to grayscale
removes near-black frames
overlays timestamps
outputs analysis-ready MP4 videos

Requirements:

Python
OpenCV
FFmpeg

Example workflow:

python stitch_videos.py input_directory output_file.mp4

VeNFLoPi was developed for behavioral neuroscience experiments including:

operant self-administration
circadian behavior studies
sleep monitoring
home-cage activity tracking
locomotor assays
machine-learning behavioral classification

The system is particularly useful in space-constrained behavioral chambers where wide-angle imaging is required.

Limitations
OBS limits capture to ~8 cameras per computer
system requires a reasonably powerful host computer
not optimized for high-throughput (>10s of cameras) setups

If you use VeNFLoPi in your research, please cite:

Delorme TC, Gamble MC, Logan RW.
VeNFLoPi: Versatile Night/Day Framework for Longitudinal Pi-based Imaging.
(Open-source behavioral video acquisition system)
