import pygame
import random
import math
from settings import *

class Particle:
    """A single pixel debris particle spawned on death."""
    COLORS = [
        (255, 60, 60),   # bright red
        (220, 100, 40),  # orange-red
        (255, 160, 50),  # orange
        (255, 220, 100), # yellow
        (255, 255, 255), # white flash
    ]

    def __init__(self, x, y, death_count=1):
        self.x = float(x)
        self.y = float(y)
        speed = random.uniform(2, 6 + min(death_count * 0.1, 6))
        angle = random.uniform(0, math.pi * 2)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(1, 4)
        self.timer = random.randint(18, 38)
        self.max_timer = self.timer
        self.color = random.choice(self.COLORS)
        self.size = random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += GRAVITY * 0.6  # particles are light
        self.vx *= 0.97           # air resistance
        self.timer -= 1

    def render(self, surface, offset=(0, 0)):
        if self.timer <= 0:
            return
        # Fade out: alpha approximated by shrinking radius
        ratio = self.timer / self.max_timer
        r = max(1, int(self.size * ratio))
        sx = int(self.x) + offset[0]
        sy = int(self.y) + offset[1]
        pygame.draw.circle(surface, self.color, (sx, sy), r)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, count=30, death_count=1):
        """Emit `count` particles. Scales with death_count for escalating explosions."""
        for _ in range(count):
            self.particles.append(Particle(x, y, death_count))

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.timer > 0]

    def render(self, surface, offset=(0, 0)):
        for p in self.particles:
            p.render(surface, offset)


class CameraShake:
    """Non-linear camera shake: fast initial burst, slow decay."""
    def __init__(self):
        self.intensity = 0.0
        self.decay = 0.88  # exponential decay factor

    def trigger(self, intensity=10):
        # Only escalate, never reduce mid-shake
        if intensity > self.intensity:
            self.intensity = float(intensity)

    def get_offset(self):
        if self.intensity < 0.5:
            self.intensity = 0.0
            return (0, 0)
        ox = random.randint(-int(self.intensity), int(self.intensity))
        oy = random.randint(-int(self.intensity), int(self.intensity))
        self.intensity *= self.decay
        return (ox, oy)


class GlitchText:
    """Renders text with a brief glitch animation (color corruption + position shift)."""
    def __init__(self, duration=8):
        self.timer = 0
        self.duration = duration

    def trigger(self):
        self.timer = self.duration

    def render(self, surface, font, text, base_pos, normal_color):
        if self.timer > 0:
            self.timer -= 1
            # Glitch: render at shifted position in corrupted color
            glitch_color = (
                random.randint(200, 255),
                random.randint(0, 60),
                random.randint(0, 60),
            )
            shift = (random.randint(-5, 5), random.randint(-3, 3))
            surf = font.render(text, True, glitch_color)
            surface.blit(surf, (base_pos[0] + shift[0], base_pos[1] + shift[1]))
        else:
            surf = font.render(text, True, normal_color)
            surface.blit(surf, base_pos)
