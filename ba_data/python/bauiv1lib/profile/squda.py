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
import random
import fromgoverhaul.mell_resources as mell
from bauiv1lib.popup import PopupMenu
from bauiv1lib.texturepicker import TexturePicker
from bauiv1lib.colorpicker import ColorPicker
from pathlib import Path

if TYPE_CHECKING:
    from typing import Callable
    
class SqudaProfileEditWindow(bui.MainWindow):
    """Window for editing your profile."""
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
        height = 650
        self._r = 'friendsTab'

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
        # remember to ALWAYS increase 
        # by 50 whenever adding a new option
        self._sub_height = 500.0
        y = start_y = self._sub_height - 200
        scroll_bottom = yoffs - 56 - self._scroll_height
        self.is_small = bui.app.ui_v1.uiscale is bui.UIScale.SMALL
        
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility='menu_full',
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
        info = mell.get_info_from_id(mell.get_unique_bs_id())
        self._texture = info.get('avatar', 'null')
        self._cmtexture = info.get('cm_avatar', 'white')
        self._color = tuple(info.get('color', [1, 1, 1]))
        self._highlight = tuple(info.get('highlight', [1, 1, 1]))
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5, height - 38),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.profileEditTitle'),
            color=bui.app.ui_v1.title_color,
            maxwidth=290,
            scale=1.0,
            h_align='center',
            v_align='center',
        )
        # label and avatar
        x = self._sub_width * 0.2
        self._texture_button = bui.buttonwidget(
            label='',
            parent=self._subcontainer,
            position=(x, y),
            autoselect=True,
            on_activate_call=bui.Call(self.open_texture_picker, 'tex', (x, y)),
            texture=bui.gettexture(self._texture),
            size=(100, 100),
            color=(1, 1, 1),
            scale=1.1,
        )
        bui.textwidget(
            parent=self._subcontainer,
            position=(x, y + 100),
            size=(100, 100),
            text=bui.Lstr(resource=f'{self._r}.avatarText'),
            maxwidth=200,
            h_align='center',
            v_align='center',
        )
        # label and color mask avatar
        x = self._sub_width * 0.6
        self._cm_texture_button = bui.buttonwidget(
            label='',
            parent=self._subcontainer,
            position=(x, y),
            autoselect=True,
            on_activate_call=bui.Call(self.open_texture_picker, 'cmtex', (x, y)),
            texture=bui.gettexture(self._cmtexture),
            size=(100, 100),
            color=(1, 1, 1),
            scale=1.1,
        )
        bui.textwidget(
            parent=self._subcontainer,
            position=(x, y + 100),
            size=(100, 100),
            text=bui.Lstr(resource=f'{self._r}.avatarCMText'),
            maxwidth=200,
            h_align='center',
            v_align='center',
        )
        # full avatar preview
        y -= 200
        x = self._sub_width * 0.38
        self._icon_preview = bui.imagewidget(
            parent=self._subcontainer,
            position=(x, y),
            texture=bui.gettexture(self._texture),
            tint_texture=bui.gettexture(self._cmtexture),
            mask_texture=bui.gettexture('characterIconMask'),
            tint_color=self._color,
            tint2_color=self._highlight,
            size=(128, 128),
        )
        bui.textwidget(
            parent=self._subcontainer,
            position=(x, y + 100),
            size=(128, 128),
            text=bui.Lstr(resource=f'{self._r}.avatarPreviewText'),
            maxwidth=200,
            h_align='center',
            v_align='center',
        )
        # color pickers
        x = self._sub_width * 0.15
        y += 5
        b_size = 100
        self._color_button = btn = bui.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(x, y),
            size=(b_size, b_size),
            color=self._color,
            label='',
            button_type='square',
        )
        bui.textwidget(
            parent=self._subcontainer,
            position=(x, y + 70),
            size=(b_size, b_size),
            text=bui.Lstr(r=f'{self._r}.colorText'),
            maxwidth=200,
            h_align='center',
            v_align='center',
        )
        origin = self._color_button.get_screen_space_center()
        bui.buttonwidget(
            edit=self._color_button,
            on_activate_call=bui.WeakCall(self._make_picker, 'color', origin),
        )
        x = self._sub_width * 0.65
        self._highlight_button = btn = bui.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(x, y),
            size=(b_size, b_size),
            color=self._highlight,
            label='',
            button_type='square',
        )
        bui.textwidget(
            parent=self._subcontainer,
            position=(x, y + 70),
            size=(b_size, b_size),
            text=bui.Lstr(r=f'{self._r}.highlightText'),
            maxwidth=200,
            h_align='center',
            v_align='center',
        )
        origin = self._highlight_button.get_screen_space_center()
        bui.buttonwidget(
            edit=self._highlight_button,
            on_activate_call=bui.WeakCall(self._make_picker, 'highlight', origin),
        )
        y -= 5
        # save button
        y -= 80
        x = self._sub_width * 0.1
        bui.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(x, y),
            size=(self._sub_width * 0.8, 80),
            label=bui.Lstr(r=f'{self._r}.saveToServerText'),
            on_activate_call=bui.WeakCall(self._save_data),
        )
    
    def open_texture_picker(self, tag: str, position: Sequence[tuple, tuple]):
        # it's a little unsafe to be allowing everyone to
        # just access the textures and use them... but,
        # i do kinda want them to get creative and mesh together
        # textures to make a neat looking avatar!
        # ...or just make a character's icon manually. eh.
        path = os.path.join(
            bui.app.env.data_directory,
            'ba_data',
            'textures',
        )
        # get the stem so we only get filename
        textures = [f.stem for f in Path(path).iterdir() if f.is_file()]
        # make the picker
        TexturePicker(
            parent=self._root_widget,
            position=position,
            delegate=self,
            textures=textures,
            tag=tag,
        )
    
    def _make_picker(
        self, picker_type: str, origin: tuple[float, float]
    ) -> None:
        if picker_type == 'color':
            initial_color = self._color
        elif picker_type == 'highlight':
            initial_color = self._highlight
        else:
            raise ValueError('invalid picker_type: ' + picker_type)
        ColorPicker(
            parent=self._root_widget,
            position=origin,
            initial_color=initial_color,
            delegate=self,
            tag=picker_type,
        )
    
    def color_picker_closing(self, picker: ColorPicker) -> None:
        """Called when a color picker is closing."""
        if not self._root_widget:
            return
        tag = picker.get_tag()
        if tag == 'color':
            bui.containerwidget(
                edit=self._root_widget, selected_child=self._color_button
            )
        elif tag == 'highlight':
            bui.containerwidget(
                edit=self._root_widget, selected_child=self._highlight_button
            )
        else:
            print('color_picker_closing got unknown tag ' + str(tag))

    def color_picker_selected_color(
        self, picker: ColorPicker, color: tuple[float, float, float]
    ) -> None:
        """Called when a color is selected in a color picker."""
        if not self._root_widget:
            return
        tag = picker.get_tag()
        if tag == 'color':
            self._set_color(color)
        elif tag == 'highlight':
            self._set_highlight(color)
        else:
            print('color_picker_selected_color got unknown tag ' + str(tag))
    
    def texture_picker_selected(self, source: TexturePicker, texture: str) -> None:
        """A character has been selected by the picker."""
        if not self._root_widget:
            return
        tag = source.get_tag()
        if tag == 'tex':
            button = self._texture_button
            self._texture = texture
        elif tag == 'cmtex':
            button = self._cm_texture_button
            self._cmtexture = texture
        bui.buttonwidget(edit=button, texture=bui.gettexture(texture))
        if tag == 'tex':
            bui.imagewidget(
                edit=self._icon_preview, 
                texture=bui.gettexture(texture)
            )
        elif tag == 'cmtex':
            bui.imagewidget(
                edit=self._icon_preview, 
                tint_texture=bui.gettexture(texture)
            )
    
        
    def texture_picker_closing(self, source: TexturePicker) -> None:
        pass
        
    def _set_color(self, color: tuple[float, float, float]) -> None:
        self._color = color
        if self._color_button:
            bui.buttonwidget(edit=self._color_button, color=color)
        bui.imagewidget(
            edit=self._icon_preview, 
            tint_color=color
        )

    def _set_highlight(self, color: tuple[float, float, float]) -> None:
        self._highlight = color
        if self._highlight_button:
            bui.buttonwidget(edit=self._highlight_button, color=color)
        bui.imagewidget(
            edit=self._icon_preview, 
            tint2_color=color
        )
    
    def _save_data(self):
        data = {
            'avatar': self._texture,
            'cm_avatar': self._cmtexture,
            'color': list(self._color),
            'highlight': list(self._highlight),
        }
        result = mell.set_profile_data(data)
        if (
            result.get('status') in ['error', 'fail']
            or result.get('error')
        ):
            full_error = (
                f"{data.get('status', '')}"
                f"{chr(10) if data.get('status') else ''}"
                f"{data.get('error', '')}"
                f"{chr(10) if data.get('error') else ''}"
                f"{data.get('message', '')}"
            )
            bui.screenmessage(
                bui.Lstr(
                    resource=f'{self._r}.errorGenericDescriptive',
                    subs=[('${ERROR}', full_error)],
                ),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
        else:
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.savedText'),
                color=(0, 1, 0),
            )
            bui.getsound('ding').play()
            self.main_window_back()
        
    
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
