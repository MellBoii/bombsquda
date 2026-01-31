"""Handler for dialogue system."""
import bascenev1 as bs
import babase as ba
import re
TOKEN_RE = re.compile(r"\{(\w+)=([^}]+)\}")

class DialogueBox:
    """Dialogue box."""
    def __init__(self, entry: dict):
        self.entry = entry
        self.finished = False
        self._typing_timer: bs.Timer | None = None

        # Background
        self.bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('black'),
                'position': (0, 120),
                'scale': (900, 260),
                'opacity': 0.5,
                'attach': 'bottomCenter',
            },
        )

        # Name (optional)
        self.name_text = None
        if entry.get("name"):
            self.name_text = bs.newnode(
                'text',
                attrs={
                    'text': entry["name"],
                    'position': (-270, 170),
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
        x = -360 if not entry.get("character") else -265
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
                'text': '>>>',
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

            elif kind == "expr":
                self.set_expression(value)
            elif kind == "sound":
                bs.getsound(value).play()

        self._typing_timer = bs.Timer(0.04, tick, repeat=True)

    def _on_finished(self):
        bs.animate(self.continue_icon, 'opacity', {
            0.0: 0.0,
            0.4: 1.0,
        })

    def skip(self):
        """Instantly finish the text."""
        if self.finished:
            return
        self.text_node.text = re.sub(r"\{[^}]+\}", "", self.full_text)
        self.finished = True
        self._typing_timer = None

    def delete(self):
        for node in (self.bg, self.name_text, self.text_node, self.portrait, self.continue_icon):
            if node:
                node.delete()


class DialogueManager:
    """Manager for the dialogue. Use this to create dialogue."""
    def __init__(self, entries: list[dict]):
        self.entries = entries
        self.index = 0
        self.box: DialogueBox | None = None

        self._bind_inputs()
        self._show_entry()

    # -------------------------

    def _show_entry(self):
        if self.box:
            self.box.delete()

        try:
            entry = self.entries[self.index]
        except IndexError:
            self.end()
            return
        self.box = DialogueBox(entry)

        if entry.get("interrupt"):
            # auto-advance when text finishes
            def wait_and_continue():
                if self.box and self.box.finished:
                    self.index += 1
                    self._show_entry()
                else:
                    self.wait_timer = bs.Timer(0.05, wait_and_continue)
            wait_and_continue()

    def advance(self):
        if not self.box:
            return

        if not self.box.finished:
            self.box.skip()
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

    def _unbind_inputs(self):
        for player in bs.get_foreground_host_activity().players:
            if player.actor:
                player.actor.connect_controls_to_player()
