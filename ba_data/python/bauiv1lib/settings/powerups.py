"""ui for turning on and off powerups"""
from typing import override

import bascenev1 as bs
import bauiv1 as bui
import fromgoverhaul.mell_resources as mell

class PowerupSetupWindow(bui.MainWindow):
    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        safesize = bui.get_virtual_safe_area_size()
        uiscale = bui.app.ui_v1.uiscale
        # We're a generally widescreen shaped window, so bump our
        # overall scale up a bit when screen width is wider than safe
        # bounds to take advantage of the extra space.
        smallscale = min(2.0, 1.5 * screensize[0] / safesize[0])
        scale = (
            smallscale
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.8
        )
        width = 1000 if uiscale is bui.UIScale.SMALL else 800
        height = 600
        target_height = min(height - 70, screensize[1] / scale)
        target_width = min(width - 80, screensize[0] / scale)
        yoffs = 0.5 * height + 0.5 * target_height + 30.0
        self._r = 'powerupsWindow'
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
        self.tex_bomb = bui.gettexture('powerupBomb')
        self.tex_punch = bui.gettexture('powerupPunch')
        self.tex_ice_bombs = bui.gettexture('powerupIceBombs')
        self.tex_sticky_bombs = bui.gettexture('powerupStickyBombs')
        self.tex_shield = bui.gettexture('powerupShield')
        self.tex_impact_bombs = bui.gettexture('powerupImpactBombs')
        self.tex_health = bui.gettexture('powerupHealth')
        self.tex_metal = bui.gettexture('powerupMetal')
        self.tex_fireball = bui.gettexture('powerupFireball')
        self.tex_bloxy = bui.gettexture('powerupBloxy')
        self.tex_deton = bui.gettexture('powerupDeton')
        self.tex_hook = bui.gettexture('powerupHook')
        self.tex_shotgun = bui.gettexture('powerupShotgun')
        self.tex_random = bui.gettexture('powerupRandom')
        self.tex_strong = bui.gettexture('powerupStrong')
        self.tex_spongebob = bui.gettexture('powerupSponge')
        self.tex_star = bui.gettexture('powerupStar')
        self.tex_land_mines = bui.gettexture('powerupLandMines')
        self.tex_curse = bui.gettexture('powerupCurse')
        self.tex_random = bui.gettexture('powerupRandom')
        self.tex_kookoo = bui.gettexture('curseKookoo')
        
        self._powerups = dict(bs._powerup.get_default_powerup_distribution())
        self._scroll = bui.scrollwidget(
            parent=self._root_widget,
            size=(width - 80, height - 100),
            position=(40, 40),
        )
        self._sub = bui.containerwidget(
            parent=self._scroll,
            size=(width - 100, len(self._powerups) * 63),
            background=False,   
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
        self._checkboxes = {}
        for i, (ptype, weight) in enumerate(self._powerups.items()):
            offset = 30
            y = len(self._powerups) * 60 - i * 60 - offset
            x = 150
            tex = mell.get_texture_for_powerup(self, ptype)
            # icon
            bui.imagewidget(
                parent=self._sub,
                position=(x, y),
                size=(50, 50),
                texture=tex,
            )

            # checkbox
            self._checkboxes[ptype] = bui.checkboxwidget(
                parent=self._sub,
                position=(x + 60, y),
                size=(300, 40),
                text=bui.Lstr(resource=f'{self._r}.{ptype}'),
                value=weight > 0,
                on_value_change_call=bui.Call(self._toggle_powerup, ptype),
            )
    def _toggle_powerup(self, ptype: str, value: bool):
        cfg = bui.app.config

        custom = cfg.get('squda_powerup_dist', {})

        if value:
            custom[ptype] = 1  # enable
        else:
            custom[ptype] = 0  # disable

        cfg['squda_powerup_dist'] = custom
        cfg.apply_and_commit()
    
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )