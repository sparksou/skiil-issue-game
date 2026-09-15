"""
audio.py — Procedural sound engine for Skill Issue.
All sounds synthesized from math at runtime. Zero external audio files.
Includes audio gaslighting sounds (fake Discord ping, Windows bonk, keyboard click).
"""
import math
import random
import struct
import pygame

SAMPLE_RATE = 44100  # Hz
_PEAK = 32767        # Max amplitude for 16-bit signed PCM


# ─────────────────────────────────────────────
#  Raw waveform generators
#  All return bytes (raw 16-bit signed LE PCM, mono)
# ─────────────────────────────────────────────

def _gen_sine(freq: float, duration_ms: int, volume: float = 0.5, fade: bool = True) -> bytes:
    """Pure sine wave — smooth, almost pleasant."""
    n = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(_PEAK * volume)
    buf = bytearray(n * 2)
    for i in range(n):
        t = i / SAMPLE_RATE
        val = math.sin(2 * math.pi * freq * t)
        if fade:
            val *= max(0.0, 1.0 - i / n)
        struct.pack_into('<h', buf, i * 2, max(-_PEAK, min(_PEAK, int(val * peak))))
    return bytes(buf)


def _gen_square(freq: float, duration_ms: int, volume: float = 0.2, fade: bool = True) -> bytes:
    """Square wave — harsh, chiptune buzz."""
    n = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(_PEAK * volume)
    buf = bytearray(n * 2)
    for i in range(n):
        t = i / SAMPLE_RATE
        val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        if fade:
            val *= max(0.0, 1.0 - i / n)
        struct.pack_into('<h', buf, i * 2, int(val * peak))
    return bytes(buf)


def _gen_sweep(freq_start: float, freq_end: float, duration_ms: int, volume: float = 0.4) -> bytes:
    """Frequency sweep — slide whistle / descending flatline."""
    n = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(_PEAK * volume)
    buf = bytearray(n * 2)
    phase = 0.0
    for i in range(n):
        t = i / n                                     # 0.0 → 1.0 progress
        freq = freq_start + (freq_end - freq_start) * t
        phase += 2 * math.pi * freq / SAMPLE_RATE
        val = math.sin(phase) * max(0.0, 1.0 - t * 0.6)
        struct.pack_into('<h', buf, i * 2, max(-_PEAK, min(_PEAK, int(val * peak))))
    return bytes(buf)


def _gen_noise(duration_ms: int, volume: float = 0.45) -> bytes:
    """White noise burst — crunchy death crackle."""
    n = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(_PEAK * volume)
    buf = bytearray(n * 2)
    for i in range(n):
        val = random.randint(-peak, peak)
        fade = max(0.0, 1.0 - i / n)
        struct.pack_into('<h', buf, i * 2, int(val * fade))
    return bytes(buf)


def _mix(a: bytes, b: bytes) -> bytes:
    """Mix two equal-length PCM byte strings by summing (with clipping)."""
    assert len(a) == len(b), "Audio buffers must be the same length to mix"
    out = bytearray(len(a))
    for i in range(0, len(a), 2):
        va = struct.unpack_from('<h', a, i)[0]
        vb = struct.unpack_from('<h', b, i)[0]
        struct.pack_into('<h', out, i, max(-_PEAK, min(_PEAK, va + vb)))
    return bytes(out)


def _concat(*parts) -> bytes:
    result = bytearray()
    for p in parts:
        result.extend(p)
    return bytes(result)


# ─────────────────────────────────────────────
#  AudioEngine
# ─────────────────────────────────────────────

class AudioEngine:
    """Manages all synthesized game audio. No external files required."""

    MUSIC_CH     = 0   # Channel reserved for looping background music
    SFX_CH       = 1   # Channel for sound effects
    GASLIGHT_CH  = 2   # Channel for ambient gaslighting sounds

    def __init__(self):
        # Re-init mixer to guarantee our PCM format (mono 16-bit 44100 Hz)
        pygame.mixer.quit()
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
        pygame.mixer.set_num_channels(8)

        self.enabled = True
        self._ch_music    = pygame.mixer.Channel(self.MUSIC_CH)
        self._ch_sfx      = pygame.mixer.Channel(self.SFX_CH)
        self._ch_gaslight = pygame.mixer.Channel(self.GASLIGHT_CH)

        self._build_sfx()
        self._build_music()
        self._build_gaslight_sfx()

    # ── Sound Construction ────────────────────

    def _build_sfx(self):
        # Death: sharp noise crunch → descending electronic flatline
        self.snd_death = pygame.mixer.Sound(buffer=_concat(
            _gen_noise(75, volume=0.50),
            _gen_sweep(880, 60, 320, volume=0.35),
        ))

        # Checkpoint troll: descending slide-whistle (triumphant → failure)
        self.snd_checkpoint = pygame.mixer.Sound(
            buffer=_gen_sweep(900, 140, 450, volume=0.45)
        )

        # Loop sting: tritone dissonance (C5 + F#4 = "devil's interval")
        c5  = bytearray(_gen_sine(523.3, 700, volume=0.28, fade=True))
        fs4 = bytearray(_gen_sine(369.9, 700, volume=0.28, fade=True))
        self.snd_loop_sting = pygame.mixer.Sound(buffer=_mix(bytes(c5), bytes(fs4)))

    def _build_music(self):
        """
        Looping chiptune arpeggio in C natural minor.
        Deliberately ends on Bb (the 7th) so the loop never harmonically resolves —
        creating endless low-level musical unease.
        """
        bpm = 118
        note_ms = int(60000 / bpm / 4)  # 16th note duration

        # C natural minor, ascending then descending, never landing on root
        melody = [
            261.6, 311.1, 349.2, 392.0,   # C4  Eb4 F4  G4  (ascend)
            466.2, 523.3, 466.2, 392.0,   # Bb4 C5  Bb4 G4  (peak)
            349.2, 311.1, 261.6, 293.7,   # F4  Eb4 C4  D4
            311.1, 349.2, 392.0, 466.2,   # Eb4 F4  G4  Bb4 (never resolves)
        ]

        raw = bytearray()
        for freq in melody:
            # Layer square (body) + sine (warmth) for each note
            sq = bytearray(_gen_square(freq, note_ms, volume=0.13, fade=False))
            si = bytearray(_gen_sine(freq,   note_ms, volume=0.06, fade=False))
            mixed = bytearray(_mix(bytes(sq), bytes(si)))
            raw.extend(mixed)

        self.snd_music = pygame.mixer.Sound(buffer=bytes(raw))

    def _build_gaslight_sfx(self):
        """
        Audio gaslighting: sounds that mimic real notifications/errors.
        Quiet enough to feel ambient, loud enough to break concentration.
        """
        # Fake Discord ping: two-tone ascending chime (800Hz → 1200Hz)
        self.snd_discord_ping = pygame.mixer.Sound(buffer=_concat(
            _gen_sine(800,  80, volume=0.18, fade=True),
            _gen_sine(1200, 80, volume=0.22, fade=True),
        ))

        # Fake Windows error bonk: low thud
        self.snd_windows_bonk = pygame.mixer.Sound(buffer=_concat(
            _gen_sine(200, 120, volume=0.20, fade=True),
            _gen_sine(150,  60, volume=0.10, fade=True),
        ))

        # Fake keyboard click: tiny filtered noise burst
        self.snd_key_click = pygame.mixer.Sound(
            buffer=_gen_noise(30, volume=0.12)
        )

        self._gaslight_sounds = [
            self.snd_discord_ping,
            self.snd_windows_bonk,
            self.snd_key_click,
        ]

    # ── Public API ────────────────────────────

    def start_music(self):
        if self.enabled:
            self._ch_music.play(self.snd_music, loops=-1)

    def stop_music(self):
        self._ch_music.stop()

    def play_death(self):
        if self.enabled:
            self._ch_sfx.play(self.snd_death)

    def play_checkpoint(self):
        if self.enabled:
            self._ch_sfx.play(self.snd_checkpoint)

    def play_loop_sting(self):
        if self.enabled:
            self.stop_music()
            self._ch_sfx.play(self.snd_loop_sting)

    def play_random_gaslight(self):
        """Play a random fake notification sound on its own channel."""
        if self.enabled:
            snd = random.choice(self._gaslight_sounds)
            self._ch_gaslight.play(snd)
