import bascenev1 as bs
import babase
import babase as ba
import os
import bauiv1 as bui
import time
from .discordrp_handler import RichPresence
import threading
import json
import urllib.request
import _babase
import sys
import traceback
import datetime
import bascenev1 as bs

class Startup():
    # very important stuff that needs to be set on startup
    _last_error_time = None
    _recent_error = False
    ba.app.config['timeserrored'] = 0
    # check if values exist
    global cfg
    cfg = bui.app.config
    # made by temp in the 'bombarmy' discussion in the discord server.
    config = bs.app.config
    conflist = {
    "parryalways": False,
    "richpresence": True,
    "spazfuckedup": False,
    "spazhardmode": False,
    "unlockedmel": False,
    "noisepolution": False,
    "canopencredits": False,
    "dontdomarioman": False,
    "dontshutdown": False,
    "enablemeter": False,
    "gamblingmode": False,
    "playersfirsttime": True,
    "isplayingmusic": False,
    "timesattracted": 1,
    "timeserrored": 0,
    }
    # "setdefault" to create config settings
    # won't affect already existing ones.
    for k,v in conflist.items():
        config.setdefault(k, v)
    # save changes
    cfg['isbombsqudaorsomething'] = None
    config.apply_and_commit()
    try:
        cfg['playersfirsttime']
    except:
        print('incredibly bad fuckin error.')
        print('something went bad in fromgoverhaul\'s startup, and we couldn\t add config stuff')

    if babase.app.classic.platform not in ['android', 'mac']:
        if babase.app.config.get("richpresence", True):
            try:
                babase.apptimer(1.3, RichPresence)
            except Exception as e:
                print(f'Enable to start rich presence: {e}')
    bui.app.config['isplayingmusic'] = False
    bui.app.config['timesattracted'] = 0
    def my_global_exception_hook(exc_type, exc_value, exc_traceback):
        """
        custom ass exception hook
        """
        global _last_error_time, _recent_error

        # Don't shadow SystemExit, KeyboardInterrupt
        # i EXCEPTIONALLY do not know what these mean
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # convert a error to text
        error_text = ''.join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        
        _last_error_time = datetime.datetime.now()
        _recent_error = True
        # Log it somewhere visible
        print(error_text)
        bs.screenmessage(
            f"An error occured:\n{error_text}", 
            color=(1, 0.3, 0.3)
        )
        bui.getsound('error').play()
        bui.getsound('OUUHH').play()
        
        try:
            icon = bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('melIcon'),  # lol
                    'position': (0, 0),   # pos
                    'fill_screen': True,
                    'opacity': 1.0,
                    'absolute_scale': True,
                    'attach': 'center'
                },
            )
            # fade image step by step
            def _fade_step():
                if icon and icon.exists():
                    new_opacity = icon.opacity - 0.05
                    if new_opacity <= 0.0:
                        icon.delete()
                    else:
                        icon.opacity = new_opacity
                        bs.timer(0.03, _fade_step)  # repeat until gone

            # after a bit of delay THEN start fading
            bs.timer(0.1, _fade_step)
        except babase._error.ContextError:
            pass
            
        ba.app.config['timeserrored'] += 1
        def error_reset():
            ba.app.config['timeserrored'] = 0
        bs.timer(3.0, error_reset)
        # stop everything if we get a number exceptions so we dont get flooded
        if ba.app.config['timeserrored'] > 20:
            newnode = bs.newnode(
                'image', 
                attrs={
                    'texture': bs.gettexture('white2'),
                    'attach': 'center',
                    'opacity': 0.5,
                    'fill_screen': True,
                    'color': (0, 0, 1)
                }
            )
            newnode2 = bs.newnode(
                'text',
                attrs={
                    'text': f"Too many errors occured within a certain timeframe.\nMost recent error:\n{error_text}",
                    'h_align': 'left',
                    'v_attach': 'top',
                    'h_attach': 'left',
                    'position': (0, -30),
                    'scale': 0.9,
                    'color': (1, 1, 1),
                    'shadow': 0.7,
                    'flatness': 0.5,
                },
            )
            newnode3 = bs.newnode(
                'text',
                attrs={
                    'text': 'The game will now hang to prevent further errors.\nPlease check your console :^)',
                    'h_align': 'left',
                    'v_attach': 'bottom',
                    'h_attach': 'left',
                    'position': (5, 30),
                    'scale': 0.9,
                    'color': (1, 1, 1),
                    'shadow': 0.7,
                    'flatness': 0.5,
                },
            )
            newnode4 = bs.newnode(
                'image', 
                attrs={
                    'texture': bs.gettexture('error'),
                    'absolute_scale': True,
                    'position': (400, -130),
                    'attach': 'center',
                    'opacity': 1.0,
                    'scale': (550, 550),
                    'color': (1, 1, 1)
                }
            )
            print('Too many errors occured within a certain timeframe.')
            print('The game will now hang to prevent further errors.')
            print('Please check any lines above for bugs :^)')
            bs.setmusic(bs.MusicType.CRASH_HANDLER)
            ba.apptimer(0.1, lambda: time.sleep(9999))
            ba.apptimer(0.1, lambda: time.sleep(9999))

    # Install the hook
    sys.excepthook = my_global_exception_hook




