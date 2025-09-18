from flask import Flask, request, jsonify
import os, subprocess, tempfile, logging
from praatio import textgrid

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

os.environ["MFA_ROOT_DIR"] = "/mfa/models"

LANG_MODELS = {
    "en": ("english_us_mfa", "english_mfa"),
    "zh": ("mandarin_mfa", "mandarin_mfa"),
    "ja": ("japanese_mfa", "japanese_mfa")
}

@app.post("/align")
def align():
    lang = request.form.get("lang", "en")
    transcript = request.form.get("transcript", "")
    file = request.files.get("file")

    if not file:
        return jsonify({"error": "audio file missing"}), 400

    if lang[:2] not in LANG_MODELS:
        return jsonify({"error": "unsupported language"}), 400

    dictionary, acoustic = LANG_MODELS[lang[:2]]

    # tạo thư mục tạm
    with tempfile.TemporaryDirectory() as work_dir:
        basename = "utt"
        wav_path = os.path.join(work_dir, f"{basename}.wav")
        lab_path = os.path.join(work_dir, f"{basename}.lab")
        out_dir = os.path.join(work_dir, "aligned")
        os.makedirs(out_dir, exist_ok=True)

        # lưu file audio
        file.save(wav_path)

        # lưu transcript
        with open(lab_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        # chạy MFA
        cmd = ["mfa", "align", work_dir, dictionary, acoustic, out_dir, "--clean"]
        logger.debug(f"Running MFA command: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug(f"MFA stdout: {result.stdout}")
            logger.debug(f"MFA stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            return jsonify({
                "status": "error",
                "stdout": e.stdout,
                "stderr": e.stderr
            }), 500

        # đọc kết quả TextGrid
        tg_path = os.path.join(out_dir, f"{basename}.TextGrid")
        if not os.path.exists(tg_path):
            return jsonify({"error": "TextGrid not generated"}), 500

        tg = textgrid.openTextgrid(tg_path, includeEmptyIntervals=True)
        tier = next((t for t in tg.tiers if t.name == "phones"), tg.tiers[0])
        phones = [e.label for e in tier.entries if e.label.strip()]
        alignment = [
            {"phone": e.label, "start": e.start, "end": e.end}
            for e in tier.entries if e.label.strip()
        ]

        return jsonify({"phones": phones, "alignment": alignment})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
