""" 
Common-ish resources that are either 
too long or should be easier to edit here.
It has stuff like lyrics, the server address, and such.
"""
# Lyrics for Feel The Fury
FEEL_THE_FURY = [
    ("C'mon, bring it!", 12.33),
    ('How are you him? Can you please explain it?', 27.29),
    ('No matter who you are, you just cannot fake it', 28.65),
    ("Livin' on the edge of reality", 30.33),
    ('If you mess with my friends, you gonna mess with me', 31.96),
    ('You destroy my home, you invade this land', 33.93),
    ('Listen real close so you understand', 35.52),
    ('Tougher than leather, we in this together', 37.15),
    ("You're never gonna win, team Knuckles forever!", 38.75),
    ('Pick up the pace, let me see what you got now', 40.76),
    ("Keep it real short, this will end, that's my vow", 42.21),
    ('No time for the fake, only real ones allowed', 44.03),
    ('Stand in my way, watch me tear through the crowd', 45.61),
    ('Left right, left right, left right, down', 47.34),
    ('Left right, left right, left right, down', 49.03),
    ("You got another thing coming if you think I'll quit", 50.99),
    ('Can you feel the fury, that primal rage?', 53.25),
    ('It holds me back every day, this urge with no release', 55.91),
    ('Will you feel the fury and show me what was taken', 59.6),
    ('Shaken, that had made you this way?', 63.07),
    ('Can you feel the fury that has held me back?', 66.53),
    ("Stopped me from seeing the way, but I won't hold back now", 69.48),
    ('Can you feel the fury? So please, just let this be', 73.24),
    ('The way that I can honor their names', 76.2),
    ("You can't have it all, no matter how much you want it", 94.75),
    ("Some things in life, you just can't flaunt it", 96.33),
    ("I see through, no need for the frontin'", 98.12),
    ("You need a mask, that's the only assumption", 99.66),
    ("The truth hits hard, but it's what you need", 101.39),
    ('Stay steady on your grind, let your actions lead', 102.89),
    ("No time for the fake, I'm too busy stayin' true", 104.61),
    ('Keep it real, real, real', 106.29),
    ("Time's ticking low, let's go another round", 108.21),
    ('Victory in sight, hear that champion sound', 109.66),
    ("Fueling up the fire, you can't keep me down", 111.4),
    ('Push past my limits turning fate all around', 113.03),
    ('Left right, left right, left right, down', 114.81),
    ('Left right, left right, left right, down', 116.64),
    ("If you think this is over, you're wrong", 118.32),
    ("We're just getting started", 119.86),
    ('Can you feel the fury, that primal rage?', 120.84),
    ('It holds me back every day, this urge with no release', 123.55),
    ('Will you feel the fury and show me what was taken', 127.01),
    ('Shaken, that had made you this way?', 130.51),
    ('Can you feel the fury that has held me back?', 134.02),
    ("Stopped me from seeing the way, but I won't hold back now", 137.06),
    ('Can you feel the fury? So please, just let this be', 140.57),
    ('The way that I can honor their names', 143.8),
    ('Can you feel the fury, that primal rage?', 174.8),
    ('It holds me back every day, this urge with no release', 177.65),
    ('Will you feel the fury and show me what was taken', 181.2),
    ('Shaken, that had made you this way?', 184.57),
    ('Can you feel the fury that has held me back?', 188.3),
    ("Stopped me from seeing the way, but I won't hold back now", 191.25),
    ('Can you feel the fury? So please, just let this be', 194.76),
    ('The way that I can honor their names', 197.74),
    ('Oh, oh', 201.02),
    ('Can you feel the fury?', 206.45),
]
screams = ['screams/scream' + str(i + 1) + '' for i in range(10)]
server = "https://bombsquda.tailc76b25.ts.net"
version = '2.1'
update_date = '2/21/2026'
currencies = ['tix', 'tokens']

def add_spaz(
    amount: int | float = 50, 
    currency: str = 'tix', 
    text_pos = None,
    notif_type: str = 'screen',
):
    """
    A config change function; made to
    just simplify changing a amount of currency.
    As per suggested, it adds the specified amount to a 'spaz' currency
    (eg. spaztickets, spaztokens, and stuff that can be added later...)
    """
    import bascenev1 as bs
    import babase as ba
    # Return if currency not in current currency types
    if currency not in currencies:
        raise TypeError(f'{currency} is a incorrect custom currency type. \nAllowed: {currencies} (tix is short for tickets)')
        return
    # Change config
    ba.app.config[f'squda_spaz{currency}'] += amount
    ba.app.config.apply_and_commit()
    # Show text if we have a position and activity
    activity = bs.get_foreground_host_activity()
    glyph = (
        ba.charstr(ba.SpecialChar.OUYA_BUTTON_Y) # tickets
        if currency == 'tix' else
        ba.charstr(ba.SpecialChar.OUYA_BUTTON_A) # tokens
        if currency == 'tokens' else
        ba.charstr(ba.SpecialChar.TICKET) # placeholder
    )
    if notif_type == 'popup':
        if text_pos and activity:
            with activity.context:
                from bascenev1lib.actor.popuptext import PopupText
                PopupText(
                    f'+{amount}{glyph}',
                    position=text_pos,
                    color=(0.643, 0.4, 0.961),
                    scale=1.4,
                    lifespan=3.5,
                ).autoretain()
                bs.getsound('cashRegister2').play(volume=2.0, position=text_pos)
        else:
            raise TypeError("Notification type was 'popup' but no text_pos was given or no activity exists")
    elif notif_type == 'screen':
        display = (
            f'{glyph} {bs.Lstr(resource='spazTickets').evaluate()}' if currency == 'tix'
            else f'{glyph} {bs.Lstr(resource='spazTokens').evaluate()}' if currency == 'tokens'
            else f'{glyph} {bs.Lstr(resource='unknownCurrency').evaluate()}'
        )
        bs.broadcastmessage(bs.Lstr(
                resource='wonCustomCurrency', 
                subs=[
                    ('${AMOUNT}', str(amount)),
                    ('${CURRENCY}', display),
                ]
            ),
        )
        bs.getsound('cashRegister2').play(volume=2.0)
    else:
        raise TypeError(f"{notif_type} is a incorrect notification type.\nAllowed: ['screen', 'popup']")


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
