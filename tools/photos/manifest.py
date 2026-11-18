"""The 2026 photo set (Rich Nixx Media): which original becomes which web file, and its alt text.

id -> (source file stem on the photo drive, or "event folder words|stem" when two events share a number, crop box as fractions (left, top, right, bottom) or None, alt text)
Web files are sl26-<id>.webp (2000 px), sl26-<id>-m.webp (1200 px) and sl26-<id>-t.webp (800 px).
Alt text rules: one plain sentence, no dashes, no staff or member names.
"""
PHOTOS = {
    # drone
    "morning-ponds":     ("DJI_20260701094719_0014_D", None, "Morning light over two ponds, pines and bunkers at Spring Lakes, seen from the air"),
    "golden-flare":      ("DJI_20260712202345_0107_D", (0, 0, .93, 1), "The sun setting over fairways and bunkers at Spring Lakes, seen from the air"),
    "property-wide":     ("DJI_20260701162502_0098_D", None, "Aerial view across Spring Lakes with the island green and the clubhouse"),
    "dusk-fairway":      ("DJI_20260712203621_0131_D", (0, .08, .745, .86), "Dusk over a fairway and bunkers, with the clubhouse in the trees"),
    "island-green":      ("DJI_20260701162144_0092_D", None, "The island green beside the clubhouse, seen from the air"),
    "golden-fairways":   ("DJI_20260712202841_0116_D", (.53, .2, 1, .71), "Golden evening light over fairways, ponds and bunkers, seen from the air"),
    "clubhouse-aerial":  ("DJI_20260701163128_0113_D", None, "The clubhouse and the island green from the air"),
    "ponds-wide":        ("DJI_20260712203312_0126_D", None, "Wide aerial view of fairways, ponds and bunkers at Spring Lakes"),
    "ponds-above":       ("DJI_20260701145025_0086_D", None, "Two ponds, a green and winding cart paths seen from straight above"),
    "figure-eight-pond": ("DJI_20260712192400_0105_D", (0, 0, .95, .735), "A figure eight pond ringed by bunkers, seen from straight above"),
    # the land
    "bunker-blue-sky":   ("_RSN0355", None, "A bunker and fairway under a blue summer sky"),
    "green-big-sky":     ("RSN06834", None, "A green on the East Course under a big summer sky"),
    "storm-fairway":     ("_RSN0417", None, "Storm clouds building over a fairway"),
    "bunker-big-sky":    ("RSN06553", None, "A greenside bunker under a wide sky"),
    "pond-pines":        ("_RSN9900", None, "A pond edged with reeds and tall pines"),
    "flag-green-pond":   ("_RSN0120", None, "A Canada flag on a green beside a pond"),
    "pond-reflection":   ("_RSN0168", None, "Golfers on a green, reflected in a pond"),
    "fescue":            ("_RSN0009", None, "Tall fescue in front of a line of spruce"),
    "swan":              ("RSN07908", None, "A swan on one of the ponds"),
    "sun-rays":          ("_RSN0419", None, "Sun rays breaking through storm cloud over a fairway"),
    "green-bunker":      ("_RSN9149", None, "A green and bunker framed by maples"),
    "pond-channel":      ("Club Championship|_RSN9866", None, "A quiet channel of water between reeds and willows"),
    # the clubhouse and grounds
    "clubhouse-green":   ("_RSN0152", None, "The clubhouse across a green with a Canada flag on the pin"),
    "clubhouse-fountain": ("_RSN0096", None, "The clubhouse across the pond and fountain"),
    "clubhouse-gardens": ("_RSN5979", None, "The clubhouse veranda and gardens"),
    "heron-sculpture":   ("_RSN5992", None, "A heron sculpture in the flower garden by the clubhouse"),
    "white-chairs":      ("_RSN9724", None, "Two white chairs in the shade of a spruce"),
    "stone-lettering":   ("_RSN0441", None, "Spring Lakes Golf Club engraved in stone at the entrance"),
    # members at play
    "chip-shot":         ("_RSN5965", None, "A golfer chipping onto a green"),
    "bunker-shot":       ("RSN06108", (0, 0, .93, 1), "A golfer playing from a bunker, sand in the air"),
    "members-putting":   ("RSN06700", None, "Members putting under a big sky"),
    "teams-clubhouse":   ("RSN06409", (0, .04, 1, .76), "Two teams of members gathered in front of the clubhouse"),
    "banquet-room":      ("_RSN8579", None, "Members at round tables in the clubhouse banquet room"),
    "handshake-green":   ("_RSN9302", None, "Four players shaking hands on a green"),
    "tee-shot-maple":    ("_RSN9143", None, "A tee shot framed by a maple"),
    "foursome-tee":      ("_RSN8959", None, "A foursome on the tee"),
    "walking-bags":      ("_RSN9469", None, "Two members walking a fairway with their bags"),
    "driver-swing":      ("RSN06336", None, "A member finishing a driver swing"),
}

def name(pid, size=""):
    """size: "" full (2000 px), "m" (1200 px), "t" (800 px)"""
    return f"sl26-{pid}{'-' + size if size else ''}.webp"
