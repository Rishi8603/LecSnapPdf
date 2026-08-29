from fastapi import FastAPI, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse, Response
import os
import uuid
import asyncio
import core
import uvicorn
from smart_extractor import extract_unique_frames

app = FastAPI()

# Global progress tracker
progress_store = {}

# Ensure upload + output folders exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("output", exist_ok=True)


@app.get("/favicon.ico")
async def favicon():
    # Return a tiny transparent icon so browsers stop retrying a missing asset.
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    is_local = "localhost" in str(request.url) or "127.0.0.1" in str(request.url)

    if is_local:
        info_box = """
        <div style="
            margin-top:15px;
            padding:15px;
            background:#d4edda;
            border:1px solid #c3e6cb;
            border-radius:6px;
            font-size:14px;
        ">
            <strong>YouTube Fully Supported</strong><br><br>
            You are running this project locally.<br>
            YouTube downloads using <b>yt-dlp</b> will work normally.
        </div>
        """
    else:
        info_box = """
        <div style="
            margin-top:15px;
            padding:15px;
            background:#fff3cd;
            border:1px solid #ffeeba;
            border-radius:6px;
            font-size:14px;
        ">
            <strong>⚠ Important for YouTube Users</strong><br><br>
            Cloud platforms block video downloading tools like <b>yt-dlp</b>.<br><br>

            <strong>Solution:</strong><br>
             1. Clone the GitHub repository:
            <a href="https://github.com/Rishi8603/LecSnapPdf" target="_blank">
                https://github.com/Rishi8603/LecSnapPdf
            </a><br>
            2. Run the project locally on your system.<br>
            3. Paste the YouTube URL there — it will download and generate the PDF successfully.<br><br>

            OR download the video manually and upload it using the 
            <b>Upload Video</b> option above.
        </div>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>LecSnapPdf</title>
    <link rel="icon" href="/favicon.ico" sizes="any">
    <style>
        :root {{
            --bg: linear-gradient(135deg, #f4f7fb 0%, #edf4ff 100%);
            --panel: #ffffff;
            --panel-border: #dce6f5;
            --text: #1c2430;
            --muted: #617083;
            --primary: #1f6feb;
            --primary-dark: #1659be;
            --soft: #f7faff;
            --shadow: 0 18px 45px rgba(24, 63, 122, 0.12);
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            min-height: 100vh;
            padding: 28px 14px;
            font-family: "Segoe UI", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
        }}
        .hidden {{ display: none; }}
        .page {{ max-width: 760px; margin: 0 auto; }}
        .card {{
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 22px;
            padding: 30px;
            box-shadow: var(--shadow);
        }}
        h1 {{
            margin: 0 0 8px;
            font-size: 34px;
            letter-spacing: -0.02em;
        }}
        .subtitle {{
            margin: 0 0 26px;
            color: var(--muted);
            font-size: 15px;
            line-height: 1.6;
        }}
        .section {{
            margin-top: 20px;
            padding: 18px;
            background: var(--soft);
            border: 1px solid #e2ebfa;
            border-radius: 16px;
        }}
        .section-title {{
            margin: 0 0 14px;
            font-size: 13px;
            font-weight: 700;
            color: #3d4a5d;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .option-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .option-card {{
            flex: 1 1 220px;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 14px 15px;
            background: #ffffff;
            border: 1px solid #d5e2f6;
            border-radius: 14px;
            cursor: pointer;
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }}
        .option-card:hover {{
            transform: translateY(-1px);
            border-color: #a9c6f5;
            box-shadow: 0 8px 20px rgba(31, 111, 235, 0.08);
        }}
        .option-card input {{ accent-color: var(--primary); }}
        .field {{ margin-top: 14px; }}
        input[type="text"],
        input[type="number"],
        input[type="file"] {{
            width: 100%;
            padding: 13px 14px;
            border: 1px solid #cfd9ea;
            border-radius: 12px;
            background: #ffffff;
            font-size: 14px;
        }}
        input[type="text"]:focus,
        input[type="number"]:focus,
        input[type="file"]:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(31, 111, 235, 0.12);
        }}
        .hint {{
            margin: 0 0 14px;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.6;
        }}
        .subhint {{
            margin: 10px 0 0;
            color: var(--muted);
            font-size: 12px;
            line-height: 1.5;
        }}
        .limit-box {{
            margin-top: 14px;
            padding: 16px 18px;
            background: #fff8e8;
            border: 1px solid #f2d49b;
            border-radius: 14px;
            color: #5f4307;
        }}
        .limit-title {{
            margin: 0 0 10px;
            font-size: 14px;
            font-weight: 700;
        }}
        .limit-list {{
            margin: 0;
            padding-left: 18px;
            line-height: 1.7;
            font-size: 13px;
        }}
        .actions {{ margin-top: 26px; }}
        button {{
            width: 100%;
            padding: 15px 18px;
            border: none;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--primary) 0%, #3b82f6 100%);
            color: #ffffff;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 12px 24px rgba(31, 111, 235, 0.22);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 16px 30px rgba(31, 111, 235, 0.28);
        }}
        button:disabled {{
            opacity: 0.78;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }}
        .spinner {{
            display: none;
            margin-top: 20px;
            padding: 18px;
            background: #f8fbff;
            border: 1px solid #d8e5fb;
            border-radius: 16px;
            text-align: center;
        }}
        .loader {{
            border: 5px solid #e7eef9;
            border-top: 5px solid var(--primary);
            border-radius: 50%;
            width: 42px;
            height: 42px;
            animation: spin 0.9s linear infinite;
            margin: 12px auto 0;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        #statusText {{
            margin: 0;
            min-height: 20px;
            font-size: 14px;
            font-weight: 600;
            color: #31507a;
            text-align: center;
        }}
        .message {{
            display: none;
            margin-top: 16px;
            padding: 14px 16px;
            border-radius: 14px;
            font-size: 14px;
            line-height: 1.5;
            font-weight: 600;
        }}
        .message.error {{
            display: block;
            background: #fff1f2;
            border: 1px solid #fecdd3;
            color: #b42318;
        }}
        .message.info {{
            display: block;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1d4ed8;
        }}
        a {{ color: var(--primary); }}
        @media (max-width: 640px) {{
            .card {{ padding: 20px; border-radius: 18px; }}
            h1 {{ font-size: 28px; }}
            .option-card {{ flex-basis: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="page">
        <div class="card">
            <h1>LecSnapPdf</h1>
            <p class="subtitle">
                Convert lecture videos into clean, downloadable PDF notes with manual interval capture or smart slide detection.
            </p>

            <form id="pdfForm" method="post" enctype="multipart/form-data">

                <div class="section">
                    <p class="section-title">Video Source</p>

                    <div class="option-row">
                        <label class="option-card">
                            <input type="radio" name="source_type" value="upload" checked>
                            <span>Upload Video</span>
                        </label>

                        <label class="option-card">
                            <input type="radio" name="source_type" value="url">
                            <span>Paste Video URL</span>
                        </label>
                    </div>

                    <div class="field" id="uploadSection">
                        <input type="file" name="video_file" accept="video/*">
                    </div>

                    <div class="field hidden" id="urlSection">
                        <input type="text" name="url" placeholder="Enter video URL">
                        {info_box}
                    </div>
                </div>

                <div class="section">
                    <p class="section-title">Capture Mode</p>

                    <div class="option-row">
                        <label class="option-card">
                            <input type="radio" name="mode" value="manual" checked onchange="toggleMode(this)">
                            <span>Manual Interval</span>
                        </label>

                        <label class="option-card">
                            <input type="radio" name="mode" value="smart" onchange="toggleMode(this)">
                            <span>Smart Detection</span>
                        </label>
                    </div>

                    <div class="field" id="intervalSection">
                        <input type="number" name="interval" placeholder="Interval in seconds">
                    </div>

                    <div class="field" id="smartInfo" style="display:none;">
                        <p class="hint">
                            Smart mode captures frames only when the slide changes. Best for lectures, slide recordings, and screencasts.
                        </p>

                        <div class="limit-box">
                            <p class="limit-title">Limitations</p>
                            <ul class="limit-list">
                                <li>Smart mode works best with slide-based lectures and screencasts.</li>
                                <li>Scrolling notebooks and blackboard videos are supported, but results may be less precise.</li>
                                <li>Animated or fast-cut videos usually work better with Manual Interval mode.</li>
                            </ul>
                        </div>

                        <div class="option-row">
                            <label class="option-card">
                                <input type="radio" name="smart_type" value="simple" checked>
                                <span>Simple Frames</span>
                            </label>

                            <label class="option-card">
                                <input type="radio" name="smart_type" value="ai">
                                <span>AI Summary</span>
                            </label>
                        </div>

                        <div class="field hidden" id="aiLayoutSection">
                            <p class="hint">
                                AI Summary will place a short concept summary beside each captured slide inside the final PDF.
                            </p>
                            <p class="subhint">
                                Choose where you want that summary panel to appear.
                            </p>

                            <div class="option-row">
                                <label class="option-card">
                                    <input type="radio" name="ai_layout" value="top">
                                    <span>Top</span>
                                </label>

                                <label class="option-card">
                                    <input type="radio" name="ai_layout" value="right" checked>
                                    <span>Right</span>
                                </label>

                                <label class="option-card">
                                    <input type="radio" name="ai_layout" value="left">
                                    <span>Left</span>
                                </label>

                                <label class="option-card">
                                    <input type="radio" name="ai_layout" value="bottom">
                                    <span>Bottom</span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="actions">
                    <button id="submitBtn" type="submit">Generate PDF</button>
                </div>
            </form>

            <div id="messageBox" class="message"></div>

            <div class="spinner" id="spinner">
                <p id="statusText">Processing...</p>
                <div class="loader"></div>
            </div>
        </div>
    </div>

    <script>
        const radios = document.querySelectorAll("input[name='source_type']");
        const uploadSection = document.getElementById("uploadSection");
        const urlSection = document.getElementById("urlSection");
        const smartTypeRadios = document.querySelectorAll("input[name='smart_type']");
        const aiLayoutSection = document.getElementById("aiLayoutSection");
        const form = document.getElementById("pdfForm");
        const spinner = document.getElementById("spinner");
        const button = document.getElementById("submitBtn");
        const statusEl = document.getElementById("statusText");
        const messageBox = document.getElementById("messageBox");

        function setMessage(message, type = "info") {{
            if (!message) {{
                messageBox.className = "message";
                messageBox.textContent = "";
                return;
            }}
            messageBox.className = `message ${{type}}`;
            messageBox.textContent = message;
        }}

        function resetUi() {{
            spinner.style.display = "none";
            button.disabled = false;
            button.innerText = "Generate PDF";
        }}

        radios.forEach(radio => {{
            radio.addEventListener("change", function() {{
                if (this.value === "upload") {{
                    uploadSection.classList.remove("hidden");
                    urlSection.classList.add("hidden");
                }} else {{
                    uploadSection.classList.add("hidden");
                    urlSection.classList.remove("hidden");
                }}
            }});
        }});

        smartTypeRadios.forEach(radio => {{
            radio.addEventListener("change", toggleAiLayout);
        }});

        form.addEventListener("submit", async (e) => {{
            e.preventDefault();
            setMessage("");
            spinner.style.display = "block";
            button.disabled = true;
            button.innerText = "Processing...";

            const formData = new FormData(form);

            try {{
                const response = await fetch("/generate", {{
                    method: "POST",
                    body: formData
                }});

                if (!response.ok) {{
                    let errorMessage = "Something went wrong";
                    try {{
                        const errorData = await response.json();
                        errorMessage = errorData.error || errorMessage;
                    }} catch (err) {{}}
                    throw new Error(errorMessage);
                }}

                const {{ job_id }} = await response.json();

                const evtSource = new EventSource(`/progress/${{job_id}}`);

                evtSource.onmessage = function(e) {{
                    if (e.data === "DONE") {{
                        evtSource.close();
                        setMessage("");
                        window.location.href = `/download/${{job_id}}`;
                        resetUi();
                    }} else if (e.data.startsWith("ERROR")) {{
                        evtSource.close();
                        setMessage(e.data, "error");
                        resetUi();
                    }} else {{
                        setMessage("");
                        statusEl.innerText = e.data;
                    }}
                }};

                evtSource.onerror = function() {{
                    evtSource.close();
                    setMessage("Connection lost while tracking progress. Please try again.", "error");
                    resetUi();
                }};

            }} catch (error) {{
                setMessage(error.message || "Network error", "error");
                resetUi();
            }}
        }});

        function toggleMode(radio) {{
            const intervalSection = document.getElementById("intervalSection");
            const smartInfo = document.getElementById("smartInfo");
            if (radio.value === "smart") {{
                intervalSection.style.display = "none";
                smartInfo.style.display = "block";
                toggleAiLayout();
            }} else {{
                intervalSection.style.display = "block";
                smartInfo.style.display = "none";
                aiLayoutSection.classList.add("hidden");
            }}
        }}

        function toggleAiLayout() {{
            const aiSelected = document.querySelector("input[name='smart_type']:checked")?.value === "ai";
            aiLayoutSection.classList.toggle("hidden", !aiSelected);
        }}

        toggleAiLayout();
    </script>

</body>
</html>
"""


@app.post("/generate")
async def generate_pdf(
    background_tasks: BackgroundTasks,
    source_type: str = Form(...),
    mode: str = Form(...),
    interval: int = Form(None),
    smart_type: str = Form(None),
    ai_layout: str = Form("right"),
    video_file: UploadFile | None = File(None),
    url: str = Form(None),
):
    video_path = None

    if source_type == "upload":
        if not video_file or not video_file.filename:
            return JSONResponse({"error": "No file uploaded"}, status_code=400)

        os.makedirs("uploads", exist_ok=True)

        filename = os.path.basename(video_file.filename)
        video_path = os.path.join("uploads", filename)

        with open(video_path, "wb") as f:
            content = await video_file.read()
            f.write(content)

    elif source_type == "url":
        if not url:
            return JSONResponse({"error": "URL missing"}, status_code=400)

        # The download itself is deferred into run_pipeline. yt-dlp is a
        # blocking subprocess, so calling it here would freeze the event loop
        # for the entire download and stall every other request.

    else:
        return JSONResponse({"error": "Invalid source selection"}, status_code=400)

    job_id = str(uuid.uuid4())
    progress_store[job_id] = "Starting..."

    def run_pipeline():
        try:
            path = video_path

            if path is None:
                progress_store[job_id] = "Downloading video from URL..."
                path = core.download_youtube_video(url, job_id=job_id)

                if path is None:
                    progress_store[job_id] = "ERROR: Download failed"
                    return

            if mode == "smart":
                if smart_type == "ai":
                    core.smart_pipeline(path, job_id, progress_store, ai_layout)
                else:
                    frames = extract_unique_frames(path, threshold=25)
                    core.save_frames_as_pdf(frames, job_id)
            else:
                if not interval:
                    progress_store[job_id] = "ERROR: Interval required"
                    return
                core.main(path, interval, job_id)
            progress_store[job_id] = "DONE"
        except Exception as e:
            import traceback
            traceback.print_exc()
            progress_store[job_id] = f"ERROR: {str(e)}"

    background_tasks.add_task(run_pipeline)

    return JSONResponse({"job_id": job_id})


@app.get("/download/{job_id}")
async def download_pdf(job_id: str):
    pdf_path = f"output/{job_id}.pdf"
    if not os.path.exists(pdf_path):
        return JSONResponse({"error": "PDF not ready"}, status_code=404)

    return FileResponse(pdf_path, filename="notes.pdf", media_type="application/pdf")


@app.get("/api/health")
async def health():
    return {"status": "OK"}


@app.get("/progress/{job_id}")
async def progress(job_id: str):
    async def event_stream():
        last = None
        while True:
            msg = progress_store.get(job_id)
            if msg and msg != last:
                yield f"data: {msg}\n\n"
                last = msg
                if msg == "DONE" or msg.startswith("ERROR"):
                    break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    is_local = os.environ.get("RENDER") is None
    host = "127.0.0.1" if is_local else "0.0.0.0"
    uvicorn.run(app, host=host, port=port)
