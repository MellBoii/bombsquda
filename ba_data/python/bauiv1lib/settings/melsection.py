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

if TYPE_CHECKING:
    from typing import Callable

class ParrySelectionWindow(bui.Window):
    """
    Allows you to like
    set different parry time windows
    but then like
    you dont get  as much benefit
    or somethin idk
    """

    def __init__(self, origin: Sequence[float] = (0, 0)):
        bui.set_party_window_open(True)
        self._width = 800
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._height= 600
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
            ),
            # We exist in the overlay stack so main-windows being
            # recreated doesn't affect us.
            prevent_main_window_auto_recreate=False,
        )
        uiscale = bui.app.ui_v1.uiscale
        leftside = self._width / self._width + 100
        short = 180
        self.parry1button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(leftside, self._height - short),
            size=(200, 200),
            textcolor=(1, 1, 1),
            scale=0.8,
            text_scale=1.5,
            label='ez',
            on_activate_call=self.parrysetup3,
        )
        self.parry2button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(leftside, self._height - short * 2),
            size=(200, 200),
            textcolor=(1, 1, 1),
            scale=0.8,
            text_scale=1.5,
            label='mid',
            on_activate_call=self.parrysetup2,
        )
        self.parry3button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(leftside, self._height - short * 3),
            size=(200, 200),
            textcolor=(1, 1, 1),
            scale=0.8,
            text_scale=1.3,
            label='precise \nas fuck',
            on_activate_call=self.parrysetup1,
        )
        textersspace = 210
        bui.textwidget(
            parent=self._root_widget,
            position=(leftside + textersspace, self._height - short),
            size=(150, 150),
            text='This will change parry timing to be 0.3. \nEasier to parry, but you get less health.',
            h_align='left',
            v_align='center',
            scale=1.0,
            maxwidth=500,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(leftside + textersspace, self._height - short * 2),
            size=(150, 150),
            text='This will change parry timing to be 0.2. \nIt will not affect health, nor will \nadd anything special.',
            h_align='left',
            v_align='center',
            scale=1.0,
            maxwidth=500,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(leftside + textersspace, self._height - short * 3),
            size=(150, 150),
            text='This will change parry timing to be 0.1. \nHarder to hit parries, but you can \ncounter and get more health.',
            h_align='left',
            v_align='center',
            scale=1.0,
            maxwidth=500,
        )
        
    def close(self) -> None:
        """Close the window."""
        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
        
    # can someone out there tell me if 
    # there's a easier way to do this
    def parrysetup1(self) -> None:
        cfg = bui.app.config
        cfg['squda_parrytype'] = 1
        cfg.apply_and_commit()
        self.close()
        
    def parrysetup2(self) -> None:
        cfg = bui.app.config
        cfg['squda_parrytype'] = 2
        cfg.apply_and_commit()
        self.close()
        
    def parrysetup3(self) -> None:
        cfg = bui.app.config
        cfg['squda_parrytype'] = 3
        cfg.apply_and_commit()
        self.close()
    
class MelWindow(bui.MainWindow):
    """Window for selecting BombSquda settings."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
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
        self._settings = [
            ("squda_spazfuckedup", "spazBigEyesText", 300, False),
            ("squda_noisepolution", "noisePollutionText", 250, False),
            ("squda_gamblingmode", "gamblingModeText", 200, False),
            ("squda_spazhardmode", "spazHardModeText", 150, True),
            ("squda_parryalways", "parryAlwaysText", 100, False),
            ("squda_dontshutdown", "dontShutdownText", 50, False),
            ("squda_dontdomarioman", "noMarioDelayText", 0, False),
            ("squda_richpresence", "discordRpcText", -50, False),
            ("squda_enablemeter", "enableMeterText", -100, False),
            ("squda_nosugarcoats", "noSugarcoatingText", -150, False),
            ("squda_disablemm", "disableMetalMusicText", -200, False),
            ("squda_customfont", "customFontWarningText", -250, False),
            ("squda_speedrunner", "speedrunTimerText", -300, False),
            ("squda_blood", "enableBloodText", -350, False),
        ]
        self.is_small = bui.app.ui_v1.uiscale is bui.UIScale.SMALL
        scale = (
            smallscale
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.8
        )
        if self.is_small:
            col_x = [150, 500]   # left & right columns
            start_y = 320
            row_height = 60
        else:
            col_x = [250]
            start_y = 300
            row_height = 50
        
        target_height = min(height - 70, screensize[1] / scale)
        yoffs = 0.5 * height + 0.5 * target_height + 30.0
        
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
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
                position=(50, yoffs - 80.0),
                size=(70, 70),
                scale=0.8,
                text_scale=1.2,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            scale=1.0,
            maxwidth=4000,
        )
        # i love thefuckedupuifix!! thefuckedupuifix forever!!
        thefuckedupuifix = 210 if self.is_small else 350
        self._checkboxes = {}

        for i, (key, label_key, _y, playsound) in enumerate(self._settings):
            
            if self.is_small:
                col = i % 2
                row = i // 2
            else:
                col = 0
                row = i

            x = col_x[col]
            y = start_y - row * row_height

            self._checkboxes[key] = bui.checkboxwidget(
                parent=self._root_widget,
                position=(x, y + thefuckedupuifix),
                size=(220, 40),
                autoselect=False,
                maxwidth=260,
                textcolor=(1.0, 1.0, 1.0),
                value=bui.app.config.get(key, False),
                text=bui.Lstr(resource=f"{self._r}.{label_key}"),
                on_value_change_call=bui.Call(self._set_config, key, sound=playsound),
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
        if platform not in ['windows', 'linux']:
            bs.screenmessage('twinny. this clearly renames files. it doesnt work on non-windows.')
            return
        local = os.getcwd() + '\\ba_data'
        textures = local + '\\textures\\'
        os.rename(textures + 'fontSmall0.dds', textures + 'oldefont.dds')
        os.rename(textures + 'fontBig.dds', textures + 'oldefont2.dds')
        os.rename(textures + 'fontALT0.dds', textures + 'fontSmall0.dds')
        os.rename(textures + 'fontBigALT.dds', textures + 'fontBig.dds')
        os.rename(textures + 'oldefont.dds', textures + 'fontALT0.dds')
        os.rename(textures + 'oldefont2.dds', textures + 'fontBigALT.dds')
        bs.screenmessage('doing media reload to apply change...')
        bui.app.classic.run_media_reload_benchmark()

    def _set_config(self, key: str, val: bool, sound: bool = False) -> None:
        cfg = bui.app.config
        cfg[key] = val
        cfg.apply_and_commit()
        bs.debprint(f'{key} changed into {val}')
        if key == 'squda_customfont':
            self.changefont()

        if sound:
            if val:
                bui.getsound('baditem').play()
            else:
                bui.getsound('okitem').play()