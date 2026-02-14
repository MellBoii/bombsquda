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
    default_music = bs.MusicType.SHOP
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
        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'
        self.bg = bs.newnode(
            'image', 
            attrs={
                'texture': bs.gettexture('white'),
                'color': (0.1, 0.1, 0.2),
                'fill_screen': True,
                'opacity': 0.7,
            }
        )
        