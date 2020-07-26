
import sys
import math
import pickle
import logging
logging.basicConfig(level=logging.DEBUG)

from vmath import Vector, Matrix, Transform, Quaternion

import pyglet
from pyglet.window import key

import retroreload

import toy
import toy.app
import toy.coloring
import toy.draw


class Game(toy.app.IGame):
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_key_press(self, symbol, modifiers):
        if symbol == key.F5:
            retroreload.retroreload(sys.modules[__name__])

    def init(self, app):
        self.app = app
        self.game_time = 0.0

    def update2(self, dt):
        self.game_time += dt
        draw = self.app.draw
        draw.draw_axis(Matrix(), 2.0)
        draw.draw_grid(1.0, 10, toy.coloring.GRAY)

        angle = self.game_time
        q = Quaternion.from_euler_angles(Vector(0.0, angle, 0.0))
        R = Matrix.from_rotation(q)
        S = Matrix.from_scale(Vector(4.0, 1.0, 1.0))
        draw.draw_box(R * S, toy.coloring.GREEN)
        draw.draw_box(S * R, toy.coloring.YELLOW)

    def update(self, dt):
        draw = self.app.draw

        n = 25
        step = 0.5
        vortex_origin = Vector(0.0, 0.0, 0.0)
        vortex_alpha = 1.0
        up = Vector(0.0, 1.0, 0.0)
        for i in range(-n, n):
            for j in range(-n, n):
                pos = Vector(i * step, 0.0, j * step)
                delta = pos - vortex_origin
                r = delta.length()
                r_direction = delta.normalized()
                if r > 0.0:

                    speed = vortex_alpha / r
                    direction = up.cross(delta).normalized()
                    draw.draw_line(pos, pos + direction * speed)

                    centri = vortex_alpha / (r**3)
                    draw.draw_line(pos, pos - r_direction * centri, color=toy.coloring.GREEN)

                    draw.draw_point(pos, color=toy.coloring.BLACK)

    def update3(self, dt):
        # print('game_time', id(self), self.game_time)
        self.game_time += dt
        draw = self.app.draw
        draw.draw_axis(Matrix(), 10.0)
        draw.draw_grid(10.0, 5, toy.coloring.LIGHT_GRAY)
        draw.draw_grid(1.0, 10, toy.coloring.GRAY)
        
        camera = self.app.camera
        p = camera.top_down_screen_to_world(Vector(camera.width / 2.0, camera.height / 2.0, 0.0))
        draw.draw_sphere(p, 1.0, toy.coloring.RED)
        
        p = camera.top_down_screen_to_world(Vector(0.0, 0.0, 0.0))
        draw.draw_sphere(p, 1.0, toy.coloring.GREEN)

        p = camera.top_down_screen_to_world(Vector(camera.width, camera.height, 0.0))
        draw.draw_sphere(p, 1.0, toy.coloring.BLUE)

        model_matrix = Transform(
            # Vector(5.0*math.cos(self.game_time), 0.0, 5.0*math.sin(self.game_time)),
            # Quaternion.from_euler_angles(Vector(self.game_time * 3.0, self.game_time, 0.0))
            ).to_matrix()

        sub_model_matrix = Transform(
            Vector(0.0, 2.0 * self.game_time, 0.0)
        ).to_matrix()

        draw = toy.draw.LocalDraw(self.app.batch, model_matrix)
        sub_draw = toy.draw.LocalDraw(self.app.batch, model_matrix * sub_model_matrix)
        sub_draw.draw_sphere(Vector(0.0, 0.0, 0.0), 5.0, toy.coloring.MAGENTA)

        draw.draw_point(Vector(0.0, 2.0, 0.0))
        draw.draw_line(Vector(-5.0, 1.0, 0.0), Vector(5.0, 1.0, 0.0))
        draw.draw_sphere(Vector(0.0, 3.0, 0.0), 2.0, toy.coloring.BLUE)
        transform = Transform(Vector(1.0, 2.0, 4.0), Quaternion.from_euler_angles(Vector(0.8, 0.2, 0.0)))
        matrix = transform.to_matrix()
        draw.draw_cone(matrix, 1.0, 2.0)
        draw.draw_axis(matrix, 1.0)
        draw.draw_cube(Vector(), 1.0)
        draw.draw_box(matrix, toy.coloring.GREEN)
        
        p0 = Vector(0.0, 100.0, 0.0)
        p1 = Vector(3.0, 6.0, 9.0)
        draw.draw_line(p0, p1, toy.coloring.CYAN)
        draw.draw_cylinder(p0, p1, 1.0)

        p0 = Vector(0.0, 10.0, 0.0)
        p1 = 30.0 * Vector(math.cos(self.game_time), math.sin(self.game_time), 1.0)
        draw.draw_cylinder(p0, p1, 3.0)
        draw.draw_sphere(p1, 3.0, toy.coloring.CYAN)

        points = []
        for i in range(50):
            r = i * 0.5
            a = r + self.game_time
            points.append(Vector(math.cos(a), r, math.sin(a)))
        draw.draw_polyline(points, toy.coloring.CYAN)


        text_batch = self.app.text_batch
        text_batch.draw_text(Vector(0.0, 0.0, 0.0), 'abcabfdsfdc')
        text_batch.draw_text(Vector(0.0, 20.0, 0.0), 'defdef', toy.coloring.MAGENTA)
        text_batch.draw_text(Vector(0.0, 200.0, 0.0), 'ABCABC\nDEFDEF')
        text_batch.draw_text(Vector(0.0, 500.0, 0.0), '1234567890', toy.coloring.BLUE, 2.0)
        view_eye = self.app.camera.view_eye
        view_at = self.app.camera.view_at
        view_info = 'eye {}, dir {}'.format(view_eye, view_at - view_eye)
        text_batch.draw_text(Vector(10.0, 400.0, 0.0), view_info, toy.coloring.BLACK, 0.4)

        world_p = (model_matrix * sub_model_matrix).transform_point(Vector(0.0, 0.0, 0.0))
        # world_p = Vector()
        screen_p = camera.world_to_screen(world_p)

        text_batch.draw_text(screen_p, 'Lklm world{}'.format(world_p), toy.coloring.BLACK, 0.5)

        model_matrix = Transform(
            Vector(),
            Quaternion.from_euler_angles(Vector(0.0, 0.0 * self.game_time, 0.0)),
            Vector(1.0, 1.0, 1.0) * 1.0
            ).to_matrix()

    def draw(self):
        pass
