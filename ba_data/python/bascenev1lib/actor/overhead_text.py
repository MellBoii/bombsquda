"""Overhead text manager for announcing things and such"""
import bascenev1 as bs
import babase as ba
from typing import Sequence, Union

def estimate_text_width(
    text: str | ba.Lstr,
    *,
    scale: float = 1.0,
) -> float:
    if type(text) is ba.Lstr:
        return len(text.evaluate()) * scale
    else:
        return len(text) * scale
    return None

class OverheadText:
    """
    A text that can appear on the top of the screen.
    When it initiates, it'll fade in a background and then soon
    makes the text that scrolls in. The speed attribute controls how fast
    the texts scrolls through, and text is what it'll show. Accepts either ba.Lstr or strings.
    """
    def __init__(
            self, 
            text: str | ba.Lstr, 
            speed: int = 240.0,
            color: Sequence[float] = (0, 0, 0),
            sound: str = 'elevator_ding',
    ):
        self.scale = 1.1
        self.fadeTime = 0.6
        self.text = text
        self.speed = speed
        self._delete_x = None
        self.animateTimer = bs.Timer(self.fadeTime + 0.4, lambda: self.animate(speed=self.speed))
        self.checkTimer = None
        base_y = 30
        base_node_y = 45
        spacing = 50
        activity = bs.getactivity()
        if not hasattr(activity, 'overheads'):
            bs.getactivity().overheads = {}
        overheads = activity.overheads
        self._slot = self._get_free_slot(overheads)
        overheads[self._slot] = self
        bgy = base_y + (self._slot * spacing)
        nodey = base_node_y + (self._slot * spacing)
        self.bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('white'),
                'scale': (999999, 50),
                'color': color,
                'position': (0, -bgy),
                'opacity': 0.0,
                'attach': 'topCenter',
            },
        )
        self.node = bs.newnode(
            'text',
            attrs={
                'text': text,
                'scale': self.scale,
                'position': (99999, -nodey),
                'v_attach': 'top',
                'h_align': 'left',
            },
        )
        bs.animate(
            self.bg,
            'opacity',
            {
                0.0: 0.0,
                self.fadeTime: 0.5,
            }
        )
        bs.getsound(sound).play()
        
    def _get_free_slot(self, overheads: dict) -> int:
        slot = 0
        while slot in overheads:
            slot += 1
        return slot
        
    def _check_position(self):
        if not self.node:
            return

        x = self.node.position[0]
        if x <= self._delete_x + 1:
            self._check_timer = None
            self.stop()

    def animate(self, speed: float):
        width = estimate_text_width(self.text, scale=self.scale)

        start_x = 800
        end_x = -1300 - width * 8
        self._delete_x = end_x

        pos_y = self.node.position[1]

        bs.animate_array(
            self.node,
            'position',
            2,
            {
                0.0: (start_x, pos_y),
                (start_x - self._delete_x) / speed: (self._delete_x, pos_y),
            },
        )

        self.checkTimer = bs.Timer(
            0.05,
            self._check_position,
            repeat=True,
        )
        
    def stop(self):
        self.node.delete()
        if hasattr(bs.getactivity(), 'overheads'):
            bs.getactivity().overheads.pop(self._slot, None)
        bs.animate(
            self.bg,
            'opacity',
            {
                0.0: 0.5,
                self.fadeTime: 0.0,
            }
        )
        bs.timer(self.fadeTime, self.bg.delete)