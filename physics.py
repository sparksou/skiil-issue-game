import pygame
from settings import GRAVITY, TERMINAL_VELOCITY

class PhysicsEngine:
    @staticmethod
    def apply_gravity(entity, multiplier=1.0):
        """Applies gravity to an entity's velocity. multiplier scales per loop."""
        entity.velocity.y += GRAVITY * multiplier
        cap = TERMINAL_VELOCITY * max(1.0, multiplier * 0.8)
        if entity.velocity.y > cap:
            entity.velocity.y = cap

    @staticmethod
    def check_collision(rect, tiles):
        """
        Checks for collision between a rect and a list of pygame.Rect objects.
        Returns a list of tiles that collide with the rect.
        """
        hit_list = []
        for tile in tiles:
            if rect.colliderect(tile):
                hit_list.append(tile)
        return hit_list

    @staticmethod
    def move(entity, tiles):
        """
        Moves the entity considering collisions.
        Returns a dict indicating collision directions: top/bottom/left/right.
        """
        collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

        # --- Horizontal pass ---
        entity.rect.x += int(entity.velocity.x)
        hit_list = PhysicsEngine.check_collision(entity.rect, tiles)
        for tile in hit_list:
            if entity.velocity.x > 0:
                entity.rect.right = tile.left
                collision_types['right'] = True
            elif entity.velocity.x < 0:
                entity.rect.left = tile.right
                collision_types['left'] = True

        # --- Vertical pass ---
        entity.rect.y += int(entity.velocity.y)
        hit_list = PhysicsEngine.check_collision(entity.rect, tiles)
        for tile in hit_list:
            if entity.velocity.y > 0:   # Falling down
                entity.rect.bottom = tile.top
                collision_types['bottom'] = True
                entity.velocity.y = 0
            elif entity.velocity.y < 0: # Jumping up
                entity.rect.top = tile.bottom
                collision_types['top'] = True
                entity.velocity.y = 0

        return collision_types
