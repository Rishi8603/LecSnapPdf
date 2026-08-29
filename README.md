# LecSnapPdf 📄🎥

Convert any lecture video into intelligent PDF notes — automatically.

LecSnapPdf captures only the frames that matter, transcribes the audio, and adds AI-generated concept summaries beside each slide. No manual screenshots. No wasted pages.

---

## 🚀 Try It

**Live Web Version:** [lecsnappdf-takh.onrender.com](https://lecsnappdf-takh.onrender.com)

> YouTube URL support requires local setup (cloud platforms block yt-dlp). Upload mode works fully on the web version.

---

## ✨ What's New

### 🧠 Smart Mode — AI-Powered PDF Generation
LecSnapPdf now goes beyond fixed-interval screenshots.

**How it works:**
1. **Auto-classifies** the video type using a vision AI model
2. **Extracts only unique frames** using perceptual hashing — skips duplicate slides
3. **Transcribes the audio** using AssemblyAI (Universal-2) — word-level timings consumed at sentence granularity
4. **Aligns each transcript span to frame boundaries** — a slide's summary uses only the audio spoken while that slide was on screen
5. **Generates concept summaries** using Groq (LLaMA) for each slide
6. **Renders a clean PDF** with the frame on one side and the AI summary panel beside it

### 🎯 Video Type Detection
The classifier automatically detects what kind of video you uploaded and applies the optimal extraction strategy:

| Video Type | Strategy |
|---|---|
| Slide-based lecture | Perceptual hash dedup (threshold tuned) |
| Blackboard / whiteboard | Lower threshold — captures gradual buildup |
| Scrolling notebook | Higher cooldown — avoids scroll noise |
| Coding / screen recording | Center-crop before hashing — ignores webcam |
| Animated / fast-paced | High threshold + long cooldown — suppresses constant motion |

### 📊 Real-Time Progress
Processing steps stream live to your browser — no guessing whether it's stuck.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| Frame Extraction | OpenCV + imagehash (perceptual hashing) |
| Audio Transcription | AssemblyAI (cloud, timestamp-aligned) |
| AI Summarization | Groq API — LLaMA 3.3 70B |
| Video Classification | Groq Vision — LLaMA 4 Scout |
| PDF Generation | Pillow |
| Media Handling | yt-dlp + FFmpeg |

---

## ⚙️ Modes

### Manual Mode
Classic interval-based capture. You set the interval in seconds — one frame every N seconds, compiled into a PDF. Best for fast-paced or animated videos.

### Smart Mode — Simple
Captures frames only when the slide visually changes. No fixed interval. Skips duplicate frames automatically using perceptual hashing.

### Smart Mode — AI Summary
Full pipeline. Unique frames + audio transcription + per-slide AI concept summaries rendered as a side panel in the PDF. Choose panel position: top, right, left, or bottom.

---

## 💻 Local Setup

Running locally unlocks YouTube URL support via yt-dlp.

### 1. Clone

```bash
git clone https://github.com/Rishi8603/LecSnapPdf.git
cd LecSnapPdf
```

### 2. Install FFmpeg

Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to system PATH. Verify:

```bash
ffmpeg -version
```

### 3. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up environment variables

Create a `.env` file in the project root:

```
ASSEMBLYAI_API_KEY=your_assemblyai_key
GROQ_API_KEY=your_groq_key
```

Get your keys from:
- [assemblyai.com](https://www.assemblyai.com/) — free $50 credit (~185 hours)
- [console.groq.com](https://console.groq.com/) — free tier available

### 6. Run

```bash
python app.py
```

Visit `http://localhost:10000`

---

## 📁 Project Structure

```
LecSnapPdf/
│
├── app.py              # FastAPI app — routes, SSE progress, frontend HTML
├── core.py             # Core pipelines — manual, smart simple, smart AI
├── classifier.py       # Vision AI video type classifier
├── router.py           # Maps video type → extraction strategy
├── smart_extractor.py  # Perceptual hash frame deduplication
├── transcriber.py      # AssemblyAI audio transcription
├── summarizer.py       # Transcript alignment + Groq summarization
├── layout.py           # PDF page layout — frame + AI summary panel
│
├── uploads/            # Temporary uploaded videos (gitignored)
├── input/              # Downloaded YouTube videos (gitignored)
├── output/             # Generated PDFs per job_id (gitignored)
│
├── .env                # API keys (gitignored)
├── requirements.txt
└── README.md
```

---

## ⚠️ Limitations

- Smart mode works best with **slide-based lectures and screencasts**
- Scrolling notebooks and blackboard videos are supported but less precise
- Animated or fast-cut videos (YouTube explainers etc.) should use Manual mode
- YouTube downloads require local setup — cloud platforms block yt-dlp

---

## 🚧 Roadmap

- OCR-based frame diffing for scrolling notebook videos
- Searchable PDF via embedded OCR text layer
- Anki flashcard export per slide
- React frontend with drag-and-drop upload

---

## 👤 Author

**Rishi Raj** — [GitHub](https://github.com/Rishi8603)