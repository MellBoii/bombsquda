"""UI class for selecting specific textures."""
from __future__ import annotations

from typing import TYPE_CHECKING, cast, override
from bauiv1lib.popup import PopupWindow
import bauiv1 as bui

class TexturePicker(PopupWindow):
    """Popup UI to select a texture."""

    def __init__(
        self,
        parent: bui.Widget,
        position: tuple[float, float],
        *,
        textures: list[str],
        delegate: Any = None,
        scale: float | None = None,
        offset: tuple[float, float] = (0.0, 0.0),
        tag: Any = '',
    ):
        assert bui.app.classic is not None

        self._textures = textures
        self._delegate = delegate
        self._parent = parent
        self._position = position
        self._offset = offset
        self._tag = tag
        self._transitioning_out = False

        uiscale = bui.app.ui_v1.uiscale
        if scale is None:
            scale = (
                2.3
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            )
        self._scale = scale

        # Grid sizing (auto based on amount)
        cols = 4
        rows = (len(textures) + cols - 1) // cols

        width = 22 + cols * 45
        height = 40 + rows * 45

        super().__init__(
            position=position,
            size=(width, height),
            scale=scale,
            bg_color=(0.5, 0.5, 0.5),
            offset=offset,
        )

        self._buttons: list[bui.Widget] = []

        for i, tex_name in enumerate(textures):
            x = i % cols
            y = i // cols

            tex = bui.gettexture(tex_name)

            btn = bui.buttonwidget(
                parent=self.root_widget,
                position=(22 + 45 * x, height - 50 - 45 * y),
                size=(40, 40),
                label='',
                button_type='square',
                texture=tex,
                on_activate_call=bui.WeakCall(self._select, tex_name),
                autoselect=True,
                color=(1, 1, 1),
            )
            self._buttons.append(btn)

    def _select(self, texture: str) -> None:
        if self._delegate:
            self._delegate.texture_picker_selected(self, texture)
        bui.apptimer(0.05, self._transition_out)

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            if self._delegate:
                self._delegate.texture_picker_closing(self)
            bui.containerwidget(edit=self.root_widget, transition='out_scale')
    
    def get_tag(self) -> Any:
        """Return this popup's tag value."""
        return self._tag

    @override
    def on_popup_cancel(self) -> None:
        if not self._transitioning_out:
            bui.getsound('swish').play()
        self._transition_out()