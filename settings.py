import pygame

# Display Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Skill Issue"

# ─────────────────────────────────────────────
#  THEME SYSTEM
#  Dark = default moody aesthetic
#  Light = weaponized eye-strain punishment
# ─────────────────────────────────────────────

THEME_DARK = {
    'bg':               (30, 30, 30),
    'tile':             (100, 100, 100),
    'spike':            (160, 160, 160),
    'trap_platform':    (90, 90, 90),
    'player':           (255, 60, 60),
    'checkpoint':       (255, 215, 0),
    'goal':             (0, 200, 80),
    'hud_text':         (255, 255, 255),
    'hud_mock':         (255, 100, 100),
    'hud_dim':          (130, 130, 130),
    'death_marker':     (220, 30, 30),
    'fake_wall':        (100, 100, 100),
}

THEME_LIGHT = {
    'bg':               (255, 255, 255),
    'tile':             (235, 235, 235),       # Nearly invisible on white
    'spike':            (245, 225, 225),        # Faint pink — almost impossible to see
    'trap_platform':    (230, 230, 230),
    'player':           (120, 20, 20),          # Dark red — only clearly visible element
    'checkpoint':       (240, 230, 180),        # Washed out yellow
    'goal':             (200, 240, 210),        # Faint green
    'hud_text':         (30, 30, 30),
    'hud_mock':         (180, 60, 60),
    'hud_dim':          (180, 180, 180),
    'death_marker':     (255, 200, 200),        # Barely visible pink
    'fake_wall':        (235, 235, 235),
}

# ─────────────────────────────────────────────
#  BASE COLORS (still used for non-themed elements)
# ─────────────────────────────────────────────
BLACK = (30, 30, 30)
WHITE = (255, 255, 255)
RED = (220, 30, 30)
BRIGHT_RED = (255, 60, 60)
ORANGE = (255, 140, 0)
YELLOW = (255, 215, 0)
GREEN = (0, 200, 80)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (55, 55, 55)
LOOP_RED = (180, 0, 0)
CHAOS_GREEN = (30, 180, 50)

# Physics Settings
GRAVITY = 0.5
TERMINAL_VELOCITY = 15
FRICTION = -0.12

# Loop Escalation
GRAVITY_PER_LOOP_MULTIPLIER = 0.12
MAX_GRAVITY_MULTIPLIER = 2.5

# Player Settings
PLAYER_SPEED = 5
PLAYER_JUMP_FORCE = -12
PLAYER_SIZE = (28, 28)
PLAYER_COLOR = BRIGHT_RED

# UI Settings
FONT_COLOR = WHITE
MOCK_COLOR = (255, 100, 100)
CHECKPOINT_COLOR = YELLOW
SPIKE_COLOR = (160, 160, 160)
TRAP_PLATFORM_COLOR = (90, 90, 90)

# Transition
TRANSITION_DURATION = 150  # frames (~2.5s at 60fps)

# Ghost System
GHOST_TRIGGER_INTERVAL = 20  # Spawn ghost every N deaths

# Key-Swap Glitch
KEY_SWAP_INTERVAL = 25       # Trigger every N deaths
KEY_SWAP_DURATION = 180      # Frames (3 seconds at 60fps)

# Audio Gaslighting
GASLIGHT_MIN_INTERVAL = 1200   # 20 seconds (frames)
GASLIGHT_MAX_INTERVAL = 2700   # 45 seconds (frames)

# Chaos Loop
CHAOS_LOOP_START = 4          # Which loop number enables chaos mode
CHAOS_TAUNTS = [
    "Why?", "Again?", "Quit.", "Please.", "Stop.", "...",
    "No.", "Done?", "Leave.", "Why?", "Seriously.", "Go."
]

# --- Insult System ---
MOCKING_QUOTES = [
    (0,   "Getting warmed up?"),
    (11,  "Are your hands made of butter?"),
    (31,  "Maybe try a nice quiet puzzle game?"),
    (61,  "Actually painful to watch."),
    (101, "This is genuinely tragic."),
    (200, "At this point you're a burden to the CPU."),
]

LOOP_INSULTS = {
    0: "",
    1: "",
    2: "Loop 2. You literally already failed this exact jump.",
    3: "Repeating history is a mental illness. Look it up.",
    4: "Four loops deep. The definition of insanity applies here.",
    5: "You are the game's best advertisement for giving up.",
    6: "Six loops. The map has gotten worse. So have you.",
    7: "Seven loops. I genuinely feel nothing for you anymore.",
}
LOOP_INSULTS_DEFAULT = "Still going? Remarkable. Not in a good way."
