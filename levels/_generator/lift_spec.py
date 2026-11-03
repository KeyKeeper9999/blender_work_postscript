"""Numbers shared by build_lift.py and paint_interior.py (lift cab button plate)."""
PANEL_W, PANEL_H = .14, .56          # button plate, m (texture 64 x 256 px)
PANEL_PX = (64, 256)
ROW0, PITCH = 60, 16                 # first button row centre, row pitch (px from the top of the plate)
BTN_X, LABEL_X = 40, 17              # button / engraved label centre (px from the plate's left edge, seen from the cab)
BTN_W, BTN_H = .03, .022             # button cap, m
BURNT = ('7', '4')                   # melted with a lighter


def rows(variant):
    """button rows top to bottom; the Trader cab has one extra button with a triangle"""
    return (['tri'] if variant == 'Trader' else []) + [str(n) for n in range(9, 0, -1)] + ['call', 'stop']
