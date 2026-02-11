from flask import Flask, request, send_file, jsonify
import os
import core  

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>LecSnapPdf</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 50px;
        }
        .spinner {
            display: none;
            margin-top: 20px;
        }
        .loader {
            border: 6px solid #f3f3f3;
            border-top: 6px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        button:disabled {
            background: #aaa;
            cursor: not-allowed;
        }
    </style>
</head>
<body>

    <h2>LecSnapPdf</h2>

    <form id="pdfForm" action="/generate" method="post">
        <input type="text" name="url" placeholder="Video URL" size="50" required>
        <br><br>
        <input type="number" name="interval" placeholder="Interval (seconds)" required>
        <br><br>
        <button id="submitBtn" type="submit">Generate PDF</button>
    </form>

    <div class="spinner" id="spinner">
        <p>Please wait, generating PDF…</p>
        <div class="loader"></div>
        <p>This may take 1–2 minutes for long videos.</p>
    </div>

    <script>
        const form = document.getElementById("pdfForm");
        const spinner = document.getElementById("spinner");
        const button = document.getElementById("submitBtn");

        form.addEventListener("submit", () => {
            spinner.style.display = "block";
            button.disabled = true;
            button.innerText = "Processing...";
        });
    </script>

</body>
</html>
"""


@app.route("/generate", methods=["POST"])
def generate_pdf():
    url = request.form.get("url")
    interval = request.form.get("interval")

    if not url or not interval:
        return jsonify({"error": "Missing URL or interval"}), 400

    # Monkey patch input() usage
    core.get_video_source = lambda: core.download_youtube_video(url)
    core.get_interval_from_user = lambda: int(interval)

    try:
        core.main()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    pdf_path = "output/notes.pdf"

    if not os.path.exists(pdf_path):
        return jsonify({"error": "PDF not generated"}), 500

    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  
    app.run(host="0.0.0.0", port=port, debug=False)
