"""stuff for the earthbound like engine"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, override
import bascenev1 as bs
import weakref

SHOW_HITBOXES = False
SPRITE_MAP = {
    'up_right': 'ur',
    'up_left': 'ul',
    'down_right': 'dr',
    'down_left': 'dl',
    'right': 'right',
    'left': 'left',
    'up': 'up',
    'down': 'down',
}
OPPOSITE_DIRECTION = {
    "up_left": "down_right",
    "up_right": "down_left",
    "down_left": "up_right",
    "down_right": "up_left",
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left",
}
COLBOX_COLOR = (1, 0, 0.5)
HITBOX_COLOR = (1, 1, 1)

# Messages are often a safe 
# way to communicate so use that, 
# instead of directly running a function.
class MoveMessage:
    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y

class PauseMessage:
    def __init__(self, state: bool):
        self.state = state

class DummyCharacterActor(bs.Actor):
    """A dummy actor that does nothing. This should ALWAYS be 
    used as a parent-class (subclass?) so we can check for it's instance."""
    def __init__(self):
        super().__init__()

class Scene(bs.Actor):
    """A 2D Scene. Any actors should be attached to it, 
    whether moving around if not static, or just connected when static."""
    def __init__(
        self, 
        texture: str, 
        size: tuple[float, float] = (2048, 1024),
        scale: int | float = 2.2,
        position = (0.0, 0.0),
    ):
        super().__init__()
        self.connected_actors: list[bs.Actor] = []
        self.walls: list[CollisionBox] = []
        self.texture = texture
        self.scale = (size[0] * scale, size[1] * scale)
        self.node = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture(self.texture),
                'opacity': 1.0,
                'absolute_scale': True,
                'position': position,
                'scale': self.scale,
                'attach': 'center',
            },
        )
        
    def _move(self, x: int = 0, y: int = 0):
        px, py = self.node.position
        self.node.position = (px + x, py + y)
    
    def _would_collide(self, actor, wall, dx, dy):
        future_x = actor.hitbox.position[0] - dx
        future_y = actor.hitbox.position[1] - dy
        ax, ay = future_x, future_y
        bx, by = wall.node.position
        aw = actor.hitbox.scale[0] / 2
        ah = actor.hitbox.scale[1] / 2
        bw = wall.node.scale[0] / 2
        bh = wall.node.scale[1] / 2
        return (
            abs(ax - bx) < aw + bw and
            abs(ay - by) < ah + bh
        )
    
    def try_move(self, dx, dy):
        for wall in self.walls:
            actor = self._activity().players[0].actor
            if self._would_collide(actor, wall, dx, dy):
                return  # block movement
        for actor in self.connected_actors:
            if isinstance(actor, ScenePlayer):
                continue
            actor.handlemessage(MoveMessage(dx, dy))
        self._move(dx, dy)
    
    @override
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            for actor in self.connected_actors:
                actor.handlemessage(bs.DieMessage())
            self.node.delete()
        elif isinstance(msg, MoveMessage):
            self.try_move(msg.x, msg.y)
        else:
            super().handlemessage(msg) # Augment standard behavior.
    
class CollisionBox(bs.Actor):
    """A wall or something that can be collided with. 
    This should tell actors to push themselves back 
    from the direction they pointed at when they collide 
    with us. There is no special things that can be done with this; 
    this is meant to be used as a simple collision object."""
    def __init__(
        self, 
        position: tuple[float, float], 
        scale: tuple[float, float] = (50.0, 50.0),
    ):
        super().__init__()
        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': bs.gettexture('white'),
                'opacity': 0.5 if SHOW_HITBOXES else 0.0,
                'absolute_scale': True,
                'position': position,
                'scale': scale,
                'attach': 'center',
                'color': COLBOX_COLOR,
            },
        )
        # Connect to the scene so we can move along with the map
        # sprite and ACTUALLY act like proper collision
        self._activity().scene.connected_actors.append(self)
        # Turn off this timer, and i'll make sure both 
        # sides of your pillow this night are warm.
        scene = self._activity().scene
        scene.walls.append(self)

    def _overlaps(self, a, b):
        dx = abs(a.position[0] - b.position[0])
        dy = abs(a.position[1] - b.position[1])

        limit_x = a.scale[0] / 2 + b.scale[0] / 2
        limit_y = a.scale[1] / 2 + b.scale[1] / 2
        result = dx < limit_x and dy < limit_y
        return result
    
    def _move(self, x: int = 0, y: int = 0):
        px, py = self.node.position
        self.node.position = (px + x, py + y)
    
    @override
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
        elif isinstance(msg, MoveMessage):
            self._move(msg.x, msg.y)
        else:
            super().handlemessage(msg) # Augment standard behavior.

class SceneNPC(bs.Actor):
    """This is a scene NPC that ScenePlayers can interact with.
    Use this for NPCs around that should have dialogue.
    Since interacting calls a function, you can make it 
    do anything instead of just show up some dialogue!"""
    def __init__(
        self, 
        scene: Scene,
        position: tuple[float, float] = (0.0, 0.0),
        size: tuple[float, float] = (50.0, 50.0),
        scale: int | float = 1.6,
        charname: str = 'mell'
    ):
        super().__init__()
        self.scene = scene
        self.xTimer = None
        self.yTimer = None
        self._frame = 1
        self._last_facing = None
        self.scale = (size[0] * scale, size[1] * scale)
        self.hscale = (size[0] - 3.5 * scale, size[1] - 5 * scale)
        self.facing = 'down'
        self.charname = charname
        self.anim_timer = bs.Timer(0.17, self._set_sprite, repeat=True)
        self.check_timer = bs.Timer(0.02, self._check_for_overlap, repeat=True)        

        # Our node. Control it like a sprite.
        self.node = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture(f'{charname}_down1'),
                'opacity': 1.0,
                'absolute_scale': True,
                'position': position,
                'scale': self.scale,
                'attach': 'center',
            },
        )
        # The reason we often use images for hitboxes
        # is so we can calculate whether another actor
        # is within the hitbox by using the image's
        # position and scale. This is often easier, and 
        # allows for custom sized hitboxes.
        # Ugly, but it works!
        self.hitbox = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': bs.gettexture('white'),
                'opacity': 0.5 if SHOW_HITBOXES else 0.0,
                'absolute_scale': True,
                'position': (position[0], position[1]),
                'scale': self.hscale,
                'attach': 'center',
                'color': HITBOX_COLOR,
            },
        )
        cam = 5
        self.collision = CollisionBox(
            position=self.node.position, 
            scale=(
                self.hscale[0] - cam, 
                self.hscale[1] - cam,
            )
        )
        self.scene.connected_actors.append(self)
        mathnode = bs.newnode(
            'math',
            owner=self.node,
            attrs={'input1': (0, -20), 'operation': 'add'},
        )
        self.node.connectattr('position', mathnode, 'input2')
        mathnode.connectattr('output', self.hitbox, 'position')
        mathnode.connectattr('output', self.collision.node, 'position')
    
    def _overlaps(self, a, b):
        dx = abs(a.position[0] - b.position[0])
        dy = abs(a.position[1] - b.position[1])

        limit_x = a.getdelegate(bs.Actor).hscale[0] / 2 + b.getdelegate(bs.Actor).hscale[0] / 2
        limit_y = a.getdelegate(bs.Actor).hscale[1] / 2 + b.getdelegate(bs.Actor).hscale[1] / 2
        result = dx < limit_x and dy < limit_y
        return result
        
    def _set_sprite(self):
        self._frame = 2 if self._frame == 1 else 1

        sprite = SPRITE_MAP.get(self.facing)
        if not sprite:
            return

        self.node.texture = bs.gettexture(
            f'{self.charname}_{sprite}{self._frame}'
        )
    
    def _move(self, x: int = 0, y: int = 0):
        px, py = self.node.position
        self.node.position = (px + x, py + y)
    
    def _check_for_overlap(self):
        player = self._activity().players[0].actor

        if self._overlaps(player.hitbox, self.hitbox):
            player._can_interact = True
            player._int_actor = weakref.ref(self)

        else:
            if player._int_actor is not None:
                actor = player._int_actor()
                if actor is self:
                    player._can_interact = False
                    player._int_actor = player._nothing
    
    def face_player(self, player):
        player_facing = player.facing
        self.facing = OPPOSITE_DIRECTION.get(player_facing)
        self._set_sprite()
    
    def on_interacted(self):
        print('hi')
        
    @override
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
            self.hitbox.delete()
            self.xTimer = None
            self.yTimer = None
        elif isinstance(msg, MoveMessage):
            self._move(msg.x, msg.y)
        if isinstance(msg, PauseMessage):
            if msg.state == True:
                self.anim_timer = None
            else:
                self.anim_timer = bs.Timer(0.17, self._set_sprite, repeat=True)
        else:
            super().handlemessage(msg) # Augment standard behavior.
        return super().handlemessage(msg) # Augment standard behavior.

class ScenePlayer(DummyCharacterActor):
    """Rather than being a normal player type, this is a actor that should 
    be controlled by a player. It is meant to be attached to a scene, and move around with it."""
    @override
    def on_expire(self):
        self.xTimer = None
        self.yTimer = None
        self._anim_timer = None
    
    def __init__(
        self, 
        player: bs.Player, 
        scene: Scene,
        position: tuple[float, float] = (0.0, 0.0),
        size: tuple[float, float] = (50.0, 50.0),
        scale: int | float = 1.6,
        charname: str = 'mell'
    ):
        super().__init__()
        self.player = player
        self.scene = scene
        self.xTimer = None
        self.yTimer = None
        self._frame = 1
        self._last_facing = None
        self._anim_timer: bs.Timer | None = None
        self.scale = (size[0] * scale, size[1] * scale)
        self._size = scale
        self.hscale = (size[0] - 3.5 * scale, size[1] - 15 * scale)
        self.facing = 'down' # default facing, can be changed by update_spritetype
        self.charname = charname
        self._int_actor = self._nothing
        self._can_interact = False
        self.x_stick = 0.0
        self.y_stick = 0.0

        # Our node. Control it like a sprite.
        self.node = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture(f'{charname}_down1'),
                'opacity': 1.0,
                'absolute_scale': True,
                'position': position,
                'scale': self.scale,
                'attach': 'center',
            },
        )
        # The reason we often use images for hitboxes
        # is so we can calculate whether another actor
        # is within the hitbox by using the image's
        # position and scale. This is often easier, and 
        # allows for custom sized hitboxes.
        # Ugly, but it works!
        self.hitbox = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': bs.gettexture('white'),
                'opacity': 0.5 if SHOW_HITBOXES else 0.0,
                'absolute_scale': True,
                'position': (position[0], position[1]),
                'scale': self.hscale,
                'attach': 'center',
                'color': HITBOX_COLOR,
            },
        )
        self.scene.connected_actors.append(self)
        mathnode = bs.newnode(
            'math',
            owner=self.node,
            attrs={'input1': (0, -25), 'operation': 'add'},
        )
        self.node.connectattr('position', mathnode, 'input2')
        mathnode.connectattr('output', self.hitbox, 'position')
        self.speed = 0.001
        self._anim_counter = 0
        self._anim_rate = max(4, int(0.03 / self.speed))
        self.amount_mult = 2
        self.paused = False
    
    def interact(self):
        if not self._can_interact and not self._int_actor():
            return
        bs.getsound('confirm').play()
        self._int_actor().on_interacted()
        self._int_actor().face_player(self)
    
    def _nothing(self):
        pass
    
    def _move(self, x=0, y=0):
        self.scene.handlemessage(MoveMessage(x=x, y=y))
        if x or y:
            self._anim_counter += 1

            if self._anim_counter >= self._anim_rate:
                self._anim_counter = 0
                self._advance_frame()
    
    def handle_x_hold(self, amount: int):
        self.x_stick = amount
        self.update_spritetype()
        self.xTimer = bs.Timer(
            self.speed,
            lambda: self._move(x=-amount * self.amount_mult),
            repeat=True
        )

    def handle_y_hold(self, amount: int):
        self.y_stick = amount
        self.update_spritetype()
        self.yTimer = bs.Timer(
            self.speed,
            lambda: self._move(y=-amount * self.amount_mult),
            repeat=True
        )
        
    def update_spritetype(self) -> str:
        deadzone = 0

        x = self.x_stick
        y = self.y_stick

        if x == 0 and y == 0:
            return self.facing

        horizontal = 'right' if x > 0 else 'left' if x < 0 else ''
        vertical = 'up' if y > 0 else 'down' if y < 0 else ''

        new_facing = f'{vertical}_{horizontal}'.strip('_') or horizontal or vertical

        if new_facing != self.facing:
            self.facing = new_facing
            self._frame = 1
            self._anim_counter = 0
            self._advance_frame()

        return self.facing
        
    def _advance_frame(self):
        if self.paused:
            return
        self._frame = 2 if self._frame == 1 else 1

        sprite = SPRITE_MAP.get(self.facing)
        if not sprite:
            return

        self.node.texture = bs.gettexture(
            f'{self.charname}_{sprite}{self._frame}'
        )

    @override
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
            self.hitbox.delete()
            self.xTimer = None
            self.yTimer = None
            self._anim_timer = None
        elif isinstance(msg, MoveMessage):
            self._move(msg.x, msg.y)
        elif isinstance(msg, PauseMessage):
            self.paused = msg.state
            self.xTimer = None
            self.yTimer = None
        else:
            super().handlemessage(msg) # Augment standard behavior.
        return super().handlemessage(msg) # Augment standard behavior.