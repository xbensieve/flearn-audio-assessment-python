from typing import List
from phonemizer import phonemize
from praatio import textgrid

def levenshtein(a: List[str], b: List[str]) -> int:
    n, m = len(a), len(b)
    dp = [[0]*(m+1) for _ in range(n+1)]
    for i in range(n+1): dp[i][0] = i
    for j in range(m+1): dp[0][j] = j
    for i in range(1,n+1):
        for j in range(1,m+1):
            cost = 0 if a[i-1]==b[j-1] else 1
            dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)
    return dp[n][m]

def phonemize_text(text: str, lang: str):
    if lang.startswith("ja"):
        import pyopenjtalk
        try:
            phones = pyopenjtalk.g2p(text, kana=False)
            return phones.split()
        except Exception as e:
            return []
    elif lang.startswith("zh"):
        from pypinyin import pinyin, Style
        pys = pinyin(text, style=Style.TONE3, neutral_tone_with_five=True)
        phonemes = []
        for py in pys:
            p = py[0].split()
            if len(p) > 1:
                base = p[0][:-1]
                tone = p[0][-1]
                phonemes.extend(list(base))
                phonemes.append(f"t{tone}")
            else:
                phonemes.extend(list(p[0]))
        return phonemes
    else:
        phones = phonemize(text, language="en-us", backend="espeak", strip=True)
        return phones.split()
    
def normalize_to_ipa(phonemes: list, lang: str):
    """
    Convert phonemes from language-specific representations to IPA.
    """
    # Japanese mapping (pyopenjtalk output -> IPA)
    ja_map = {
        "a": "a", "i": "i", "u": "ɯ", "e": "e", "o": "o",
        "N": "ŋ", "cl": "ʔ", "s": "s", "sh": "ɕ", "ch": "tɕ",
        "j": "ʑ", "ts": "ts", "f": "ɸ", "h": "h", "r": "ɾ",
        "y": "j", "w": "w", "g": "g", "k": "k", "t": "t", "d": "d",
        "n": "n", "m": "m", "b": "b", "p": "p", "z": "z"
    }

    # Chinese mapping (pinyin -> IPA) (simplified)
    zh_map = {
        "a": "a", "ai": "ai̯", "an": "an", "ang": "ɑŋ", "ao": "au̯",
        "e": "ɤ", "ei": "ei̯", "en": "ən", "eng": "ɤŋ", "er": "aɻ",
        "i": "i", "ia": "ja", "iao": "jau̯", "ian": "jɛn",
        "in": "in", "ing": "iŋ", "ie": "jɛ",
        "o": "o", "ong": "ʊŋ", "ou": "ou̯",
        "u": "u", "ua": "wa", "uo": "wo", "un": "uən",
        "ü": "y", "üe": "yɛ",
        # consonants
        "b": "p", "p": "pʰ", "m": "m", "f": "f",
        "d": "t", "t": "tʰ", "n": "n", "l": "l",
        "g": "k", "k": "kʰ", "h": "x",
        "j": "tɕ", "q": "tɕʰ", "x": "ɕ",
        "zh": "ʈʂ", "ch": "ʈʂʰ", "sh": "ʂ", "r": "ʐ",
        "z": "ts", "c": "tsʰ", "s": "s",
        "y": "j", "w": "w"
    }

    en_map = {
        "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
        "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "EH": "ɛ", "ER": "ɝ",
        "EY": "eɪ", "F": "f", "G": "ɡ", "HH": "h", "IH": "ɪ", "IY": "i",
        "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ",
        "OW": "oʊ", "OY": "ɔɪ", "P": "p", "R": "ɹ", "S": "s", "SH": "ʃ",
        "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u", "V": "v", "W": "w",
        "Y": "j", "Z": "z", "ZH": "ʒ"
    }

    normalized = []
    if lang.startswith("ja"):
        for p in phonemes:
            normalized.append(ja_map.get(p, p))
    elif lang.startswith("zh"):
        for p in phonemes:
            if p.startswith("t") and p[1:].isdigit():  
                normalized.append(p)  
            else:
                normalized.append(zh_map.get(p, p))
    else:
        for p in phonemes:
            normalized.append(en_map.get(p.upper(), p))
    return normalized

def calculate_accuracy(ref_phones: List[str], hyp_phones: List[str], lang: str) -> float:
    """
    Calculate % phoneme match between reference and hypothesis, both in IPA.
    """
    if not ref_phones or not hyp_phones:
        return 0.0

    ref_ipa = normalize_to_ipa(ref_phones, lang)
    hyp_ipa = normalize_to_ipa(hyp_phones, lang)

    dist = levenshtein(ref_ipa, hyp_ipa)
    max_len = max(len(ref_ipa), len(hyp_ipa))

    accuracy = (1 - dist / max_len) * 100
    return max(0.0, min(accuracy, 100.0))

def normalize_script_for_mfa(script: str, lang: str) -> str:
    """
    Chuẩn hóa script đầu vào cho MFA service.
    """
    script = script.strip()

    if lang.startswith("ja"):
        # MFA Nhật thường chấp nhận romaji, nên convert kana -> romaji nếu có
        import pyopenjtalk
        try:
            romaji = pyopenjtalk.g2p(script, kana=False)
            return romaji
        except Exception:
            return script  # fallback giữ nguyên
    elif lang.startswith("zh"):
        # MFA Mandarin chấp nhận pinyin, convert Hán tự -> pinyin
        from pypinyin import pinyin, Style
        pys = pinyin(script, style=Style.TONE3, neutral_tone_with_five=True)
        # nối thành string cách nhau bằng space
        pinyin_text = " ".join([s[0] for s in pys])
        return pinyin_text
    else:
        # English: loại bỏ ký tự lạ, giữ text chuẩn
        import re
        script = re.sub(r"[^a-zA-Z0-9\s'.!?-]", "", script)
        return script
