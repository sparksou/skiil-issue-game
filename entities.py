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

        self.on_ground = collisions['bottom']


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
