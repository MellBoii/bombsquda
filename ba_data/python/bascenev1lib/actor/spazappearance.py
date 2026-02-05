# Released under the MIT License. See LICENSE for details.
#
"""Appearance functionality for spazzes."""
from __future__ import annotations

import bascenev1 as bs
import babase as ba


def get_appearances(include_locked: bool = False) -> list[str]:
    """Get the list of available spaz appearances."""
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    plus = bs.app.plus
    assert plus is not None

    assert bs.app.classic is not None
    get_purchased = plus.get_v1_account_product_purchased
    disallowed = []
    if not include_locked:
        # alternative to updating modpack since it will TAKING TOO LONG
        if not ba.app.config.get("squda_unlockedmel", True):
            disallowed.append('Mel')
            
    return [
        s
        for s in list(bs.app.classic.spaz_appearances.keys())
        if s not in disallowed
    ]


class Appearance:
    """Create and fill out one of these suckers to define a spaz appearance."""

    def __init__(self, name: str):
        assert bs.app.classic is not None
        self.name = name
        if self.name in bs.app.classic.spaz_appearances:
            raise RuntimeError(
                f'spaz appearance name "{self.name}" already exists.'
            )
        bs.app.classic.spaz_appearances[self.name] = self
        self.color_texture = ''
        self.color_mask_texture = ''
        self.icon_texture = ''
        self.earthportrait = ''
        self.icon_mask_texture = ''
        self.head_mesh = ''
        self.torso_mesh = ''
        self.pelvis_mesh = ''
        self.upper_arm_mesh = ''
        self.forearm_mesh = ''
        self.hand_mesh = ''
        self.upper_leg_mesh = ''
        self.lower_leg_mesh = ''
        self.toes_mesh = ''
        self.jump_sounds: list[str] = []
        self.attack_sounds: list[str] = []
        self.impact_sounds: list[str] = []
        self.death_sounds: list[str] = []
        self.pickup_sounds: list[str] = []
        self.victory_sounds: list[str] = []
        self.fall_sounds: list[str] = []
        self.style = 'spaz'
        self.default_color: tuple[float, float, float] | None = None
        self.default_highlight: tuple[float, float, float] | None = None


def register_appearances() -> None:
    """Register our builtin spaz appearances."""

    # This is quite ugly but will be going away so not worth cleaning up.
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    # spazling #######################################
    t = Appearance('Spaz')
    t.color_texture = 'spazlingColor'
    t.color_mask_texture = 'spazlingColorMask'
    t.icon_texture = 'spazlingIcon'
    t.earthportrait = 'spazbound'
    t.icon_mask_texture = 'spazlingIconCM'
    t.head_mesh = 'spazlingHead'
    t.torso_mesh = 'spazlingTorso'
    t.pelvis_mesh = 'spazlingPelvis'
    t.upper_arm_mesh = 'spazlingUpperArm'
    t.forearm_mesh = 'spazlingForeArm'
    t.hand_mesh = 'spazlingHand'
    t.upper_leg_mesh = 'spazlingUpperLeg'
    t.lower_leg_mesh = 'spazlingLowerLeg'
    t.toes_mesh = 'spazlingToes'
    t.jump_sounds = ['voicelines/spaz/jump0' + str(i + 1) + '' for i in range(4)]
    t.attack_sounds = ['voicelines/spaz/attack0' + str(i + 1) + '' for i in range(4)]
    t.impact_sounds = ['voicelines/spaz/hurt0' + str(i + 1) + '' for i in range(4)]
    t.death_sounds = ['voicelines/spaz/death0' + str(i + 1) + '' for i in range(4)]
    t.pickup_sounds = ['voicelines/spaz/pickup']
    t.victory_sounds = ['voicelines/spaz/win']
    t.gloat_sounds = ['voicelines/spaz/gloat']
    t.fall_sounds = ['voicelines/spaz/fall0' + str(i + 1) + '' for i in range(4)]
    t.style = 'agent'

    # Roaring Knight's right hand they/them #####################################
    t = Appearance('Kris')
    t.color_texture = 'krisColor'
    t.color_mask_texture = 'krisColorMask'
    t.icon_texture = 'krisIcon'
    t.earthportrait = 'krisbound'
    t.icon_mask_texture = 'krisIconColorMask'
    t.head_mesh = 'krisHead'
    t.torso_mesh = 'krisTorso'
    t.pelvis_mesh = 'krisPelvis'
    t.upper_arm_mesh = 'krisUpperArm'
    t.forearm_mesh = 'krisForeArm'
    t.hand_mesh = 'krisHand'
    t.upper_leg_mesh = 'krisUpperLeg'
    t.lower_leg_mesh = 'krisLowerLeg'
    t.toes_mesh = 'krisToes'
    t.jump_sounds = ['voicelines/kris/jump']
    t.attack_sounds = ['voicelines/kris/attack' + str(i + 1) + '' for i in range(4)]
    t.impact_sounds = ['voicelines/kris/hurt' + str(i + 1) + '' for i in range(4)]
    t.death_sounds = ['voicelines/kris/death']
    t.pickup_sounds = ['voicelines/kris/pickup']
    t.fall_sounds = ['voicelines/kris/fall']
    t.victory_sounds = ['voicelines/kris/win']
    t.style = 'female'
    t.default_color = (0.9215686274509803, 0.0, 0.5843137254901961)
    t.default_highlight = (0.4588235294117647, 0.984313725490196, 0.9294117647058824)

    # gummy ##########################################
    t = Appearance('GummyBoiYT')
    t.color_texture = 'snakeyColor'
    t.color_mask_texture = 'snakeyColorMask'
    t.icon_texture = 'snakeyIcon'
    t.earthportrait = 'snakebound'
    t.icon_mask_texture = 'snakeyIconCM'
    t.head_mesh = 'snakeyHead'
    t.torso_mesh = 'snakeyTorso'
    t.pelvis_mesh = 'snakeyPelvis'
    t.upper_arm_mesh = 'snakeyUpperArm'
    t.forearm_mesh = 'snakeyForeArm'
    t.hand_mesh = 'snakeyHand'
    t.upper_leg_mesh = 'snakeyUpperLeg'
    t.lower_leg_mesh = 'snakeyLowerLeg'
    t.toes_mesh = 'snakeyToes'
    t.jump_sounds = ['voicelines/snakey/attack' + str(i + 1) + '' for i in range(7)]
    t.attack_sounds = ['voicelines/snakey/attack' + str(i + 1) + '' for i in range(7)]
    t.impact_sounds = ['voicelines/snakey/hurt' + str(i + 1) + '' for i in range(8)]
    t.death_sounds = ['voicelines/snakey/death']
    t.pickup_sounds = ['voicelines/snakey/attack' + str(i + 1) + '' for i in range(7)]
    t.fall_sounds = ['voicelines/snakey/fall' + str(i + 1) + '' for i in range(2)]
    t.gloat_sounds = ['voicelines/snakey/gloat']
    t.victory_sounds = ['voicelines/snakey/win']
    t.style = 'ninja'
    t.default_color = (0.2, 1, 1)
    t.default_highlight = (1, 1, 1)

    # barney wannabe #####################################
    t = Appearance('Susie')
    t.color_texture = 'susieColor'
    t.color_mask_texture = 'susieColorMask'
    t.icon_texture = 'susieIcon'
    t.earthportrait = 'susiebound'
    t.icon_mask_texture = 'susieIconCM'
    t.head_mesh = 'susieHead'
    t.torso_mesh = 'susieTorso'
    t.pelvis_mesh = 'susiePelvis'
    t.upper_arm_mesh = 'susieUpperArm'
    t.forearm_mesh = 'susieForeArm'
    t.hand_mesh = 'susieHand'
    t.upper_leg_mesh = 'susieUpperLeg'
    t.lower_leg_mesh = 'susieLowerLeg'
    t.toes_mesh = 'susieToes'
    t.jump_sounds = ['voicelines/susie/jump' + str(i + 1) + '' for i in range(4)]
    t.attack_sounds = ['voicelines/susie/attack' + str(i + 1) + '' for i in range(4)]
    t.victory_sounds = ['voicelines/susie/win']
    t.gloat_sounds = ['voicelines/susie/gloat']
    t.impact_sounds = ['voicelines/susie/hurt' + str(i + 1) + '' for i in range(2)]
    t.death_sounds = ['voicelines/susie/death']
    t.pickup_sounds = ['voicelines/susie/attack' + str(i + 1) + '' for i in range(4)]
    t.fall_sounds = ['voicelines/susie/fall']
    t.style = 'kronk'
    t.default_color = (0.9725490196078431, 0.5137254901960784, 0.8431372549019608)
    t.default_highlight = (0.5333333333333333, 0.09019607843137255, 0.41568627450980394)

    # fatass ###########################################
    # thank you lemon for this incredible voice acting
    t = Appearance('Mell')
    t.color_texture = 'mellColor'
    t.color_mask_texture = 'mellColorMask'
    t.icon_texture = 'mellIcon'
    t.earthportrait = 'mellbound'
    t.icon_mask_texture = 'mellIconCM'
    t.head_mesh = 'mellHead'
    t.torso_mesh = 'mellTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'mellUpperArm'
    t.forearm_mesh = 'mellForeArm'
    t.hand_mesh = 'mellHand'
    t.upper_leg_mesh = 'mellUpperLeg'
    t.lower_leg_mesh = 'mellLowerLeg'
    t.toes_mesh = 'mellToes'
    mell_sounds = ['voicelines/mell/sound' + str(i + 1) + '' for i in range(7)]
    t.jump_sounds = mell_sounds
    t.attack_sounds = mell_sounds
    t.impact_sounds = mell_sounds
    t.death_sounds = ['voicelines/mell/death']
    t.victory_sounds = mell_sounds
    t.gloat_sounds = ['voicelines/mell/gloat']
    t.pickup_sounds = mell_sounds
    t.fall_sounds = ['voicelines/mell/fall' + str(i + 1) + '' for i in range(2)]
    t.style = 'mel'
    t.default_color = (1, 1, 1)
    t.default_highlight = (0, 1, 0)

    # BALL! ###########################################
    # not many assets; it's for a different actor
    # (just here so it appears in appearances)
    t = Appearance('Baller')
    t.icon_mask_texture = 'ballerIconCM'
    t.icon_texture = 'ballerIcon'
    t.default_color = (1, 0.1, 0.1)
    t.default_highlight = (0, 1, 0)

    # Noob #######################################
    t = Appearance('Noob')
    t.color_texture = 'noobColor'
    t.color_mask_texture = 'noobColorMask'
    t.icon_texture = 'noobIcon'
    t.earthportrait = 'noobbound'
    t.icon_mask_texture = 'noobIconColorMask'
    t.head_mesh = 'noobHead'
    t.torso_mesh = 'noobTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'noobUpperArm'
    t.forearm_mesh = 'noobForeArm'
    t.hand_mesh = 'noobHand'
    t.upper_leg_mesh = 'noobUpperLeg'
    t.lower_leg_mesh = 'noobLowerLeg'
    t.toes_mesh = 'noobToes'
    noob_sounds = ['voicelines/noob/sound' + str(i + 1) + '' for i in range(6)]
    t.jump_sounds = noob_sounds
    t.attack_sounds = noob_sounds
    t.impact_sounds = ['voicelines/noob/hurt' + str(i + 1) + '' for i in range(7)]
    t.death_sounds = ['voicelines/noob/death']
    t.pickup_sounds = noob_sounds
    t.fall_sounds = ['voicelines/noob/fall']
    t.style = 'pirate'
    t.default_color = (1.0, 0.99, 0.13999999999999968)
    t.default_highlight = (0.30999999999999994, 0.4599999999999999, 1)   
    
    # tubby plumber man ######################################
    t = Appearance('SM64 Mario')
    t.color_texture = 'marioColor'
    t.color_mask_texture = 'marioColorMask'
    t.icon_texture = 'marioIcon'
    t.icon_mask_texture = 'marioIconCM'
    t.head_mesh = 'santaHead'
    t.torso_mesh = 'santaTorso'
    t.pelvis_mesh = 'santaPelvis'
    t.upper_arm_mesh = 'santaUpperArm'
    t.forearm_mesh = 'santaForeArm'
    t.hand_mesh = 'santaHand'
    t.upper_leg_mesh = 'santaUpperLeg'
    t.lower_leg_mesh = 'santaLowerLeg'
    t.toes_mesh = 'santaToes'
    t.jump_sounds = ['voicelines/mario64/jump' + str(i + 1) + '' for i in range(3)]
    t.attack_sounds = ['voicelines/mario64/attack' + str(i + 1) + '' for i in range(3)]
    t.impact_sounds = ['voicelines/mario64/hurt' + str(i + 1) + '' for i in range(3)]
    t.death_sounds = ['voicelines/mario64/death']
    t.pickup_sounds = ['voicelines/mario64/pickup']
    t.fall_sounds = ['voicelines/mario64/fall']
    t.victory_sounds = ['voicelines/mario64/win']
    t.gloat_sounds = ['voicelines/mario64/gloat']
    t.style = 'agent'
    t.default_color = (1, 0, 0)
    t.default_highlight = (0.1, 0.1, 1)

    # that one character from the asym they canceled because why not ######################################
    t = Appearance('Sonic')
    t.color_texture = 'sonicColor'
    t.color_mask_texture = 'sonicColorMask'
    t.icon_texture = 'sonicIcon'
    t.icon_mask_texture = 'sonicIconCM'
    t.head_mesh = 'sonicHead'
    t.torso_mesh = 'sonicTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'sonicUpperArm'
    t.forearm_mesh = 'sonicForeArm'
    t.hand_mesh = 'sonicHand'
    t.upper_leg_mesh = 'sonicUpperLeg'
    t.lower_leg_mesh = 'sonicLowerLeg'
    t.toes_mesh = 'none'
    t.jump_sounds = ['voicelines/sonic/jump' + str(i + 1) + '' for i in range(3)]
    t.attack_sounds = ['voicelines/sonic/attack' + str(i + 1) + '' for i in range(4)]
    t.impact_sounds = ['voicelines/sonic/hit' + str(i + 1) + '' for i in range(5)]
    t.death_sounds = ['voicelines/sonic/death']
    t.pickup_sounds = ['voicelines/sonic/attack' + str(i + 1) + '' for i in range(4)]
    t.fall_sounds = ['voicelines/sonic/fall']
    t.victory_sounds = ['voicelines/sonic/win']
    t.gloat_sounds = ['voicelines/sonic/gloat']
    t.style = 'agent'
    t.default_color = (0.2, 0.2, 0.7)
    t.default_highlight = (1, 0.1, 0.1)

    # Rayman! ################################
    t = Appearance('Rayman')
    t.color_texture = 'raymanColor'
    t.color_mask_texture = 'raymanColorMask'
    t.icon_texture = 'raymanIcon'
    t.earthportrait = 'raybound'
    t.icon_mask_texture = 'raymanIconColorMask'
    t.head_mesh = 'raymanHead'
    t.torso_mesh = 'raymanTorso'
    t.pelvis_mesh = 'raymanPelvis'
    t.upper_arm_mesh = 'raymanUpperArm'
    t.forearm_mesh = 'raymanForeArm'
    t.hand_mesh = 'raymanHand'
    t.upper_leg_mesh = 'raymanUpperLeg'
    t.lower_leg_mesh = 'raymanLowerLeg'
    t.toes_mesh = 'raymanToes'
    t.jump_sounds = ['voicelines/rayman/jump' + str(i + 1) + '' for i in range(3)]
    t.attack_sounds = ['voicelines/rayman/attack' + str(i + 1) + '' for i in range(2)]
    t.impact_sounds = ['voicelines/rayman/hurt' + str(i + 1) + '' for i in range(3)]
    t.victory_sounds = ['voicelines/rayman/win']
    t.death_sounds = ['voicelines/rayman/death']
    t.pickup_sounds = ['voicelines/rayman/attack' + str(i + 1) + '' for i in range(2)]
    t.fall_sounds = ['voicelines/rayman/fall']
    t.style = 'bones'
    t.default_color = (0.5, 0.25, 1.0)
    t.default_highlight = (1.0, 0.15, 0.15)

    # Shooowwwtime!! ###################################
    t = Appearance('Bowser')
    t.color_texture = 'bowserColor'
    t.color_mask_texture = 'bowserColorMask'
    t.icon_texture = 'bowserIcon'
    t.earthportrait = 'bowserbound'
    t.icon_mask_texture = 'bowserIconColorMask'
    t.head_mesh = 'bowserHead'
    t.torso_mesh = 'bowserTorso'
    t.pelvis_mesh = 'bowserPelvis'
    t.upper_arm_mesh = 'bowserUpperArm'
    t.forearm_mesh = 'bowserForeArm'
    t.hand_mesh = 'bowserHand'
    t.upper_leg_mesh = 'bowserUpperLeg'
    t.lower_leg_mesh = 'bowserLowerLeg'
    t.toes_mesh = 'bowserToes'
    bowser_sounds = ['bowser1', 'bowser2', 'bowser3', 'bowser4']
    bowser_hit_sounds = ['bowserHit1', 'bowserHit2']
    t.jump_sounds = bowser_sounds
    t.attack_sounds = bowser_sounds
    t.impact_sounds = bowser_hit_sounds
    t.death_sounds = ['bowserDeath']
    t.victory_sounds = ['bowserWin']
    t.gloat_sounds = ['bowserGloat']
    t.pickup_sounds = bowser_sounds
    t.fall_sounds = ['bowserFall']
    t.style = 'bowser'
    t.default_color = (
        0.996078431372549, 
        0.8372549019607842, 
        0.022745098039215678
    )
    t.default_highlight = (
        0.0, 
        0.5686274509803921, 
        0.22745098039215686
    )

    # Prince of the Dark ###################################
    t = Appearance('Ralsei')
    t.color_texture = 'ralseiColor'
    t.color_mask_texture = 'ralseiColorMask'
    t.icon_texture = 'ralsIcon'
    t.earthportrait = 'ralseibound'
    t.icon_mask_texture = 'ralsIconCM'
    t.head_mesh = 'ralseiHead'
    t.torso_mesh = 'ralseiTorso'
    t.pelvis_mesh = 'ralseiPelvis'
    t.upper_arm_mesh = 'ralseiUpperArm'
    t.forearm_mesh = 'ralseiForeArm'
    t.hand_mesh = 'ralseiHand'
    t.upper_leg_mesh = 'ralseiUpperLeg'
    t.lower_leg_mesh = 'ralseiLowerLeg'
    t.toes_mesh = 'ralseiToes'
    ralsei_sounds = ['voicelines/ralsei/sound' + str(i + 1) + '' for i in range(4)]
    ralsei_hit_sounds = ['voicelines/ralsei/hit' + str(i + 1) + '' for i in range(2)]
    t.jump_sounds = ralsei_sounds
    t.attack_sounds = ralsei_sounds
    t.impact_sounds = ralsei_hit_sounds
    t.death_sounds = ['voicelines/ralsei/death']
    t.pickup_sounds = ralsei_sounds
    t.fall_sounds = ['voicelines/ralsei/fall']
    t.victory_sounds = ['voicelines/ralsei/win']
    t.gloat_sounds = ['voicelines/ralsei/gloat']
    t.style = 'agent'
    t.default_color = (0.0, 0.7699999999999998, 0.11999999999999998)
    t.default_highlight = (1, 0.08, 0.5)

    # Ali ###################################
    t = Appearance('Taobao Mascot')
    t.color_texture = 'aliColor'
    t.color_mask_texture = 'aliColorMask'
    t.icon_texture = 'aliIcon'
    t.icon_mask_texture = 'aliIconColorMask'
    t.head_mesh = 'aliHead'
    t.torso_mesh = 'aliTorso'
    t.pelvis_mesh = 'aliPelvis'
    t.upper_arm_mesh = 'aliUpperArm'
    t.forearm_mesh = 'aliForeArm'
    t.hand_mesh = 'aliHand'
    t.upper_leg_mesh = 'aliUpperLeg'
    t.lower_leg_mesh = 'aliLowerLeg'
    t.toes_mesh = 'aliToes'
    ali_sounds = ['ali1', 'ali2', 'ali3', 'ali4']
    ali_hit_sounds = ['aliHit1', 'aliHit2']
    t.jump_sounds = ali_sounds
    t.attack_sounds = ali_sounds
    t.impact_sounds = ali_hit_sounds
    t.death_sounds = ['aliDeath']
    t.pickup_sounds = ali_sounds
    t.fall_sounds = ['aliFall']
    t.style = 'ali'
    t.default_color = (1, 0.5, 0)
    t.default_highlight = (1, 1, 1)

    # knite. ###################################
    t = Appearance('Roaring Knight')
    t.color_texture = 'knightColor'
    t.color_mask_texture = 'knightColorMask'
    t.icon_texture = 'knightIcon'
    t.earthportrait = 'knightbound'
    t.icon_mask_texture = 'knightIconColorMask'
    t.head_mesh = 'knightHead'
    t.torso_mesh = 'knightTorso'
    t.pelvis_mesh = 'knightPelvis'
    t.upper_arm_mesh = 'knightUpperArm'
    t.forearm_mesh = 'knightForeArm'
    t.hand_mesh = 'knightHand'
    t.upper_leg_mesh = 'knightUpperLeg'
    t.lower_leg_mesh = 'knightLowerLeg'
    t.toes_mesh = 'knightToes'
    knightsounds = ['voicelines/knight/sound' + str(i + 1) + '' for i in range(4)]
    t.jump_sounds = knightsounds
    t.attack_sounds = knightsounds
    t.impact_sounds = ['voicelines/knight/hurt' + str(i + 1) + '' for i in range(2)]
    t.death_sounds = ['voicelines/knight/death']
    t.pickup_sounds = knightsounds
    t.victory_sounds = ['voicelines/knight/win']
    t.gloat_sounds = ['voicelines/knight/gloat']
    t.fall_sounds = ['voicelines/knight/fall']
    t.style = 'agent'
    t.default_color = (0.0, 0.0, 0.0)
    t.default_highlight = (1, 1, 1)

    # Noise Noise Noise Noise NOise ###################################
    t = Appearance('The Noise')
    t.color_texture = 'noiseColor'
    t.color_mask_texture = 'noiseColorMask'
    t.icon_texture = 'noiseIcon'
    t.earthportrait = 'noisebound'
    t.icon_mask_texture = 'noiseIconCM'
    t.head_mesh = 'noiseHead'
    t.torso_mesh = 'noiseTorso'
    t.pelvis_mesh = 'noisePelvis'
    t.upper_arm_mesh = 'noiseUpperArm'
    t.forearm_mesh = 'noiseForeArm'
    t.hand_mesh = 'noiseHand'
    t.upper_leg_mesh = 'noiseUpperLeg'
    t.lower_leg_mesh = 'noiseLowerLeg'
    t.toes_mesh = 'noiseToes'
    noise_sounds = ['voicelines/noise/sound' + str(i + 1) + '' for i in range(4)]
    noise_hit_sounds = ['voicelines/noise/hit' + str(i + 1) + '' for i in range(2)]
    t.jump_sounds = noise_sounds
    t.attack_sounds = noise_sounds
    t.impact_sounds = noise_hit_sounds
    t.death_sounds = ['voicelines/noise/death']
    t.pickup_sounds = noise_sounds
    t.victory_sounds = ['voicelines/noise/sound1']
    t.gloat_sounds = ['voicelines/noise/gloat']
    t.fall_sounds = ['voicelines/noise/fall']
    t.style = 'agent'
    t.default_color = (
        0.9725490196078431,
        0.8784313725490196,
        0.5019607843137255
    )
    t.default_highlight = (
        0.8470588235294118,
        0.5333333333333333,
        0.09411764705882353
    )
    
    # homero doh homero cerveza ###################################
    t = Appearance('Homer')
    t.color_texture = 'theSimpsonColor'
    t.color_mask_texture = 'theSimpsonColorMask'
    t.icon_texture = 'tsHomerIconColor'
    t.icon_mask_texture = 'tsHomerIconColorMask'
    t.earthportrait = 'homerbound'
    t.head_mesh = 'tsHomerHead'
    t.torso_mesh = 'tsHomerTorso'
    t.pelvis_mesh = 'none'
    t.upper_arm_mesh = 'tsHomerUpperArm'
    t.forearm_mesh = 'tsHomerForeArm'
    t.hand_mesh = 'tsHomerHand'
    t.upper_leg_mesh = 'tsHomerUpperLeg'
    t.lower_leg_mesh = 'tsHomerLowerLeg'
    t.toes_mesh = 'tsHomerToes'
    homersounds = ['voicelines/homer/sound' + str(i + 1) + '' for i in range(2)]
    homerhurtsfx = ['voicelines/homer/hit' + str(i + 1) + '' for i in range(3)]
    t.jump_sounds = homersounds
    t.attack_sounds = homersounds
    t.impact_sounds = homerhurtsfx
    t.death_sounds = ['voicelines/homer/death']
    t.pickup_sounds = ['voicelines/homer/pickup']
    t.victory_sounds = ['voicelines/homer/sound3']
    t.gloat_sounds = ['voicelines/homer/fall']
    t.fall_sounds = ['voicelines/homer/fall']
    t.style = 'agent'
    t.default_color = (0.3, 0.3, 0.33)
    t.default_highlight = (1, 0.5, 0.3)

    # orange guy with the cap... like some kinda buddy... ###################################
    t = Appearance('Orangecap')
    t.color_texture = 'ocapColor'
    t.color_mask_texture = 'ocapColorMask'
    t.icon_texture = 'ocapIcon'
    t.earthportrait = 'capbound'
    t.icon_mask_texture = 'ocapIconCM'
    t.head_mesh = 'ocapHead'
    t.torso_mesh = 'ocapTorso'
    t.pelvis_mesh = 'ocapPelvis'
    t.upper_arm_mesh = 'ocapUpperArm'
    t.forearm_mesh = 'ocapForeArm'
    t.hand_mesh = 'ocapHand'
    t.upper_leg_mesh = 'ocapUpperLeg'
    t.lower_leg_mesh = 'ocapLowerLeg'
    t.toes_mesh = 'ocapToes'
    t.jump_sounds = ['voicelines/ocap/jump' + str(i + 1) + '' for i in range(4)]
    t.attack_sounds = ['voicelines/ocap/punch' + str(i + 1) + '' for i in range(4)]
    t.impact_sounds = ['voicelines/ocap/hurt1']
    t.death_sounds = ['voicelines/ocap/death' + str(i + 1) + '' for i in range(2)]
    t.pickup_sounds = ['voicelines/ocap/pickup' + str(i + 1) + '' for i in range(4)]
    t.fall_sounds = ['voicelines/ocap/fall' + str(i + 1) + '' for i in range(3)]
    t.style = 'agent'
    t.default_color = (0.87, 0.44, 0.15)
    t.default_highlight = (0.46, 0.26, 0.54)

    # The Original      Spaz ###################################
    t = Appearance('OG Spaz')
    t.color_texture = 'spazColor'
    t.color_mask_texture = 'spazColorMask'
    t.icon_texture = 'spazIcon'
    t.icon_mask_texture = 'spazIconCM'
    t.head_mesh = 'spazHead'
    t.torso_mesh = 'spazTorso'
    t.pelvis_mesh = 'spazPelvis'
    t.upper_arm_mesh = 'spazUpperArm'
    t.forearm_mesh = 'spazForeArm'
    t.hand_mesh = 'spazHand'
    t.upper_leg_mesh = 'spazUpperLeg'
    t.lower_leg_mesh = 'spazLowerLeg'
    t.toes_mesh = 'spazToes'
    old_lady_sounds = ['spaz1', 'spaz2', 'spaz3', 'spaz4']
    old_lady_hit_sounds = ['spazHit1', 'spazHit2', 'spazogImpact03', 'spazogImpact04']
    t.jump_sounds = ['spazogJump01', 'spazogJump02', 'spazogJump03', 'spazogJump04']
    t.attack_sounds = old_lady_sounds
    t.impact_sounds = old_lady_hit_sounds
    t.death_sounds = ['spazDeath']
    t.pickup_sounds = ['spazogPickup']
    t.victory_sounds = ['spazogJump01']
    t.fall_sounds = ['spazFall']
    t.style = 'spaz'

    # Bombgeon's Ninja ###################################
    t = Appearance('Bombgeon Snake Shadow')
    t.color_texture = 'ninjaColor'
    t.color_mask_texture = 'ninjaColorMask'
    t.icon_texture = 'ninjaIcon'
    t.icon_mask_texture = 'ninjaIconColorMask'
    t.head_mesh = 'ninjaHead'
    t.torso_mesh = 'ninjaTorso'
    t.pelvis_mesh = 'ninjaPelvis'
    t.upper_arm_mesh = 'ninjaUpperArm'
    t.forearm_mesh = 'ninjaForeArm'
    t.hand_mesh = 'ninjaHand'
    t.upper_leg_mesh = 'ninjaUpperLeg'
    t.lower_leg_mesh = 'ninjaLowerLeg'
    t.toes_mesh = 'ninjaToes'
    ninja_attacks = ['ninjaAttack' + str(i + 1) + '' for i in range(7)]
    ninja_hits = ['ninjaHit' + str(i + 1) + '' for i in range(8)]
    ninja_jumps = ['ninjaAttack' + str(i + 1) + '' for i in range(7)]
    t.jump_sounds = ninja_jumps
    t.attack_sounds = ninja_attacks
    t.impact_sounds = ninja_hits
    t.death_sounds = ['ninjaDeath1']
    t.pickup_sounds = ninja_attacks
    t.fall_sounds = ['ninjaFall2']
    t.style = 'ninja'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
