"""
localization.py — Multilingual Insult Engine for Skill Issue.
Intentionally bad, condescending pseudo-translations for non-English languages.
"""
import random

# ─────────────────────────────────────────────
#  SUPPORTED LANGUAGES
# ─────────────────────────────────────────────
LANGUAGES = ["English", "Español", "Français", "Deutsch", "日本語", "हिन्दी"]

# ─────────────────────────────────────────────
#  INSULT TABLES
#  English is the source of truth. All other languages
#  use intentionally robotic, pseudo-literal translations
#  that sound like bad Google Translate output.
# ─────────────────────────────────────────────

_INSULTS = {
    "English": [
        (0,   "Getting warmed up?"),
        (11,  "Are your hands made of butter?"),
        (31,  "Maybe try a nice quiet puzzle game?"),
        (61,  "Actually painful to watch."),
        (101, "This is genuinely tragic."),
        (200, "At this point you're a burden to the CPU."),
    ],
    "Español": [
        (0,   "¿Estás calentando tus capacidades?"),
        (11,  "¿Sus manos son fabricadas de mantequilla?"),
        (31,  "Quizás intente un juego de rompecabezas de la quietud."),
        (61,  "Es de un dolor auténtico observar esto."),
        (101, "Esto es de una tragedia genuina."),
        (200, "En este punto, usted es una carga para la unidad central de procesamiento."),
    ],
    "Français": [
        (0,   "Vous effectuez le réchauffement?"),
        (11,  "Vos mains sont-elles fabriquées en beurre?"),
        (31,  "Peut-être essayez un jeu de puzzle de la tranquillité?"),
        (61,  "C'est d'une douleur authentique à observer."),
        (101, "Ceci est d'une tragédie véritablement sincère."),
        (200, "À ce stade, vous êtes un fardeau pour l'unité centrale."),
    ],
    "Deutsch": [
        (0,   "Vollziehen Sie die Aufwärmung?"),
        (11,  "Sind Ihre Hände aus Butter hergestellt?"),
        (31,  "Vielleicht versuchen Sie ein Rätselspiel der Stille?"),
        (61,  "Es ist von einem echten Schmerz, dies zu beobachten."),
        (101, "Dies ist von einer wahrhaft aufrichtigen Tragödie."),
        (200, "An diesem Punkt sind Sie eine Belastung für die Zentraleinheit."),
    ],
    "日本語": [
        (0,   "ウォーミングアップを実行していますか？"),
        (11,  "あなたの手はバターで製造されていますか？"),
        (31,  "静けさのパズルゲームを試みてはいかがでしょうか？"),
        (61,  "これを観察することは本物の痛みです。"),
        (101, "これは真に誠実な悲劇です。"),
        (200, "この時点で、あなたは中央処理装置にとっての負担です。"),
    ],
    "हिन्दी": [
        (0,   "क्या आप अपनी क्षमताओं का तापन कर रहे हैं?"),
        (11,  "क्या आपके हाथ मक्खन से निर्मित हैं?"),
        (31,  "शायद शांति की पहेली खेल का प्रयास करें?"),
        (61,  "इसका अवलोकन करना प्रामाणिक पीड़ा है।"),
        (101, "यह वास्तव में ईमानदार त्रासदी है।"),
        (200, "इस बिंदु पर, आप केंद्रीय प्रसंस्करण इकाई के लिए भार हैं।"),
    ],
}

# Loop-aware insults (only English, others get the English version with a prefix)
_LOOP_INSULTS_EN = {
    0: "",
    1: "",
    2: "Loop 2. You literally already failed this exact jump.",
    3: "Repeating history is a mental illness. Look it up.",
    4: "Four loops deep. The definition of insanity applies here.",
    5: "You are the game's best advertisement for giving up.",
    6: "Six loops. The map has gotten worse. So have you.",
    7: "Seven loops. I genuinely feel nothing for you anymore.",
}
_LOOP_INSULTS_DEFAULT = "Still going? Remarkable. Not in a good way."

# Chaos taunts per language
_CHAOS = {
    "English":  ["Why?", "Again?", "Quit.", "Please.", "Stop.", "...", "No.", "Done?", "Leave.", "Seriously.", "Go."],
    "Español":  ["¿Por qué?", "¿Otra vez?", "Renuncie.", "Por favor.", "Pare.", "...", "No.", "¿Terminó?", "Váyase.", "En serio.", "Vaya."],
    "Français": ["Pourquoi?", "Encore?", "Quittez.", "S'il vous plaît.", "Arrêtez.", "...", "Non.", "Fini?", "Partez.", "Sérieusement.", "Allez."],
    "Deutsch":  ["Warum?", "Nochmal?", "Aufhören.", "Bitte.", "Stopp.", "...", "Nein.", "Fertig?", "Gehen.", "Ernsthaft.", "Los."],
    "日本語":    ["なぜ？", "また？", "やめろ。", "お願い。", "止まれ。", "…", "いいえ。", "終わり？", "去れ。", "本気？", "行け。"],
    "हिन्दी":    ["क्यों?", "फिर?", "छोड़ो।", "कृपया।", "रुको।", "...", "नहीं।", "हो गया?", "जाओ।", "गंभीरता।", "चलो।"],
}

# Fake translation error messages
_FAKE_ERRORS = [
    "Error 404: Skill translation not found",
    "TRANSLATION_BUFFER_OVERFLOW: too many failures to localize",
    "UnicodeDecodeError: 'skill' codec can't decode byte 0x00",
    "Warning: talent.dll is missing or corrupted",
    "Fatal: Motivation module returned NULL",
]


class InsultEngine:
    """Resolves mocking quotes based on language, death count, and loop."""

    def __init__(self):
        self.lang_index = 0   # Index into LANGUAGES

    @property
    def language(self) -> str:
        return LANGUAGES[self.lang_index]

    def cycle_language(self):
        """Advance to next language."""
        self.lang_index = (self.lang_index + 1) % len(LANGUAGES)

    def get_mocking_quote(self, death_count: int, loop_count: int, chaos_start: int) -> str:
        lang = self.language
        if loop_count >= chaos_start:
            taunts = _CHAOS.get(lang, _CHAOS["English"])
            return taunts[death_count % len(taunts)]

        table = _INSULTS.get(lang, _INSULTS["English"])
        current = table[0][1]
        for threshold, quote in table:
            if death_count >= threshold:
                current = quote
        return current

    def get_loop_insult(self, loop_count: int, chaos_start: int) -> str:
        if loop_count >= chaos_start:
            return ""
        return _LOOP_INSULTS_EN.get(loop_count,
                                     _LOOP_INSULTS_DEFAULT if loop_count > max(_LOOP_INSULTS_EN) else "")

    @staticmethod
    def get_fake_error() -> str:
        return random.choice(_FAKE_ERRORS)
