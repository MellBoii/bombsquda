# Released under the MIT License. See LICENSE for details.
#
"""Music related bits."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import _bascenev1
import bascenev1 as bs
import babase
import bauiv1 as bui
import babase as ba
import fromgoverhaul.mell_resources as mell

if TYPE_CHECKING:
    pass

class MusicType(Enum):
    """Types of music available to play in-game.

    These do not correspond to specific pieces of music, but rather to
    'situations'. The actual music played for each type can be overridden
    by the game or by the user.
    """

    # ok lesson learned dont rename default music so it doesnt break vanilla online-play
    # perhaps should add music for when playing online?? seems cool audibly
    # also, don't rename the other names. they'll break if you pause and upnause.
    MENU1 = 'MENU1'
    MENU2 = 'MENU2'
    MENU3 = 'MENU3'
    MENU4 = 'MENU4'
    MENU5 = 'MENU5'
    MENU6 = 'MENU6'
    MENU7 = 'MENU7'
    MENU8 = 'MENU8'
    MENU9 = 'MENU9'
    MENU10 = 'MENU10'
    MENU11 = 'MENU11'
    MENU12 = 'MENU12'
    MENU13 = 'MENU13'
    MENU14 = 'MENU14'
    MENU15 = 'MENU15'
    MENU16 = 'MENU16'
    MENU17 = 'MENU17'
    MENU67 = 'MENU67'
    VICTORY = 'Victory'
    VICTORYFINAL = 'VictoryFinal'
    CHAR_SELECT = 'Char_Select'
    CHAR_SELECT2 = 'Char_Select2'
    CHAR_SELECT_F = 'Char_Select_F'
    TUTORIAL = 'Tutorial'
    RUN_AWAY = 'Run_Away'
    MODULATINGTIME = 'ModulatingTime'
    HURRYUP = 'HURRYUP'
    CUTSCENE1 = 'Cutscene1'
    CUTSCENE2 = 'Cutscene2'
    ONSLAUGHT = 'Onslaught'
    ONSLAUGHT2 = 'Onslaught2'
    KEEP_AWAY = 'Keep_Away'
    RACE = 'Race'
    GAMBLING = 'Gambling'
    EPIC_RACE = 'Epic_Race'
    SCORES = 'Scores'
    GRAND_ROMP = 'Grand_Romp'
    METALCAPTIME = 'MetalCapTime'
    RAGE = 'Rage'
    NOISESUPER = 'NoiseSuper'
    BUSINESS = 'Business'
    TO_THE_DEATH = 'To_The_Death'
    TO_THE_DEATHFAST = 'To_The_DeathFast'
    TO_THE_DEATH2FAST = 'To_The_Death2Fast'
    TO_THE_DEATH2 = 'To_The_Death2'
    TO_THE_DEATH3FAST = 'To_The_Death3Fast'
    TO_THE_DEATH3 = 'To_The_Death3'
    KEEP_AWAY2 = 'Keep_Away2'
    CHOSEN_ONE = 'Chosen_One'
    FORWARD_MARCH = 'Forward_March'
    FLAG_CATCHER = 'Flag_Catcher'
    SURVIVAL = 'Survival'
    EPIC = 'Epic'
    ONLINE = 'Online'
    PAUSE = 'Pause'
    D_RUNNIN = 'D_RUNNIN' # <- if you get the reference to what this is, you already know why its here.
    EPICFAST = 'EpicFast' # otherwise, it's used as the default music if there is a broken one
    SPORTS = 'Sports'
    FOOTBALL = 'Football'
    FLYING = 'Flying'
    FLYING2 = 'Flying2'
    SCARY = 'Scary'
    SUPER = 'Super'
    FEEL_THE_FURY = 'Feel_The_Fury'
    RAINBOW_ROAD = 'RAINBOW_ROAD'
    SRB2_OVERTIME = 'SRB2_Overtime'
    SRB2_PINCH = 'SRB2_Pinch'
    MARCHING = 'Marching'
    DEFEAT = 'Defeat'
    CREDITS = 'Credits'
    THEFINALE = 'TheFinale'
    FINALDESTINATION = 'FinalDestination'
    RUNAROUNDFINAL = 'RunaroundFinal'
    WAR = 'War'
    WWR = 'Wwr'
    LAP0 = 'Lap0'
    LAP0H = 'Lap0H'
    LAP1 = 'Lap1'
    LAP2 = 'Lap2'
    LAP3 = 'Lap3'
    LAP4 = 'Lap4'
    LAP5 = 'Lap5'
    LAP6 = 'Lap6'
    LAP7 = 'Lap7'
    LAP8 = 'Lap8'
    LAP9 = 'Lap9'
    SNESCOURSE = 'SNESCourse'
    SNESCOURSE2 = 'SNESCourse2'
    DS1 = 'DS1'
    DS2 = 'DS2'
    DS3 = 'DS3'
    SURVEY = 'SURVEY'
    LOGOTYPE = 'LOGOTYPE'
    OPENING = 'Opening'
    CRASH_HANDLER = 'Crash_Handler'
    ELIM_DANGER = 'Elim_Danger'
    ELIM_VERSUS = 'Elim_Versus'
    
def show_music_now_playing(music_type: bs.MusicType) -> None:
        """
        Display current music on screen.
        """
        from bascenev1lib.actor.text import Text
        from bascenev1lib.actor.image import Image
        excluded_types = [
            None,
            bs.MusicType.CUTSCENE1,
            bs.MusicType.CUTSCENE2,
            bs.MusicType.HURRYUP,
        ]
        
        if music_type in excluded_types:
            return
        music_names = {
            # bs.MusicType.MUSICTYPE: "musictitleandartistmaybe",
            bs.MusicType.TO_THE_DEATH: "Daniel Bautista - Intro",
            bs.MusicType.TO_THE_DEATH2: "Chrono Symphonic - Darkness Dueling (Plastic Men and Iron Blades)",
            bs.MusicType.TO_THE_DEATH2FAST: "Daniel Bautista - Flight of the Bumblebee",
            bs.MusicType.TO_THE_DEATH3FAST: "Bãtutã la trompeta - Rabbids Go Home",
            bs.MusicType.TO_THE_DEATH3: "Bãtutã din Moldova - Rabbids Go Home",
            bs.MusicType.TO_THE_DEATHFAST: "Daniel Bautista - Flight of the Bumblebee",
            bs.MusicType.EPIC: "Nocturne no. 2 in E-Flat major, op. 9 no. 2",
            bs.MusicType.EPICFAST: "Starvation V2 - T_heonlywhitesofa",
            bs.MusicType.CHAR_SELECT: "Overworld Map - Mario Kart World",
            bs.MusicType.CHAR_SELECT2: "Your Name, Please - EarthBound Dimensions",
            bs.MusicType.CHAR_SELECT_F: "Sky Map - Mario Kart World",
            bs.MusicType.TUTORIAL: "Go Go Go Summer, Nobuhamu - Tetr.io",
            bs.MusicType.ONLINE: "Across The World - Tyron",
            bs.MusicType.D_RUNNIN: "Runnin from Evil - Doom II", 
            bs.MusicType.BUSINESS: "Porky Means Business! - EarthBound",
            bs.MusicType.PAUSE: "Upgrade Station - Team Fortress 2",
            bs.MusicType.ELIM_DANGER: "Danger - Dr. Robotnik's Mean Bean Machine",
            bs.MusicType.ELIM_VERSUS: "2P. Versus - Dr. Robotnik's Mean Bean Machine",
            bs.MusicType.SCORES: "Intermission - Sonic Robo Blast 2",
            bs.MusicType.FLYING: "Ducktales Moon Theme meets Metal - 331Erock",
            bs.MusicType.FLYING2: "Sky Theme - Mario vs Luigi Online",
            bs.MusicType.RACE: "VS Metal Sonic - Sonic Mania",
            bs.MusicType.EPIC_RACE: "Final Boss - Sonic Mania",
            bs.MusicType.MENU1: "Artistic Mindset - Spamton123",
            bs.MusicType.MENU2: "Super Mario Kart Title Remastered",
            bs.MusicType.MENU3: "Mario vs Luigi 2.0 Title Theme Remix - Goldyber",
            bs.MusicType.MENU4: "Cascade Zone Act 2 (Track B) - Bomb Boy",
            bs.MusicType.MENU5: "Mario vs Luigi 2.0 Title Theme",
            bs.MusicType.MENU6: "Mario Kart: Double Dash!! Title Theme",
            bs.MusicType.MENU7: "Start your Engines - CTGP-7",
            bs.MusicType.MENU8: "Dog...? - Item Asylum",
            bs.MusicType.MENU9: "Title Theme -  Mario Kart 7",
            bs.MusicType.MENU10: "Friends no More x Papá Cerdito vs Bebé George",
            bs.MusicType.MENU11: "Title Theme - Mario Kart 8",
            bs.MusicType.MENU12: "Title Theme - Mario Kart 64",
            bs.MusicType.MENU13: "Title Theme - Dr. Robotnik's Mean Bean Machine",
            bs.MusicType.MENU14: "Pizza Deluxe - POST ELVIS",
            bs.MusicType.MENU15: "Pollyanna Rock My World - Furries in a blender",
            bs.MusicType.MENU16: "Wii Theme but it's September - Mr Rock",
            bs.MusicType.MENU17: "The Final Fight - Sonic 3D Blast",
            bs.MusicType.MENU67: "Super Compressed Version of the JRMP Menu Music That Isn't Really From JRMP But I Also Sing It With Myself Whilst Screaming - Mell",
            bs.MusicType.CREDITS: "Sonic Mania Unused Credits - Tee Lopes",
            bs.MusicType.SNESCOURSE: "SNES Battle Course - Mario Kart World",
            bs.MusicType.SNESCOURSE2: "Battle Course - Super Mario Kart",
            bs.MusicType.DEFEAT: "Blues in Velvet Room - Persona 3",
            bs.MusicType.FINALDESTINATION: "Final Destination - Super Smash Bros Melee",
            bs.MusicType.THEFINALE: "In The Finale - Bowser's Inside Story",
            bs.MusicType.WAR: "Thousand March - Mr. Sauceman",
            bs.MusicType.WWR: "War Without Reason - Heaven Pierce Her",
            bs.MusicType.LAP0: "It's Pizza Time! - Mr. Sauceman",
            bs.MusicType.LAP0H: "Nuclear Avalanche - Ronach",
            bs.MusicType.LAP1: "The Death I Deservioli - Mr. Sauceman",
            bs.MusicType.LAP2: "Pillar John's Revenge - Lap 3",
            bs.MusicType.LAP3: "Absolute AbsurZiti V2 - bilkshaker",
            bs.MusicType.LAP4: "Pasta La Vista - Oofator",
            bs.MusicType.LAP5: "Doppelganger's Delight V1 - ???",
            bs.MusicType.LAP6: "Moon-Eyed Madness - spooklass",
            bs.MusicType.LAP7: "Holy Ravioli S&%t - Parpal",
            bs.MusicType.LAP8: "Closed for Renovations - LyteRayz",
            bs.MusicType.LAP9: "Vengeance With a Pinch of Sauce - skibsthegoober2500",
            bs.MusicType.GAMBLING: "WEXECUTED (Instrumental) - Sherry",
            bs.MusicType.METALCAPTIME: "IT'S TV TIME but it's Metal Cap Theme - @secret_fan48",
            bs.MusicType.SUPER: "Super Sonic - Sonic Robo Blast 2",
            bs.MusicType.SRB2_PINCH: "Hurry Up! - Sonic Robo Blast 2 Battle",
            bs.MusicType.SRB2_OVERTIME: "OVERTIME!! - Sonic Robo Blast 2 Battle",
            bs.MusicType.RAGE: "Dr. Andonuts' Rage SSBU Mix - Frakture",
            bs.MusicType.GRAND_ROMP: "It's TV Time! - Deltarune",
            bs.MusicType.SPORTS: "Opening Movie (Beta Mix) - Eek! The Cat",
            bs.MusicType.FOOTBALL: "GOLF CENTRAL - Uncanny Cat Golf",
            bs.MusicType.VICTORY: "Stars and Stripes Forever (Metal Rock Remix) - Blue Claw Philharmonic",
            bs.MusicType.VICTORYFINAL: "Stars and Stripes Forever (Metal Rock Remix, Longer) - Blue Claw Philharmonic",
            bs.MusicType.ONSLAUGHT: "Ruder Buster - Deltarune",
            bs.MusicType.SURVIVAL: "Tough Guy Alert! - M&L:BIS GaMetal Remix",
            bs.MusicType.ONSLAUGHT2: "Rude Buster - Deltarune",
            bs.MusicType.NOISESUPER: "Unexpectancy Gatcha Remix - ClascyJitto",
            bs.MusicType.MODULATINGTIME: "A Journey in Modulating Time - MaliceX",
            bs.MusicType.KEEP_AWAY: "Flying Battery Zone 1 - Tee Lopes",
            bs.MusicType.KEEP_AWAY2: "Flying Battery Zone 2 - Tee Lopes",
            bs.MusicType.MARCHING: "Boss - Bowser Jr.'s Journey",
            bs.MusicType.RUNAROUNDFINAL: "Final Boss - Bowser Jr.'s Journey",
            bs.MusicType.DS1: "Battle Theme - Mario Kart DS",
            bs.MusicType.DS2: "Waluigi Pinball - Mario Kart DS",
            bs.MusicType.DS3: "Twilight House - Mario Kart Wii",
            bs.MusicType.SURVEY: "ANOTHER HIM - Deltarune",
            bs.MusicType.CRASH_HANDLER: "Cloudcones - Nagz",
            bs.MusicType.LOGOTYPE: "LOGOTYPE - Mother 3",
            bs.MusicType.FLAG_CATCHER: "Metallic Madness 1 - Tee Lopes",
            bs.MusicType.FORWARD_MARCH: "Metallic Madness 2 - Tee Lopes",
            bs.MusicType.OPENING: "Opening Credits - Bound to the Dark World",
            bs.MusicType.CHOSEN_ONE: "Tough Guy Alert! - M&L Bowser's Inside Story - GaMetal Cover",
            bs.MusicType.RUN_AWAY: "Tough Guy Alert! - M&L Bowser's Inside Story - GaMetal Cover",
            bs.MusicType.FEEL_THE_FURY: "Feel The Fury - ThatGuyRamon",
            bs.MusicType.RAINBOW_ROAD: "Rainbow Road Pentagon Path Remix - B1itz Lunar",
            bs.MusicType.SCARY: "???",
        }
        # Get the music name from the list.
        # If we don't get any, tell the player it's either unknown
        # or will be added later down the line. Laziness kills the mellboii. 
        name = music_names.get(music_type, ba.Lstr(resource='npUnknownMusic'))
        if music_type not in music_names:
            print(f'QUICK NOTE: {music_type} is missing from the music popup list.')
            print('Please add it later.')
        activity = bs.get_foreground_host_activity()
        with activity.context:
            # get important variables
            uiscale = bui.app.ui_v1.uiscale
            amt = activity.music_texts
            base_y = 0
            step_y = 30
            ypos = base_y + len(activity.music_texts) * step_y
            xpos = 635
            ofscrX = 1500
            tscale = (
                1.3 if uiscale is bui.UIScale.SMALL
                else 0.8
            )
            # make our disc image..
            img = Image(
                bs.gettexture('coverDisc'),
                position=(ofscrX, ypos),
                scale=(300, 300),
                attach=Image.Attach.BOTTOM_CENTER,
                color=(1, 1, 1, 0.5),
            ).autoretain()
            # and our now playing text
            txt = Text(
                ba.Lstr(
                    resource='npPlaying',
                    subs=[
                        ('${MUSIC}', name)
                    ],
                ),
                position=(ofscrX, ypos),
                h_attach=Text.HAttach.CENTER,
                h_align=Text.HAlign.RIGHT,
                v_attach=Text.VAttach.BOTTOM,
                color=(1, 1, 1, 1),
                scale=tscale,
                shadow=0.5,
                flatness=0.5,
            ).autoretain()
            # animate text going on screen then back out
            bs.animate_array(
                txt.node,
                "position",
                2,
                {
                    0.0: (ofscrX, ypos),
                    1.0: (xpos, ypos),  # visible position
                    6.0: (xpos, ypos),  # stay for ~6s
                    7.0: (ofscrX, ypos),  # slide back out
                },
            )
            # repeat for image
            bs.animate_array(
                img.node,
                "position",
                2,
                {
                    0.0: (ofscrX, ypos),
                    1.0: (xpos, ypos),  # visible position
                    6.0: (xpos, ypos),  # stay for ~6s
                    7.0: (ofscrX, ypos),  # slide back out
                },
            )
            # append us to the activity's music texts
            # so we can track how many texts there are
            # so we don't show up infront of one
            activity.music_texts.append(txt)
            # define stuff
            def add_one():
                # add 5 to rotation
                img.node.rotate += 5
            def do_delete():
                # stop everything that's needed
                # and delete stuff
                txt.node.delete()
                img.node.delete()
                activity.music_texts.remove(txt)
                img.rotatetimer = None
            # timers
            img.rotatetimer = bs.Timer(0.01, add_one, repeat=True)
            bs.timer(7.0, do_delete)

def setmusic(musictype: MusicType | None, continuous: bool = False, show_playing: bool = True) -> None:
    """Set the app to play (or stop playing) a certain type of music.

    This function will handle loading and playing sound assets as
    necessary, and also supports custom user soundtracks on specific
    platforms so the user can override particular game music with their
    own.

    Pass ``None`` to stop music.

    if ``continuous`` is True and musictype is the same as what is
    already playing, the playing track will not be restarted.
    """

    # All we do here now is set a few music attrs on the current globals
    # node. The foreground globals' current playing music then gets fed to
    # the do_play_music call in our music controller. This way we can
    # seamlessly support custom soundtracks in replays/etc since we're being
    # driven purely by node data.
    
    # Check if we have a activity.
    try:
        activity = bs.getactivity()
        gnode = activity.globalsnode
    # Use foreground host activity instead.
    except babase._error.ActivityNotFoundError:
        activity = bs.get_foreground_host_activity()
        gnode = activity.globalsnode
    gnode.music_continuous = continuous
    gnode.music = '' if musictype is None else musictype.value
    gnode.music_count += 1
    # Ensure activity has lyric storage
    if not hasattr(activity, '_lyric_player'):
        activity._lyric_player = None

    # Stop any existing lyric player
    if activity._lyric_player:
        bs.debprint('[LyricPlayer] stopping previous instance')
        activity._lyric_player.stop()
        activity._lyric_player = None

    # Start lyrics if needed
    if musictype == bs.MusicType.FEEL_THE_FURY:
        lp = LyricPlayer(
            mell.FEEL_THE_FURY,
            loop=True,
            song_length=213,
            offset=-1.20,
        )
        activity._lyric_player = lp
        lp.play()

    with activity.context:
        # Don't show game-set music if the player
        # is using the boombox
        if ba.app.config.get("squda_isplayingmusic"):
            return
        if not show_playing:
            return
        ba.apptimer(0.1, lambda: show_music_now_playing(music_type=musictype))
    
def localsetmusic(musictype: MusicType | None, continuous: bool = False) -> None:
    """
    Allows you to set music locally,
    which is better than just muting the volume
    and using the fuckin music app
    Probably like a replacement for soundtracks
    on windows lfmafoafoafoaofa
    """
    musiclassic = bui.app.classic.music
    if musictype == None:
        musiclassic.set_music_play_mode(
            bui.app.classic.MusicPlayMode.REGULAR, force_restart=True
        )
    else:
        musiclassic.set_music_play_mode(bui.app.classic.MusicPlayMode.TEST)
        musiclassic.do_play_music(
            musictype,
            mode=bui.app.classic.MusicPlayMode.TEST,
        )
def getmusic():
    """
    gets the current playing music
    """
    return getattr(bs.MusicType, bs.get_foreground_host_activity().globalsnode.music.upper())

def test_musicnames():
    """
    this plays all music types that are in bs.MusicType.
    refrain from using this unless you wanna test 
    if the Now Playing is missing any musictypes
    """
    list = [getattr(bs.MusicType, music_type) for music_type in 
    dir(bs.MusicType) if not music_type.startswith('__')]
    for musictype in list:
        bs.setmusic(musictype)

class LyricPlayer:
    """Plays a timed sequence of lyrics onscreen."""

    def __init__(
        self,
        lyric_list: list[tuple[str, float]],
        *,
        pos=(0, 60),
        color=(1, 1, 1),
        v_attach='bottom',
        scale=1.2,
        song_length: float | None = None,
        loop: bool = False,
        offset: float = 0.0,
    ):
        bs.debprint("[LyricPlayer] __init__")

        self.lyrics = lyric_list
        self.pos = pos
        self.color = color
        self.v_attach = v_attach
        self.scale = scale
        self.song_length = song_length
        self.loop = loop
        self.offset = offset
        self._start_time: float | None = None

        self._timers: list[bs.Timer] = []
        self._running = False

    def play(self):
        bs.debprint("[LyricPlayer] play()")

        self.stop()
        self._running = True

        self._start_time = bs.apptime()   # <-- anchor
        fade_time = 2.0

        for text, t in self.lyrics:
            scheduled_time = max(0.0, t + self.offset)
            delay = max(0.0, self._start_time + scheduled_time - bs.apptime())

            bs.debprint(f"[LyricPlayer] scheduling in {delay:.3f}s: {text}")

            def make_fn(msg=text):
                if not self._running:
                    return

                bs.debprint(f"[LyricPlayer] showing lyric: {msg}")

                node = bs.newnode(
                    'text',
                    attrs={
                        'text': msg,
                        'position': self.pos,
                        'scale': self.scale,
                        'color': self.color,
                        'h_align': 'center',
                        'v_attach': self.v_attach,
                    },
                )

                bs.animate(node, 'opacity', {0.0: 1.0, fade_time: 0.0})
                bs.timer(fade_time + 0.2, node.delete)

            self._timers.append(bs.Timer(delay, make_fn))

        if self.loop and self.song_length:
            loop_delay = max(0.0, self._start_time + self.song_length + self.offset - bs.apptime())
            self._timers.append(bs.Timer(loop_delay, self._restart))

    def _restart(self):
        if not self._running:
            return
        self._start_time = bs.apptime()
        self.play()

    def stop(self):
        if self._running:
            bs.debprint("[LyricPlayer] stop()")
        self._running = False
        self._timers.clear()
