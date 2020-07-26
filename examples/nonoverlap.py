
import itertools

from vmath import Vector, Matrix, Quaternion, Transform

from pyglet.window import key

import toy
import gel


class Character(gel.Actor):
    def __init__(self, world, actor_id, param):
        super().__init__(world, actor_id, param)
        self._radius = 1.0

        self._speed = 5.0

    def get_radius(self):
        return self._radius

    def update(self, delta_time):
        game = self.world.game

        _get_key = self.world.input_manager.get_key

        horz_axis = 0.0
        vert_axis = 0.0
        if _get_key(key.UP):
            vert_axis += 1.0
        if _get_key(key.DOWN):
            vert_axis -= 1.0
        if _get_key(key.LEFT):
            horz_axis += 1.0
        elif _get_key(key.RIGHT):
            horz_axis -= 1.0

        if horz_axis == 0.0 and vert_axis == 0.0:
            pass
        else:
            move_direction = Vector(horz_axis, 0.0, vert_axis).normalized()

            delta_position = move_direction * self._speed * delta_time
            new_position = self._position + delta_position
            self._position = new_position

        draw = toy.draw.LocalDraw(game.app.batch, Transform(self._position))
        draw.draw_sphere(Vector(), self._radius)


class Enemy(gel.Actor):
    def __init__(self, world, actor_id, param):
        super().__init__(world, actor_id, param)
        self._radius = 1.0

    def update(self, delta_time):
        game = self.world.game
        
        draw = toy.draw.LocalDraw(game.app.batch, Transform(self._position))
        draw.draw_sphere(Vector(), self._radius, color=toy.coloring.BLUE)

    def get_radius(self):
        return self._radius


class Block(gel.Actor):
    def __init__(self, world, actor_id, param):
        super().__init__(world, actor_id, param)
        self._radius = 3.0

    def update(self, delta_time):
        game = self.world.game
        draw = toy.draw.LocalDraw(game.app.batch, Transform(self._position))
        draw.draw_sphere(Vector(), self._radius, color=toy.coloring.BLACK)

    def get_radius(self):
        return self._radius


class NonOverlapManager(object):
    def __init__(self, world):
        self.world = world

    def update(self, delta_time):
        actors = self.world.actor_manager.get_actors()
        # get contacts
        for pair in itertools.combinations(actors, 2):
            actor_a, actor_b = pair
            delta_position = actor_b.get_position() - actor_a.get_position()
            distance = delta_position.length()
            total_radius = actor_a.get_radius() + actor_b.get_radius()
            penetration = total_radius - distance
            if penetration > 0.0:
                # overlap
                contact_normal = delta_position.normalized()
                ratio_a = 1.0
                ratio_b = 1.0
                if actor_a.__class__ == Block:
                    ratio_a = 0.0
                if actor_b.__class__ == Block:
                    ratio_b = 0.0
                ratio_total = ratio_a + ratio_b
                if ratio_total == 0.0:
                    continue
                percent_a = ratio_a / ratio_total
                percent_b = ratio_b / ratio_total
                actor_a.set_position(actor_a.get_position() - contact_normal * penetration * percent_a)
                actor_b.set_position(actor_b.get_position() + contact_normal * penetration * percent_b)


class Game(toy.app.IGame):
    def init(self, app):
        self.app = app
        self.world = gel.World(self)
        self.non_overlap_manager = NonOverlapManager(self.world)
        self.player = self.world.actor_manager.create_actor(Character)
        self.enemy = self.world.actor_manager.create_actor(Enemy, {'position': Vector(0.0, 0.0, 5.0)})
        self.block = self.world.actor_manager.create_actor(Block, {'position': Vector(5.0, 0.0, 0.0)})
        self.block2 = self.world.actor_manager.create_actor(Block, {'position': Vector(4.0, 0.0, 4.0)})
        camera = self.app.camera
        camera.set_mode(camera.MODE_ORTHO)
        camera.set_look_at(
            Vector(0.0, 50.0, 0.0), Vector(0.0, 0.0, 0.0), Vector(0.0, 0.0, 1.0)
        )

    def update(self, delta_time):
        draw = self.app.draw
        draw.draw_grid(1.0, 10, toy.coloring.GRAY)

        self.world.update(delta_time)
        self.non_overlap_manager.update(delta_time)

    def on_key_press(self, symbol, modifiers):
        self.world.input_manager.process_key_down(symbol)

    def on_key_release(self, symbol, modifiers):
        self.world.input_manager.process_key_up(symbol)
