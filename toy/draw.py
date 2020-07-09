"""
Draw.
"""

import math

from vmath import Vector, Matrix, Quaternion, Transform

from toy import coloring


CIRCLE_SEGMENTS = 8
CIRCLE_STEP = math.pi * 2.0 / CIRCLE_SEGMENTS
CIRCLE_POINTS = [Vector(math.cos(i*CIRCLE_STEP), 0.0, math.sin(i*CIRCLE_STEP)) for i in range(CIRCLE_SEGMENTS)]

CUBE_VERTICES = [Vector(-0.5, -0.5, -0.5), Vector(-0.5, -0.5, 0.5), Vector(0.5, -0.5, 0.5), Vector(0.5, -0.5, -0.5),
                 Vector(-0.5, 0.5, -0.5), Vector(-0.5, 0.5, 0.5), Vector(0.5, 0.5, 0.5), Vector(0.5, 0.5, -0.5)]


def matrix_position(matrix):
    return Vector(matrix.d, matrix.h, matrix.l)


class Draw(object):
    def __init__(self, batch):
        self.batch = batch

    def draw_point(self, position, color=coloring.RED):
        self.batch.draw_point(position, color)

    def draw_line(self, position0, position1, color=coloring.RED):
        self.batch.draw_line(position0, position1, color)

    def draw_polyline(self, points, color=coloring.RED):
        for i in range(len(points) - 1):
            self.draw_line(points[i], points[i+1], color)

    def draw_polygon(self, points, color=coloring.RED):
        for i in range(len(points)):
            self.draw_line(points[i-1], points[i], color)

    def draw_pair_lines(self, points0, points1, color=coloring.RED):
        for point0, point1 in zip(points0, points1):
            self.draw_line(point0, point1, color)

    def draw_tip_lines(self, tip, points, color=coloring.RED):
        for point in points:
            self.draw_line(tip, point, color)

    def draw_sphere(self, position, radius, color=coloring.RED):
        longitude_segments = 8
        longitude_step = math.pi / longitude_segments
        sub_circle_points = [position + Vector(0.0, radius, 0.0)] * CIRCLE_SEGMENTS
        for i in range(1, longitude_segments):
            phi = i * longitude_step
            sub_radius = radius * math.sin(phi)
            sub_height = radius * math.cos(phi)
            offset = position + Vector(0.0, sub_height, 0.0)
            next_sub_circle_points = [offset + sub_radius * point for point in CIRCLE_POINTS]
            self.draw_polygon(next_sub_circle_points, color)
            self.draw_pair_lines(sub_circle_points, next_sub_circle_points, color)
            sub_circle_points = next_sub_circle_points
        next_sub_circle_points = [position + Vector(0.0, -radius, 0.0)] * CIRCLE_SEGMENTS
        self.draw_pair_lines(sub_circle_points, next_sub_circle_points, color)

    def draw_cone(self, matrix, radius, height, color=coloring.RED):
        tip = Vector(0.0, height, 0.0)
        wtip = matrix.transform_point(tip)
        circle_points = [matrix.transform_point(point * radius) for point in CIRCLE_POINTS]
        self.draw_polygon(circle_points, color)
        self.draw_tip_lines(wtip, circle_points, color)

    def draw_box_vertices(self, vertices, color):
        lower_half = vertices[:4]
        upper_half = vertices[4:]
        self.draw_polygon(lower_half, color)
        self.draw_polygon(upper_half, color)
        self.draw_pair_lines(lower_half, upper_half, color)

    def draw_cube(self, position, length, color=coloring.RED):
        cube_vertices = [position + v * length for v in CUBE_VERTICES]
        self.draw_box_vertices(cube_vertices, color)
        self.draw_point(position, color)

    def draw_box(self, matrix, color=coloring.RED):
        box_vertices = [matrix.transform_point(point) for point in CUBE_VERTICES]
        self.draw_box_vertices(box_vertices, color)
        self.draw_point(matrix.decompose().translation, color)

    def draw_cylinder(self, position0, position1, radius, color=coloring.RED):
        normal = (position1 - position0).normalized()
        rotation = Quaternion.from_from_to_rotation(Vector(0.0, 1.0, 0.0), normal)
        transform0 = Transform(position0, rotation, Vector(radius, radius, radius))
        matrix0 = transform0.to_matrix()
        circle_points0 = [matrix0.transform_point(point) for point in CIRCLE_POINTS]
        transform1 = Transform(position1, rotation, Vector(radius, radius, radius))
        matrix1 = transform1.to_matrix()
        circle_points1 = [matrix1.transform_point(point) for point in CIRCLE_POINTS]
        self.draw_polygon(circle_points0, color)
        self.draw_polygon(circle_points1, color)
        self.draw_pair_lines(circle_points0, circle_points1, color)
        self.draw_point(position0, color)
        self.draw_point(position1, color)

    def draw_grid(self, step, n, color=coloring.RED):
        self.draw_point(Vector(0.0, 0.0, 0.0), color)
        border = n * step
        for i in range(1, n + 1):
            seg = i * step
            v0 = Vector(-seg, 0.0, -border)
            v1 = Vector(-seg, 0.0, border)
            self.draw_line(v0, v1, color)
            v0 = Vector(seg, 0.0, -border)
            v1 = Vector(seg, 0.0, border)
            self.draw_line(v0, v1, color)
            v0 = Vector(-border, 0.0, -seg)
            v1 = Vector(border, 0.0, -seg)
            self.draw_line(v0, v1, color)
            v0 = Vector(-border, 0.0, seg)
            v1 = Vector(border, 0.0, seg)
            self.draw_line(v0, v1, color)
        v0 = Vector(-border, 0.0, 0.0)
        v1 = Vector(border, 0.0, 0.0)
        red = Vector(1.0, 0.0, 0.0)
        self.draw_line(v0, v1, red)
        self.draw_point(Vector(border, 0.0, 0.0), red)
        v0 = Vector(0.0, 0.0, -border)
        v1 = Vector(0.0, 0.0, border)
        blue = Vector(0.0, 0.0, 1.0)
        self.draw_line(v0, v1, blue)
        self.draw_point(Vector(0.0, 0.0, border), blue)

    def draw_axis(self, matrix, length):
        transform = matrix.decompose()
        position = transform.translation
        rotation = transform.rotation
        axis_x, axis_y, axis_z = rotation.to_axes()
        head_x = position + axis_x * length
        head_y = position + axis_y * length
        head_z = position + axis_z * length
        red = coloring.RED
        green = coloring.GREEN
        blue = coloring.BLUE
        self.draw_line(position, head_x, red)
        self.draw_line(position, head_y, green)
        self.draw_line(position, head_z, blue)
        self.draw_point(head_x, red)
        self.draw_point(head_y, green)
        self.draw_point(head_z, blue)

        head_radius = length * 0.1
        head_height = head_radius * 3.0
        head_translate_matrix = Matrix.from_translation(Vector(0.0, length, 0.0))
        head_x_rotate_matrix = Matrix.from_angle_axis(-math.pi / 2.0, Vector(0.0, 0.0, 1.0))
        self.draw_cone(matrix * head_x_rotate_matrix * head_translate_matrix, head_radius, head_height, red)
        self.draw_cone(matrix * head_translate_matrix, head_radius, head_height, green)
        head_z_rotate_matrix = Matrix.from_angle_axis(math.pi / 2.0, Vector(1.0, 0.0, 0.0))
        self.draw_cone(matrix * head_z_rotate_matrix * head_translate_matrix, head_radius, head_height, blue)


class LocalDraw(Draw):
    def __init__(self, batch, matrix):
        super().__init__(batch)
        self.matrix = matrix

    def draw_point(self, position, color=coloring.RED):
        world_position = self.matrix.transform_point(position)
        super().draw_point(world_position, color)

    def draw_line(self, position0, position1, color=coloring.RED):
        world_position0 = self.matrix.transform_point(position0)
        world_position1 = self.matrix.transform_point(position1)
        super().draw_line(world_position0, world_position1, color)
