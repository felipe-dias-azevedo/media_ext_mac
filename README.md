# Media.Ext (Mac)

<p align="center">
  <img src=".github/images/logo.png" alt="Logo" width="176">
</p>

<b>Media.Ext</b> lets you extract and download media from the web as easily as possible — with a clean, native macOS interface.

## About

### Features

🧩 Native and modern macOS look & feel — built with PyObjC for great system integration

⚙️ Powerful backend — uses yt-dlp and FFmpeg under the hood

🎞️ Supports a wide range of media sites (anything yt-dlp can handle)

💾 Automatic file naming

🚀 Lightweight & fast, no extra dependencies beyond what you need

### Tech Stack

- Language: Python 3
- Framework: PyObjC
- Backend tools: yt-dlp, FFmpeg

### Screenshots

![App.](.github/images/screenshot_1.jpeg)

## Run locally

### Install dependencies

```sh
pip install -r requirements.txt
```

### Run (dev)

```sh
python src/app.py
```

## Run release

### Build .app

```sh
source ./build.sh
```
