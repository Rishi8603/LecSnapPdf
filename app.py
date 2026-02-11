from flask import Flask, request, send_file, jsonify
import os
import core

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Ensure upload + output folders exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("output", exist_ok=True)


@app.route("/", methods=["GET"])
def home():

    is_local = "localhost" in request.host or "127.0.0.1" in request.host

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
            1. Clone the GitHub repository.<br>
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

        <input type="number" name="interval" placeholder="Interval (seconds)" required>

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
    </script>

</body>
</html>
"""



@app.route("/generate", methods=["POST"])
def generate_pdf():

    source_type = request.form.get("source_type")
    interval = request.form.get("interval")

    if not interval:
        return jsonify({"error": "Interval missing"}), 400

    try:
        interval = int(interval)
    except:
        return jsonify({"error": "Invalid interval"}), 400

    if source_type == "upload":
        uploaded_file = request.files.get("video_file")

        if not uploaded_file or uploaded_file.filename == "":
            return jsonify({"error": "No file uploaded"}), 400

        os.makedirs("uploads", exist_ok=True)
        video_path = os.path.join("uploads", uploaded_file.filename)
        uploaded_file.save(video_path)

    elif source_type == "url":
        url = request.form.get("url")

        if not url:
            return jsonify({"error": "URL missing"}), 400

        video_path = core.download_youtube_video(url)

        if video_path is None:
            return jsonify({"error": "Download failed"}), 500

    else:
        return jsonify({"error": "Invalid source selection"}), 400

    try:
        core.main(video_path, interval)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file("output/notes.pdf", as_attachment=True)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
