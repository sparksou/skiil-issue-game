import pygame
from settings import *
from physics import PhysicsEngine

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, gravity_multiplier=1.0):
        super().__init__()
        self.image = pygame.Surface(PLAYER_SIZE)
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))

        self.velocity = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.gravity_multiplier = gravity_multiplier  # Escalates each loop
        
        # Squash and stretch properties
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.color = PLAYER_COLOR

    def update(self, keys, tiles, invert: bool = False):
        self.velocity.x = 0

        # Key-Swap Glitch: when inverted, left=right and right=left
        key_left  = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) if invert else (keys[pygame.K_LEFT] or keys[pygame.K_a])
        key_right = (keys[pygame.K_LEFT]  or keys[pygame.K_a]) if invert else (keys[pygame.K_RIGHT] or keys[pygame.K_d])
        key_jump  = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]

        if key_left:
            self.velocity.x = -PLAYER_SPEED
        if key_right:
            self.velocity.x = PLAYER_SPEED

        if key_jump and self.on_ground:
            if invert:
                # Jump = drop (forces downward velocity — total betrayal)
                self.velocity.y = abs(PLAYER_JUMP_FORCE) * 0.5
            else:
                # Normal jump (slightly weaker at higher gravity)
                self.velocity.y = PLAYER_JUMP_FORCE * min(1.0, 1.0 / (self.gravity_multiplier ** 0.15))
            self.on_ground = False

        PhysicsEngine.apply_gravity(self, self.gravity_multiplier)
        collisions = PhysicsEngine.move(self, tiles)

        was_on_ground = self.on_ground
        self.on_ground = collisions['bottom']

        # Squash and stretch logic
        target_scale_x, target_scale_y = 1.0, 1.0
        if not self.on_ground:
            # Stretch based on vertical velocity
            stretch = min(0.4, abs(self.velocity.y) * 0.02)
            target_scale_y = 1.0 + stretch
            target_scale_x = 1.0 - stretch * 0.5
        elif not was_on_ground:
            # Squash on landing
            self.scale_x = 1.4
            self.scale_y = 0.6
        
        # Interpolate towards target scale
        self.scale_x += (target_scale_x - self.scale_x) * 0.2
        self.scale_y += (target_scale_y - self.scale_y) * 0.2

    def render(self, surface, offset, color):
        w = int(PLAYER_SIZE[0] * self.scale_x)
        h = int(PLAYER_SIZE[1] * self.scale_y)
        
        # Center bottom alignment
        cx = self.rect.centerx + offset[0]
        cy = self.rect.bottom + offset[1]
        
        # Draw Glow
        glow_w, glow_h = w + 12, h + 12
        glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*color[:3], 100), (0, 0, glow_w, glow_h), border_radius=6)
        surface.blit(glow_surf, (cx - glow_w // 2, cy - glow_h))
        
        # Draw Core
        pygame.draw.rect(surface, color, (cx - w // 2, cy - h, w, h))


class TrapPlatform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, fall_speed=1.0):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(TRAP_PLATFORM_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_falling = False
        self.velocity_y = 0
        self.fall_speed = fall_speed  # Multiplier for how fast it drops

    def update(self, *args):
        if self.is_falling:
            self.velocity_y += GRAVITY * self.fall_speed
            self.rect.y += int(self.velocity_y)

    def trigger(self):
        self.is_falling = True


class Spike(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(SPIKE_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, *args):
        pass


class TrollCheckpoint(pygame.sprite.Sprite):
    """Looks like a checkpoint. Teleports player BACKWARD."""
    def __init__(self, x, y, width, height, dest_x, dest_y):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(CHECKPOINT_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.dest_x = dest_x
        self.dest_y = dest_y
        self.cooldown = 0  # Prevent re-triggering instantly

    def trigger(self, player):
        if self.cooldown <= 0:
            player.rect.x = self.dest_x
            player.rect.y = self.dest_y
            player.velocity.y = 0
            self.cooldown = 60  # 1 second cooldown

    def update(self, *args):
        if self.cooldown > 0:
            self.cooldown -= 1


class MovingDeceptionPlatform(pygame.sprite.Sprite):
    """Looks like a normal platform. Shoots away the instant you approach."""
    def __init__(self, x, y, width, height, move_speed_x=0, move_speed_y=0):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(TRAP_PLATFORM_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.original_x = x
        self.original_y = y
        self.move_speed_x = move_speed_x
        self.move_speed_y = move_speed_y
        self.is_triggered = False

    def trigger(self):
        self.is_triggered = True

    def update(self, *args):
        if self.is_triggered:
            self.rect.x += self.move_speed_x
            self.rect.y += self.move_speed_y


class ProximitySpike(pygame.sprite.Sprite):
    """Hidden below a surface, snaps up when player gets close."""
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(SPIKE_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y + height))
        self.target_y = y
        self.is_triggered = False

    def trigger(self):
        self.is_triggered = True

    def update(self, *args):
        if self.is_triggered and self.rect.y > self.target_y:
            self.rect.y -= 18  # Very fast snap
            if self.rect.y < self.target_y:
                self.rect.y = self.target_y


class VariableSpeedHazard(pygame.sprite.Sprite):
    """Moves horizontally. Accelerates abruptly when the player jumps."""
    def __init__(self, x, y, width, height, slow_speed, fast_speed):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(SPIKE_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.slow_speed = slow_speed
        self.fast_speed = fast_speed
        self.current_speed = slow_speed
        self.original_x = x

    def trigger_fast(self):
        self.current_speed = self.fast_speed

    def trigger_slow(self):
        self.current_speed = self.slow_speed

    def update(self, *args):
        self.rect.x += self.current_speed


class FakeWall(pygame.sprite.Sprite):
    """Looks identical to a real tile but has no collision — purely visual deception."""
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(GRAY)  # Indistinguishable from real tile
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, *args):
        pass


class InvisibleBlock(pygame.sprite.Sprite):
    """Completely invisible but has real collision — trial and error."""
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))  # Fully transparent
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, *args):
        pass
