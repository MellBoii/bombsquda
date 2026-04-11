# Released under the MIT License. See LICENSE for details.
#
"""UI for setting... settings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence, override
import logging

import bauiv1 as bui
import bascenev1 as bs
import os
import babase
from bauiv1lib.popup import PopupMenu

if TYPE_CHECKING:
    from typing import Callable
    
class MelWindow(bui.MainWindow):
    """Window for selecting BombSquda settings."""
    @staticmethod
    def _create(t, o, ft):
        return MelWindow(
            transition=t,
            origin_widget=o,
            first_time=ft,
        )
    
    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        first_time: bool = False,
    ):
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('BombSquda Settings')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 750
        self._r = 'melWindow'

        uiscale = bui.app.ui_v1.uiscale
        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        safesize = bui.get_virtual_safe_area_size()

        # We're a generally widescreen shaped window, so bump our
        # overall scale up a bit when screen width is wider than safe
        # bounds to take advantage of the extra space.
        smallscale = min(2.0, 1.5 * screensize[0] / safesize[0])
        scale = (
            smallscale
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.8
        )
        target_height = min(height - 70, screensize[1] / scale)
        target_width = min(width - 80, screensize[0] / scale)
        yoffs = 0.5 * height + 0.5 * target_height + 30.0
        self._scroll_width = target_width - 30
        self._scroll_height = target_height - 45
        self._sub_width = min(500, self._scroll_width * 0.95)
        self._sub_height = 1300.0
        start_y = self._sub_height - 60
        spacing = 2
        scroll_bottom = yoffs - 56 - self._scroll_height
        col_x = width * 0.12
        if uiscale is bui.UIScale.SMALL:
            col_x -= 40
        raw_settings = [
            ("squda_noisepolution", "noisePollutionText", None),
            ("squda_foxyjumpscare", "foxyJumpscareText", None),
            ("squda_spazhardmode", "spazHardModeText", ['hardmode', 'okitem']),
            ("squda_parryalways", "parryAlwaysText", ['attempt_parry', 'voicelines/kris/pickup']),
            ("squda_dontshutdown", "dontShutdownText", ['gooditem', 'baditem']),
            ("squda_dontdomarioman", "noMarioDelayText", ['quit', 'blip']),
            ("squda_richpresence", "discordRpcText", None),
            ("squda_enablemeter", "enableMeterText", ['shield2', 'shieldReflect']),
            ("squda_nosugarcoats", "noSugarcoatingText", ['bellLow', 'bellMed']),
            ("squda_disablemm", "disableMetalMusicText", None),
            ("squda_customfont", "customFontWarningText", None),
            ("squda_speedrunner", "speedrunTimerText", None),
            ("squda_blood", "enableBloodText", ['gibbed', 'party_blower']),
            ("squda_noparticles", "noParticlesText", None),
            ("squda_coopnames", "coopNamesText", ['voicelines/spaz/jump02', 'spazJump02']),
            ("squda_pausemusic", "pauseMusicText", ['pause', 'unpause']),
            ("squda_showerrors", "showErrorsText", ['randomnoises/noisePolution8', 'default_win']),
            ("squda_noonline", "noOnlineText", ['connected', 'connecting']),
            ("squda_botnames", "botNamesText", None),
            ("squda_randomgrace", "randomEntitiesText", ['mikiwhatthefuck', 'mikiwhatthefuck2']),
        ]
        self._settings = [
            (key, text, start_y - i * spacing, sound)
            for i, (key, text, sound) in enumerate(raw_settings)
        ]
        self.is_small = bui.app.ui_v1.uiscale is bui.UIScale.SMALL
        self.reset_clicks = 0
        self._first_time = first_time
        
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL or first_time
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(self._scroll_width, self._scroll_height),
            position=(
                width * 0.5 - self._scroll_width * 0.5,
                scroll_bottom,
            ),
            simple_culling_v=20.0,
            highlight=False,
            center_small_content_horizontally=True,
            selection_loops_to_parent=True,
            border_opacity=0.4,
        )
        bui.widget(edit=self._scrollwidget, right_widget=self._scrollwidget)
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            selection_loops_to_parent=True,
        )
        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(50, yoffs - 50.0),
                size=(70, 70),
                scale=0.8,
                text_scale=1.2,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        if first_time:
            position = (width - 30, yoffs - 80.0)
            scale = 0.8
            if uiscale is bui.UIScale.SMALL:
                position = (width - 140, yoffs - 130.0)
                scale = 1.0
            contbtn = bui.buttonwidget(
                parent=self._root_widget,
                position=position,
                size=(70, 70),
                label='->',
                scale=scale,
                autoselect=True,
                on_activate_call=self._continue,
            )

        bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (55 if uiscale is bui.UIScale.SMALL else 35)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,
        )
        self._checkboxes = {}
        row_height = 50

        for i, (key, label_key, start_y, playsound) in enumerate(self._settings):
            row = i
            x = col_x
            y = start_y - row * row_height

            self._checkboxes[key] = bui.checkboxwidget(
                parent=self._subcontainer,
                position=(x, y),
                size=(220, 40),
                autoselect=False,
                maxwidth=300,
                textcolor=(1.0, 1.0, 1.0),
                value=bui.app.config.get(key, False),
                text=bui.Lstr(resource=f"{self._r}.{label_key}"),
                on_value_change_call=bui.Call(self._set_config, key, sound=playsound),
            )
            
        size = (350, 50)
        
        row += 1
        y = start_y - row * row_height
        xoffset = 70
        bui.textwidget(
            parent=self._subcontainer,
            position=(col_x - xoffset, y + 25),
            size=(0, 0),
            text=bui.Lstr(resource=f"{self._r}.entityChance"),
            maxwidth=300,
            scale=0.8,
            h_align='left',
            v_align='center',
        )
        choices = [0.1, 0.3, 0.5, 0.8, 1.0]
        def _format_chance(c: float) -> str:
            text = f"{c:.1f}".rstrip('0').rstrip('.')
            newtext = text.replace('.', '')
            return newtext
        choices_display = [
            bui.Lstr(resource=f"{self._r}.chance{_format_chance(c)}")
            for c in choices
        ]
        self._entity_chance_popup = PopupMenu(
            parent=self._subcontainer,
            position=(col_x + 280 - xoffset, y),
            width=250,
            autoselect=False,
            on_value_change_call=bui.WeakCall(self._chance_choice),
            choices=choices,
            choices_display=choices_display,
            button_size=(200, 50),
            current_choice=bui.app.config.get("squda_entitychance"),
        )
        
        
        row += 1
        y = start_y - row * row_height
        bui.textwidget(
            parent=self._subcontainer,
            position=(col_x - xoffset, y + 25),
            size=(0, 0),
            text=bui.Lstr(resource=f"{self._r}.menuMusic"),
            maxwidth=300,
            scale=0.8,
            h_align='left',
            v_align='center',
        )
        choices = [str(None)]
        choices.extend('MENU' + str(i + 1) for i in range(17))
        self._music_popup = PopupMenu(
            parent=self._subcontainer,
            position=(col_x + 280 - xoffset, y),
            width=250,
            autoselect=False,
            on_value_change_call=bui.WeakCall(self._music_choice),
            choices=choices,
            button_size=(200, 50),
            current_choice=bui.app.config.get("squda_menumusic"),
        )
        
        
        row += 1
        y = start_y - row * row_height
        self.powerup_setup = bui.buttonwidget(
            parent=self._subcontainer,
            position=(col_x, y),
            size=size,
            text_scale=1.0,
            label=bui.Lstr(resource=f'{self._r}.powerupSetup'),
            on_activate_call=self._open_powerup_setup,
        )
        if not first_time:
            row += 1
            y = start_y - row * row_height
            self.name_setup = bui.buttonwidget(
                parent=self._subcontainer,
                position=(col_x, y),
                size=size,
                text_scale=1.0,
                label=bui.Lstr(resource=f'{self._r}.nameSetup'),
                on_activate_call=self._open_name_setup,
            )
        row += 1
        y = start_y - row * row_height
        self.reset_ach_btn = bui.buttonwidget(
            parent=self._subcontainer,
            position=(col_x, y),
            size=size,
            text_scale=1.0,
            label=bui.Lstr(resource=f'{self._r}.resetAchievements'),
            on_activate_call=self._reset_achievements,
        )

    
    def changefont(self) -> None:
        # THE FOLLOWING CODE BELOW
        # SHOULD **NEVER** BE REPLICATED IN
        # AN ACTUAL WELL DEVELOPED MODPACK!!
        # NOT ONLY ARE THEY ARBITRARY AND RENAME
        # FILES (WHICH ALSO MEANS THEY REVERT
        # EVERY UPDATE), BUT THEY COULD JUST SCREW UP
        # SOMETHING AND I DON'T EVEN KNOW THAT!!
        app = babase.app
        platform = app.classic.platform
       
        local = bui.app.env.data_directory + '\\ba_data'
        textures = local + '\\textures\\'
        os.rename(textures + 'fontSmall0.dds', textures + 'oldefont.dds')
        os.rename(textures + 'fontBig.dds', textures + 'oldefont2.dds')
        os.rename(textures + 'fontALT0.dds', textures + 'fontSmall0.dds')
        os.rename(textures + 'fontBigALT.dds', textures + 'fontBig.dds')
        os.rename(textures + 'oldefont.dds', textures + 'fontALT0.dds')
        os.rename(textures + 'oldefont2.dds', textures + 'fontBigALT.dds')
        bs.screenmessage('doing media reload to apply change...')
        bui.app.classic.run_media_reload_benchmark()
    
    def _chance_choice(self, choice):
        key = "squda_entitychance"
        cfg = bui.app.config
        cfg[key] = choice
        cfg.apply_and_commit()
        bs.debprint(f'{key} changed into {choice}')
    
    def _music_choice(self, choice):
        from bascenev1lib.mainmenu import MainMenuActivity
        key = "squda_menumusic"
        cfg = bui.app.config
        cfg[key] = choice
        cfg.apply_and_commit()
        bs.debprint(f'{key} changed into {choice}')
        activity = bs.get_foreground_host_activity()
        if isinstance(activity, MainMenuActivity):
            activity.menu_music()

    def _set_config(self, key: str, val: bool, sound: bool = False) -> None:
        cfg = bui.app.config
        cfg[key] = val
        cfg.apply_and_commit()
        bs.debprint(f'{key} changed into {val}')
        if key == 'squda_customfont':
            self.changefont()

        if sound:
            if val:
                bui.getsound(sound[0]).play()
            else:
                bui.getsound(sound[1]).play()

    def _continue(self) -> None:
        from bascenev1lib.game.surveyprogram import SurveyIntroWindow
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
            
        self.main_window_replace(
            SurveyIntroWindow(
                transition='in_right',
                origin_widget=self._root_widget,
                step=1,
            )
        )
        
    def _open_name_setup(self):
        from bauiv1lib.settings.rename_survey import NameSurveyAllWindow
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
            
        self.main_window_replace(
            NameSurveyAllWindow(
                origin_widget=self._root_widget
            )
        )
    
    def _open_powerup_setup(self):
        from bauiv1lib.settings.powerups import PowerupSetupWindow
        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
            
        self.main_window_replace(
            PowerupSetupWindow(
                origin_widget=self._root_widget
            )
        )
    
    def _reset_achievements(self):
        if self.reset_clicks < 2:
            bui.getsound('error').play()
            bui.screenmessage(
                bs.Lstr(resource=f'{self._r}.confirmReset'),
                color=(1, 0.5, 0)
            )
            self.reset_clicks += 1
        else:
            bui.getsound('baditem').play()
            bui.app.config['squda_achievements'] = {}
            bui.screenmessage(
                bs.Lstr(resource=f'{self._r}.achResetDone'),
                color=(1, 0.1, 0.1)
            )
            self.reset_clicks = 0
            
    @override
    def get_main_window_state(self):
        return bui.BasicMainWindowState(
            create_call=lambda t, o, ft=self._first_time:
                MelWindow._create(t, o, ft)
        )