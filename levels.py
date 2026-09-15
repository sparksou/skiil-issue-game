import pygame
import random
from settings import *
from entities import (Player, TrapPlatform, Spike, TrollCheckpoint,
                      MovingDeceptionPlatform, ProximitySpike,
                      VariableSpeedHazard, FakeWall, InvisibleBlock)


class Scene:
    def __init__(self, game):
        self.game = game

    def update(self, keys):
        pass

    def render(self, surface, offset=(0, 0)):
        pass


# ─────────────────────────────────────────────
#  Helper: draw death markers (theme-aware)
# ─────────────────────────────────────────────
def _draw_death_markers(surface, death_locations, offset, color):
    for dx, dy in death_locations:
        ox, oy = dx + offset[0], dy + offset[1]
        pygame.draw.line(surface, color, (ox - 5, oy - 5), (ox + 5, oy + 5), 2)
        pygame.draw.line(surface, color, (ox - 5, oy + 5), (ox + 5, oy - 5), 2)


# ─────────────────────────────────────────────
#  Helper: recolor sprite surfaces for active theme
# ─────────────────────────────────────────────
def _recolor_group(group, color):
    """Set fill color on all sprites in a group (for theme switching)."""
    for sprite in group:
        sprite.image.fill(color)


# ─────────────────────────────────────────────
#  LEVEL 1 — "The False Sense of Security"
#  Loop escalation: extra spike rows on safe paths
# ─────────────────────────────────────────────
class Level1Scene(Scene):
    def __init__(self, game, loop_count=0):
        super().__init__(game)
        grav_mult = min(1.0 + loop_count * GRAVITY_PER_LOOP_MULTIPLIER, MAX_GRAVITY_MULTIPLIER)
        trap_speed = 1.0 + loop_count * 0.3

        self.player = Player(50, SCREEN_HEIGHT - 100, gravity_multiplier=grav_mult)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)

        # ── Base geometry ──
        self.tiles = [
            pygame.Rect(0,    SCREEN_HEIGHT - 40,  200, 40),   # Spawn floor
            pygame.Rect(300,  SCREEN_HEIGHT - 80,  100, 40),   # Step A
            pygame.Rect(500,  SCREEN_HEIGHT - 120, 100, 40),   # Step B
            pygame.Rect(700,  SCREEN_HEIGHT - 160, 100, 40),   # Step C
            pygame.Rect(900,  SCREEN_HEIGHT - 160, 300, 40),   # Tunnel floor
            pygame.Rect(900,  SCREEN_HEIGHT - 260, 300, 40),   # Tunnel ceiling
            pygame.Rect(1250, SCREEN_HEIGHT - 400, 150, 40),   # Gauntlet platform
            pygame.Rect(1500, SCREEN_HEIGHT - 400, 200, 40),   # Final safe platform
        ]

        self.goal_rect = pygame.Rect(1550, SCREEN_HEIGHT - 500, 40, 100)

        # ── Base traps ──
        self.trap_platforms = pygame.sprite.Group()
        self.spikes = pygame.sprite.Group()
        self.troll_checkpoints = pygame.sprite.Group()
        self.moving_platforms = pygame.sprite.Group()
        self.proximity_spikes = pygame.sprite.Group()

        self.spikes.add(Spike(950, SCREEN_HEIGHT - 220, 40, 20))   # Tunnel spike

        self.troll_checkpoints.add(
            TrollCheckpoint(1150, SCREEN_HEIGHT - 220, 40, 60, 50, SCREEN_HEIGHT - 100)
        )

        self.moving_platforms.add(
            MovingDeceptionPlatform(1350, SCREEN_HEIGHT - 200, 100, 40, move_speed_x=10)
        )

        self.proximity_spikes.add(ProximitySpike(1050, SCREEN_HEIGHT - 200, 40, 40))

        # ── Loop escalation: extra spikes on "safe" steps ──
        if loop_count >= 2:
            self.spikes.add(Spike(320, SCREEN_HEIGHT - 100, 30, 20))   # Under Step A
        if loop_count >= 3:
            self.spikes.add(Spike(520, SCREEN_HEIGHT - 140, 30, 20))   # Under Step B
            self.spikes.add(Spike(990, SCREEN_HEIGHT - 220, 40, 20))   # Extra tunnel spike
        if loop_count >= 4:
            self.spikes.add(Spike(720, SCREEN_HEIGHT - 180, 30, 20))   # Under Step C
        if loop_count >= 5:
            # Silently delete a safe tile
            del self.tiles[2]  # Remove Step B

        # Faster trap on higher loops
        fall_plat = TrapPlatform(1270, SCREEN_HEIGHT - 440, 110, 40, fall_speed=trap_speed)
        self.trap_platforms.add(fall_plat)

        self.all_sprites.add(self.trap_platforms, self.spikes,
                              self.troll_checkpoints, self.moving_platforms,
                              self.proximity_spikes)

    def update(self, keys):
        solid_rects = self.tiles.copy()
        for tp in self.trap_platforms:
            solid_rects.append(tp.rect)
        for mp in self.moving_platforms:
            solid_rects.append(mp.rect)

        # Pass invert flag from game's key-swap system
        self.player.update(keys, solid_rects, invert=self.game.controls_inverted)

        self.trap_platforms.update()
        self.spikes.update()
        self.troll_checkpoints.update()
        self.moving_platforms.update()
        self.proximity_spikes.update()

        # Trap platform — trigger on touch
        for tp in self.trap_platforms:
            if self.player.rect.colliderect(tp.rect):
                tp.trigger()

        # Moving deception — trigger when player approaches
        for mp in self.moving_platforms:
            if (abs(self.player.rect.centerx - mp.rect.centerx) < 150 and
                    abs(self.player.rect.centery - mp.rect.centery) < 150):
                mp.trigger()

        # Proximity spikes — trigger if player is above
        for ps in self.proximity_spikes:
            if (abs(self.player.rect.centerx - ps.rect.centerx) < 100 and
                    self.player.rect.bottom <= ps.rect.top + 100):
                ps.trigger()
            if self.player.rect.colliderect(ps.rect):
                self.game.die()

        # Spike deaths
        for spike in self.spikes:
            if self.player.rect.colliderect(spike.rect):
                self.game.die()

        # Troll checkpoint — teleports back AND plays mocking sound
        for cp in self.troll_checkpoints:
            if self.player.rect.colliderect(cp.rect):
                if cp.cooldown <= 0:
                    self.game.audio.play_checkpoint()
                cp.trigger(self.player)

        if self.player.rect.top > SCREEN_HEIGHT:
            self.game.die()

        if self.player.rect.colliderect(self.goal_rect):
            self.game.next_level()

    def render(self, surface, offset=(0, 0)):
        t = self.game.theme
        surface.fill(t['bg'])

        for tile in self.tiles:
            pygame.draw.rect(surface, t['tile'], tile.move(*offset))
        pygame.draw.rect(surface, t['goal'], self.goal_rect.move(*offset))
        _draw_death_markers(surface, self.game.death_locations, offset, t['death_marker'])

        # Recolor sprites to match active theme
        self.player.image.fill(t['player'])
        _recolor_group(self.spikes, t['spike'])
        _recolor_group(self.proximity_spikes, t['spike'])
        _recolor_group(self.trap_platforms, t['trap_platform'])
        _recolor_group(self.moving_platforms, t['trap_platform'])
        _recolor_group(self.troll_checkpoints, t['checkpoint'])

        for sprite in self.all_sprites:
            surface.blit(sprite.image, (sprite.rect.x + offset[0], sprite.rect.y + offset[1]))


# ─────────────────────────────────────────────
#  LEVEL 2 — "Muscle Memory Massacre"
#  Loop escalation: more variable hazards, faster speeds
# ─────────────────────────────────────────────
class Level2Scene(Scene):
    def __init__(self, game, loop_count=0):
        super().__init__(game)
        grav_mult = min(1.0 + loop_count * GRAVITY_PER_LOOP_MULTIPLIER, MAX_GRAVITY_MULTIPLIER)
        speed_bonus = loop_count * 1.5

        self.player = Player(50, SCREEN_HEIGHT - 100, gravity_multiplier=grav_mult)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)

        self.tiles = [
            pygame.Rect(0,    SCREEN_HEIGHT - 40,  200, 40),   # Spawn
            pygame.Rect(1500, SCREEN_HEIGHT - 400, 200, 40),   # Final platform
        ]
        self.goal_rect = pygame.Rect(1550, SCREEN_HEIGHT - 500, 40, 100)

        self.variable_hazards = pygame.sprite.Group()
        # Base hazards
        self.variable_hazards.add(
            VariableSpeedHazard(300, SCREEN_HEIGHT - 80,  40, 40,  2 + speed_bonus,  15 + speed_bonus)
        )
        self.variable_hazards.add(
            VariableSpeedHazard(600, SCREEN_HEIGHT - 180, 40, 40, -2 - speed_bonus, -15 - speed_bonus)
        )
        self.variable_hazards.add(
            VariableSpeedHazard(900, SCREEN_HEIGHT - 280, 40, 40,  3 + speed_bonus,  20 + speed_bonus)
        )

        # Loop escalation: add more hazard lanes
        if loop_count >= 2:
            self.variable_hazards.add(
                VariableSpeedHazard(450, SCREEN_HEIGHT - 130, 40, 40, 2.5 + speed_bonus, 18 + speed_bonus)
            )
        if loop_count >= 3:
            self.variable_hazards.add(
                VariableSpeedHazard(750, SCREEN_HEIGHT - 230, 40, 40, -3 - speed_bonus, -20 - speed_bonus)
            )
        if loop_count >= 4:
            self.variable_hazards.add(
                VariableSpeedHazard(1100, SCREEN_HEIGHT - 320, 40, 40, 4 + speed_bonus, 25 + speed_bonus)
            )

        self.all_sprites.add(self.variable_hazards)

    def update(self, keys):
        self.player.update(keys, self.tiles, invert=self.game.controls_inverted)
        self.variable_hazards.update()

        for vh in self.variable_hazards:
            if not self.player.on_ground:
                vh.trigger_fast()
            else:
                vh.trigger_slow()

            # Loop them back around
            if vh.rect.x > SCREEN_WIDTH + 200:
                vh.rect.x = vh.original_x
            elif vh.rect.x < -200:
                vh.rect.x = vh.original_x

            if self.player.rect.colliderect(vh.rect):
                self.game.die()

        if self.player.rect.top > SCREEN_HEIGHT:
            self.game.die()

        if self.player.rect.colliderect(self.goal_rect):
            self.game.next_level()

    def render(self, surface, offset=(0, 0)):
        t = self.game.theme
        surface.fill(t['bg'])

        for tile in self.tiles:
            pygame.draw.rect(surface, t['tile'], tile.move(*offset))
        pygame.draw.rect(surface, t['goal'], self.goal_rect.move(*offset))
        _draw_death_markers(surface, self.game.death_locations, offset, t['death_marker'])

        self.player.image.fill(t['player'])
        _recolor_group(self.variable_hazards, t['spike'])

        for sprite in self.all_sprites:
            surface.blit(sprite.image, (sprite.rect.x + offset[0], sprite.rect.y + offset[1]))


# ─────────────────────────────────────────────
#  LEVEL 3 — "Gaslight Peak"
#  Loop escalation: more invisible blocks removed, more spikes
# ─────────────────────────────────────────────
class Level3Scene(Scene):
    def __init__(self, game, loop_count=0):
        super().__init__(game)
        grav_mult = min(1.0 + loop_count * GRAVITY_PER_LOOP_MULTIPLIER, MAX_GRAVITY_MULTIPLIER)

        self.player = Player(50, SCREEN_HEIGHT - 100, gravity_multiplier=grav_mult)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)

        self.tiles = [
            pygame.Rect(0,    SCREEN_HEIGHT - 40,  200, 40),   # Spawn
            pygame.Rect(1500, SCREEN_HEIGHT - 400, 200, 40),   # Final platform
        ]
        self.goal_rect = pygame.Rect(1550, SCREEN_HEIGHT - 500, 40, 100)

        self.fake_walls = pygame.sprite.Group()
        self.fake_walls.add(FakeWall(400, SCREEN_HEIGHT - 300, 40, 300))

        # Invisible bridge — some blocks removed each loop
        bridge_positions = [
            (250,  SCREEN_HEIGHT - 100),
            (350,  SCREEN_HEIGHT - 140),
            (500,  SCREEN_HEIGHT - 170),
            (650,  SCREEN_HEIGHT - 200),
            (820,  SCREEN_HEIGHT - 240),
            (1000, SCREEN_HEIGHT - 270),
            (1180, SCREEN_HEIGHT - 300),
            (1300, SCREEN_HEIGHT - 340),
        ]
        # On higher loops, silently remove random bridge segments
        remove_count = min(loop_count, len(bridge_positions) - 2)
        random.seed(loop_count * 7)
        to_remove = set(random.sample(range(len(bridge_positions)), remove_count))

        self.invisible_blocks = pygame.sprite.Group()
        for i, (bx, by) in enumerate(bridge_positions):
            if i not in to_remove:
                self.invisible_blocks.add(InvisibleBlock(bx, by, 60, 20))

        self.spikes = pygame.sprite.Group()
        self.spikes.add(Spike(400, SCREEN_HEIGHT - 20, 40, 20))
        self.spikes.add(Spike(0,   SCREEN_HEIGHT - 20, SCREEN_WIDTH * 2, 20))

        # Loop escalation: ceiling spikes appear
        if loop_count >= 2:
            self.spikes.add(Spike(300, SCREEN_HEIGHT - 640, SCREEN_WIDTH * 2, 20))
        if loop_count >= 4:
            self.spikes.add(Spike(1450, SCREEN_HEIGHT - 500, 20, 500))

        self.all_sprites.add(self.fake_walls, self.invisible_blocks, self.spikes)

    def update(self, keys):
        solid_rects = self.tiles.copy()
        for ib in self.invisible_blocks:
            solid_rects.append(ib.rect)

        self.player.update(keys, solid_rects, invert=self.game.controls_inverted)

        for spike in self.spikes:
            if self.player.rect.colliderect(spike.rect):
                self.game.die()

        if self.player.rect.top > SCREEN_HEIGHT:
            self.game.die()

        if self.player.rect.colliderect(self.goal_rect):
            self.game.next_level()

    def render(self, surface, offset=(0, 0)):
        t = self.game.theme
        surface.fill(t['bg'])

        for tile in self.tiles:
            pygame.draw.rect(surface, t['tile'], tile.move(*offset))
        pygame.draw.rect(surface, t['goal'], self.goal_rect.move(*offset))
        _draw_death_markers(surface, self.game.death_locations, offset, t['death_marker'])

        self.player.image.fill(t['player'])
        _recolor_group(self.fake_walls, t['fake_wall'])
        _recolor_group(self.spikes, t['spike'])

        for sprite in self.all_sprites:
            surface.blit(sprite.image, (sprite.rect.x + offset[0], sprite.rect.y + offset[1]))
