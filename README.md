# LecSnapPdf 📄🎥

A lightweight tool that converts lecture videos into organized PDF notes by capturing snapshots at specific intervals.

Ideal for students and learners who want to turn a 60-minute lecture into a scannable document without manual screenshots.

---

## 🚀 Getting Started

**Try the Web Version:** [lecsnappdf.onrender.com](https://lecsnappdf.onrender.com/)

> **Note:** The cloud version is limited to **file uploads only** due to YouTube blocking server-side downloads from cloud providers. For YouTube URL support, please run the app locally.

---

## 🛠 Tech Stack

* **Backend:** Flask (Python)
* **Processing:** OpenCV (Frame extraction)
* **PDF Engine:** Pillow
* **Media Handling:** yt-dlp & FFmpeg

---

## ⚙️ How it Works

1. **Input:** Upload an `.mp4` or provide a YouTube link (local only).
2. **Extraction:** The script slices the video at your chosen time interval (e.g., every 30 seconds).
3. **Stamping:** Each captured frame is watermarked with its corresponding timestamp.
4. **Generation:** Images are compiled into a single, high-quality PDF.

---

## 💻 Local Setup (Full Version)

Running locally unlocks the YouTube download feature.

### 1. Clone & Enter

```bash
git clone https://github.com/Rishi8603/LecSnapPdf.git
cd LecSnapPdf

```

### 2. Install Dependencies

Ensure you have **FFmpeg** installed on your system, then run:

```bash
pip install -r requirements.txt

```

### 3. Launch

```bash
python app.py

```

Visit `http://localhost:10000` in your browser.

---

## 🚧 Road Map

* **Smart Detection:** Use structural similarity (SSIM) to only capture frames when the slide actually changes.
* **UX Updates:** Real-time progress bars for long video processing.
* **Frontend:** Migrate to a dedicated React dashboard.
* **Cloud Fix:** Implement client-side proxying for YouTube links.

---

## 👤 Author

**Rishi Raj** [GitHub](https://github.com/Rishi8603)

---
