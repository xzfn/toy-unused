
import logging
logger = logging.getLogger(__name__)
from ctypes import *

from pyglet.gl import *

import vmathop


class GLError(Exception):
    pass


def compile_shader(source, shader_type):
    source_c = c_char_p(source.encode('utf-8'))
    shader = glCreateShader(shader_type)
    glShaderSource(shader, 1, cast(byref(source_c), POINTER(POINTER(c_char))), None)
    glCompileShader(shader)
    success = GLint()
    glGetShaderiv(shader, GL_COMPILE_STATUS, byref(success))
    if not success:
        log_len = GLint()
        glGetShaderiv(shader, GL_INFO_LOG_LENGTH, byref(log_len))
        info_log = create_string_buffer(log_len.value)
        glGetShaderInfoLog(shader, log_len, None, info_log)
        logger.warning('Compile shader failed, info log:')
        logger.warning(info_log.value.decode('utf-8'))
        raise GLError('Compile shader failed')
    return shader

def link_program(vertex_shader, fragment_shader):
    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)
    success = GLint()
    glGetProgramiv(program, GL_LINK_STATUS, byref(success))
    if not success:
        log_len = GLint()
        glGetProgramiv(program, GL_INFO_LOG_LENGTH, byref(log_len))
        info_log = create_string_buffer(log_len.value)
        glGetProgramInfoLog(program, log_len, None, info_log)
        logger.warning('Link program failed, info log:')
        logger.warning(info_log.value.decode('utf-8'))
        raise GLError('Link program failed')
    return program

def create_program(vertex_shader_source, fragment_shader_source):
    vertex_shader = compile_shader(vertex_shader_source, GL_VERTEX_SHADER)
    fragment_shader = compile_shader(fragment_shader_source, GL_FRAGMENT_SHADER)
    program = link_program(vertex_shader, fragment_shader)
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)
    return program


class Shader(object):
    def __init__(self, vertex_source, fragment_source):
        self.program = create_program(vertex_source, fragment_source)
        self._uniform_locations = {}

    def use(self):
        glUseProgram(self.program)

    def get_uniform_location(self, uniform_name):
        try:
            return self._uniform_locations[uniform_name]
        except KeyError:
            uniform_location = glGetUniformLocation(self.program, c_char_p(uniform_name))
            self._uniform_locations[uniform_name] = uniform_location
            return uniform_location

    def set_uniform_matrix(self, uniform_name, matrix):
        uniform_location = self.get_uniform_location(uniform_name)
        glUniformMatrix4fv(uniform_location, 1, False, vmathop.matrix_to_ctype(matrix))

    def set_uniform_color(self, uniform_name, color):
        uniform_location = self.get_uniform_location(uniform_name)
        glUniform4f(uniform_location, color.x, color.y, color.z, 1.0)
