"""Handler for dialogue system."""
import bascenev1 as bs
import babase as ba

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
                    'position': (-290, 200),
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
        x = -250 if not entry.get("character") else -180 
        # Text node
        self.text_node = bs.newnode(
            'text',
            attrs={
                'text': '',
                'position': (x, 160),
                'scale': 1.3,
                'h_align': 'left',
                'v_align': 'top',
                'maxwidth': 600,
                'color': (1, 1, 1),
                'v_attach': 'bottom',
            },
        )

        self.full_text = entry["text"]
        self.index = 0
        self.sound = entry.get("sound")

        self._start_typing()

    # -------------------------

    def _start_typing(self):
        def tick():
            if not self.text_node:
                self._typing_timer = None
                return
            if self.index >= len(self.full_text):
                self.finished = True
                self._typing_timer = None
                return

            self.text_node.text += self.full_text[self.index]
            self.index += 1

            if self.sound:
                bs.getsound(self.sound).play()

        self._typing_timer = bs.Timer(0.04, tick, repeat=True)

    def skip(self):
        """Instantly finish the text."""
        if self.finished:
            return
        self.text_node.text = self.full_text
        self.finished = True
        self._typing_timer = None

    def delete(self):
        for node in (self.bg, self.name_text, self.text_node, self.portrait):
            if node:
                node.delete()


class DialogueManager:
    """Manager for the dialogue. Use this to create dialogue."""
    def __init__(self, activity: bs.Activity, entries: list[dict]):
        self.activity = activity
        self.entries = entries
        self.index = 0
        self.box: DialogueBox | None = None

        self._bind_inputs()
        self._show_entry()

    # -------------------------

    def _show_entry(self):
        if self.box:
            self.box.delete()

        if self.index >= len(self.entries):
            self.end()
            return

        self.box = DialogueBox(self.entries[self.index])

    def advance(self):
        if not self.box:
            return

        if not self.box.finished:
            self.box.skip()
        else:
            self.index += 1
            self._show_entry()

    def end(self):
        if self.box:
            self.box.delete()
        self._unbind_inputs()

    # -------------------------
    # INPUT
    # -------------------------

    def _bind_inputs(self):
        for player in self.activity.players:
            player.assigninput(bs.InputType.PUNCH_PRESS, self.advance)
            player.assigninput(bs.InputType.BOMB_PRESS, self.end)
            player.assigninput(bs.InputType.JUMP_PRESS, self.advance)

    def _unbind_inputs(self):
        for player in self.activity.players:
            if player.actor:
                player.actor.connect_controls_to_player()
