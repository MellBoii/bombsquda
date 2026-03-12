"""Some custom spinners :trol:"""
import bauiv1 as bui

class DefaultSpinner:
    """A simple bui.imagewidget but animated. 
    Meant to be used as spinners, like with bui.spinnerwidget."""
    frames = 1
    """float: How many frames. Starting frame is always 0."""
    
    frame_time = 0.3
    """int: Speed."""
    
    prefix = 'spaztest'
    """str: Texture name. Will be interpreted as texturename0, then texturename1, and so on"""
    
    def __init__(
        self, 
        pos: tuple[float, float] = (0, 0),
        scale: tuple[float, float] = (200, 200),
    ):
        self._current_frame = 0
        self.node = bui.imagewidget(
            position=pos,
            size=scale,
            texture=bui.gettexture(f'{self.prefix}{self._current_frame}'),
        )
        # Start the animation timer.
        self._timer = bui.AppTimer(self.frame_time, self._next_frame, repeat=True)

    def _next_frame(self):
        """Advance to the next frame."""
        self._current_frame += 1

        # Wrap around if looping.
        if self._current_frame > self.frames:
            self._current_frame = 0

        tex_name = f"{self.prefix}{self._current_frame}"
        try:
            bui.imagewidget(edit=self.node, texture=bui.gettexture(tex_name))
        except:
            self.die()
    
    def die(self):
        """Kills our timer and our image."""
        self._timer = None
        self.node.delete()

class KookooSpinner(DefaultSpinner):
    frames = 3
    prefix = 'kooku_spin'
    frame_time = 0.2