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
    "squda_parryalways": False,
    "squda_richpresence": False,
    "squda_spazfuckedup": False,
    "squda_spazhardmode": False,
    "squda_unlockedmel": False,
    "squda_noisepolution": False,
    "squda_canopencredits": False,
    "squda_dontdomarioman": False,
    "squda_dontshutdown": False,
    "squda_enablemeter": False,
    "squda_gamblingmode": False,
    "squda_nosugarcoats": False,
    "squda_playersfirsttime": True,
    "squda_isplayingmusic": False,
    "squda_customfont": False,
    "squda_timesattracted": 1,
    "squda_timeserrored": 0,
    "squda_parrytype": 2,
    }
    # "setdefault" to create config settings
    # won't affect already existing ones.
    for k,v in conflist.items():
        config.setdefault(k, v)
    # save changes
    cfg['isbombsqudaorsomething'] = None
    config.apply_and_commit()
    try:
        cfg['squda_playersfirsttime']
    except:
        print('incredibly bad fuckin error.')
        print('something went bad in fromgoverhaul\'s startup, and we couldn\t add config stuff')

    if babase.app.classic.platform not in ['android', 'mac']:
        if babase.app.config.get("squda_richpresence", True):
            try:
                babase.apptimer(1.3, RichPresence)
            except Exception as e:
                print(f'Unable to start rich presence: {e}')
    bui.app.config['squda_isplayingmusic'] = False
    bui.app.config['squda_timesattracted'] = 0
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
            color=(1, 0, 0)
        )
        bui.getsound('error').play()
        
    # Install the hook
    sys.excepthook = my_global_exception_hook




