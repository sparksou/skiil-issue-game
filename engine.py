import pygame
import sys
import math
import random
import asyncio
import math
import random
from settings import *
from fx import ParticleSystem, CameraShake, GlitchText, TrailSystem
from levels import Scene, Level1Scene, Level2Scene, Level3Scene
from audio import AudioEngine
from ghost import GhostRecorder, GhostPlayer, ShameGhost
from localization import InsultEngine


# ─────────────────────────────────────────────
#  FAKE CRASH OVERLAY
# ─────────────────────────────────────────────
class FakeCrashOverlay:
    def __init__(self, game):
        self.game = game
        self.visible = False
        self._btn_rect: pygame.Rect | None = None

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def handle_event(self, event) -> bool:
        if not self.visible:
            return False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self._accept()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and self._btn_rect:
            if self._btn_rect.collidepoint(event.pos):
                self._accept()
                return True

        return True

    def _accept(self):
        self.hide()
        self.game._crash_accept()

    def render(self, surface: pygame.Surface):
        if not self.visible:
            return

        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        surface.blit(dim, (0, 0))

        BW, BH = 500, 230
        bx = SCREEN_WIDTH  // 2 - BW // 2
        by = SCREEN_HEIGHT // 2 - BH // 2

        pygame.draw.rect(surface, (195, 195, 195), (bx, by, BW, BH))
        pygame.draw.rect(surface, (90, 90, 90),    (bx, by, BW, BH), 2)

        TB = 28
        pygame.draw.rect(surface, (140, 0, 0), (bx, by, BW, TB))
        title = self.game.font_tiny.render("  Fatal Error — Skill Issue.exe", True, WHITE)
        surface.blit(title, (bx + 4, by + 6))

        xbtn = pygame.Rect(bx + BW - 26, by + 2, 24, 24)
        pygame.draw.rect(surface, (190, 20, 20), xbtn)
        xsurf = self.game.font_tiny.render("✕", True, WHITE)
        surface.blit(xsurf, (xbtn.x + 5, xbtn.y + 4))

        ic_cx, ic_cy = bx + 55, by + 105
        pygame.draw.circle(surface, (200, 30, 30), (ic_cx, ic_cy), 26)
        exc = self.game.font_large.render("!", True, WHITE)
        surface.blit(exc, (ic_cx - exc.get_width() // 2, ic_cy - exc.get_height() // 2))

        lines = [
            (self.game.font_small, "Skill Not Found.",                          (25, 25, 25)),
            (self.game.font_tiny,  "Reinstalling motivation...",                 (70, 70, 70)),
            (self.game.font_tiny,  "(This may require several more attempts.)",  (110, 110, 110)),
        ]
        ly = by + TB + 22
        for font, text, color in lines:
            surf = font.render(text, True, color)
            surface.blit(surf, (bx + 100, ly))
            ly += surf.get_height() + 8

        btn_w, btn_h = 90, 30
        btn_x = bx + BW // 2 - btn_w // 2
        btn_y = by + BH - 48
        self._btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(surface, (175, 175, 175), self._btn_rect)
        pygame.draw.rect(surface, (80, 80, 80),    self._btn_rect, 2)
        ok = self.game.font_tiny.render("  OK  ", True, (25, 25, 25))
        surface.blit(ok, (btn_x + btn_w // 2 - ok.get_width() // 2, btn_y + 7))


# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────
class MainMenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.tick = 0
        
        # Escaping Quit Button tracking
        self.quit_text = "[ESC]  Quit (Coward)"
        self.quit_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150]
        self.quit_rect = pygame.Rect(0, 0, 10, 10) # Updated in render
        
        # Background effects
        self.particles = []
        for _ in range(50):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.5, 0.5),
                'size': random.randint(2, 5),
                'alpha': random.randint(50, 150)
            })

    def update(self, keys):
        if keys[pygame.K_SPACE]:
            self.game.start_game()
        elif keys[pygame.K_l]:
            self.game.toggle_theme()
            # Debounce key
            pygame.time.wait(200)
        elif keys[pygame.K_t]:
            self.game.insult_engine.cycle_language()
            pygame.time.wait(200)

        # Escaping Quit Button logic
        mx, my = pygame.mouse.get_pos()
        qx, qy = self.quit_pos
        
        dist = math.hypot(mx - qx, my - qy)
        if dist < 120:  # Mouse gets near
            # Move away
            dx = qx - mx
            dy = qy - my
            # Normalize
            if dist != 0:
                dx /= dist
                dy /= dist
            
            self.quit_pos[0] += dx * 15
            self.quit_pos[1] += dy * 15
            
            # Clamp to screen bounds
            self.quit_pos[0] = max(100, min(SCREEN_WIDTH - 100, self.quit_pos[0]))
            self.quit_pos[1] = max(100, min(SCREEN_HEIGHT - 50, self.quit_pos[1]))

        # Check if clicked (if they manage to corner it)
        if pygame.mouse.get_pressed()[0] and self.quit_rect.collidepoint(mx, my):
            self.game.audio.play_death()
            self.quit_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150] # Reset position instead of quitting

    def render(self, surface: pygame.Surface, offset=(0, 0)):
        surface.fill(self.game.theme['bg'])
        self.tick += 1

        # Draw scrolling grid
        grid_color = self.game.theme['tile']
        grid_size = 40
        offset_x = (self.tick // 2) % grid_size
        offset_y = (self.tick // 2) % grid_size
        for x in range(0 - offset_x, SCREEN_WIDTH, grid_size):
            pygame.draw.line(surface, grid_color, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0 - offset_y, SCREEN_HEIGHT, grid_size):
            pygame.draw.line(surface, grid_color, (0, y), (SCREEN_WIDTH, y), 1)

        # Draw particles
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            if p['x'] < 0: p['x'] = SCREEN_WIDTH
            if p['x'] > SCREEN_WIDTH: p['x'] = 0
            if p['y'] < 0: p['y'] = SCREEN_HEIGHT
            if p['y'] > SCREEN_HEIGHT: p['y'] = 0
            
            color = self.game.theme['hud_dim']
            surf = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color[:3], p['alpha']), (p['size'], p['size']), p['size'])
            surface.blit(surf, (int(p['x']), int(p['y'])))

        # ── Animated title — sin-wave color pulse per letter ──
        title_str = "SKILL ISSUE"
        total_w = self.game.font_large.size(title_str)[0]
        x_cur = SCREEN_WIDTH // 2 - total_w // 2
        ty = SCREEN_HEIGHT // 4

        for i, ch in enumerate(title_str):
            wave = math.sin(self.tick * 0.05 + i * 0.45)
            # In light mode, use darker colors for the title
            if self.game.is_light_mode:
                r = max(0, min(255, int(150 + 50 * wave)))
                g = max(0, min(255, int(20  + 10 * abs(wave))))
                b = max(0, min(255, int(20  + 10 * wave)))
            else:
                r = max(0, min(255, int(225 + 30 * wave)))
                g = max(0, min(255, int(30  + 20 * abs(wave))))
                b = max(0, min(255, int(30  + 10 * wave)))
            ch_surf = self.game.font_large.render(ch, True, (r, g, b))
            surface.blit(ch_surf, (x_cur, ty + int(wave * 5)))
            x_cur += ch_surf.get_width()

        # Subtitle
        sub = self.game.font_small.render("It's not a bug, you're just bad.", True, self.game.theme['hud_dim'])
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 4 + 68))

        # Controls
        s1 = self.game.font_small.render("[SPACE]  Start Suffering", True, self.game.theme['hud_text'])
        surface.blit(s1, (SCREEN_WIDTH // 2 - s1.get_width() // 2, SCREEN_HEIGHT // 2))

        # Theme & Lang
        mode_text = "Light Mode" if self.game.is_light_mode else "Dark Mode"
        s2 = self.game.font_small.render(f"[L] Toggle Theme: {mode_text}", True, self.game.theme['hud_dim'])
        s3 = self.game.font_small.render(f"[T] Language: {self.game.insult_engine.language}", True, self.game.theme['hud_dim'])
        
        surface.blit(s2, (SCREEN_WIDTH // 2 - s2.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        surface.blit(s3, (SCREEN_WIDTH // 2 - s3.get_width() // 2, SCREEN_HEIGHT // 2 + 90))

        # Escaping Quit
        q_surf = self.game.font_small.render(self.quit_text, True, self.game.theme['hud_dim'])
        self.quit_rect = q_surf.get_rect(center=(self.quit_pos[0], self.quit_pos[1]))
        surface.blit(q_surf, self.quit_rect.topleft)

        # Last-session stats
        if self.game.death_count > 0:
            stat = self.game.font_tiny.render(
                f"Last session — Deaths: {self.game.death_count}  |  "
                f"Loops: {self.game.loop_count}  |  "
                f"Time Wasted: {self.game._fmt_time(self.game.time_wasted)}",
                True, self.game.theme['hud_dim']
            )
            surface.blit(stat, (SCREEN_WIDTH // 2 - stat.get_width() // 2, SCREEN_HEIGHT - 55))


# ─────────────────────────────────────────────
#  MAIN GAME CLASS
# ─────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # ── Persistent state ──
        self.death_count      = 0
        self.death_locations: list[tuple[int, int]] = []
        self.loop_count       = 0
        self.current_level_num = 1
        self.time_wasted      = 0   
        self.start_time       = pygame.time.get_ticks()

        # ── Theme System ──
        self.is_light_mode = False
        self.theme = THEME_DARK

        # ── Fonts ──
        self.font_large = pygame.font.Font(None, 54)
        self.font_small = pygame.font.Font(None, 34)
        self.font_tiny  = pygame.font.Font(None, 26)

        # ── Subsystems ──
        self.audio = AudioEngine()
        self.insult_engine = InsultEngine()
        self.camera_shake  = CameraShake()
        self.particle_sys  = ParticleSystem()
        self.trail_sys     = TrailSystem()
        self.glitch_deaths = GlitchText(duration=8)
        self.ghost_recorder = GhostRecorder()
        
        self.ghost_player: GhostPlayer | None = None
        self.shame_ghost: ShameGhost | None = None

        self.fake_crash = FakeCrashOverlay(self)

        # ── State Timers ──
        self.death_timer = 0   
        self.controls_inverted = False
        self.key_swap_timer = 0
        self.gaslight_timer = random.randint(GASLIGHT_MIN_INTERVAL, GASLIGHT_MAX_INTERVAL)
        self.fake_error_timer = 0
        
        # ── Lying progress bar ──
        self._pb_pct    = 0.0     
        self._pb_target = 0.98    

        # Start immediately on the main menu
        self.current_scene = MainMenuScene(self)

    # ─── Helpers ─────────────────────────────

    def _fmt_time(self, ms: int) -> str:
        total_s = ms // 1000
        m, s = divmod(total_s, 60)
        return f"{m:02d}:{s:02d}"

    def toggle_theme(self):
        self.is_light_mode = not self.is_light_mode
        self.theme = THEME_LIGHT if self.is_light_mode else THEME_DARK

    # ─── Game Flow ───────────────────────────

    def start_game(self):
        self.start_time = pygame.time.get_ticks()
        self.current_level_num = 1
        self._pb_target = 0.98
        self.current_scene = Level1Scene(self, self.loop_count)
        self.audio.start_music()

    def start_loop(self):
        self.current_level_num = 1
        self._pb_target = 0.98
        self.current_scene = Level1Scene(self, self.loop_count)
        self.audio.start_music()

    def reset_level(self):
        constructors = {1: Level1Scene, 2: Level2Scene, 3: Level3Scene}
        cls = constructors.get(self.current_level_num, Level1Scene)
        self.current_scene = cls(self, self.loop_count)
        self.ghost_recorder.current_run = []
        
        # 15% chance to show fake localization error on reset if non-english
        if self.insult_engine.language != "English" and random.random() < 0.15:
            self.fake_error_timer = 90

    def next_level(self):
        self.current_level_num += 1
        if self.current_level_num > 3:
            self.loop_count += 1
            self._pb_target = 0.0
            self.audio.play_loop_sting()
            self.current_scene = Level1Scene(self, self.loop_count)
            self.audio.start_music()
        else:
            self.reset_level()

    def die(self):
        if self.death_timer > 0:
            return

        self.death_count += 1
        self.glitch_deaths.trigger()
        self.audio.play_death()

        shake = min(12 + self.death_count * 1.5, 55)
        self.camera_shake.trigger(shake)

        if hasattr(self.current_scene, 'player'):
            px = self.current_scene.player.rect.centerx
            py = self.current_scene.player.rect.centery
            self.death_locations.append((px, py))
            count = min(30 + self.death_count // 5, 90)
            self.particle_sys.emit(px, py, count, self.death_count)

        # Key Swap Glitch check
        if self.death_count % KEY_SWAP_INTERVAL == 0:
            self.controls_inverted = True
            self.key_swap_timer = KEY_SWAP_DURATION

        # Ghost: save run, spawn replayer, update shame ghost
        saved = self.ghost_recorder.save_and_reset()
        if self.ghost_recorder.should_spawn_ghost(self.death_count):
            run = self.ghost_recorder.get_last_run()
            if run:
                self.ghost_player = GhostPlayer(run)
        
        if self.ghost_recorder.worst_run:
            if not self.shame_ghost:
                self.shame_ghost = ShameGhost(self.ghost_recorder.worst_run)
            else:
                self.shame_ghost.update_positions(self.ghost_recorder.worst_run)

        self.death_timer = 30

    def _crash_accept(self):
        self.current_level_num = 1
        self._pb_target = 0.98
        self.current_scene = Level1Scene(self, self.loop_count)
        self.audio.start_music()

    # ─── Main Loop ───────────────────────────

    async def run(self):
        while self.running:
            keys = pygame.key.get_pressed()

            for event in pygame.event.get():
                if self.fake_crash.handle_event(event):
                    continue

                if event.type == pygame.QUIT:
                    self.fake_crash.show()
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Allow normal quit from main menu maybe?
                        if isinstance(self.current_scene, MainMenuScene):
                            self.running = False
                        else:
                            # From inside level, don't let them escape easily
                            self.fake_crash.show()
                    
                    if event.key == pygame.K_F4 and (pygame.key.get_mods() & pygame.KMOD_ALT):
                        self.fake_crash.show()

            # ── Update ──────────────────────────────────────────────
            in_level = isinstance(self.current_scene, (Level1Scene, Level2Scene, Level3Scene))

            if in_level:
                self.time_wasted = pygame.time.get_ticks() - self.start_time

                if hasattr(self.current_scene, 'player'):
                    p = self.current_scene.player
                    self.ghost_recorder.record(p.rect.centerx, p.rect.centery)

                diff = self._pb_target - self._pb_pct
                speed = 0.08 if self._pb_target > self._pb_pct else 0.025
                self._pb_pct += diff * speed
                self._pb_pct = max(0.0, min(1.0, self._pb_pct))
                
                # Update Key Swap Glitch
                if self.key_swap_timer > 0:
                    self.key_swap_timer -= 1
                    if self.key_swap_timer == 0:
                        self.controls_inverted = False

                # Update Fake Error
                if self.fake_error_timer > 0:
                    self.fake_error_timer -= 1
                    
                # Update Gaslight Audio
                self.gaslight_timer -= 1
                if self.gaslight_timer <= 0:
                    self.audio.play_random_gaslight()
                    self.gaslight_timer = random.randint(GASLIGHT_MIN_INTERVAL, GASLIGHT_MAX_INTERVAL)

            if self.death_timer > 0:
                self.death_timer -= 1
                if self.death_timer == 0:
                    self.reset_level()
            else:
                self.current_scene.update(keys)

            self.particle_sys.update()
            self.trail_sys.update()
            if self.ghost_player and not self.ghost_player.done:
                self.ghost_player.update()
            if self.shame_ghost and in_level:
                self.shame_ghost.update()

            # ── Render ──────────────────────────────────────────────
            offset = self.camera_shake.get_offset()
            self.current_scene.render(self.screen, offset)

            # Ghosts render on top of scene, beneath HUD
            if self.shame_ghost and in_level:
                self.shame_ghost.render(self.screen, offset)
            if self.ghost_player and not self.ghost_player.done:
                self.ghost_player.render(self.screen, offset)

            self.trail_sys.render(self.screen, offset)
            self.particle_sys.render(self.screen, offset)

            if self.loop_count >= CHAOS_LOOP_START and in_level:
                tint_alpha = min(28 + (self.loop_count - CHAOS_LOOP_START) * 10, 80)
                tint = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                tint.fill((0, 180, 50, int(tint_alpha)))
                self.screen.blit(tint, (0, 0))

            if in_level:
                self._render_hud()

            self.fake_crash.render(self.screen)

            pygame.display.flip()
            self.clock.tick(FPS)
            await asyncio.sleep(0)  # Yield control to the browser for WebAssembly

        pygame.quit()
        sys.exit()

    # ─── HUD Rendering ───────────────────────

    def _render_hud(self):
        t = self.theme
        chaos = self.loop_count >= CHAOS_LOOP_START

        # ── LEFT: Deaths ──
        if chaos:
            death_str = f"SANITY: -{self.death_count:03}"
        else:
            death_str = f"DEATHS: {self.death_count:03}"
        self.glitch_deaths.render(self.screen, self.font_large, death_str, (20, 20), t['hud_text'])

        # Mocking quote
        quote = self.insult_engine.get_mocking_quote(self.death_count, self.loop_count, CHAOS_LOOP_START)
        if quote:
            q = self.font_tiny.render(quote, True, t['hud_mock'])
            self.screen.blit(q, (20, 70))

        # ── CENTER TOP: Loop ──
        if self.loop_count > 0:
            lc = self.font_large.render(f"LOOP  {self.loop_count}", True, (255, 90, 90) if not self.is_light_mode else (180, 20, 20))
        else:
            lc = self.font_large.render("LOOP  —", True, t['hud_dim'])
        self.screen.blit(lc, (SCREEN_WIDTH // 2 - lc.get_width() // 2, 20))

        insult = self.insult_engine.get_loop_insult(self.loop_count, CHAOS_LOOP_START)
        if insult:
            li = self.font_tiny.render(insult, True, (215, 115, 115) if not self.is_light_mode else (180, 80, 80))
            self.screen.blit(li, (SCREEN_WIDTH // 2 - li.get_width() // 2, 70))

        # ── RIGHT: Time Wasted ──
        ts = self.font_large.render(f"TIME WASTED: {self._fmt_time(self.time_wasted)}", True, t['hud_text'])
        self.screen.blit(ts, (SCREEN_WIDTH - ts.get_width() - 20, 20))

        # ── RIGHT: Lying Progress Bar ──
        bar_right = SCREEN_WIDTH - 20
        bar_w = 180
        bar_x = bar_right - bar_w
        bar_y = 64
        bar_h = 8
        pct_int = int(self._pb_pct * 100)

        lbl = self.font_tiny.render(f"Level Progress: {pct_int}%", True, t['hud_dim'])
        self.screen.blit(lbl, (bar_x, bar_y - 18))
        pygame.draw.rect(self.screen, t['hud_dim'], (bar_x, bar_y, bar_w, bar_h))
        fill = int(bar_w * self._pb_pct)
        if fill > 0:
            pygame.draw.rect(self.screen, t['goal'], (bar_x, bar_y, fill, bar_h))

        # ── BOTTOM RIGHT: Level ──
        lv = self.font_tiny.render(f"Level {self.current_level_num} / 3", True, t['hud_dim'])
        self.screen.blit(lv, (SCREEN_WIDTH - lv.get_width() - 20, SCREEN_HEIGHT - 34))

        # ── OVERLAYS ──
        if self.key_swap_timer > 0:
            # Flash "CONTROLS CORRUPTED" on screen
            if self.key_swap_timer % 20 > 10:
                cw = self.font_large.render("CONTROLS CORRUPTED", True, RED)
                self.screen.blit(cw, (SCREEN_WIDTH // 2 - cw.get_width() // 2, SCREEN_HEIGHT // 2))

        if self.fake_error_timer > 0:
            err = self.insult_engine.get_fake_error()
            ew = self.font_small.render(err, True, YELLOW if not self.is_light_mode else RED)
            # Draw semi-transparent background for readability
            bg_rect = pygame.Rect(0, 0, ew.get_width() + 20, ew.get_height() + 10)
            bg_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)
            pygame.draw.rect(self.screen, (0, 0, 0) if not self.is_light_mode else (255, 255, 255), bg_rect)
            pygame.draw.rect(self.screen, YELLOW if not self.is_light_mode else RED, bg_rect, 2)
            self.screen.blit(ew, (bg_rect.x + 10, bg_rect.y + 5))
