"""
Batching.
"""

import array
from ctypes import *

import pyglet
from pyglet.gl import *

from vmath import Matrix

import toy
import toy.shader
import toy.coloring


vertex_shader_source = """
#version 330 core
layout(location=0) in vec3 Position;
layout(location=1) in vec3 Color;
uniform mat4 ModelViewProjection;
out vec3 VertexColor;

void main() {
    vec4 world_position = ModelViewProjection * vec4(Position, 1.0f);
    gl_Position = world_position;
    VertexColor = Color;
}
"""

fragment_shader_source = """
#version 330 core
in vec3 VertexColor;
out vec4 FragColor;

void main() {
    FragColor = vec4(VertexColor, 1.0f);
}
"""

SIZEOF_FLOAT = sizeof(GLfloat)


class PrimitiveBatch(object):
    VERTEX_SIZE = 6
    VERTEX_SIZE_BYTES = VERTEX_SIZE * SIZEOF_FLOAT
    BATCH_SIZE = 6 * 1000
    BATCH_SIZE_FLOATS = VERTEX_SIZE * BATCH_SIZE
    BATCH_SIZE_BYTES = BATCH_SIZE_FLOATS * SIZEOF_FLOAT
    def __init__(self, app, camera):
        self.app = app
        self.camera = camera
        self.shader = toy.shader.Shader(vertex_shader_source, fragment_shader_source)
        self.point_vertices = array.array('f')
        self.line_vertices = array.array('f')
        self.vao = GLuint()
        glGenVertexArrays(1, byref(self.vao))
        glBindVertexArray(self.vao)
        self.vbo = GLuint()
        glGenBuffers(1, byref(self.vbo))
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.BATCH_SIZE_BYTES, None, GL_STREAM_DRAW)
        stride = self.VERTEX_SIZE_BYTES
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, None)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, 3 * SIZEOF_FLOAT)
        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)
        glPointSize(2.0)

    def draw_point(self, position, color):
        self.point_vertices.extend((position.x, position.y, position.z,
            color.x, color.y, color.z))

    def draw_line(self, position0, position1, color):
        self.line_vertices.extend((position0.x, position0.y, position0.z,
            color.x, color.y, color.z,
            position1.x, position1.y, position1.z,
            color.x, color.y, color.z))

    def _draw_vertices(self, vertices, primitive_mode):
        address, length_floats = vertices.buffer_info()
        batch_count, last_floats = divmod(length_floats, self.BATCH_SIZE_FLOATS)
        for i in range(batch_count):
            sub_address = address + i * self.BATCH_SIZE_BYTES
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.BATCH_SIZE_BYTES, sub_address)
            glDrawArrays(primitive_mode, 0, self.BATCH_SIZE)
        if last_floats > 0:
            sub_address = address + batch_count * self.BATCH_SIZE_BYTES
            glBufferSubData(GL_ARRAY_BUFFER, 0, last_floats * SIZEOF_FLOAT, sub_address)
            glDrawArrays(primitive_mode, 0, last_floats // self.VERTEX_SIZE)

    def draw(self):
        self.shader.use()
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        vp_matrix = self.camera.get_view_projection()
        self.shader.set_uniform_matrix(b'ModelViewProjection', vp_matrix)
        if self.point_vertices:
            self._draw_vertices(self.point_vertices, GL_POINTS)
            del self.point_vertices[:]
        if self.line_vertices:
            self._draw_vertices(self.line_vertices, GL_LINES)
            del self.line_vertices[:]


texture_vertex_shader_source = """
#version 330 core
layout(location=0) in vec2 Position;
layout(location=1) in vec2 InTexCoord;
layout(location=2) in vec3 Color;
uniform mat4 ModelViewProjection;

out vec2 TexCoord;
out vec3 VertexColor;

void main() {
    vec4 world_position = ModelViewProjection * vec4(Position, 0.0, 1.0);
    gl_Position = world_position;
    TexCoord = InTexCoord;
    VertexColor = Color;
}
"""

texture_fragment_shader_source = """
#version 330 core
uniform sampler2D Texture;

in vec2 TexCoord;
in vec3 VertexColor;
out vec4 FragColor;

void main() {
    vec4 color = texture(Texture, TexCoord);
    FragColor = color * vec4(VertexColor, 1.0);
    // FragColor = vec4(1.0, 0.0, 1.0, 1.0);
}
"""


def create_texture(imagepath):
    texture = GLuint()
    glGenTextures(1, byref(texture))
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    image = pyglet.image.load(imagepath)
    image_data = image.get_image_data().get_data('RGBA', image.width * 4)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
    return texture

class TextBatch(object):
    VERTEX_SIZE = 7
    VERTEX_SIZE_BYTES = VERTEX_SIZE * SIZEOF_FLOAT
    BATCH_SIZE = 3 * VERTEX_SIZE * 1000
    BATCH_SIZE_FLOATS = VERTEX_SIZE * BATCH_SIZE
    BATCH_SIZE_BYTES = BATCH_SIZE_FLOATS * SIZEOF_FLOAT
    def __init__(self, app, camera):
        self.app = app
        self.camera = camera
        self.shader = toy.shader.Shader(texture_vertex_shader_source, texture_fragment_shader_source)
        self.texture = create_texture('ascii.png')
        self.textinfos = []

        self.vao = GLuint()
        glGenVertexArrays(1, byref(self.vao))
        glBindVertexArray(self.vao)
        self.vbo = GLuint()
        glGenBuffers(1, byref(self.vbo))
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.BATCH_SIZE_BYTES, None, GL_STREAM_DRAW)
        stride = self.VERTEX_SIZE_BYTES
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, None)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, 2 * SIZEOF_FLOAT)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, 4 * SIZEOF_FLOAT)
        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)
        glEnableVertexAttribArray(2)

    def draw_text(self, position, text, color=toy.coloring.RED, scale=1.0):
        info = (position, text, scale, color)
        self.textinfos.append(info)

    def _draw_vertices(self, vertices, primitive_mode):
        address, length_floats = vertices.buffer_info()
        batch_count, last_floats = divmod(length_floats, self.BATCH_SIZE_FLOATS)
        for i in range(batch_count):
            sub_address = address + i * self.BATCH_SIZE_BYTES
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.BATCH_SIZE_BYTES, sub_address)
            glDrawArrays(primitive_mode, 0, self.BATCH_SIZE)
        if last_floats > 0:
            sub_address = address + batch_count * self.BATCH_SIZE_BYTES
            glBufferSubData(GL_ARRAY_BUFFER, 0, last_floats * SIZEOF_FLOAT, sub_address)
            glDrawArrays(primitive_mode, 0, last_floats // self.VERTEX_SIZE)

    def _draw_texts(self):
        vertices_array = array.array('f')
        for textinfo in self.textinfos:
            vertices = self._build_text(textinfo)
            vertices_array.extend(vertices)
        self._draw_vertices(vertices_array, GL_TRIANGLES)

    def _build_text(self, textinfo):
        position, text, scale, color = textinfo
        offset = ord(' ')
        start_x = position.x
        start_y = position.y
        current_x = start_x
        current_y = start_y
        delta_x = 22
        delta_y = 41
        real_delta_x = delta_x * scale
        real_delta_y = delta_y * scale
        ncol = 16
        width = 512
        delta_u = delta_x / width
        delta_v = delta_y / width
        vertices = []
        for char in text:
            if char == '\n':
                current_x = start_x
                current_y -= real_delta_y
                continue
            char_index = ord(char) - offset  # build a lookup table would be better
            char_row, char_col = divmod(char_index, ncol)
            u_ac = char_col * delta_u
            u_bd = (char_col + 1) * delta_u
            v_ab = 1.0 - (char_row + 1) * delta_v
            v_cd = 1.0 - char_row * delta_v
            x_ac = current_x
            x_bd = current_x + real_delta_x
            y_ab = current_y
            y_cd = current_y + real_delta_y
            point_a = (x_ac, y_ab, u_ac, v_ab, color.x, color.y, color.z)
            point_b = (x_bd, y_ab, u_bd, v_ab, color.x, color.y, color.z)
            point_c = (x_ac, y_cd, u_ac, v_cd, color.x, color.y, color.z)
            point_d = (x_bd, y_cd, u_bd, v_cd, color.x, color.y, color.z)
            quad_vertices = [point_a, point_b, point_c, point_c, point_b, point_d]
            for vertex in quad_vertices:
                vertices.extend(vertex)
            current_x += real_delta_x
        return vertices

    def draw(self):
        self.shader.use()
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        vp_matrix = self.camera.get_screen_view_projection()
        self.shader.set_uniform_matrix(b'ModelViewProjection', vp_matrix)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        self._draw_texts()
        self.textinfos.clear()
