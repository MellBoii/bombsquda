""" why are we still here... just to suffer... """
import random
import bascenev1 as bs
import math

class ImageJumper:
    
    _active_timers: dict[int, bs.Timer] = {}

    @classmethod
    def stop(cls, node: bs.Node):
        cls.stop_by_id(id(node))

    @classmethod
    def stop_by_id(cls, node_id: int):
        timer = cls._active_timers.pop(node_id, None)
        if timer:
            timer = None

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
    def jump_to_position(
        cls,
        node: bs.Node,
        target_pos: tuple[float, float],
        time: float = 0.65,
        height: float = 220.0
    ):
        """
        Jump to target_pos in EXACTLY `time` seconds.

        height = arc height above the higher of start/end.
        """

        if not node:
            return

        node_id = id(node)
        cls.stop(node)

        x0, y0 = node.position
        x1, y1 = target_pos

        dt = 1.0 / 60.0
        total_time = max(0.05, time)

        # Horizontal speed needed
        vx = (x1 - x0) / total_time

        # Choose arc peak
        peak_y = max(y0, y1) + height

        # Solve gravity + vy so:
        # y(total_time) = y1
        # peak happens midway nicely

        # time to peak = total_time / 2
        t_up = total_time / 2.0

        # From v = 0 at peak:
        # 0 = vy + g*t_up
        # => vy = -g*t_up

        # From peak height:
        # peak_y = y0 + vy*t_up + 0.5*g*t_up²

        # Substitute vy:
        # peak_y = y0 -0.5*g*t_up²
        # => g = -2*(peak_y-y0)/t_up²

        g = -2.0 * (peak_y - y0) / (t_up * t_up)
        vy = -g * t_up

        elapsed = 0.0
        px = x0
        py = y0

        def tick():
            nonlocal elapsed, px, py, vy

            if not node:
                cls.stop_by_id(node_id)
                return

            try:
                elapsed += dt

                px += vx * dt
                py += vy * dt
                vy += g * dt

                if elapsed >= total_time:
                    node.position = (x1, y1)
                    cls.stop_by_id(node_id)
                    return

                node.position = (px, py)

            except Exception:
                cls.stop_by_id(node_id)

        cls._active_timers[node_id] = bs.Timer(dt, tick, repeat=True)
