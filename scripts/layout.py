"""The board, as a drawing: where every part sits and where every wire runs.

The board is the schematic of Lab 10L.  Signal flows left to right and top
to bottom the way the book's figures read: the TARGET knob and jack on the
left, the pseudo op-amp (difference amplifier, inverter, summing amplifier)
along the top row, the DIFFERENTIATOR and INTEGRATOR in two rows under it
feeding up into the summing node, the MOTOR DRIVER with its push-pull on the
right, and the plant (the fader's motor and track) on screw terminals along
the bottom edge, where the POSITION comes back along the bottom to the LOOP
switch.  +15 V is a line along the top.  -15 V runs on the back of the board:
each op-amp has its own "-15 V" flag, a via, exactly as the sheet draws a
power symbol at each one.

Coordinates are millimetres from the board's top-left corner, y down.
Rotations are KiCad's, degrees counter-clockwise.

  Each op-amp (SOT-23-5, rotation 0: pins 1 +IN, 2 V-, 3 -IN on the left,
  4 OUT and 5 V+ on the right) sits at the centre of a drawn triangle
  (gen_pcb.oa_geometry): the + input enters on the left at cy - OA_IN, the
  - input at cy + OA_IN, the output leaves the right vertex at cy, V+ leaves
  the top edge at cx going up, and V- leaves the bottom edge at cx going
  down through a via (pin 2 is trapped between the two inputs, so its
  copper goes to the back inside the triangle).  Wires reach an op-amp at
  those four points.
  0805/1206 at rot 270: pad 1 on top; at rot 90: pad 1 at the bottom;
  at rot 0 pad 1 on the left; at rot 180 pad 1 on the right.
  D_SMA / SOD-123 at rot 270: cathode (pad 1) on top; rot 90: cathode at
  the bottom.  LED_0805 the same (pad 1 = cathode).
  TO-252 (DPAK) at rot 90: tab (pad 2, the collector) up, base pad 1 at the
  lower left, emitter pad 3 at the lower right; rot 270: tab down, base
  upper right, emitter upper left.
  MSK12C02 slide switch at rot 0: the three pins along the top edge, 1 on
  the left, 2 (the common) just right of centre, 3 on the right; the slider
  moves along x.  rot 180: pins along the bottom, 1 on the right.
  rot 90: pins down the left side, 3 top, 2, 1 bottom; rot 270: pins down
  the right side, 1 top, 2, 3 bottom.
  3362P trimmer at rot 0: pins 1 and 3 at the bottom corners (left, right),
  the wiper 2 at the top centre; the screw on top.
  RK09K knob at rot 180: pins in a column, 1 at the bottom, 2, 3 at the top,
  the body to the left of the pins.
  KF301 terminal at rot 180: pins in a row 5 mm apart, 1 on the right, the
  wire openings toward +y (the board's bottom edge).  rot 270: pins in a
  column, 1 at the top, openings toward +x.
  BNC at rot 180: the barrel points -x (left edge); rot 270: -y... no:
  rot 270 points the barrel down (+y), the bottom edge.

A wire is (net, [point, ...], width); a point is (x, y) or ("REF", "pad"),
which the board generator resolves to that pad's centre (or, for an op-amp,
to the point where the symbol's lead leaves the triangle; for a power
transistor, to the point its lead leaves the symbol) after placement, and
checks is on the named net.  Segments listed in HOPS dive under a crossing
wire on the back between two vias; the silkscreen draws them as jumps.
BACK lists copper that runs on the back only (-15 V): vias at both ends.
"""
import parts

BOARD_W, BOARD_H = 160.0, 110.0
VP_Y = 14.0                      # the +15 V rail along the top
A_Y = 34.0                       # the top row of op-amps (pseudo op-amp)
D_Y = 62.0                       # the differentiator
I_Y = 86.0                       # the integrator
OA_IN = 3.0                      # the inputs enter the triangle at cy -/+ OA_IN
OA_H, OA_W = 12.0, 10.4          # the triangle
OA_VM_DY = 4.0                   # V- leaves the triangle at (cx, cy + OA_VM_DY): the via
U1X, U2X, U3X = 60.0, 86.0, 114.0
U4X, U5X = 100.0, 100.0
U6X, U7X = 134.0, 100.0
ERR_X = 70.0                     # the ERROR column, down from U1's output
SUM_X = U3X - 7.2                # the summing node column, up into U3's - input
BOT_Y = 105.5                    # the bottom-edge connectors' pin row
DRV_Y = 58.0                     # the driver's output row (DRIVE)
QX = 147.0                       # the push-pull column

# ------------------------------------------------------------ placement ----
PLACE = {
    # TARGET: the knob between its end resistors, the jack, the source switch
    "RV1": (24.0, 36.5, 180),
    "R1": (28.0, 22.0, 270), "C1": (31.0, 27.0, 0),
    "R2": (24.0, 46.0, 270), "C2": (27.0, 41.0, 180),
    "J1": (5.7, 60.0, 180),
    "SW1": (40.0, 40.0, 90),
    "R5": (50.0, A_Y - OA_IN, 0),
    "TP1": (45.0, 31.0, 90),
    # the LOOP switch under the TARGET source switch, the POSITION return comes up to it
    "SW2": (40.0, 52.0, 90),
    "R7": (50.0, A_Y + OA_IN, 0),
    # U1 the difference amplifier
    "U1": (U1X, A_Y, 0),
    "R6": (U1X - 7.2, 26.0, 270),      # from the + node up to ground
    "R8": (U1X, A_Y + 13.0, 180),      # feedback, under the triangle
    "TP2": (ERR_X, 43.0, 0),
    # U2 the inverter
    "U2": (U2X, A_Y, 0),
    "R9": (U2X - 11.0, A_Y + OA_IN, 0), "R10": (U2X, A_Y + 13.0, 180),
    "TP3": (U2X + 9.5, A_Y, 90),
    # U3 the summing amplifier with its gain trimmer
    "U3": (U3X, A_Y, 0),
    "R11": (U3X - 11.0, A_Y + OA_IN, 0),
    "R14": (U3X - 2.5, A_Y + 13.0, 180), "RV2": (U3X + 4.0, A_Y + 17.0, 0),
    "TP6": (U3X + 9.5, A_Y, 90),
    # the differentiator row
    "SW5": (80.0, D_Y + OA_IN - 4.5, 0), "C5": (76.0, D_Y + OA_IN, 0), "C6": (84.0, D_Y + OA_IN, 0),
    "R15": (U4X - 11.0, D_Y + OA_IN, 0),
    "U4": (U4X, D_Y, 0),
    "RV3": (U4X + 1.0, D_Y + 17.0, 0), "C7": (U4X - 2.0, D_Y + 13.0, 180),
    "SW3": (U4X + 12.0, D_Y, 270), "R12": (SUM_X, D_Y - 6.0, 270),
    "TP4": (U4X + 8.5, D_Y - 3.5, 0),
    # the integrator row
    "R17": (76.0, I_Y + OA_IN, 0), "RV4": (84.0, I_Y + OA_IN + 2.0, 0),
    "U5": (U5X, I_Y, 0),
    "C8": (U5X, I_Y + 13.0, 180),
    "SW4": (U5X + 12.0, I_Y, 270), "R13": (SUM_X, I_Y - 6.0, 270),
    "TP5": (U5X + 8.5, I_Y - 3.5, 0),
    # the motor driver
    "U6": (U6X, DRV_Y, 0),
    "C9": (U6X, DRV_Y + 13.0, 180), "R18": (U6X - 7.2, DRV_Y + 9.0, 270),
    "R19": (U6X + 9.0, DRV_Y, 0),
    "Q1": (QX, DRV_Y - 14.0, 90), "Q2": (QX, DRV_Y + 14.0, 270),
    "R21": (QX, DRV_Y - 5.5, 270), "R22": (QX, DRV_Y + 5.5, 270),
    "D3": (153.5, DRV_Y - 8.0, 270), "D4": (153.5, DRV_Y + 8.0, 270),
    "TP7": (QX + 4.0, DRV_Y, 90),
    "R20": (153.5, DRV_Y + 20.0, 270), "C10": (153.5, DRV_Y + 25.0, 270),
    "F1": (140.0, DRV_Y + 20.0, 90), "R23": (136.0, DRV_Y + 24.0, 270),
    "LED3": (134.0, DRV_Y + 30.0, 90), "LED4": (138.0, DRV_Y + 30.0, 270),
    "TP11": (143.0, DRV_Y + 36.0, 0),
    "J4": (126.0, BOT_Y, 180),
    "R24": (118.0, DRV_Y + 30.0, 90), "J3": (112.0, 104.3, 270),
    # the plant's track: its end resistors, the follower for the POSITION jack
    "J5": (146.0, BOT_Y, 180),
    "R3": (153.5, 84.0, 270), "C3": (156.5, 90.0, 270),
    "R4": (140.0, 94.0, 270), "C4": (136.0, 94.0, 270),
    "U7": (U7X - 4.0, 98.0, 0), "R25": (U7X + 6.0, 98.0, 0), "J2": (92.0, 104.3, 270),
    "TP8": (120.0, 96.0, 90),
    # power: in at the right edge, down the rail
    "J6": (155.5, 22.0, 270),
    "D1": (147.0, 14.0, 180), "D2": (147.0, 28.0, 180),
    "C11": (138.0, 20.0, 270), "C13": (133.0, 19.0, 270),
    "C12": (138.0, 34.0, 90), "C14": (133.0, 33.0, 90),
    "R26": (128.0, 19.0, 270), "LED1": (128.0, 24.0, 90),
    "R27": (128.0, 38.0, 90), "LED2": (128.0, 33.0, 270),
    "TP9": (120.0, VP_Y, 90), "TP10": (122.0, 42.0, 90),
    # op-amp bypass: +15 hangs from the rail beside each V+ line, -15 under each triangle
    "C20": (U1X + 4.0, VP_Y + 3.0, 270), "C21": (U1X, A_Y + 6.3, 90),
    "C22": (U2X + 4.0, VP_Y + 3.0, 270), "C23": (U2X, A_Y + 6.3, 90),
    "C24": (U3X + 4.0, VP_Y + 3.0, 270), "C25": (U3X, A_Y + 6.3, 90),
    "C26": (U4X + 4.0, D_Y - 8.0, 270), "C27": (U4X, D_Y + 6.3, 90),
    "C28": (U5X + 4.0, I_Y - 8.0, 270), "C29": (U5X, I_Y + 6.3, 90),
    "C30": (U6X + 4.0, DRV_Y - 8.0, 270), "C31": (U6X, DRV_Y + 6.3, 90),
    "C32": (U7X, 90.0, 270), "C33": (U7X - 4.0, 98.0 + 6.3, 90),
    "TP100": (12.0, 80.0, 0), "TP101": (50.0, 100.0, 0), "TP102": (70.0, 100.0, 0), "TP103": (150.0, 50.0, 0),
    "MH1": (4.0, 4.0, 0), "MH2": (156.0, 4.0, 0), "MH3": (4.0, 106.0, 0), "MH4": (156.0, 106.0, 0),
}

# ---------------------------------------------------------------- wires ----
W_SIG, W_RAIL, W_PWR = 0.35, 0.6, 1.0
FB_Y = 100.0          # the POSITION return along the bottom, back to the LOOP switch
SRC_X = 44.0          # the TARGET source switch's output column... (unused)
ERR_TOP = A_Y         # ERROR leaves U1's output row here


def oa(ref, which):
    """A point on op-amp `ref`'s symbol: '+', '-', 'out', 'v+', 'v-'."""
    return (ref, {"+": "1", "-": "3", "out": "4", "v+": "5", "v-": "2"}[which])


WIRES = [
    # ---- +15 V rail and what hangs from it
    ("+15V", [(28.0, VP_Y), ("D1", "2")], W_RAIL),
    ("+15V", [("R1", "1"), (28.0, VP_Y)], W_SIG),
    ("+15V", [("R26", "1"), (128.0, VP_Y)], W_SIG),
    ("+15V", [("C11", "1"), (138.0, VP_Y)], W_SIG),
    ("+15V", [("C13", "1"), (133.0, VP_Y)], W_SIG),
    ("+15V", [("R3", "1"), (153.5, 80.0), (158.0, 80.0), (158.0, 50.0), (158.0, VP_Y - 0.0), (147.0 + 2.0, VP_Y)], W_SIG),
    # ---- power entry: the terminal, the series diodes, the bulk capacitors, the lamps
    ("/+15V_IN", [("J6", "1"), (152.0, 17.0), (152.0, 14.0), ("D1", "1")], W_RAIL),
    ("/-15V_IN", [("J6", "3"), (152.0, 27.0), (152.0, 28.0), ("D2", "1")], W_RAIL),
    ("-15V", [("D2", "2"), (138.0, 28.0)], W_RAIL),
    ("-15V", [("C12", "2"), (138.0, 28.0)], W_SIG),
    ("-15V", [("C14", "2"), (133.0, 28.0), (138.0, 28.0)], W_SIG),
    ("-15V", [("R27", "2"), (128.0, 28.0), (133.0, 28.0)], W_SIG),
    ("Net-(LED1-A)", [("R26", "2"), ("LED1", "2")], W_SIG),
    ("Net-(LED2-K)", [("R27", "1"), ("LED2", "1")], W_SIG),
    # ---- TARGET: knob, end resistors, decoupling, jack, source switch
    ("Net-(C1-Pad1)", [("RV1", "3"), (28.0, 31.5), ("R1", "2")], W_SIG),
    ("Net-(C1-Pad1)", [(28.0, 27.0), ("C1", "1")], W_SIG),
    ("Net-(C2-Pad2)", [("RV1", "1"), (24.0, 41.0), ("R2", "1")], W_SIG),
    ("Net-(C2-Pad2)", [(24.0, 41.0), ("C2", "2")], W_SIG),
    ("/KNOB", [("RV1", "2"), (34.0, 34.0), (34.0, 37.75), ("SW1", "3")], W_SIG),
    ("/TARGET IN", [("J1", "1"), (34.0, 60.0), (34.0, 42.25), ("SW1", "1")], W_SIG),
    ("/TARGET", [("SW1", "2"), (45.0, 40.75), (45.0, A_Y - OA_IN), ("R5", "1")], W_SIG),
    # ---- U1, the difference amplifier (unity): 4 x 100k
    ("Net-(U1-+)", [("R5", "2"), oa("U1", "+")], W_SIG),
    ("Net-(U1-+)", [(U1X - 7.2, A_Y - OA_IN), ("R6", "2")], W_SIG),
    ("/LOOP", [("SW2", "2"), (45.0, 52.75), (45.0, A_Y + OA_IN), ("R7", "1")], W_SIG),
    ("Net-(U1--)", [("R7", "2"), oa("U1", "-")], W_SIG),
    ("Net-(U1--)", [(U1X - 7.2, A_Y + OA_IN), (U1X - 7.2, A_Y + 13.0), ("R8", "2")], W_SIG),
    ("/ERROR", [oa("U1", "out"), (U1X + 7.2, A_Y), (ERR_X, A_Y), (ERR_X, 43.0), (ERR_X, D_Y + OA_IN), (ERR_X, I_Y + OA_IN)], W_SIG),
    ("/ERROR", [(U1X + 7.2, A_Y), (U1X + 7.2, A_Y + 13.0), ("R8", "1")], W_SIG),
    ("/ERROR", [(ERR_X, A_Y + OA_IN), ("R9", "1")], W_SIG),
    # ---- U2, the inverter
    ("Net-(U2--)", [("R9", "2"), oa("U2", "-")], W_SIG),
    ("Net-(U2--)", [(U2X - 7.2, A_Y + OA_IN), (U2X - 7.2, A_Y + 13.0), ("R10", "2")], W_SIG),
    ("/P", [oa("U2", "out"), (U2X + 7.2, A_Y), (U2X + 9.5, A_Y), ("R11", "1")], W_SIG),
    ("/P", [(U2X + 7.2, A_Y), (U2X + 7.2, A_Y + 13.0), ("R10", "1")], W_SIG),
    # ---- U3, the summing amplifier with its gain trimmer
    ("Net-(U3--)", [("R11", "2"), oa("U3", "-")], W_SIG),
    ("Net-(U3--)", [(SUM_X, A_Y + OA_IN), (SUM_X, A_Y + 13.0), ("R14", "2")], W_SIG),
    ("Net-(U3--)", [(SUM_X, A_Y + 13.0), (SUM_X, D_Y - 7.0), ("R12", "1")], W_SIG),
    ("Net-(U3--)", [(SUM_X, D_Y - 7.0), (SUM_X, I_Y - 7.0), ("R13", "1")], W_SIG),
    ("Net-(R14-Pad2)", [("R14", "1"), (U3X - 0.5, A_Y + 13.0), (U3X + 1.46, A_Y + 13.0), ("RV2", "1")], W_SIG),
    ("/SUM", [oa("U3", "out"), (U3X + 7.2, A_Y), (U3X + 9.5, A_Y), (124.0, A_Y), (124.0, DRV_Y - OA_IN), oa("U6", "+")], W_SIG),
    ("/SUM", [(U3X + 7.2, A_Y), (U3X + 7.2, A_Y + 18.27), ("RV2", "3")], W_SIG),
    ("/SUM", [("RV2", "2"), (U3X + 4.0, A_Y + 13.0), (U3X + 7.2, A_Y + 13.0)], W_SIG),
    # ---- the differentiator: C through the switch, 1k, the op-amp, 1M || 470 pF
    ("Net-(SW5-A)", [("C5", "2"), ("SW5", "1")], W_SIG),
    ("Net-(SW5-C)", [("C6", "2"), ("SW5", "3")], W_SIG),
    ("Net-(SW5-B)", [("SW5", "2"), (80.75, D_Y + OA_IN), ("R15", "1")], W_SIG),
    ("/ERROR", [(ERR_X, D_Y + OA_IN), ("C5", "1")], W_SIG),
    ("/ERROR", [(ERR_X, D_Y - 3.0), (84.0, D_Y - 3.0), (84.0, D_Y + OA_IN - 1.0), ("C6", "1")], W_SIG),
    ("Net-(SW3-C)", [("R15", "2"), oa("U4", "-")], W_SIG),
    ("Net-(SW3-C)", [(U4X - 7.2, D_Y + OA_IN), (U4X - 7.2, D_Y + 13.0), ("C7", "2")], W_SIG),
    ("Net-(SW3-C)", [(U4X - 7.2, D_Y + 13.0), (U4X - 7.2, D_Y + 18.27), ("RV3", "1")], W_SIG),
    ("Net-(SW3-C)", [(U4X - 7.2, D_Y + 18.27), (U4X - 7.2, D_Y + 22.0), (U4X + 14.0, D_Y + 22.0), (U4X + 14.0, D_Y + 2.25), ("SW3", "3")], W_SIG),
    ("/D", [oa("U4", "out"), (U4X + 7.2, D_Y), (U4X + 8.5, D_Y), ("SW3", "2")], W_SIG),
    ("/D", [(U4X + 7.2, D_Y), (U4X + 7.2, D_Y + 13.0), ("C7", "1")], W_SIG),
    ("/D", [(U4X + 7.2, D_Y + 13.0), (U4X + 7.2, D_Y + 18.27), ("RV3", "3")], W_SIG),
    ("/D", [("RV3", "2"), (U4X + 1.0, D_Y + 13.0), (U4X + 7.2, D_Y + 13.0)], W_SIG),
    ("Net-(SW3-A)", [("SW3", "1"), (U4X + 14.0, D_Y - 2.25), (U4X + 14.0, D_Y - 9.0), (SUM_X, D_Y - 9.0), ("R12", "2")], W_SIG),
    # ---- the integrator: 1k + 1M in, 10 uF across
    ("/ERROR", [(ERR_X, I_Y + OA_IN), ("R17", "1")], W_SIG),
    ("Net-(R17-Pad2)", [("R17", "2"), (80.0, I_Y + OA_IN), (80.0, I_Y + OA_IN + 3.27), ("RV4", "1")], W_SIG),
    ("Net-(SW4-C)", [("RV4", "3"), (88.0, I_Y + OA_IN + 3.27), (88.0, I_Y + OA_IN), oa("U5", "-")], W_SIG),
    ("Net-(SW4-C)", [("RV4", "2"), (84.0, I_Y + OA_IN - 2.0), (88.0, I_Y + OA_IN - 2.0), (88.0, I_Y + OA_IN)], W_SIG),
    ("Net-(SW4-C)", [(U5X - 7.2, I_Y + OA_IN), (U5X - 7.2, I_Y + 13.0), ("C8", "2")], W_SIG),
    ("Net-(SW4-C)", [(U5X - 7.2, I_Y + 13.0), (U5X - 7.2, I_Y + 16.0), (U5X + 14.0, I_Y + 16.0), (U5X + 14.0, I_Y + 2.25), ("SW4", "3")], W_SIG),
    ("/I", [oa("U5", "out"), (U5X + 7.2, I_Y), (U5X + 8.5, I_Y), ("SW4", "2")], W_SIG),
    ("/I", [(U5X + 7.2, I_Y), (U5X + 7.2, I_Y + 13.0), ("C8", "1")], W_SIG),
    ("Net-(SW4-A)", [("SW4", "1"), (U5X + 14.0, I_Y - 2.25), (U5X + 14.0, I_Y - 9.0), (SUM_X, I_Y - 9.0), ("R13", "2")], W_SIG),
    # ---- the motor driver: split feedback, 270 ohm, the push-pull, 1 ohm each
    ("Net-(U6--)", [oa("U6", "-"), (U6X - 7.2, DRV_Y + OA_IN), ("R18", "1")], W_SIG),
    ("Net-(U6--)", [(U6X - 7.2, DRV_Y + OA_IN), (U6X - 7.2, DRV_Y + 13.0), ("C9", "2")], W_SIG),
    ("Net-(C9-Pad2)", [oa("U6", "out"), (U6X + 7.2, DRV_Y), ("R19", "1")], W_SIG),
    ("Net-(C9-Pad2)", [(U6X + 7.2, DRV_Y), (U6X + 7.2, DRV_Y + 13.0), ("C9", "1")], W_SIG),
    ("/BASES", [("R19", "2"), (QX - 6.0, DRV_Y), (QX - 6.0, DRV_Y - 14.0), ("Q1", "1")], W_SIG),
    ("/BASES", [(QX - 6.0, DRV_Y), (QX - 6.0, DRV_Y + 14.0), ("Q2", "1")], W_SIG),
    ("Net-(Q1-E)", [("Q1", "3"), ("R21", "1")], W_SIG),
    ("Net-(Q2-E)", [("Q2", "3"), ("R22", "2")], W_SIG),
    ("/DRIVE", [("R21", "2"), (QX, DRV_Y), ("R22", "1")], W_SIG),
    ("/DRIVE", [(QX, DRV_Y), (QX + 4.0, DRV_Y), (153.5, DRV_Y)], W_SIG),
    ("/DRIVE", [("D3", "2"), (153.5, DRV_Y), ("D4", "1")], W_SIG),
    ("+15V", [("D3", "1"), (153.5, DRV_Y - 12.0), (158.0, DRV_Y - 12.0)], W_SIG),
    ("-15V", [("D4", "2"), (153.5, DRV_Y + 12.0), (158.0, DRV_Y + 12.0), (158.0, 84.0)], W_SIG),
    ("/DRIVE", [(153.5, DRV_Y), (153.5, DRV_Y + 12.0 + 0.0)], W_SIG),  # replaced below
    ("/DRIVE", [(QX, DRV_Y), (QX, DRV_Y + 7.4)], W_SIG),
    ("/DRIVE", [(140.0, DRV_Y), (140.0, DRV_Y + 16.0), ("F1", "1")], W_SIG),
    ("/DRIVE", [(140.0, DRV_Y + 16.0), (136.0, DRV_Y + 16.0), ("R23", "1")], W_SIG),
    ("/DRIVE", [(136.0, DRV_Y + 16.0), (130.0, DRV_Y + 16.0), (130.0, DRV_Y + 20.0), (U6X - 7.2, DRV_Y + 20.0)], W_SIG),
    ("Net-(LED3-K)", [("R23", "2"), (136.0, DRV_Y + 27.0), ("LED3", "1")], W_SIG),
    ("Net-(LED3-K)", [(136.0, DRV_Y + 27.0), ("LED4", "2")], W_SIG),
    ("/MOTOR", [("F1", "2"), (140.0, DRV_Y + 33.0), ("LED3", "2")], W_SIG),
    ("/MOTOR", [(140.0, DRV_Y + 33.0), ("LED4", "1")], W_SIG),
    ("/MOTOR", [(140.0, DRV_Y + 33.0), (140.0, DRV_Y + 36.0), ("TP11", "1"), (131.0, DRV_Y + 36.0), ("J4", "1")], W_SIG),
    ("/DRIVE", [(130.0, DRV_Y + 20.0), (130.0, DRV_Y + 24.0), (118.0, DRV_Y + 24.0), ("R24", "2")], W_SIG),
    ("Net-(J3-In)", [("R24", "1"), (118.0, DRV_Y + 36.0), (112.0, DRV_Y + 36.0), ("J3", "1")], W_SIG),
    # ---- the plant's track and the POSITION follower
    ("/POT+", [("R3", "2"), (153.5, 90.0), ("C3", "1")], W_SIG),
    ("/POT+", [(153.5, 90.0), (153.5, 100.0), (151.0, 100.0), ("J5", "1")], W_SIG),
    ("/POT-", [("R4", "1"), (140.0, 90.0), ("C4", "1")], W_SIG),
    ("/POT-", [(140.0, 90.0), (141.0, 100.0), ("J5", "3")], W_SIG),
    ("-15V", [("R4", "2"), (140.0, 98.0), (158.0, 98.0), (158.0, 84.0)], W_SIG),
    ("/POSITION", [("J5", "2"), (146.0, 96.0), (120.0, 96.0), ("TP8", "1"), (U7X - 11.2, 96.0), oa("U7", "+")], W_SIG),
    ("/POSITION", [(U7X - 11.2, 96.0), (48.0, 96.0), (48.0, 56.75), ("SW2", "3")], W_SIG),
    ("Net-(U7--)", [oa("U7", "out"), (U7X + 3.2, 98.0), ("R25", "1")], W_SIG),
    ("Net-(U7--)", [(U7X + 3.2, 98.0), (U7X + 3.2, 103.0), (U7X - 11.2, 103.0), (U7X - 11.2, 101.0), oa("U7", "-")], W_SIG),
    ("Net-(J2-In)", [("R25", "2"), (108.0, 98.0), (108.0, 104.3), ("J2", "1")], W_SIG),
    # ---- the op-amps' supplies
    ("+15V", [oa("U1", "v+"), (U1X, VP_Y)], W_SIG), ("+15V", [("C20", "1"), (U1X + 4.0, VP_Y)], W_SIG),
    ("+15V", [oa("U2", "v+"), (U2X, VP_Y)], W_SIG), ("+15V", [("C22", "1"), (U2X + 4.0, VP_Y)], W_SIG),
    ("+15V", [oa("U3", "v+"), (U3X, VP_Y)], W_SIG), ("+15V", [("C24", "1"), (U3X + 4.0, VP_Y)], W_SIG),
    ("+15V", [oa("U4", "v+"), (U4X, D_Y - 11.0), (U4X + 4.0, D_Y - 11.0), ("C26", "1")], W_SIG),
    ("+15V", [oa("U5", "v+"), (U5X, I_Y - 11.0), (U5X + 4.0, I_Y - 11.0), ("C28", "1")], W_SIG),
    ("+15V", [oa("U6", "v+"), (U6X, DRV_Y - 11.0), (U6X + 4.0, DRV_Y - 11.0), ("C30", "1")], W_SIG),
    ("+15V", [oa("U7", "v+"), (U7X - 4.0, 91.0), (U7X, 91.0), ("C32", "1")], W_SIG),
    ("-15V", [oa("U1", "v-"), ("C21", "2")], W_SIG), ("-15V", [oa("U2", "v-"), ("C23", "2")], W_SIG),
    ("-15V", [oa("U3", "v-"), ("C25", "2")], W_SIG), ("-15V", [oa("U4", "v-"), ("C27", "2")], W_SIG),
    ("-15V", [oa("U5", "v-"), ("C29", "2")], W_SIG), ("-15V", [oa("U6", "v-"), ("C31", "2")], W_SIG),
    ("-15V", [oa("U7", "v-"), ("C33", "2")], W_SIG),
]

# Segments that run on the back layer between two vias, under a crossing wire.
HOPS = []

# Copper on the back only: -15 V, from the power entry to every -15 V flag.
# (net, [points], width): a via at each end unless the end is a through-hole
# pad; the plane flows round it.  Drawn nowhere on the front: the flags say
# where it surfaces, as the sheet's power symbols do.
VM_TRUNK_Y = 50.0                # the back trunk between the top row and the differentiator
VM_TRUNK2_Y = 94.0               # ... and along the bottom for the integrator and the follower
BACK = [
    ("-15V", [(138.0, 28.0), (138.0, VM_TRUNK_Y), (24.0, VM_TRUNK_Y)], W_RAIL),          # the trunk, from the entry
    ("-15V", [(24.0, VM_TRUNK_Y), (24.0, 49.5)], W_SIG),                                    # the knob's end resistor
    ("-15V", [(U1X, A_Y + OA_VM_DY), (U1X + 3.0, A_Y + OA_VM_DY), (U1X + 3.0, VM_TRUNK_Y)], W_SIG),
    ("-15V", [(U2X, A_Y + OA_VM_DY), (U2X + 3.0, A_Y + OA_VM_DY), (U2X + 3.0, VM_TRUNK_Y)], W_SIG),
    ("-15V", [(U3X, A_Y + OA_VM_DY), (U3X + 3.0, A_Y + OA_VM_DY), (U3X + 3.0, VM_TRUNK_Y)], W_SIG),
    ("-15V", [(U4X, D_Y + OA_VM_DY), (U4X + 3.0, D_Y + OA_VM_DY), (U4X + 3.0, VM_TRUNK_Y)], W_SIG),
    ("-15V", [(U6X, DRV_Y + OA_VM_DY), (U6X + 3.0, DRV_Y + OA_VM_DY), (U6X + 3.0, VM_TRUNK_Y)], W_SIG),
    ("-15V", [(138.0, VM_TRUNK_Y), (138.0, 94.0 - 0.0)], W_RAIL),                            # down to the bottom trunk... via Q2's pour
    ("-15V", [(U5X, I_Y + OA_VM_DY), (U5X + 3.0, I_Y + OA_VM_DY), (U5X + 3.0, VM_TRUNK2_Y), (138.0, VM_TRUNK2_Y)], W_SIG),
    ("-15V", [(U7X - 4.0, 98.0 + OA_VM_DY), (U7X - 1.0, 98.0 + OA_VM_DY), (U7X - 1.0, VM_TRUNK2_Y)], W_SIG),
]
# Where the back copper surfaces as a flag with no front wire of its own: (net, x, y)
FLAGS = [("-15V", 24.0, 49.5)]

# Ground: a stub from the pad to a via (a point, or a path of points), the
# ground symbol drawn at the via pointing the way the last segment runs.
GND_STUBS = [
    (("J1", "2"), [(5.7, 64.0), (5.7, 67.5)]),
    (("C1", "2"), [(33.5, 27.0), (33.5, 30.0)]),
    (("C2", "1"), [(29.5, 41.0), (29.5, 44.0)]),
    (("R6", "1"), (U1X - 7.2, 22.0)),
    (("SW2", "1"), [(38.05, 54.25), (36.0, 54.25), (36.0, 57.0)]),
    (("C20", "2"), (U1X + 4.0, VP_Y + 6.5)), (("C22", "2"), (U2X + 4.0, VP_Y + 6.5)), (("C24", "2"), (U3X + 4.0, VP_Y + 6.5)),
    (("C26", "2"), (U4X + 4.0, D_Y - 4.5)), (("C28", "2"), (U5X + 4.0, I_Y - 4.5)), (("C30", "2"), (U6X + 4.0, DRV_Y - 4.5)),
    (("C32", "2"), (U7X, 93.5)),
    (("C21", "1"), (U1X, A_Y + 9.0)), (("C23", "1"), (U2X, A_Y + 9.0)), (("C25", "1"), (U3X, A_Y + 9.0)),
    (("C27", "1"), (U4X, D_Y + 9.0)), (("C29", "1"), (U5X, I_Y + 9.0)), (("C31", "1"), (U6X, DRV_Y + 9.0)),
    (("C33", "1"), (U7X - 4.0, 98.0 + 9.0)),
    (("U2", "1"), [(U2X - 7.2, A_Y - OA_IN), (U2X - 7.2, A_Y - 1.0)]),
    (("U3", "1"), [(U3X - 7.2, A_Y - OA_IN), (U3X - 7.2, A_Y - 1.0)]),
    (("U4", "1"), [(U4X - 7.2, D_Y - OA_IN), (U4X - 7.2, D_Y - 1.0)]),
    (("U5", "1"), [(U5X - 7.2, I_Y - OA_IN), (U5X - 7.2, I_Y - 1.0)]),
    (("C10", "2"), (153.5, DRV_Y + 29.0)),
    (("C3", "2"), (156.5, 93.5)), (("C4", "2"), (136.0, 97.5)),
    (("C11", "2"), (138.0, 23.5)), (("C13", "2"), (133.0, 22.5)),
    (("C12", "1"), (138.0, 30.5)), (("C14", "1"), (133.0, 29.5)),
    (("LED1", "1"), (128.0, 27.5)), (("LED2", "2"), (128.0, 29.5)),
    (("J6", "2"), [(151.5, 22.0), (151.5, 24.0)]),
    (("J2", "2"), [(96.0, 100.3), (96.0, 98.0)]), (("J3", "2"), [(116.0, 100.3), (116.0, 98.0)]),
    (("J4", "2"), [(126.0, 102.0), (126.0, 100.0)]),
    (("TP100", "1"), (12.0, 83.5)), (("TP101", "1"), (50.0, 103.5)), (("TP102", "1"), (70.0, 103.5)), (("TP103", "1"), (150.0, 53.5)),
]
GND_MARKS = []

# --------------------------------------------------------- silkscreen -----
# Op-amps: every one is drawn as a triangle round its SOT-23-5 (gen_pcb.oa_geometry).
OPAMPS = ["U1", "U2", "U3", "U4", "U5", "U6", "U7"]
# Power transistors: ref -> (kind, base side).  Drawn as the textbook symbol
# round the DPAK, with the tab's copper pour as the collector.
TRANSISTORS = {"Q1": ("NPN", "left"), "Q2": ("PNP", "left")}
Q_RADIUS = 6.0
Q_CAPTION = {"Q1": (QX - 9.5, DRV_Y - 22.0, "left", 0.9), "Q2": (QX - 9.5, DRV_Y + 22.0, "left", 0.9)}
# The copper pours under the tabs: ref -> (x0, y0, x1, y1)
POURS = {"Q1": (QX - 7.5, DRV_Y - 25.0, QX + 7.5, DRV_Y - 15.5), "Q2": (QX - 7.5, DRV_Y + 15.5, QX + 7.5, DRV_Y + 25.0)}

# Free text: (x, y, text, size, thickness, justify, angle)
TEXTS = [
    (80.0, 5.0, parts.BOARD_NAME.upper(), 2.4, 0.4, "center", 0),
    (80.0, 8.2, "Learning the Art of Electronics (Hayes & Horowitz), Lab 10L: a motorized fader held to a target", 1.0, 0.15, "center", 0),
    (80.0, 10.4, "circuit: Hayes & Horowitz    board: Jason Gallicchio and Claude    rev " + parts.REV + "  " + parts.BOARD_DATE + "    " + parts.PROJECT_URL, 1.0, 0.15, "center", 0),
    (28.5, 12.3, "+15 V", 1.2, 0.2, "left", 0),
]
LEGENDS = []
FIELD_AT = {}
HIDE_REF = set()
HIDE_VALUE = set()
TP_LABEL = {}
BOXES = []
FIDUCIALS = [(10.0, 100.0), (150.0, 100.0), (10.0, 10.0)]
QR_AT, QR_MODULE = (40.0, 75.0), 0.6
BACK_TITLE_AT = (80.0, 60.0)
BACK_X, BACK_Y, BACK_PITCH = 20.0, 70.0, 1.9
BACK_TEXT = ["(how to use the board: written once the layout settles)"]
