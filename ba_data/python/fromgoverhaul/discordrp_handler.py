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
    'Lake Frigid': 'lake_fridgid', 
    'Tip Top': 'tiptop', 
    'Crag Castle': 'crag_castle',
    'Tower D': 'tower_d', 
    'Happy Thoughts': 'happy_thoughts', 
    'Step Right Up': 'step_right_up', 
    'Courtyard': 'courtyard', 
    'Rampage': 'rampage', 
    'Nintendo DS': 'nintendoDS', 
    'SNES Battle Course 1': 'snes', 
    'Space': 'space', 
}

class RichPresence:
        def __init__(self):           
            self.presence = Presence(portal_id)
            self.mode = 'menu'
            self._r = 'discordRPC'
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
                        
                        "details": bs.Lstr(resource=f'{self._r}.menuText').evaluate(),
                        "assets": {
                            "large_image": "logo",
                            "large_text": f"BombSquda v{melly.version} (In-dev)",
                        },
                        "state": lstr.evaluate(),
                        "timestamps": {"start": self.starting_time},
                    }
                )
                    
                    
                if self.mode == 'menu_idle':
                    self.presence.set(
                    {  
                        
                        "details": bs.Lstr(resource=f'{self._r}.menuAFKText').evaluate(),
                        "assets": {
                            "large_image": "logo",
                            "large_text": f"BombSquda v{melly.version} (In-dev)",
                        },
                        "timestamps": {"start": self.starting_time},
                    }
                )
            
                
                elif self.mode == 'gameplay':
                    try:
                        map_image = maps[self.map]
                    except:
                        map_image = 'unkmap'
                    players = bs.get_foreground_host_activity().players
                    count = len(players)
                    session = bs.get_foreground_host_session()
                    activity = bs.get_foreground_host_activity()
                    if count > 1:
                        party = None
                        playerformatted = []
                        for player in players:
                            playerformatted.append(f'{player.getname()} ({player.character})')
                        if not playerformatted:
                            playerformatted = [bs.Lstr(resource=f'{self._r}.noOne').evaluate()]
                        plist = ", ".join(playerformatted)
                        state = bs.Lstr(
                            resource=f'{self._r}.coopMultiplayerText',
                            subs=[
                                ('${LIST}', plist),
                            ]
                        ).evaluate()
                    else:
                        party = None
                        try:
                            name = players[0].getname()
                        except IndexError:
                            name = bs.Lstr(resource=f'{self._r}.noOne').evaluate()
                        try:
                            character = players[0].character
                        except IndexError:
                            character = bs.Lstr(resource=f'{self._r}.noPlayers').evaluate()
                        state = bs.Lstr(
                            resource=f'{self._r}.coopSingleplayerText',
                            subs=[
                                ('${NAME}', name),
                                ('${CHAR}', character),
                            ]
                        ).evaluate()
                    if not isinstance(session, bs.CoopSession):
                        state = bs.Lstr(resource='partyText').evaluate()
                        party = {
                            "id": "00",
                            "size": ( max(0, len( activity.players) ), 8 ),                    
                        }
                    small_text2 = f'({session.campaign_level_name})' if isinstance(session, bs.CoopSession) else ''
                    if not sesssion:
                        sesssion = ''
                    
                    if isinstance(session, bs.CoopSession):
                        score = getattr(activity, '_score', None)
                        meter = getattr(activity, 'ultrameter', None)
                        rank = getattr(meter, '_rank', None)
                        pltext = bs.Lstr(
                            resource=f'{self._r}.coopScoreRankText',
                            subs=[
                                ('${SCORE}', str(score)),
                                ('${RANK}', str(rank)),
                            ]
                        ).evaluate()
                    else:
                        pltext = bs.Lstr(
                            resource=f'{self._r}.activityPlaying',
                            subs=[
                                ('${ACTIVITY}', activity.name),
                            ]
                        ).evaluate()
                        
                    self.presence.set(
                        {  
                            "details": pltext,
                            "state": state,
                            "assets": {
                                "large_image": map_image,
                                "large_text": self.map,
                                "small_image": sesssion_image,
                                "small_text": sesssion + small_text2,
                            },
                            "timestamps": {"start":  self.starting_time},
                            "party": party
                        }
                    )

                elif self.mode == 'lobby':
                    self.presence.set(
                        {  
                            "details": bs.Lstr(resource=f'{self._r}.charSelectText').evaluate(),
                            "state": 'Party',
                            "assets": {
                                "large_text": bs.Lstr(resource=f'{self._r}.lobbyText').evaluate(),
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
                        name = bs.Lstr(resource=f'{self._r}.partyNameFallback').evaluate()
                    
                    if not name:
                        name = bs.Lstr(resource=f'{self._r}.partyNameFallback').evaluate()
                    
                    lstr = bs.Lstr(
                        resource=f'{self._r}.playingOnline',
                        subs=[
                            ('${PARTY}', name),
                        ]
                    )

                    self.presence.set(
                        {  
                            "details": lstr.evaluate(),
                            "state": 'Party',
                            "assets": {
                                "large_image": 'online',
                                "large_text": bs.Lstr(resource=f'{self._r}.playingOnlineSimple').evaluate(),
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
                            bs.Lstr(resource=f'{self._r}.watchingReplay').evaluate(),
                        "state": 'Party',
                        "assets": {
                            "large_image": 'replay',
                            "large_text": bs.Lstr(resource=f'{self._r}.replayText'),
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
                            bs.Lstr(resource=f'{self._r}.watchingCredits'),
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
            elif isinstance(bs.get_foreground_host_activity(), MainMenuActivity):
                self.mode = 'menu'
                self.last_mode = 'menu'
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
            elif isinstance(bs.get_foreground_host_activity(), CreditsActivity):
                self.mode = 'credits'
                self.last_mode = 'credits'
                self.starting_time = int(time.time())      
            
            babase.apptimer(0.25, self.update)


