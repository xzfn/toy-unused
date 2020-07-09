"""
Camera
"""

import math

from vmath import Vector, Matrix, Quaternion
import pyglet
from pyglet.window import key


def transform_point(matrix, v):
    return matrix.transform(v)


class Camera(object):
    MODE_PERSPECTIVE = 1
    MODE_ORTHO = 2
    def __init__(self):
        self.width = 512
        self.height = 512
        self.aspect = 1.0
        self.view = Matrix()

        self.perspective_fov = math.radians(60.0)
        self.ortho_extent = 10.0

        self.view_eye = Vector(0.0, 4.0, -10.0)
        self.view_at = Vector(0.0, 0.0, 0.0)
        self.view_up = Vector(0.0, 1.0, 0.0)

        self.set_look_at(self.view_eye, self.view_at, self.view_up)
        self.set_perspective(self.perspective_fov)
        self.set_ortho(self.ortho_extent)

        self.mode = self.MODE_PERSPECTIVE

    def set_new_size(self, width, height):
        self.width = width
        self.height = height
        self.aspect = width / height
        self.set_perspective(self.perspective_fov)
        self.set_ortho(self.ortho_extent)

    def set_mode(self, mode):
        self.mode = mode

    def get_look_at(self):
        return (self.view_eye.copy(), self.view_at.copy(), self.view_up.copy())

    def set_look_at(self, eye, at, up):
        self.view_eye = eye
        self.view_at = at
        self.view_up = up
        self.view = Matrix.from_look_at(eye, at, up)

    def set_perspective(self, fov):
        self.perspective_fov = fov
        self.projection_perspective = Matrix.from_perspective(fov, self.aspect, 0.1, 1000.0)

    def set_ortho(self, extent):
        design_height = 600
        self.ortho_extent = extent
        left = -extent * self.aspect
        right = extent * self.aspect
        top = extent
        bottom = -extent
        near = 0.0
        far = 1000.0
        self.projection_ortho = Matrix.from_ortho(left, right, bottom, top, near, far)

    def get_projection(self):
        _mode = self.mode
        if _mode == self.MODE_PERSPECTIVE:
            return self.projection_perspective
        elif _mode == self.MODE_ORTHO:
            return self.projection_ortho
        else:
            return self.projection_perspective

    def get_view_projection(self):
        return self.get_projection() * self.view

    def get_screen_view_projection(self):
        design_height = 600
        height = design_height
        width = design_height * self.aspect
        return Matrix.from_ortho(0.0, width, 0.0, height, -1.0, 1.0)

    def world_to_screen(self, position):
        vp_matrix = self.get_view_projection()
        clip_position = vp_matrix.project_point(position)
        height = 600
        width = height * self.aspect
        return Vector((clip_position.x + 1.0) * width / 2.0, (clip_position.y + 1.0) * height / 2.0, 1.0 - clip_position.z)

    def top_down_screen_to_world(self, position):
        screen_x = position.x
        screen_y = self.height - position.y
        clip_x = (screen_x - self.width / 2.0) * 2.0 / self.width
        clip_y = (screen_y - self.height / 2.0) * 2.0 / self.height
        pmatrix = self.projection_ortho
        world_origin_x = (clip_x + pmatrix.m30) / pmatrix.m00
        world_origin_y = (clip_y + pmatrix.m31) / pmatrix.m11
        world_x = self.view_eye.x - world_origin_x
        world_z = self.view_eye.z - world_origin_y
        return Vector(world_x, 0.0, world_z)

    def screen_to_ray(self, position):
        pass

class FreeviewCameraController(object):
    def __init__(self, app, camera):
        self.app = app
        self.camera = camera
        self.drag_dx_dy = (0.0, 0.0)
        self.pan_dx_dy = (0.0, 0.0)

        self.move_speed = 20.0
        self.rotate_speed = 0.3
        self.scroll_move_speed = 2.0

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.MIDDLE:
            self.pan_dx_dy = (self.pan_dx_dy[0] + dx, self.pan_dx_dy[1] + dy)
        else:
            self.drag_dx_dy = (self.drag_dx_dy[0] + dx, self.drag_dx_dy[1] + dy)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        camera = self.camera
        view_eye, view_at, view_up = camera.get_look_at()
        if camera.mode == camera.MODE_PERSPECTIVE:
            view_direction = (view_at - view_eye).normalized()

            move_delta = self.scroll_move_speed * scroll_y
            view_eye += view_direction * move_delta

            camera.set_look_at(view_eye, view_eye + view_direction, view_up)
        elif camera.mode == camera.MODE_ORTHO:
            extent = camera.ortho_extent
            if scroll_y > 0:
                new_extent = extent * 0.9
            else:
                new_extent = extent * 1.3
            if new_extent < 0.1:
                new_extent = 0.1
            camera.set_ortho(new_extent)
            if camera.view_up == Vector(0.0, 0.0, 1.0):
                mouse_world = camera.top_down_screen_to_world(Vector(x, y, 0.0))
                move_delta = (mouse_world - view_eye) * (extent / new_extent - 1.0)
                move_delta.y = 0.0
                #move_delta.z *= -1.0
                view_eye += move_delta

                view_at = view_eye + Vector(0.0, -1.0, 0.0)
                camera.set_look_at(view_eye, view_at, view_up)
            

    def update(self, dt):
        keys = self.app.keys
        camera = self.camera

        going_up = 0.0
        going_horz = 0.0
        going_vert = 0.0
        if keys[key.E]:
            going_up += 1.0
        if keys[key.Q]:
            going_up -= 1.0
        if keys[key.W]:
            going_vert += 1.0
        if keys[key.S]:
            going_vert -= 1.0
        if keys[key.A]:
            going_horz -= 1.0
        if keys[key.D]:
            going_horz += 1.0

        move_delta = self.move_speed * dt
        rotate_delta = self.rotate_speed * dt

        view_eye, view_at, view_up = camera.get_look_at()
        view_direction = (view_at - view_eye).normalized()

        drag_as_pan = False
        if view_up == Vector(0.0, 0.0, 1.0):
            drag_as_pan = True

        pan_dx, pan_dy = self.pan_dx_dy
        drag_dx, drag_dy = self.drag_dx_dy
        if drag_as_pan:
            pan_dx += drag_dx
            pan_dy += drag_dy
            drag_dx = 0.0
            drag_dy = 0.0
        self.pan_dx_dy = (0.0, 0.0)
        self.drag_dx_dy = (0.0, 0.0)

        if camera.mode == camera.MODE_PERSPECTIVE:
            pan_k = view_eye.y * math.tan(camera.perspective_fov / 2.0) * 2.0 / camera.height
            move_delta = 1.0
        elif camera.mode == camera.MODE_ORTHO:
            pan_k = camera.ortho_extent * 2 / camera.height

        if pan_dx != 0.0 or pan_dy != 0.0:
            going_up -= pan_dy * pan_k
            going_horz -= pan_dx * pan_k

        if camera.mode == camera.MODE_PERSPECTIVE:
            view_eye += view_up * going_up * move_delta
            view_eye += view_direction * going_vert * move_delta
            right = view_direction.cross(view_up)
            view_eye += right * going_horz * move_delta
        elif camera.mode == camera.MODE_ORTHO:
            view_eye += view_up * (going_up + going_vert) * 1.0
            right = view_direction.cross(view_up)
            view_eye += right * going_horz * 1.0

        if drag_dx != 0.0 or drag_dy != 0.0:
            old_view_direction = view_direction.copy()
            q_yawing = Quaternion.from_angle_axis(-drag_dx * rotate_delta, view_up)
            view_direction = q_yawing.to_matrix().transform_vector(old_view_direction)
            right = view_direction.cross(view_up)
            q_pitching = Quaternion.from_angle_axis(drag_dy * rotate_delta, right)
            view_direction = q_pitching.to_matrix().transform_vector(view_direction)
        camera.set_look_at(view_eye, view_eye + view_direction, view_up)

    def on_key_press(self, symbol, modifiers):
        camera = self.camera
        if symbol == key.O:
            # ortho
            camera.set_mode(camera.MODE_ORTHO)
        elif symbol == key.P:
            # perspective
            camera.set_mode(camera.MODE_PERSPECTIVE)
        elif symbol == key.F9:        
            camera.set_look_at(Vector(-30.0, 0.0, 0.0), Vector(0.0, 0.0, 0.0), Vector(0.0, 1.0, 0.0))
        elif symbol == key.F10:
            camera.set_look_at(Vector(0.0, 50.0, 0.0), Vector(0.0, 0.0, 0.0), Vector(0.0, 0.0, 1.0))
        elif symbol == key.F11:
            camera.set_look_at(Vector(0.0, 0.0, -30.0), Vector(0.0, 0.0, 0.0), Vector(0.0, 1.0, 0.0))
