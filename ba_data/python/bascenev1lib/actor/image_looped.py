""" Images with looping. waeeww """
import bascenev1 as bs

class LoopingImageAnimation:
    def __init__(
        self,
        prefix: str = "animframe",
        cmprefix: str | None = None,
        frame_count: int = 12,
        frame_delay: float = 0.1,
        scale: tuple = (300, 300),
        position: tuple = (0, 0),
        loop: bool = True,
        attach: str = "center",
        front: bool = False,
    ):
        self.prefix = prefix
        self.cmprefix = cmprefix
        self.frame_count = frame_count
        self.frame_delay = frame_delay
        self.loop = loop
        self._current_frame = 1
        if self.cmprefix:
            tint_texture = bs.gettexture(f"{self.cmprefix}{self._current_frame}")
        else:
            tint_texture = None

        # Create the image node.
        self.node = bs.newnode(
            "image",
            attrs={
                "texture": bs.gettexture(f"{self.prefix}{self._current_frame}"),
                "tint_texture": tint_texture,
                "absolute_scale": True,
                "scale": scale,
                "position": position,
                "opacity": 1.0,
                "attach": attach,
                "front": front,
            },
        )

        # Start the animation timer.
        self._timer = bs.Timer(self.frame_delay, self._next_frame, repeat=True)

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
        if self.cmprefix:
            ttex_name = f"{self.cmprefix}{self._current_frame}"
        try:
            self.node.texture = bs.gettexture(tex_name)
            if self.cmprefix:
                self.node.tint_texture = bs.gettexture(ttex_name)
            self._timer = bs.Timer(self.frame_delay, self._next_frame, repeat=True)
        except Exception as e:
            print(f"[LoopingImageAnimation] Got error {e} while changing texture to {tex_name}")
            self._timer = None
            
    def die(self):
        if not self.node:
            print('[LoopingImageAnimation] Got non existant node while trying to kill animation')
            return
        self._timer = None
        self.node.delete()