""" Defines our Credits-Roll sequence. """
from __future__ import annotations
import bascenev1 as bs
import bauiv1 as bui
import babase as ba

from typing import TYPE_CHECKING, override

class CreditsSession(bs.Session):
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.setactivity(bs.newactivity(CreditsActivity))

class CreditsActivity(bs.GameActivity[bs.Player, bs.Team]):
    """Simple activity for rolling credits."""
    name = ''
    description = ''
    default_music = bs.MusicType.CREDITS
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
        self._text_node = None
        self.allow_emeralds = False
        self.length = 220
  
    def on_transition_in(self) -> None:
        super().on_transition_in()
        
        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'
    
    def on_begin(self) -> None:
        super().on_begin()

        self._start_credits()
        bs.timer(self.length + 8, self.leave)
        self.showlogo()
        bs.timer(self.length - 16, self.showlogo2)
        characters = [      
              # Texture   # Char. Name       # Left side?
            ('spazbound',   'Spaz',             True),
            ('susiebound',  'Susie',            False),
            ('krisbound',   'Kris',             True),
            ('noobbound',   'Noob',             False),
            ('mellbound',   'Meliso',           True),
            ('snakebound',  'Snake Shadow',     False),
            ('raybound',    'Rayman',           True),
            ('bowserbound', 'Bowser',           False),
            ('noisebound',  'The Noise',        True),
            ('ralseibound', 'Ralsei',           False),
            ('capbound',    'Orangecap',        True),
            ('knightbound', 'Roaring Knight',   False),
            ('homerbound',  'Homer',            True),
              # Texture   # Char. Name       # Left side?
        ]
        start_time = 17.0
        interval = 12.0
        for tex, name, left in characters:
            bs.timer(start_time, 
                     lambda t=tex, n=name, l=left:
                         self._start_character_scroll(t, n, leftside=l))
            start_time += interval
            
    def _start_character_scroll(
        self, 
        tex: str | None = None, 
        name: str | None = None,
        leftside: bool = False
    ):
        # attrs
        texture = bs.gettexture(tex)
        nametext = name
        x = (
            -530 if leftside
            else 530
        )
        initial_y = -580
        end_y = -initial_y
        time = 35
        # create our node
        node = bs.newnode('image', 
            attrs={
                'texture': texture,
                'position': (x, initial_y), 
                'scale': (250, 250),
                'opacity': 1.0,
                'absolute_scale': True,
                'attach': 'center'
            }
        )
        # create text
        node2 = bs.newnode("text", 
            attrs={
                "text": nametext,
                "position": (x, initial_y),
                "scale": 1.7,
                "h_attach": "center",
                "v_attach": "center",
                "h_align": "center",
                "color": (1, 1, 1),
            }
        )
        
        # create a math node
        # (used to add a bit y offset)
        mathnode = bs.newnode(
            'math',
            owner=node,
            attrs={'input1': (0, 120), 'operation': 'add'},
        )
        node.connectattr('position', mathnode, 'input2')
        mathnode.connectattr('output', node2, 'position')
        # aaanimate!
        bs.animate_array(node, 'position', 2, {
            0.0: (x, initial_y),
            time: (x, end_y)  # scroll up slowly
        })
        bs.timer(time + 1, node.delete)
    
    def showlogo(self):
        # Create image node
        node = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('logo2'),
                'position': (0, 0), 
                'scale': (800, 200),
                'opacity': 1.0,
                'absolute_scale': True,
                'attach': 'center'
            }
        )
        bs.animate_array(node, 'position', 2, {
            5.0: (0, 0),
            30.0: (0, 600) # scroll up slowly
        })
        bs.timer(45.0, node.delete)
        
    def showlogo2(self):
        # Create image node
        node = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('logo2'),
                'position': (0, -500), 
                'scale': (800, 200),
                'opacity': 1.0,
                'absolute_scale': True,
                'attach': 'center'
            }
        )
        bs.animate_array(node, 'position', 2, {
            0.0: (0, -500),
            9.0: (0, 0) # scroll up slowly
        })
        
    def leave(self):
        session = self.session
        bui.getsound('thankforplay').play()
        ba.apptimer(4.5, session.end)

    def _start_credits(self) -> None:
        """Create scrolling credits."""
        self.you = bui.app.plus.get_v1_account_display_string()

        # Create the text node off-screen at the bottom
        self._text_node = bs.newnode("text", attrs={
            "text": bs.Lstr(
                resource='creditsText', 
                subs=[
                    ('${NAME}', self.you)
                ]
            ),
            "position": (0, -500),
            "scale": 1.5,
            "h_attach": "center",
            "v_attach": "center",
            "h_align": "center",
            "color": (1, 1, 1),
            "flatness": 0.5,
            "shadow": 0.5,
            "maxwidth": 800
        })
        TEXT_START = 5.0
        TEXT_END = self.length - 6.0
        bs.animate_array(
            self._text_node,
            "position", 2,  # 2 = number of components (x, y)
            {
                TEXT_START: (0, -500),   # start position
                TEXT_END: (0, 2600)    # end position
            }
        )
    
    @override
    def spawn_player_spaz(
        self,
        player: PlayerT,
        position: Sequence[float] = (0, 0, 0),
        angle: float | None = None,
    ) -> PlayerSpaz:
        return super().spawn_player_spaz(player=player,position=(0, 5, -2))
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(bs.Player)
            self.respawn_player(player)
        else:
            return super().handlemessage(msg)
        return None

