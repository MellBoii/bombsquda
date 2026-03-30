""" I hate docstrings. Shove it. """
from __future__ import annotations
import bascenev1 as bs
import bauiv1 as bui
import babase as ba

from bascenev1lib.actor.image_looped import LoopingImageAnimation
from typing import TYPE_CHECKING, override

class ACISession(bs.Session):
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.setactivity(bs.newactivity(ACIActivity))
        self.max_players = 1

class ACIActivity(bs.GameActivity[bs.Player, bs.Team]):
    """Simple activity for rolling credits."""
    name = ''
    description = ''
    suppress_zoomtext = True
    show_controls_guide = False
    allow_pausing = False
    
    @override
    def __init__(self, settings: dict) -> None:
        super().__init__(settings)
        self.bg = None
        self.spaz = None
        self.spinny = None
        self.music = None
        
    @override
    def on_transition_in(self) -> None:
        super().on_transition_in()
        self.bg = LoopingImageAnimation('thefall', frame_count=4, frame_delay=0.05)
        self.bg.node.fill_screen = True
        bright = (1.3, 1.3, 1.3)
        dark = (0.5, 0.5, 0.5)
        bs.animate_array(
            self.bg.node, 
            'color',
            3,
            {
                0.0: dark,
                0.3: dark,
                2.0: bright,
                2.3: bright,
                4.0: dark,
            },
            loop=True,
        )
        self.spaz = LoopingImageAnimation('spaz_fall', frame_count=2, frame_delay=0.07, scale=(150, 150))
        self.spinny = bs.Timer(0.01, self.rotate_spaz, repeat=True)
        spaceout = 50
        speed = 1.0
        self.music = bs.newnode(
            'sound',
            attrs={
                'sound': bs.getsound('music/thefall'),
                'volume': 5,
                'positional': False,
                'music': True,
            }
        )
        bs.animate_array(
            self.spaz.node,
            'position',
            2,
            {
                0.0 * speed: (0, spaceout),
                0.25 * speed: (spaceout * 0.7, spaceout * 0.7),
                0.5 * speed: (spaceout, 0),
                0.75 * speed: (spaceout * 0.7, -spaceout * 0.7),
                1.0 * speed: (0, -spaceout),
                1.25 * speed: (-spaceout * 0.7, -spaceout * 0.7),
                1.5 * speed: (-spaceout, 0),
                1.75 * speed: (-spaceout * 0.7, spaceout * 0.7),
                2.0 * speed: (0, spaceout),
            },
            loop=True,
        )
        self.jointext = bs.newnode(
            'text',
            delegate=self,
            attrs={
                'text': bs.Lstr(resource='joinToContinueText'),
                'position': (0, 160),
                'h_align': 'center',
                'scale': 1.3,
            },
        )
        bs.animate(self.jointext, 'opacity', {4.0: 0, 5.0: 1})
    
    def rotate_spaz(self):
        if self.spaz and self.spaz.node:
            self.spaz.node.rotate += 1
    
    def _intro_done(self):
        bs.screenmessage(bs.Lstr(resource='mellNotDone'))
        bs.getsound('bellLeft').play(1.5)
        bs.timer(1.0, self.session.end)
    
    def animate_out(self):
        bs.animate(self.jointext, 'opacity', {0.0: 1, 0.3: 0})
        bs.animate(self.music, 'volume', {0.0: 5, 4.0: 0})
        bs.animate_array(
            self.spaz.node,
            'position',
            2,
            {
                0.0: (0, 0),
                0.3: (0, 20),
                0.6: (0, 45),
                0.9: (0, 65),
                1.2: (0, 85),
                1.4: (0, 100),
                1.6: (0, 95),
                1.8: (0, 70),
                2.0: (0, 30),
                2.15: (0, -200),
                2.3: (0, -600),
                2.45: (0, -1000),
            },
        )

        bright = (1.3, 1.3, 1.3)
        dark = (0.5, 0.5, 0.5)
        darker = (0.0, 0.0, 0.0)

        bs.animate_array(
            self.bg.node,
            'color',
            3,
            {
                0.0: dark,
                0.4: (0.7, 0.7, 0.7),
                0.8: (1.0, 1.0, 1.0),
                1.2: bright,
                1.6: (1.0, 1.0, 1.0),
                2.0: (0.7, 0.7, 0.7),
                2.5: dark,
                3.0: darker,
            },
        )
        bs.timer(4.8, self._intro_done)
    
    @override
    def on_player_join(self, player: bs.Player) -> None:
        self.animate_out()