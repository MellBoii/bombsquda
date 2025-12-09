""" Images with looping. waeeww """
import bascenev1 as bs

class LoopingImageAnimation:
    def __init__(
        self,
        prefix: str = "animframe",  # example: animframe1, animframe2, ...
        frame_count: int = 12,
        frame_delay: float = 0.1,   # seconds between frames
        scale: tuple = (300, 300),
        position: tuple = (0, 0),
        loop: bool = True
    ):
        self.prefix = prefix
        self.frame_count = frame_count
        self.frame_delay = frame_delay
        self.loop = loop
        self._current_frame = 1

        # Create the image node.
        self.node = bs.newnode(
            "image",
            attrs={
                "texture": bs.gettexture(f"{self.prefix}{self._current_frame}"),
                "absolute_scale": True,
                "scale": scale,
                "position": position,
                "opacity": 1.0,
            },
        )

        # Start the animation timer.
        self._timer = bs.Timer(frame_delay, self._next_frame, repeat=True)

    def _next_frame(self):
        """Advance to the next frame."""
        if not self.node:
            return

        self._current_frame += 1

        # Wrap around if looping.
        if self._current_frame > self.frame_count:
            if self.loop:
                self._current_frame = 1
            else:
                # Stop animation if not looping.
                self._timer = None
                return

        tex_name = f"{self.prefix}{self._current_frame}"
        try:
            self.node.texture = bs.gettexture(tex_name)
        except Exception as e:
            print(f"[LoopingImageAnimation] Got error {e} while changing texture to {tex_name}")
            self._timer = None
    def die(self):
        if not self.node:
            print('[LoopingImageAnimation] Got non existant node while trying to kill animation')
            return
        self._timer = None
        self.node.delete()