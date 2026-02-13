""" Custom store """
from __future__ import annotations
import bascenev1 as bs
import bauiv1 as bui
import babase as ba

from typing import TYPE_CHECKING, override

class MellStoreSession(bs.Session):
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.setactivity(bs.newactivity(MellStoreActivity))
		
    @override
    def on_player_request(self, player: bs.SessionPlayer) -> bool:
        # Reject all player requests.
        return False

class MellStoreActivity(bs.GameActivity[bs.Player, bs.Team]):
    """fukcing store."""
    name = ''
    description = ''
    suppress_zoomtext = True
    show_controls_guide = False
    allow_pausing = False
    
    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['CREDITS']
    
    @override
    def __init__(self, settings: dict):
        super().__init__(settings)
        self.allow_emeralds = False
  
    def on_transition_in(self) -> None:
        super().on_transition_in()
    
    def on_begin(self) -> None:
        super().on_begin()
        self.bg = bs.newnode(
            'image', 
            attrs={
                'texture': bs.gettexture('white'),
                'color': (0.1, 0.1, 0.2),
                'fill_screen': True,
                'opacity': 0.7,
            }
        )
        x = -400
        y = 0
        imgscale = 300
        boxXmult = 350
        boxYmult = -100
        self.box = bs.newnode(
            'image', 
            attrs={
                'texture': bs.gettexture('black'),
                'position': (x + imgscale + 15, y - imgscale + 80),
                'scale': (imgscale + boxXmult, imgscale + boxYmult),
                'absolute_scale': True,
                'opacity': 0.5,
            }
        )
        self.char = bs.newnode(
            'image', 
            attrs={
                'texture': bs.gettexture('dialogue/spaz_neutral'),
                'position': (x, y),
                'scale': (imgscale, imgscale),
                'absolute_scale': True,
            }
        )
        self.name = bs.newnode(
            'text',
            attrs={
                'text': 'Spazling',
                'position': (x + 10, y - imgscale + 110),
                'scale': 1.1,
                'color': (0.5, 0.1, 1),
            },
        )
        self.dialog = bs.newnode(
            'text',
            attrs={
                'text': ba.Lstr(resource='dialogTest'),
                'position': (x + 20, y - imgscale + 70),
                'scale': 1.1,
                'color': (0.7, 0.5, 1),
                'maxwidth': boxXmult + imgscale - 100
            },
        )