"""Module for the Intro class"""
import bascenev1 as bs
from bascenev1lib.intros.messages import (
    IntroStartedMessage, 
    IntroStoppedMessage
)
from typing import override

intro_list = []

PATH = 'intro_assets/'
def register(cls):
    intro_list.append(cls)
    return cls

class Intro:
    def __init__(self):
        self.active: bool = False
        bs.timer(3.3, self.start)
    
    def start(self):
        """Called when the intro should
        start playing itself."""
        bs.getactivity().handlemessage(
            IntroStartedMessage()
        )
        self.active = True
    
    def stop(self, tell_activity: bool = True):
        """Called when the intro should
        stop everything, like timers, and stop."""
        if tell_activity:
            bs.getactivity().handlemessage(
                IntroStoppedMessage()
            )
        self.active = False

@register
class SegaIntro(Intro):
    @override
    def start(self):
        from bascenev1lib.actor.image_looped import LoopingImageAnimation
        from bascenev1lib.actor.nodejumper import ImageJumper
        self.bg = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'fill_screen': True,
                'texture': bs.gettexture('white2'),
            },
        )
        offX = 1000
        image = LoopingImageAnimation(
            prefix=f'{PATH}spaz_run',
            frame_count=4,
            frame_delay=0.01,
            scale=(200, 200),
            position=(offX, 0),
        )
        image2 = LoopingImageAnimation(
            prefix=f'{PATH}spaz_run_flipped',
            frame_count=4,
            frame_delay=0.01,
            scale=(200, 200),
            position=(offX, 0),
        )
        image3 = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture(f'{PATH}spaz_jump'),
                'position': (-offX, 0), 
                'scale': (200, 200),
                'opacity': 1.0,
            }
        )
        sc = 1.4
        logo_image = bs.newnode('image', 
            attrs={
                'texture': bs.gettexture('mell_logo'),
                'position': (offX, 0), 
                'scale': (512 * sc, 256 * sc),
                'opacity': 1.0,
            }
        )
        
        def animate1():
            bs.animate_array(
                image.node, 
                'position', 
                2,
                {
                    0: (offX, 0),
                    1: (-offX, 0),
                }
            )
            bs.getsound('spinzoom').play()
        def animate2():
            bs.animate_array(
                image2.node, 
                'position', 
                2,
                {
                    0: (-offX, 0),
                    1: (offX, 0),
                }
            )
            bs.getsound('spinzoom').play()
        
        def animate3():
            bs.animate_array(
                image.node, 
                'position', 
                2,
                {
                    0: (offX, 0),
                    1: (-offX, 0),
                }
            )
            bs.animate_array(
                logo_image, 
                'position', 
                2,
                {
                    0: (offX, 0),
                    0.6: (0, 0),
                }
            )
            bs.getsound('spinzoom').play()
        def animate4():
            ImageJumper.jump_to_position(
                image3, 
                target_pos=(-370, 0),
                time=1.0,
            )
            bs.getsound('smb1_jump').play()
        def animate5():
            image3.texture = bs.gettexture(f'{PATH}spaz_peace')
            bs.getsound('voicelines/spaz/jump01').play()
            bs.timer(4, self.stop)
        animate1()
        bs.timer(1, animate2)
        bs.timer(2, animate3)
        bs.timer(4, animate4)
        bs.timer(5, animate5)

