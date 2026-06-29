"""
Audio-based speech analysis for interview answers.
Uses faster-whisper (ASR + word timestamps) and librosa (acoustic features).
"""

import os
import re
import tempfile
from typing import Dict, List, Optional

import numpy as np

from config import (
    SPEECH_WHISPER_MODEL,
    SPEECH_WHISPER_DEVICE,
    SPEECH_COMPONENT_WEIGHTS,
    SPEECH_IDEAL_WPM,
    SPEECH_LONG_PAUSE_SECONDS,
    SPEECH_MAX_FILLER_RATE,
    SPEECH_SCORE_MAX,
)

FILLER_PHRASES = [
    'you know', 'kind of', 'sort of', 'i mean', 'you see',
]
FILLER_WORDS = {
    'um', 'umm', 'uh', 'uhm', 'erm', 'ah', 'eh', 'hmm', 'hm', 'er',
    'like', 'basically', 'actually', 'literally', 'right', 'okay', 'ok',
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _cap_speech_score(value: float) -> float:
    return _clamp(value, high=SPEECH_SCORE_MAX)


def _tokenize(text: str) -> set:
    return set(re.findall(r'\b\w+\b', (text or '').lower()))


class SpeechAnalyzer:
    """Singleton analyzer for interview answer audio."""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_whisper(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            print(f"🔄 Loading speech model: {SPEECH_WHISPER_MODEL} ({SPEECH_WHISPER_DEVICE})")
            self._model = WhisperModel(
                SPEECH_WHISPER_MODEL,
                device=SPEECH_WHISPER_DEVICE,
                compute_type="int8" if SPEECH_WHISPER_DEVICE == "cpu" else "float16",
            )
            print("✅ Speech model loaded")
        return self._model

    def analyze(self, audio_bytes: bytes, reference_text: str = "", suffix: str = ".webm") -> Dict:
        if not audio_bytes or len(audio_bytes) < 500:
            raise ValueError("Audio file is too small to analyze")

        if not suffix.startswith("."):
            suffix = f".{suffix}"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            audio_path = tmp.name

        try:
            return self._analyze_file(audio_path, reference_text)
        finally:
            try:
                os.unlink(audio_path)
            except OSError:
                pass

    def _transcribe(self, audio_path: str):
        model = self._load_whisper()
        segments, info = model.transcribe(
            audio_path,
            word_timestamps=True,
            vad_filter=True,
            language="en",
        )

        words: List[Dict] = []
        transcript_parts: List[str] = []
        logprobs: List[float] = []

        for segment in segments:
            text = (segment.text or "").strip()
            if text:
                transcript_parts.append(text)

            if not segment.words:
                continue

            for word in segment.words:
                token = (word.word or "").strip()
                if not token:
                    continue
                prob = getattr(word, "probability", None)
                if prob is not None:
                    logprobs.append(float(prob))
                words.append({
                    "word": token,
                    "start": float(word.start),
                    "end": float(word.end),
                    "probability": float(prob) if prob is not None else 0.85,
                })

        transcript = " ".join(transcript_parts).strip()
        duration = float(getattr(info, "duration", 0) or 0)
        return words, transcript, logprobs, duration

    def _count_fillers(self, words: List[Dict], transcript: str) -> int:
        count = 0
        tokens = [w["word"].lower().strip(".,!?;:") for w in words]
        joined = " ".join(tokens)

        for phrase in FILLER_PHRASES:
            count += len(re.findall(rf'\b{re.escape(phrase)}\b', joined))

        for token in tokens:
            if token in FILLER_WORDS:
                count += 1

        return count

    def _score_fillers(self, words: List[Dict], transcript: str) -> float:
        filler_count = self._count_fillers(words, transcript)
        word_count = max(len(words), len(_tokenize(transcript)), 1)
        filler_rate = filler_count / word_count
        return _clamp(1.0 - (filler_rate / SPEECH_MAX_FILLER_RATE))

    def _score_pause_pacing(self, words: List[Dict], duration: float) -> float:
        long_pauses = 0
        gaps: List[float] = []
        for index in range(1, len(words)):
            gap = max(words[index]["start"] - words[index - 1]["end"], 0.0)
            gaps.append(gap)
            if gap >= SPEECH_LONG_PAUSE_SECONDS:
                long_pauses += 1

        pause_score = _clamp(1.0 - long_pauses * 0.12)

        if gaps:
            avg_gap = float(np.mean(gaps))
            spacing_score = _clamp(1.0 - abs(avg_gap - 0.25) / 0.35)
        elif len(words) <= 1:
            spacing_score = 0.75
        else:
            spacing_score = 0.5

        word_count = max(len(words), 1)
        if words:
            spoken_duration = max(words[-1]["end"] - words[0]["start"], 0.5)
        else:
            spoken_duration = max(duration, 0.5)

        wpm = word_count / spoken_duration * 60.0
        wpm_score = _clamp(1.0 - abs(wpm - SPEECH_IDEAL_WPM) / 90.0)

        return _clamp(0.40 * pause_score + 0.35 * spacing_score + 0.25 * wpm_score)

    def _score_pronunciation(
        self,
        logprobs: List[float],
        reference_text: str,
        transcript: str,
    ) -> float:
        if logprobs:
            confidence = float(np.mean(logprobs))
            confidence_score = _clamp((confidence - 0.35) / 0.55)
        else:
            confidence_score = 0.55

        ref_tokens = _tokenize(reference_text)
        trans_tokens = _tokenize(transcript)

        if ref_tokens and trans_tokens:
            overlap = len(ref_tokens & trans_tokens) / len(ref_tokens)
        elif trans_tokens:
            overlap = 0.65
        else:
            overlap = 0.25

        return _clamp(0.55 * confidence_score + 0.45 * overlap)

    def _analyze_file(self, audio_path: str, reference_text: str) -> Dict:
        words, transcript, logprobs, duration = self._transcribe(audio_path)

        filler_score = self._score_fillers(words, transcript)
        pause_pacing_score = self._score_pause_pacing(words, duration)
        pronunciation_score = self._score_pronunciation(logprobs, reference_text, transcript)

        breakdown = {
            "filler": round(filler_score, 3),
            "pause_pacing": round(pause_pacing_score, 3),
            "pronunciation": round(pronunciation_score, 3),
        }

        weights = SPEECH_COMPONENT_WEIGHTS
        speech_score = (
            breakdown["filler"] * weights["filler"]
            + breakdown["pause_pacing"] * weights["pause_pacing"]
            + breakdown["pronunciation"] * weights["pronunciation"]
        )

        return {
            "speech_score": round(_cap_speech_score(speech_score), 3),
            "breakdown": breakdown,
            "transcript": transcript,
            "source": "audio",
            "metrics": {
                "word_count": len(words),
                "duration_seconds": round(duration, 2),
            },
        }


speech_analyzer = SpeechAnalyzer()
