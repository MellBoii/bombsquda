"""Handler for dialogue system."""
import bascenev1 as bs
import babase as ba
import re
from bascenev1lib.actor.image_looped import LoopingImageAnimation
TOKEN_RE = re.compile(r"\{(\w+)=([^}]+)\}")

class DialogueChoiceBox(bs.Actor):
    """Box for choosing things"""
    def __init__(self, choices: list[tuple[str, str]], on_choose):
        super().__init__()

        self.choices = choices
        self.on_choose = on_choose
        self.index = 0
        self.nodes: list[bs.Node] = []

        base_y = 120
        spacing = 35
        base_x = 570

        for i, (text, _) in enumerate(choices):
            node = bs.newnode(
                'text',
                attrs={
                    'text': text,
                    'position': (base_x, base_y - i * spacing),
                    'h_align': 'right',
                    'v_attach': 'bottom',
                    'h_attach': 'center',
                    'scale': 1.2,
                    'color': (0.8, 0.8, 0.8, 1),
                    'shadow': 0.5,
                },
            )
            self.nodes.append(node)

        self.hand = LoopingImageAnimation(
            'spazhand', 
            frame_count=7, 
            frame_delay=0.06, 
            scale=(60, 60), 
            position=(base_x + 30, base_y),
            loop=True,
            attach="bottomCenter",
        )

        self._update_highlight()

    def _update_highlight(self):
        for i, node in enumerate(self.nodes):
            if i == self.index:
                handpos = self.hand.node.position
                self.hand.node.position = (handpos[0], node.position[1] + 40)

    def move(self, direction: int):
        self.index = (self.index + direction) % len(self.nodes)
        bs.getsound('deek').play()
        self._update_highlight()

    def confirm(self):
        _, label = self.choices[self.index]
        self.hand.node.delete()
        self.delete()
        self.on_choose(label)

    def delete(self):
        for node in self.nodes:
            if node:
                node.delete()
        self.nodes.clear()

class DialogueBox:
    """Dialogue box."""
    def __init__(self, entry: dict):
        self.entry = entry
        self.finished = False
        self._typing_timer: bs.Timer | None = None
        self.continue_timer: bs.Timer | None = None

        # Background
        self.bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('dialog_box'),
                'position': (0, 120),
                'scale': (900, 260),
                'opacity': 0.5,
                'attach': 'bottomCenter',
            },
        )

        # Name (optional)
        x = -370 if not entry.get("character") else -265
        self.name_text = None
        if entry.get("name"):
            self.name_text = bs.newnode(
                'text',
                attrs={
                    'text': entry["name"],
                    'position': (x + 15, 170),
                    'scale': 1.7,
                    'h_align': 'left',
                    'color': (1, 1, 1),
                    'v_attach': 'bottom',
                },
            )

        # Portrait (optional)
        self.portrait = None
        if entry.get("character"):
            tex = f'dialogue/{entry["character"]}_{entry.get("expression","neutral")}'
            self.portrait = bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture(tex),
                    'position': (-360, 120),
                    'scale': (200, 200),
                    'attach': 'bottomCenter',
                },
            )
        # Text node
        self.text_node = bs.newnode(
            'text',
            attrs={
                'text': '',
                'position': (x, 160),
                'scale': 1.3,
                'h_align': 'left',
                'v_align': 'top',
                'maxwidth': 500,
                'color': (1, 1, 1),
                'v_attach': 'bottom',
            },
        )
        self.continue_icon = bs.newnode(
            'text',
            attrs={
                'text': ba.charstr(ba.SpecialChar.TOP_BUTTON),
                'position': (380, 20),
                'scale': 1.2,
                'opacity': 0.0,
                'v_attach': 'bottom',
            },
        )

        self.full_text = entry["text"]
        self.index = 0
        self.sound = entry.get("sound")
        self.tokens = self.parse_dialogue(self.entry["text"])
        self.token_index = 0

        self._start_typing()

    # -------------------------
    def parse_dialogue(self, text: str):
        tokens = []
        i = 0

        for match in TOKEN_RE.finditer(text):
            # text before token
            while i < match.start():
                tokens.append(("char", text[i]))
                i += 1

            cmd, value = match.group(1), match.group(2)

            if cmd == "pause":
                tokens.append(("pause", float(value)))
            elif cmd == "expr":
                tokens.append(("expr", value))
            elif cmd == "sound":
                tokens.append(("sound", value))
            elif cmd == "eval":
                tokens.append(("eval", value))

            i = match.end()

        # remaining text
        while i < len(text):
            tokens.append(("char", text[i]))
            i += 1

        return tokens
    
    def set_expression(self, expr: str):
        if not self.portrait:
            return
        tex = f'dialogue/{self.entry["character"]}_{expr}'
        self.portrait.texture = bs.gettexture(tex)
        
    def _start_typing(self):
        def tick():
            if not self.text_node:
                self._typing_timer = None
                return
            if self.token_index >= len(self.tokens):
                self.finished = True
                self._on_finished()
                self._typing_timer = None
                return

            kind, value = self.tokens[self.token_index]
            self.token_index += 1

            if kind == "char":
                self.text_node.text += value
                if self.sound:
                    bs.getsound(self.sound).play()

            elif kind == "pause":
                self._typing_timer = bs.Timer(value, self._start_typing)
                return
            elif kind == "eval":
                eval(value)
            elif kind == "expr":
                self.set_expression(value)
            elif kind == "sound":
                bs.getsound(value).play()

        self._typing_timer = bs.Timer(0.04, tick, repeat=True)

    def _on_finished(self):
        def animate():
            bs.animate(self.continue_icon, 'opacity', {
                0.0: 0.0,
                0.4: 1.0,
                0.8: 0.0,
            })
        animate()
        self.continue_timer = bs.Timer(0.8, animate, repeat=True)

    def skip(self):
        """Instantly finish the text."""
        if self.finished:
            return
        self.text_node.text = re.sub(r"\{[^}]+\}", "", self.full_text)
        self.finished = True
        self._typing_timer = None
        self._on_finished()

    def delete(self):
        for node in (self.bg, self.name_text, self.text_node, self.portrait, self.continue_icon):
            if node:
                node.delete()
        self.continue_timer = None
        self._typing_timer = None


class DialogueManager:
    """Manager for the dialogue. Use this to create dialogue."""
    def __init__(self, entries: list[dict]):
        self.entries = entries
        self.index = 0
        self.entry = None
        self.box: DialogueBox | None = None
        self.choice_box = None
        self.current = None

        self._bind_inputs()
        self._show_entry()

    def move_choice(self, value: float):
        if not self.choice_box:
            return
        
        self.choice_box.move(value)

    def _show_entry(self):
        if self.box:
            self.box.delete()
        try:
            entry = self.entries[self.index]
        except (KeyError, IndexError):
            self.end()
            return
        if self.current:
            entry = self.entries[self.current]
        self.entry = entry
        self.box = DialogueBox(entry)

        if "choices" in entry:
            def wait_and_continue():
                if self.box and self.box.finished:
                    self.choice_box = DialogueChoiceBox(
                        entry["choices"],
                        self._on_choice
                    )
                else:
                    self.wait_timer2 = bs.Timer(0.05, wait_and_continue)
            wait_and_continue()
        else:
            self.choice_box = None

        if entry.get("interrupt"):
            # auto-advance when text finishes
            def wait_and_continue():
                if self.box and self.box.finished:
                    self.index += 1
                    self._show_entry()
                else:
                    self.wait_timer = bs.Timer(0.05, wait_and_continue)
            wait_and_continue()

    def _on_choice(self, target_id: str):
        self.current = target_id
        self._show_entry()

    def advance(self):
        if not self.box:
            return
        if self.choice_box:
            self.choice_box.confirm()
            return

        if not self.box.finished:
            self.box.skip()
        else:
            if "next" in self.entry:
                self.current = self.entry["next"]
                self._show_entry()
            else:
                self.index += 1
                self._show_entry()
                bs.getsound('deek').play()

    def end(self):
        if self.box:
            self.box.delete()
        self._unbind_inputs()

    # -------------------------
    # INPUT
    # -------------------------
    def _bind_inputs(self):
        for player in bs.get_foreground_host_activity().players:
            player.assigninput(bs.InputType.PICK_UP_PRESS, self.advance)
            player.assigninput(bs.InputType.UP_PRESS, lambda: self.move_choice(-1))
            player.assigninput(bs.InputType.DOWN_PRESS, lambda: self.move_choice(1))

    def _unbind_inputs(self):
        for player in bs.get_foreground_host_activity().players:
            if player.actor:
                player.actor.connect_controls_to_player()
