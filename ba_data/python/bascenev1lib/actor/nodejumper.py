""" why are we still here... just to suffer... """
import random
import bascenev1 as bs

class ImageJumper:
    
    _active_timers: dict[int, bs.Timer] = {}

    @classmethod
    def jump_image(cls,
                   node: bs.Node,
                   jump_force: float = 340.0,
                   randomness: float = 150.0,
                   fall_speed: float = -420.0):

        if not node:
            return

        node_id = id(node)

        # stop any previous action to the node...
        cls.stop(node)

        velocity = {
            'vx': random.uniform(-randomness, randomness),
            'vy': jump_force
        }

        dt = 1.0 / 60.0

        def tick():
            # kill the node's actions if 
            # they don't exist
            if not node:
                cls.stop_by_id(node_id)
                return

            try:
                # do the physics calculations!
                x, y = node.position

                x += velocity['vx'] * dt
                y += velocity['vy'] * dt
                node.position = (x, y)

                velocity['vy'] += fall_speed * dt
                
                # offscreen? delete ourselves and our timer
                if y < -500:
                    node.delete()
                    cls.stop_by_id(node_id)

            except Exception:
                # any exception? stop regularly.
                cls.stop_by_id(node_id)

        cls._active_timers[node_id] = bs.Timer(dt, tick, repeat=True)

    @classmethod
    def stop(cls, node: bs.Node):
        cls.stop_by_id(id(node))

    @classmethod
    def stop_by_id(cls, node_id: int):
        timer = cls._active_timers.pop(node_id, None)
        if timer:
            timer = None
