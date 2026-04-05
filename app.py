from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import os
import core
import uvicorn
from smart_extractor import extract_unique_frames

app = FastAPI()

# Ensure upload + output folders exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("output", exist_ok=True)


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
    <style>
        body {{ font-family: Arial; margin: 50px; }}
        .hidden {{ display: none; }}
        .spinner {{ display: none; margin-top: 20px; }}
        .loader {{
            border: 6px solid #f3f3f3;
            border-top: 6px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>

    <h2>LecSnapPdf</h2>

    <form id="pdfForm" method="post" enctype="multipart/form-data">

        <label>
            <input type="radio" name="source_type" value="upload" checked>
            Upload Video
        </label>

        <label>
            <input type="radio" name="source_type" value="url">
            Paste Video URL
        </label>

        <br><br>

        <div id="uploadSection">
            <input type="file" name="video_file" accept="video/*">
        </div>

        <div id="urlSection" class="hidden">
            <input type="text" name="url" placeholder="Enter video URL" size="50">
            {info_box}
        </div>

        <br><br>

        <label>
            <input type="radio" name="mode" value="manual" checked onchange="toggleMode(this)">
            Manual (enter interval)
        </label>

        <label>
            <input type="radio" name="mode" value="smart" onchange="toggleMode(this)">
            Smart (auto-detect slide changes)
        </label>

        <br><br>

        <div id="intervalSection">
            <input type="number" name="interval" placeholder="Interval (seconds)">
        </div>

        <div id="smartInfo" style="display:none; color:gray; font-size:13px;">
            Smart mode will automatically capture frames only when the slide changes.
            <br>Best for: lecture recordings, screencasts.
        </div>

        <br><br>

        <button id="submitBtn" type="submit">Generate PDF</button>
    </form>

    <div class="spinner" id="spinner">
        <p>Generating PDF...</p>
        <div class="loader"></div>
    </div>

    <script>
        const radios = document.querySelectorAll("input[name='source_type']");
        const uploadSection = document.getElementById("uploadSection");
        const urlSection = document.getElementById("urlSection");

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

        const form = document.getElementById("pdfForm");
        const spinner = document.getElementById("spinner");
        const button = document.getElementById("submitBtn");

        form.addEventListener("submit", async (e) => {{
            e.preventDefault();

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
                    const errorData = await response.json();
                    alert(errorData.error || "Something went wrong");
                }} else {{
                    const blob = await response.blob();
                    const downloadUrl = window.URL.createObjectURL(blob);

                    const a = document.createElement("a");
                    a.href = downloadUrl;
                    a.download = "notes.pdf";
                    document.body.appendChild(a);
                    a.click();
                    a.remove();

                    alert("PDF generated successfully!");
                }}

            }} catch (error) {{
                alert("Error generating PDF");
            }}

            spinner.style.display = "none";
            button.disabled = false;
            button.innerText = "Generate PDF";
        }});
        function toggleMode(radio) {{
            const intervalSection = document.getElementById("intervalSection");
            const smartInfo = document.getElementById("smartInfo");
            if (radio.value === "smart") {{
                intervalSection.style.display = "none";
                smartInfo.style.display = "block";
            }} else {{
                intervalSection.style.display = "block";
                smartInfo.style.display = "none";
            }}
        }}
    </script>

</body>
</html>
"""


@app.post("/generate")
async def generate_pdf(
    source_type: str = Form(...),
    mode: str = Form(...),
    interval: int = Form(None),
    video_file: UploadFile | None = File(None),
    url: str = Form(None),
):

    if source_type == "upload":
        if not video_file or video_file.filename == "":
            return JSONResponse({"error": "No file uploaded"}, status_code=400)

        os.makedirs("uploads", exist_ok=True)
        video_path = os.path.join("uploads", video_file.filename)

        with open(video_path, "wb") as f:
            content = await video_file.read()
            f.write(content)

    elif source_type == "url":
        if not url:
            return JSONResponse({"error": "URL missing"}, status_code=400)

        video_path = core.download_youtube_video(url)

        if video_path is None:
            return JSONResponse({"error": "Download failed"}, status_code=500)

    else:
        return JSONResponse({"error": "Invalid source selection"}, status_code=400)

    try:
        if mode == "smart":
            # Use perceptual hash dedup
            frames = extract_unique_frames(video_path, threshold=30)
            if not frames:
                return JSONResponse({"error": "No unique frames detected"}, status_code=500)
            core.save_frames_as_pdf(frames)
        else:
            # Original interval mode
            if not interval:
                return JSONResponse({"error": "Interval required for manual mode"}, status_code=400)
            core.main(video_path, interval)
    except Exception as e:
        print("FULL ERROR:", e)
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

    return FileResponse("output/notes.pdf", filename="notes.pdf", media_type="application/pdf")


@app.get("/api/health")
async def health():
    return {"status": "OK"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="127.0.0.1", port=port)
