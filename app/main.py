import re
import os, tempfile, shutil, uuid, requests
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import JSONResponse
from utils import levenshtein, phonemize_text, calculate_accuracy, normalize_to_ipa, normalize_script_for_mfa

app = FastAPI()

MFA_URL = "https://xbensieve-speaking-assessment-models.hf.space/align"
IPA_PHONEMES = [
    "tʃ", "dʒ", "uː", "iː", "eɪ", "aɪ", "oʊ", "aʊ", "ɔɪ",   
    "ɑː", "ɜː", "ɔː", "ʊə", "ɪə", "eə",
    "p", "b", "t", "d", "k", "g", "f", "v", "θ", "ð", "s", "z",
    "ʃ", "ʒ", "h", "m", "n", "ŋ", "l", "r", "j", "w",
    "æ", "ʌ", "ɪ", "ʊ", "ɛ", "ə", "ɔ", "ɒ", "u", "i"
]
IPA_REGEX = re.compile("|".join(sorted(IPA_PHONEMES, key=len, reverse=True)))

def split_ipa_word(word: str):
    return IPA_REGEX.findall(word)

@app.post("/assess_pronunciation")
async def assess_pronunciation(
    file: UploadFile = File(...),
    script: str = Form(...),
    lang: str = Form("en")
):
   
   
    ref_phones = phonemize_text(script, lang)
    script_for_mfa = normalize_script_for_mfa(script, lang)
    print(f"Debug - Script for MFA: {script_for_mfa}")
    files = {"file": (file.filename, await file.read(), file.content_type)}
    data = {"lang": lang, "transcript": script_for_mfa}
    resp = requests.post(MFA_URL, files=files, data=data)
    result = resp.json()

    if "phones" not in result:
        return JSONResponse({
            "error": result.get("error", "MFA service failed"),
            "details": result
        }, status_code=500)

    hyp_phones = result["phones"]
    alignment = result["alignment"]

    ref_phones_split = []
    for word in ref_phones:
        ref_phones_split.extend(split_ipa_word(word))

    hyp_phones_ipa = normalize_to_ipa(hyp_phones, lang)

    score = 100 * (1 - levenshtein(ref_phones_split, hyp_phones_ipa) / max(len(ref_phones_split), len(hyp_phones_ipa)))

    return JSONResponse({
        "score_percent": round(score, 2),
        "ref_phones": ref_phones,
        "audio_phones": hyp_phones,
        "alignment": alignment
    })