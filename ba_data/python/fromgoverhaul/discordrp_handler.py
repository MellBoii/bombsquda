"""
discordrp_handler.py
This module provides integration with Discord Rich Presence for the BombSquad game,
allowing the game to update the player's Discord status based on their in-game activity.
Classes:
    RichPresence:
        Handles the connection to Discord Rich Presence and updates the player's status
        according to the current game state (menu, gameplay, online, replay, credits, etc.).
        Attributes:
            presence (Presence): The Discord Presence object for communication.
            mode (str): The current mode/state of the game (e.g., 'menu', 'gameplay').
            _r (str): Internal label for Rich Presence.
            starting_time (int): Timestamp when the current mode started.
            map (str or None): The current map name.
            last_mode (str or None): The previous mode/state.
        Methods:
            __init__():
                Initializes the RichPresence object and starts the update timer.
            update():
                Updates the Discord Rich Presence status based on the current game state.
                Handles different modes such as menu, gameplay, online, replay, credits, etc.
                Sets appropriate details, images, timestamps, and party information.
            check():
                Checks the current game state and updates the mode accordingly.
                Resets the starting time when the mode changes.
                Schedules the next update.
Globals:
    portal_id (str): The Discord application ID for Rich Presence.
    maps (dict): A mapping from in-game map names to their corresponding image keys for Discord.
"""

import time
from fromgoverhaul.discordrp_folder import Presence
import babase
import bascenev1 as bs
from bascenev1lib.mainmenu import MainMenuActivity
from bascenev1._activitytypes import JoinActivity
from bascenev1._gameactivity import GameActivity
from bascenev1lib.creditsroll import CreditsActivity
from bascenev1lib.game.thefinale import TheFinaleGame
from bascenev1lib.game.onslaught import Preset
import fromgoverhaul.mell_resources as melly
import bauiv1 as bui

portal_id = "1419400467707859136"

maps: dict = {
    'Hockey Stadium': 'hockey_stadium',
    'Football Stadium': 'football_stadium',
    'Bridgit': 'bridgit',
    'Big G': 'big_g',
    'Roundabout': 'roundabout',
    'Monkey Face': 'monkey_face',
    'Zigzag': 'zigzag',
    'The Pad': 'the_pad',
    'Doom Shroom': 'doom_shroom',
    'Lake Frigid': 'lake_fridget',
    'Tip Top': 'tiptop',
    'Crag Castle': 'crag_castle',
    'Tower D': 'tower_d',
    'Happy Thoughts': 'happy_thoughts',
    'Step Right Up': 'step_right_up',
    'Courtyard': 'courtyard',
    'Rampage': 'rampage',
    'Nintendo DS': 'nintendoDS',
    'SNES Battle Course 1': 'snes',
}

class RichPresence:
        def __init__(self):           
            self.presence = Presence(portal_id)
            self.mode = 'menu'
            self._r = "rpc"
            self.starting_time = int(time.time())
            self.map = None
            self.last_mode = None
            babase.apptimer(1, self.update)
        def update(self):
            babase.apptimer(0.1, self.check)
            try:
                try:
                    sesssion = (
                    'FFA'
                    if isinstance(bs.get_foreground_host_session(), bs.FreeForAllSession) else 
                    'Co-op'
                    if isinstance(bs.get_foreground_host_session(), bs.CoopSession) else
                    'Teams'
                    if isinstance(bs.get_foreground_host_session(), bs.DualTeamSession) else
                    None
                )
                except:
                    sesssion = None
            
                try:
                    sesssion_image = (
                    'ffa'
                    if isinstance(bs.get_foreground_host_session(), bs.FreeForAllSession) else 
                    'coop'
                    if isinstance(bs.get_foreground_host_session(), bs.CoopSession) else
                    'teams'
                    if isinstance(bs.get_foreground_host_session(), bs.DualTeamSession) else
                    None
                    )
                except:
                    sesssion_image = None


                if self.mode == 'menu':
                    lstr = babase.Lstr(resource=f'{babase.app.ui_v1.get_main_window()._r}.rpcText')
                    self.presence.set(
                    {  
                        
                        "details": 'l👀king around the menu..',
                        "assets": {
                            "large_image": "logo",
                            "large_text": f"BombSquda v{melly.version}\nlinebreak",
                        },
                        "state": lstr.evaluate(),
                        "timestamps": {"start": self.starting_time},
                    }
                )
                    
                    
                if self.mode == 'menu_idle':
                    self.presence.set(
                    {  
                        
                        "details": 'afk in the menu..',
                        "assets": {
                            "large_image": "logo",
                            "large_text": f"BombSquda v{melly.version}\nlinebreak",
                        },
                        "timestamps": {"start": self.starting_time},
                    }
                )
            
                
                elif self.mode == 'gameplay':
                    try:
                        map_image = maps[self.map]
                    except:
                        map_image = 'unkmap'

                    self.presence.set(
                    {  
                        "details": 
                        'playin ' + bs.get_foreground_host_activity().name
                        if not isinstance(bs.get_foreground_host_session(), bs.CoopSession)
                        else(
                            f"SCORE: {bs.get_foreground_host_activity()._score} RANK: {bs.get_foreground_host_activity().ultrameter._rank}"
                        ),
                        "state": 'Party',
                        "assets": {
                            "large_image": map_image,
                            "large_text": self.map,
                            "small_image": sesssion_image,
                            "small_text": sesssion + (
                                (f' ({bs.get_foreground_host_activity().name})')
                                if isinstance(bs.get_foreground_host_session(), bs.CoopSession) else ""
                            ),
                        },
                        "timestamps": {"start":  self.starting_time},
                        "party": {
                            "id": "00",
                            "size": (
                                    max(1, len(bs.get_foreground_host_activity().players)),
                                    bs.get_public_party_max_size()
                                ) if self.mode != 'online' else
                                max(1, len([p for p in bs.get_game_roster()])),
                        },
                        
                    }
                )

                elif self.mode == 'lobby':
                    self.presence.set(
                    {  
                        "details": 'selecting characters',
                        "state": 'Party',
                        "assets": {
                            "large_text": 'The Lobby',
                            "small_image": sesssion_image,
                            "small_text": sesssion,
                        },
                        "timestamps": {"start": self.starting_time},
                        "party": {
                            "id": "00",
                            "size": (
                                    max(1, len([p for p in bs.get_game_roster()])),
                                    bs.get_public_party_max_size()
                                ) if self.mode != 'online' else
                                max(1, len([p for p in bs.get_game_roster()])),
                        },
                        
                    }
                )
            
                elif self.mode == 'online':
                    try:
                        name = bs.get_connection_to_host_info_2().name
                    except:
                        name = 'a Party'
                    
                    if not name:
                        name = 'a Party'

                    self.presence.set(
                        {  
                        "details": f'playin online in {name}',
                        "state": 'Party',
                        "assets": {
                            "large_image": 'online',
                            "large_text": 'Playing Online',
                        },
                        "timestamps": {"start": self.starting_time},
                        "party": {
                            "id": "00",
                            "size": (max(1, len([p for p in bs.get_game_roster()])), 8),                    
                        },
                        
                        }
                    )
                elif self.mode == 'replay':
                    
                    self.presence.set(
                        {  
                        "details": 
                            'watching a replay',
                        "state": 'Party',
                        "assets": {
                            "large_image": 'replay',
                            "large_text": 'replay',
                        },
                        "timestamps": {"start": self.starting_time},
                        "party": {
                            "id": "00",
                            "size": (max(1, len([p for p in bs.get_game_roster()])), 8),                    
                        },
                        
                        }
                    )
                elif self.mode == 'credits':
                    
                    self.presence.set(
                        {  
                        "details": 
                            'watching the credits',
                        "assets": {
                            "small_image": 'replay'
                        },
                        "timestamps": {"start": self.starting_time},
                        }
                    )
                    
            except Exception as e:
                # comment this out for now.
                bs.debprint(f'Error updating rich presence. ({e})')
                pass
        
        def check(self):
            try:
                map_name = bs.get_foreground_host_activity().map.name
            except:
                map_name = False
            
            if map_name:
               self.map = map_name
            
            if isinstance(bs.get_foreground_host_activity(), JoinActivity):
                self.mode = 'lobby'
                self.last_mode = 'lobby'
                self.starting_time = int(time.time())  
            elif isinstance(bs.get_foreground_host_activity(), GameActivity):
                self.mode = 'gameplay'
                self.last_mode = 'gameplay'
                self.starting_time = int(time.time())
            elif bui.get_input_idle_time() >= 30 and self.mode in (
                'menu'
            ):
                self.mode = 'menu_idle'
            elif bui.get_input_idle_time() <= 30 and self.mode in (
                'menu_idle'
            ):
                self.mode = 'menu'
            elif bs.get_connection_to_host_info_2() and self.last_mode != 'online':
                self.mode = 'online'
                self.starting_time = int(time.time())
                self.last_mode = 'online'

            elif (bs.is_in_replay() and 
                self.last_mode != 'replay'
            ):
                self.mode = 'replay'
                self.last_mode = 'replay'
                self.starting_time = int(time.time())  
            elif isinstance(bs.get_foreground_host_activity(), MainMenuActivity):
                self.mode = 'menu'
                self.last_mode = 'menu'
                self.starting_time = int(time.time())               
            elif isinstance(bs.get_foreground_host_activity(), CreditsActivity):
                self.mode = 'credits'
                self.last_mode = 'credits'
                self.starting_time = int(time.time())      
            
            babase.apptimer(0.25, self.update)


