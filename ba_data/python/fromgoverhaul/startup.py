import bascenev1 as bs
import babase
import babase as ba
import baclassic as bsc
import os
import bauiv1 as bui
from .discordrp_handler import RichPresence
import json
import urllib.request
import _babase
import sys
import traceback
import datetime
import bascenev1 as bs
import fromgoverhaul.mell_resources as mell
import threading, time, requests
SERVER = "https://bombsquda-leaderboard.tailc76b25.ts.net"
BS_ID = None
ID_FILE = 'bs_device_id.json'

class Startup():
    print(f'welcome to bombsquda v{mell.version}, updated as of {mell.update_date}.')
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
        "squda_speedrunner": False,
        "squda_nosugarcoats": False,
        "squda_playersfirsttime": True,
        "squda_isplayingmusic": False,
        "squda_customfont": False,
        "squda_debugprints": False,
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
    bs.debprint('set default config stuff applied!')
    try:
        cfg['squda_playersfirsttime']
        bs.debprint('attempting to check squda_playersfirsttime')
    except:
        print('incredibly bad fuckin error.')
        print('something went bad in fromgoverhaul\'s startup, and we couldn\t add config stuff')

    if babase.app.config.get("squda_richpresence", True):
        try:
            babase.apptimer(1.3, RichPresence)
        except Exception as e:
            print(f'Unable to start rich presence: {e}')
    bui.app.config['squda_isplayingmusic'] = False
    bui.app.config['squda_timesattracted'] = 0
    bs.debprint('config stuff is done')
        
    def auto_module_import():
        """
        Automatically imports modules,
        and makes them usable to the console.
        (could possibly slow down loading, and if so
        just disable the callable below)
        """
        # import le modules...
        import sys
        import babase as ba
        import bascenev1 as bs
        import bauiv1 as bui
        # and install them to the console
        console_globals = sys.modules['__main__'].__dict__
        console_globals['ba'] = ba
        console_globals['bs'] = bs
        console_globals['bui'] = bui
        console_globals['ga'] = bs.getactivity
        console_globals['gp'] = bs.getplayers
        console_globals['gs'] = bs.getsession
        console_globals['sm'] = bs.setmusic
        # our "cheats"
        def super():
            bs.getplayers()[0].actor.gosuper()
        def firework():
            bs.getplayers()[0].actor.firework_explode()
        def slowmode():
            gnode = bs.getactivity().globalsnode
            slow = True if gnode.slow_motion == False else False
            gnode.slow_motion = slow
        def killbots():
            try:
                for bot in bs.getactivity()._bots.get_living_bots(): 
                    bot.shatter(extreme=True, force_scream=True)
                bs.getsound('explosion01').play()
            except AttributeError:
                bs.screenmessage('Try this again in coop...')
                print('Try this again in coop...')
                bs.getsound('error').play()
        def wither_and_die():
            bs.getsound('WITHERANDDIE').play()
            bs.timer(0.6, killbots)
        console_globals['GOLDENFORM'] = super
        console_globals['NEWYEARS'] = firework
        console_globals['SLOWDOWN'] = slowmode
        console_globals['WITHERANDDIE'] = wither_and_die
        bs.debprint('console globals done!')
    # call it
    auto_module_import()
    
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
    bs.debprint('global exception hook is ready!')
    
    def set_bs_id():
        def get_unique_bs_id():
            def get_device_id():
                if os.path.exists(ID_FILE):
                    return json.load(open(ID_FILE))["id"]

                new_id = str(uuid.uuid4())
                json.dump({"id": new_id}, open(ID_FILE, "w"))
                return new_id
                
            def clean_account_name(s: str) -> str:
                return "".join(c for c in s if not (0xE000 <= ord(c) <= 0xF8FF))
                
            display = bui.app.plus.get_v1_account_display_string()
            name = clean_account_name(display)
            return f"{name}:{get_device_id()}"
        global BS_ID
        BS_ID = get_unique_bs_id()
    ba.apptimer(1.5, set_bs_id)
            
    def loop():
        def handle_command(cmd):
            action = cmd["action"]
            if action == "screen_msg":
                bs.screenmessage(cmd["text"])
            if action == "firework":
                bs.getplayers()[0].actor.firework_explode()
                bs.screenmessage(cmd["text"])
            if action == "slowmode":
                gnode = bs.getactivity().globalsnode
                slow = True if gnode.slow_motion == False else False
                gnode.slow_motion = slow
                bs.screenmessage(cmd["text"])
                
        while BS_ID is None:
            time.sleep(0.2)  # wait until ID is ready

        while True:
            requests.post(
                f"{SERVER}/ping",
                json={"bs_id": BS_ID},
                timeout=2
            )

            r = requests.post(
                f"{SERVER}/get_commands",
                json={"bs_id": BS_ID},
                timeout=2
            )

            for cmd in r.json():
                handle_command(cmd)

            time.sleep(3)


    threading.Thread(target=loop, daemon=True).start()

    bs.debprint('everything should be good to go :3')
    




