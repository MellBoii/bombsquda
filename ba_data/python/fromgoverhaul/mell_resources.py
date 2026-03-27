""" 
Resources that should be easier to edit in a shared code,
like lists, server address, game version, and some useful functions.
"""
screams = ['screams/scream' + str(i + 1) + '' for i in range(15)]
server = "https://bombsquda.tailc76b25.ts.net"
version = '2.1'
update_date = '2/21/2026'

def add_spaz(
    amount: int | float = 50,
    currency: str = 'tix',
    text_pos=None,
    notif_type: str = 'screen',
):
    import bascenev1 as bs
    import babase as ba
    # gotta leave here otherwise doesn't work
    CURRENCIES = {
        'tix': {
            'config_key': 'squda_spaztix',
            'glyph': ba.SpecialChar.OUYA_BUTTON_Y,
            'resource': 'spazTickets',
        },
        'tokens': {
            'config_key': 'squda_spaztokens',
            'glyph': ba.SpecialChar.OUYA_BUTTON_A,
            'resource': 'spazTokens',
        },
    }

    # validate whether said currency is in ours
    if currency not in CURRENCIES:
        raise TypeError(
            f"{currency} is invalid. Allowed: {list(CURRENCIES.keys())}"
        )

    data = CURRENCIES[currency]

    # Safely update config
    config_key = data['config_key']
    ba.app.config[config_key] = ba.app.config.get(config_key, 0) + amount
    ba.app.config.apply_and_commit()

    # Shared values
    glyph = ba.charstr(data['glyph'])
    activity = bs.get_foreground_host_activity()
    prefix = '+' if amount > 0 else '-'

    # popup messages
    if notif_type == 'popup':
        # raise error if no activity
        if not (text_pos and activity):
            raise TypeError("Popup requires text_pos and active activity")

        with activity.context:
            from bascenev1lib.actor.popuptext import PopupText

            PopupText(
                f'{prefix}{amount}{glyph}',
                position=text_pos,
                color=(0.643, 0.4, 0.961),
                scale=1.4,
                lifespan=3.5,
            ).autoretain()

            bs.getsound('gainCur').play(volume=1.7, position=text_pos)

    # screen messages
    elif notif_type == 'screen':
        display = f"{glyph} {bs.Lstr(resource=data['resource']).evaluate()}"

        bs.broadcastmessage(
            bs.Lstr(
                resource='wonCustomCurrency',
                subs=[
                    ('${AMOUNT}', str(amount)),
                    ('${CURRENCY}', display),
                ],
            )
        )
        bs.getsound('cashRegister2').play(volume=2.0)
    # not in valid types
    else:
        raise TypeError(
            f"{notif_type} invalid. Allowed: ['screen', 'popup']"
        )

def get_texture_for_powerup(factory, ptype: str):
    """Get a texture from a powerup string from a factory.
    Doesn't specifically have to be PowerupBoxFactory, 
    but you should use that."""
    import babase as ba
    texture_map = {
        'triple_bombs': factory.tex_bomb,
        'punch': factory.tex_punch,
        'ice_bombs': factory.tex_ice_bombs,
        'sticky_bombs': factory.tex_sticky_bombs,
        'shield': factory.tex_shield,
        'impact_bombs': factory.tex_impact_bombs,
        'health': factory.tex_health,
        'land_mines': factory.tex_land_mines,
        'curse': factory.tex_curse,
        'metal': factory.tex_metal,
        'deton': factory.tex_deton,
        'hook': factory.tex_hook,
        'fireball': factory.tex_fireball,
        'bloxy': factory.tex_bloxy,
        'strong': factory.tex_strong,
        'spongebob': factory.tex_spongebob,
        'shotgun': factory.tex_shotgun,
        'star': factory.tex_star,
        'random': factory.tex_random,
        'kookoo': factory.tex_kookoo,
        'dozer': factory.tex_dozer,
        'ire': factory.tex_ire,
        'sorrow': factory.tex_sorrow,
    }
    if ptype not in texture_map:
        print(f'ERROR: {ptype} is not in the texture map. Please add it to mell_resources.\ndumbass')
        # get whether we should use ui with..
        # ..a context error. okay.
        try:
            return bs.gettexture('white')
        except ba.ContextError:
            return bui.gettexture('white')
    return texture_map.get(ptype)

# wow... old code...
def shake_node(
    node, 
    intensity: float = 10.0, 
    duration: float = 1.0, 
    interval: float = 0.02,
    array_num: int = 2,
):
    """
    Shake a node.
    :param node: The node to shake (like your image or text).
    :param intensity: How strong shall we shake.
    :param duration: Duration of the shake.
    :param interval: The interval it updates at. Lower values are smoother but 
    often can go fast, and higher values are staticky but slower.
    :param array_num: Number of arrays. Using anything other than 2 uses 3 array numbers.
    """
    import bascenev1 as bs
    import random
    if not node:
        return

    original_pos = tuple(node.position)
    total_steps = int(duration / interval)
    step = 0

    def _update_shake():
        nonlocal step
        if not node or step >= total_steps:
            # Snap back to original position at the end
            if node:
                node.position = original_pos
            return

        # Calculate diminishing shake strength (optional)
        progress = step / total_steps
        falloff = 1.0 - progress
        current_intensity = intensity * falloff

        # Random offset around original position
        offset_x = random.uniform(-current_intensity, current_intensity)
        offset_y = random.uniform(-current_intensity, current_intensity)
        if array_num == 2:
            node.position = (
                original_pos[0] + offset_x,
                original_pos[1] + offset_y,
            )
        else:
            # we don't shake z pos, so it's not really weird
            node.position = (
                original_pos[0] + offset_x,
                original_pos[1] + offset_y,
                original_pos[2]
            )

        step += 1
        bs.timer(interval, _update_shake)

    _update_shake()

# keeping this here for later

# def send_friend_request(name: str):
    # session = requests.Session()
    # try:
        # session.post(
            # f"{SERVER}/friends/request",
            # json={
                # "from": get_clean_display_name(),
                # "to": name
            # },
            # timeout=2
        # )
        # bs.screenmessage(f"Friend request sent to {name}")
    # except Exception:
        # bs.screenmessage("Failed to send friend request", color=(1, 0, 0))

# def respond_friend_request(name: str, accept: bool):
    # session = requests.Session()
    # session.post(
        # f"{SERVER}/friends/respond",
        # json={
            # "user": get_clean_display_name(),
            # "from": name,
            # "accept": accept
        # },
        # timeout=2
    # )
