"""
ghost.py — Phantom Ghost replay system for Skill Issue.
Records the player's exact pixel path every frame.

Two ghost types:
  1. Milestone Ghost (red) — triggered every GHOST_TRIGGER_INTERVAL deaths,
     replays the most recent failed run once, then disappears.
  2. Shame Ghost (gray) — permanently loops the player's WORST run
     (longest struggle before death), visible at all times during gameplay.
"""
import pygame
from settings import PLAYER_SIZE, GHOST_TRIGGER_INTERVAL

_MAX_FRAMES = 36_000  # Cap: ~10 min at 60fps before oldest frames are dropped


class GhostRecorder:
    """Records player center-position every frame."""

    def __init__(self):
        self.current_run: list[tuple[int, int]] = []
        self._saved_runs: list[list[tuple[int, int]]] = []
        self.worst_run: list[tuple[int, int]] | None = None   # Longest struggle

    def record(self, cx: int, cy: int):
        """Call once per frame with the player's rect.centerx / centery."""
        self.current_run.append((cx, cy))
        if len(self.current_run) > _MAX_FRAMES:
            self.current_run.pop(0)   # Drop oldest frame — rolling window

    def save_and_reset(self) -> list[tuple[int, int]] | None:
        """
        Call on every player death.
        Saves current run internally, resets recording.
        Returns the saved run if it's long enough to be worth keeping.
        Also updates worst_run if this run is the longest yet.
        """
        run = list(self.current_run)
        self.current_run = []

        if len(run) > 15:           # Ignore sub-0.25s runs (usually level reloads)
            self._saved_runs.append(run)

            # Track worst (longest) run
            if self.worst_run is None or len(run) > len(self.worst_run):
                self.worst_run = run

            return run
        return None

    def should_spawn_ghost(self, death_count: int) -> bool:
        """True if this death count is a ghost trigger milestone."""
        return (death_count > 0
                and death_count % GHOST_TRIGGER_INTERVAL == 0
                and bool(self._saved_runs))

    def get_last_run(self) -> list[tuple[int, int]] | None:
        return self._saved_runs[-1] if self._saved_runs else None


class GhostPlayer:
    """Plays back a recorded run as a fading semi-transparent red phantom."""

    _W, _H = PLAYER_SIZE

    def __init__(self, positions: list[tuple[int, int]]):
        self.positions = positions
        self.frame_idx = 0
        self.done = False
        self._alpha = 160
        self._surf = self._make_surf(self._alpha, (255, 90, 90))

    @staticmethod
    def _make_surf(alpha: int, color: tuple) -> pygame.Surface:
        surf = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
        surf.fill((*color, alpha))
        return surf

    def update(self):
        if self.done:
            return

        if self.frame_idx < len(self.positions) - 1:
            self.frame_idx += 1
            # Fade out during the final 30 % of the replay
            progress = self.frame_idx / max(len(self.positions) - 1, 1)
            if progress >= 0.70:
                fade_ratio = 1.0 - (progress - 0.70) / 0.30
                new_alpha = int(160 * fade_ratio)
                if abs(new_alpha - self._alpha) >= 4:   # Only redraw when meaningfully changed
                    self._alpha = max(0, new_alpha)
                    self._surf = self._make_surf(self._alpha, (255, 90, 90))
        else:
            self.done = True

    def render(self, surface: pygame.Surface, offset: tuple[int, int] = (0, 0)):
        if self.done or self._alpha == 0:
            return
        cx, cy = self.positions[self.frame_idx]
        dx = cx - self._W // 2 + offset[0]
        dy = cy - self._H // 2 + offset[1]
        surface.blit(self._surf, (dx, dy))


class ShameGhost:
    """
    Permanently loops the player's WORST run (longest before death).
    Rendered as a gray, semi-transparent block that endlessly traces the
    most embarrassing path, dies at the same spot, then resets.
    """

    _W, _H = PLAYER_SIZE
    _ALPHA = 90
    _COLOR = (160, 160, 160)   # Gray

    def __init__(self, positions: list[tuple[int, int]]):
        self.positions = positions
        self.frame_idx = 0
        self._surf = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
        self._surf.fill((*self._COLOR, self._ALPHA))

    def update_positions(self, positions: list[tuple[int, int]]):
        """Hot-swap to a new worst run without resetting playback state."""
        self.positions = positions
        if self.frame_idx >= len(positions):
            self.frame_idx = 0

    def update(self):
        self.frame_idx += 1
        if self.frame_idx >= len(self.positions):
            self.frame_idx = 0   # Loop forever

    def render(self, surface: pygame.Surface, offset: tuple[int, int] = (0, 0)):
        cx, cy = self.positions[self.frame_idx]
        dx = cx - self._W // 2 + offset[0]
        dy = cy - self._H // 2 + offset[1]
        surface.blit(self._surf, (dx, dy))
