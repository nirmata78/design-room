"""Google theme tokens for every generator (seqsvg, erdsvg, statesvg, figsvg, build_video, publish_kit; C4 views come from c4-structurizr).

One source of colour and type for diagrams and frames. The CSS twin is <repo>/pdf-kit/google-theme.css; keep them in step.
Brand hex goes on fills, strokes and rules. Small coloured TEXT on a light surface uses the *_INK shade (the brand hex fails 4.5:1 there).
"""
BLUE, RED, YELLOW, GREEN = "#4285F4", "#EA4335", "#FBBC05", "#34A853"          # Google brand accents
WHITE, SOFT, INK, INK_HI, MUTED = "#FFFFFF", "#F8F9FA", "#202124", "#141413", "#5F6368"
RULE, HAIR, GREY = "#DADCE0", "#E8EAED", "#9AA0A6"                              # hairlines, strokes of quiet things
BLUE_INK, RED_INK, GREEN_INK, YELLOW_INK = "#1967D2", "#C5221F", "#188038", "#B06000"
BLUE_BG, RED_BG, GREEN_BG, YELLOW_BG = "#E8F0FE", "#FCE8E6", "#E6F4EA", "#FEF7E0"
BLUE_MID, BLUE_DEEP = "#8AB4F8", "#174EA6"                                      # C4: container fill, person fill
DISPLAY = "'Plus Jakarta Sans', 'Google Sans', Roboto, sans-serif"             # titles, numbers (SVG titles only)
FONT = "Inter, Roboto, sans-serif"                                              # every label in a diagram
MONO = "'Roboto Mono', monospace"

TEXT_INK = {BLUE: BLUE_INK, RED: RED_INK, GREEN: GREEN_INK, YELLOW: YELLOW_INK}   # brand hex -> shade that reads as small text on white/tint
def ink(c):
    """Colour for TEXT: the text-safe shade of a brand accent, anything else unchanged (case-insensitive)."""
    return {k.lower(): v for k, v in TEXT_INK.items()}.get(str(c).lower(), c)
