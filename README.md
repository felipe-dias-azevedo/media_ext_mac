# Media.Ext

<p align="center">
  <img src=".github/images/logo.png" alt="Media.Ext logo" width="176">
</p>

Media.Ext is a lightweight desktop app for downloading and extracting media from supported URLs. It is built with PyQt6 and is designed to work on both macOS and Windows, with a native-feeling interface and a streamlined workflow for saving media files locally.

## Overview

Media.Ext takes a URL, validates it, downloads the media using yt-dlp, and lets the user save the result to a chosen location. The app is designed to be simple: paste a link, confirm the destination, and keep the rest of the process focused on the download.

## Features

- Cross-platform desktop UI built with PyQt6
- Compatible with macOS and Windows
- URL validation and media extraction flow
- Downloads via yt-dlp and FFmpeg
- Save dialog for selecting output location
- Theme-aware interface with modern desktop styling
- Lightweight setup with minimal dependencies

## Tech stack

- Python 3
- PyQt6
- QtAwesome
- yt-dlp
- FFmpeg / imageio-ffmpeg
- PyInstaller for packaging

## Requirements

Before running the app, make sure you have:

- Python 3.10 or newer
- pip

## Getting started

Clone the project and move into the repository folder:

```bash
git clone <repo-url>
cd media_ext_mac
```

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run locally

Start the app from the project root:

```bash
python src/app.py
```

This launches the desktop application window where you can paste a URL and start the extraction flow.

## Build release binaries

The project includes packaging scripts for both supported desktop platforms.

### macOS

```bash
source ./build_mac.sh
```

This produces a macOS app bundle using PyInstaller.

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
```

This creates a Windows executable package using PyInstaller and app metadata configuration.

## Project structure

```text
.
├── build_mac.sh
├── build_windows.ps1
├── src/
│   ├── app.py
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── utils/
│   └── views/
├── requirements.txt
├── README.md
├── LICENSE
└── icon/
```

## Notes

- The app is no longer based on PyObjC; the current codebase targets PyQt6.
- The project is intended to be multiplatform and can be run on both Windows and macOS.
- yt-dlp handles the media extraction and download layer, while FFmpeg supports media processing and conversion tasks when needed.
