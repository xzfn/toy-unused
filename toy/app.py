"""
Main.
"""

import logging
logger = logging.getLogger(__name__)

import pyglet
from pyglet.window import key
from pyglet.gl import *

import toy
import toy.camera
import toy.batching
import toy.draw


class IGame(object):
    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_mouse_release(self, x, y, button, modifiers):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_key_press(self, symbol, modifiers):
        pass

    def on_key_release(self, symbol, modifiers):
        pass

    def update(self, dt):
        pass

    def draw(self):
        pass


class App(object):
    def __init__(self, game):
        config = pyglet.gl.Config(major_version=4, minor_version=6, alpha_size=8, forward_compatible=True)
        self.game = game
        self.window = pyglet.window.Window(resizable=True, config=config)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)

        self.window.push_handlers(on_key_press=self.on_key_press)
        self.window.push_handlers(on_key_release=self.on_key_release)
        self.window.push_handlers(on_resize=self.on_resize)
        self.window.push_handlers(on_mouse_press=self.on_mouse_press)
        self.window.push_handlers(on_mouse_release=self.on_mouse_release)
        self.window.push_handlers(on_mouse_drag=self.on_mouse_drag)
        self.window.push_handlers(on_draw=self.on_draw)
        self.window.push_handlers(on_mouse_scroll=self.on_mouse_scroll)

        self.camera = toy.camera.Camera()
        self.freeview = toy.camera.FreeviewCameraController(self, self.camera)
        self.batch = toy.batching.PrimitiveBatch(self, self.camera)
        self.text_batch = toy.batching.TextBatch(self, self.camera)
        self.draw = toy.draw.Draw(self.batch)

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        self.camera.set_new_size(width, height)
        return True

    def on_key_press(self, symbol, modifiers):
        self.freeview.on_key_press(symbol, modifiers)
        self.game.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self.game.on_key_release(symbol, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        self.game.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        self.game.on_mouse_release(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.game.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
        self.freeview.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.freeview.on_mouse_scroll(x, y, scroll_x, scroll_y)

    def on_draw(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.game.draw()
        self.batch.draw()
        self.text_batch.draw()

    def on_update(self, dt):
        self.freeview.update(dt)
        self.game.update(dt)

    def run(self):
        logger.info('Init')
        self.game.init(self)
        logger.info('Run')
        pyglet.clock.schedule(self.on_update)
        pyglet.app.run()
