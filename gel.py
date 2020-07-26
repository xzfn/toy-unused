from vmath import Vector


class Actor(object):
    def __init__(self, world, actor_id, param):
        self.world = world
        self.actor_id = actor_id
        self._position = Vector()

        if 'position' in param:
            self._position = param['position']

    def update(self, delta_time):
        pass

    def on_destroy(self):
        pass

    def get_position(self):
        return self._position.copy()

    def set_position(self, position):
        self._position = position.copy()


class ActorManager(object):
    def __init__(self, world):
        self.world = world
        self._actors = {}
        self._destroyed_actor_ids = []
        self._incremental_id = 0

    def create_actor(self, actor_class, param=None):
        if param is None:
            param = {}
        self._incremental_id += 1
        actor_id = self._incremental_id
        actor = actor_class(self.world, actor_id, param)
        self._actors[actor_id] = actor
        return actor

    def destroy_actor(self, actor_id):
        self._destroyed_actor_ids.append(actor_id)

    def get_actor(self, actor_id):
        return self._actors.get(actor_id)

    def get_actors(self):
        return list(self._actors.values())

    def update(self, delta_time):
        for actor in list(self._actors.values()):
            actor.update(delta_time)

        destroyed_actor_ids = self._destroyed_actor_ids.copy()
        self._destroyed_actor_ids.clear()
        for actor_id in destroyed_actor_ids:
            actor = self._actors.get(actor_id)
            if actor:
                actor.on_destroy()
                del self._actors[actor_id]


class InputManager(object):
    def __init__(self, world):
        self._key_states = {}
        self._key_downs = set()
        self._key_ups = set()

    def get_key(self, key):
        return self._key_states.get(key, False)

    def get_key_down(self, key):
        return key in self._key_downs

    def get_key_up(self, key):
        return key in self._key_ups

    def process_key_down(self, key):
        self._key_states[key] = True
        self._key_downs.add(key)

    def process_key_up(self, key):
        self._key_states[key] = False
        self._key_ups.add(key)

    def update(self, delta_time):
        self._key_downs.clear()
        self._key_ups.clear()


class TimeManager(object):
    def __init__(self, world):
        self.world = world

    def update(self, delta_time):
        pass


class World(object):
    def __init__(self, game):
        self.game = game
        self.actor_manager = ActorManager(self)
        self.input_manager = InputManager(self)
        self.time_manager = TimeManager(self)

    def update(self, delta_time):
        self.actor_manager.update(delta_time)
        self.input_manager.update(delta_time)
        self.time_manager.update(delta_time)
