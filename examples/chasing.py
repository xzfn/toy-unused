import sys
import math

from vmath import Vector, Matrix, Quaternion, Transform
import retroreload

import pyglet
from pyglet.window import key

import toy
import toy.app
import toy.draw


class Entity(object):
    def __init__(self, game, entity_id, param):
        self.game = game
        self.entity_id = entity_id

        self._destroyed = False

    def update(self, dt):
        pass

    def draw(self):
        pass

    def destroy(self):
        self._destroyed = True

    def is_destroyed(self):
        return self._destroyed

class Plane(Entity):
    def __init__(self, game, entity_id, param):
        super().__init__(game, entity_id, param)
        self.position = Vector()
        self.velocity = Vector(-1.0, 0.0, 0.0)

    def update(self, dt):
        side = Vector(0.0, 1.0, 0.0).cross(self.velocity).normalized()
        a = side * 0.5
        #self.velocity += a * dt
        self.position += self.velocity * dt

    def draw(self):
        model_matrix = Transform(self.position).to_matrix()
        draw = toy.draw.LocalDraw(self.game.app.batch, model_matrix)
        draw.draw_sphere(Vector(), 0.5, color=toy.coloring.GREEN)
        draw.draw_line(Vector(), self.velocity * 10.0, color=toy.coloring.MAGENTA)

def calc_chase_velocity(p1, v1, p2, s2):
    a = v1.length() ** 2 - s2 ** 2
    delta_p = p1 - p2
    b = 2.0 * delta_p.dot(v1)
    c = delta_p.length() ** 2
    under_sqrt = b ** 2 - 4.0 * a * c
    if under_sqrt < 0.0:
        return None
    the_sqrt = math.sqrt(under_sqrt)
    t = (-b - the_sqrt) / (2.0 * a)
    if t < 0:
        return None

    p3 = p1 + v1 * t
    direction2 = (p3 - p2).normalized()
    new_v2 = direction2 * s2
    return new_v2

class Missile(Entity):
    def __init__(self, game, entity_id, param):
        super().__init__(game, entity_id, param)
        self.position = Vector()
        self.velocity = Vector()

        self.speed = param['speed']
        self.target_id = param['target_id']

    def update(self, dt):
        _entity_manager = self.game.entity_manager
        target = _entity_manager.get_entity(self.target_id)
        if not target:
            _entity_manager.remove_entity(self)
            return
        
        if (target.position - self.position).length() < 0.1:
            _entity_manager.remove_entity(self)
            return

        new_v = calc_chase_velocity(
            target.position, target.velocity,
            self.position, self.speed)
        if new_v is None:
            _entity_manager.remove_entity(self)
            return

        self.velocity = new_v

        self.position += self.velocity * dt

    def draw(self):
        model_matrix = Transform(self.position).to_matrix()
        draw = toy.draw.LocalDraw(self.game.app.batch, model_matrix)
        draw.draw_sphere(Vector(), 0.5)
        draw.draw_line(Vector(), self.velocity * 10.0, color=toy.coloring.BLUE)

class EntityManager(object):
    def __init__(self, game):
        self.game = game
        self._entities = {}

        self._current_id = 1
        self._created_entities = {}
        self._removed_entity_ids = []

    def create_entity(self, entity_class, param=None):
        if param is None:
            param = {}
        entity_id = self._current_id
        self._current_id += 1
        entity = entity_class(self.game, entity_id, param)
        self._created_entities[entity_id] = entity
        return entity

    def remove_entity(self, entity):
        print('remove entity', entity)
        entity.destroy()
        self._removed_entity_ids.append(entity.entity_id)

    def get_entity(self, entity_id):
        if entity_id in self._entities:
            entity = self._entities[entity_id]
            if not entity.is_destroyed():
                return entity
        if entity_id in self._created_entities:
            entity = self._created_entities[entity_id]
            if not entity.is_destroyed():
                return entity
        return None

    def update(self, dt):
        self._entities.update(self._created_entities)
        self._created_entities.clear()

        for entity_id in self._removed_entity_ids:
            del self._entities[entity_id]
        self._removed_entity_ids.clear()

        for entity in self._entities.values():
            if not entity.is_destroyed():
                entity.update(dt)

    def draw(self):
        for entity in self._entities.values():
            if not entity.is_destroyed():
                entity.draw()

class Game(toy.app.IGame):
    def on_key_press(self, symbol, modifiers):
        if symbol == key.F5:
            print('reload')
            retroreload.retroreload(sys.modules[__name__])
        elif symbol == key.SPACE:
            print('chase plane', self.current_plane_id)
            if self.current_plane_id:
                param = {
                    'speed': 2.0,
                    'target_id': self.current_plane_id
                }
                missile = self.entity_manager.create_entity(Missile, param)
                missile.position = Vector(0.0, 0.0, -5.0)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            if self.current_plane_id:
                print('chase plane', self.current_plane_id)
                param = {
                    'speed': 2.0,
                    'target_id': self.current_plane_id
                }
                missile = self.entity_manager.create_entity(Missile, param)
                position = self.app.camera.top_down_screen_to_world(Vector(x, y, 0.0))
                missile.position = position

    def init(self, app):
        self.app = app
        self.entity_manager = EntityManager(self)
        self.current_plane_id = 0

        camera = self.app.camera
        camera.set_mode(camera.MODE_ORTHO)
        camera.set_look_at(
            Vector(0.0, 50.0, 0.0), Vector(0.0, 0.0, 0.0), Vector(0.0, 0.0, 1.0)
        )


        plane = self.entity_manager.create_entity(Plane)
        self.current_plane_id = plane.entity_id

    def update(self, dt):
        draw = self.app.draw
        draw.draw_grid(1.0, 100, toy.coloring.GRAY)

        self.entity_manager.update(dt)

    def draw(self):
        self.entity_manager.draw()
