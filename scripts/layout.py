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
power symbol at each one; the lower stages' +15 V and the POSITION return
to the LOOP switch run on the back too (a flag, or a dashed line).

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
  TO-263-2 (D2PAK) at rot 90: tab (pad 2, the collector) up, base pad 1 at
  the lower left, emitter pad 3 at the lower right, the leads 7.65 mm below
  the origin and 2.54 either side; rot 270: tab down, base upper right,
  emitter upper left.
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
  BNC at rot 180: the barrel points -x, out of the left edge.

A wire is (net, [point, ...], width); a point is (x, y) or ("REF", "pad"),
which the board generator resolves to that pad's centre (or, for an op-amp,
to the point where the symbol's lead leaves the triangle; for a power
transistor, to the point its lead leaves the symbol) after placement, and
checks is on the named net.  Segments listed in HOPS dive under a crossing
wire on the back between two vias; the silkscreen draws them as jumps.
BACK lists copper that runs on the back only (-15 V): vias at both ends.
"""
import parts

BOARD_W, BOARD_H = 170.0, 120.0
VP_Y = 14.0                      # the +15 V rail along the top
VM_TOP = 12.5                    # the -15 V trunk, on the back, just above it
A_Y = 34.0                       # the top row of op-amps (the pseudo op-amp)
D_Y = 62.0                       # the differentiator
I_Y = 94.0                       # the integrator
DRV_Y = 58.0                     # the motor driver's output row (DRIVE)
OA_IN = 3.0                      # the inputs enter the triangle at cy -/+ OA_IN
OA_H, OA_W = 12.0, 10.4          # the triangle
OA_VM_DY = 4.0                   # V- leaves the triangle at (cx, cy + OA_VM_DY): the via
VM_CAP, VM_GND = 6.0, 8.2        # the -15 V bypass under each triangle, and its ground via
FB = 12.5                        # the feedback row under an inverting op-amp
U1X, U2X, U3X = 62.0, 88.0, 116.0
U4X, U5X = 94.0, 94.0
U6X, U7X, U7Y = 135.0, 22.0, 86.0
RV4X = 78.7                       # the I trimmer, 0.8 west of its old place: room for its arc label
ERR_X = 70.0                     # the ERROR column, down from U1's output
SUM_X = U3X - 7.2                # the summing node column, up into U3's - input
QX = 154.0                       # the push-pull column
PP_Y = 59.0                      # the push-pull's DRIVE row, between R21 and R22
Q1Y, Q2Y = PP_Y - 19.9, PP_Y + 21.0   # the D2PAKs' origins: Q1's circle clears R21, Q2's the BASES hop
BH_Y = PP_Y + 7.2                # BASES crosses to Q2's base along here, under R22's end
BUS_X, FUSE_Y = 167.0, 94.0      # the push-pull's output down the right edge, then left to the fuse
MOT_X = 151.0                    # DRIVE, behind the fuse, down to the motor's terminal
PP_NET = "Net-(D3-A)"            # the push-pull's output ahead of the fuse (KiCad's name for it)
BOT_Y = 115.5                    # the bottom-edge terminals' pin row (the body 0.5 mm inside the edge)
VM_BR = 103.5                    # the -15 V branch down the D and I stages' east side (back)
VP_SP = 87.5                     # the +15 V spine up their west side (back)
POS_X = 124.0                    # the POT terminal's wiper pin

# ------------------------------------------------------------ placement ----
PLACE = {
    # TARGET: the knob between its end resistors, the jack, the source switch
    "RV1": (24.0, 36.5, 180),
    "R1": (28.0, 22.0, 270), "C1": (31.0, 27.0, 0),
    "R2": (24.0, 46.0, 270), "C2": (27.0, 41.0, 180),
    "J1": (5.7, 60.0, 180),
    "SW1": (40.0, 36.0, 180),
    "TP1": (48.0, 41.0, 90),
    "R5": (52.5, A_Y - OA_IN, 0),
    # the LOOP switch under it; POSITION comes back to it on the back
    "SW2": (44.0, 50.0, 180),
    "R7": (52.5, A_Y + OA_IN, 0),
    # U1 the difference amplifier
    "U1": (U1X, A_Y, 0), "R6": (U1X - 7.2, 27.5, 90), "R8": (U1X - 1.0, A_Y + FB, 0),
    "TP2": (ERR_X, 40.5, 0),
    # U2 the inverter
    "U2": (U2X, A_Y, 0), "R9": (78.0, A_Y + OA_IN, 0), "R10": (U2X - 1.0, A_Y + FB, 0),
    "TP3": (100.5, A_Y, 90),
    # U3 the summing amplifier with its gain trimmer
    "U3": (U3X, A_Y, 0), "R11": (106.5, A_Y + OA_IN, 0),
    "R14": (U3X - 4.7, A_Y + 18.77, 0), "RV2": (U3X + 1.0, A_Y + 17.5, 0),
    "TP6": (U6X - 7.2, 40.0, 0),
    # the differentiator row: the capacitor switch, the two capacitors, 1k, U4, 1M || 470 pF
    "SW5": (74.0, D_Y + OA_IN + 0.75, 90), "C6": (80.0, D_Y - 2.0, 0), "C5": (80.0, D_Y + 9.0, 0),
    "R15": (84.5, D_Y + OA_IN, 0),
    "U4": (U4X, D_Y, 0),
    "C7": (89.3, D_Y + 11.5, 0), "RV3": (U4X + 0.5, D_Y + 17.5, 0),
    "SW3": (106.0, D_Y + 2.75, 90), "R12": (106.5, D_Y - 6.0, 0),
    "TP4": (U4X + 7.2, D_Y + 9.8, 90),
    # the integrator row: 1k + 1M in, U5, the 1 uF film across: its leads on 15 mm
    # land on U5's input and output columns (pad 2 on the output's)
    "R17": (73.0, I_Y + OA_IN, 0), "RV4": (RV4X, I_Y + 6.0, 0),
    "U5": (U5X, I_Y, 0),
    "C8": (U5X + 7.2 - 7.5, I_Y + 16.3, 0),        # FBI, the integrator's feedback row
    "SW4": (106.0, I_Y + 2.75, 90), "R13": (106.5, I_Y - 14.0, 0),
    "TP5": (U5X + 7.2, I_Y + 6.5, 90),
    # the motor driver: split feedback, 270 ohm, the push-pull, 1 ohm each, clamps
    "U6": (U6X, DRV_Y, 0),
    "C9": (U6X - 0.35, DRV_Y + 14.0, 0), "R18": (U6X - 7.2, 80.0, 270),
    "R19": (143.8, DRV_Y, 0),
    # the D2PAKs: Q1's emitter lead is 2.54 right of QX and Q2's 2.54 left, so R21
    # and R22 stand in two columns with DRIVE running between their ends
    "Q1": (QX, Q1Y, 90), "Q2": (QX, Q2Y, 270),
    "R21": (QX + 2.54, PP_Y - 2.9625, 270), "R22": (QX - 2.54, PP_Y + 2.9625, 270),
    "TP7": (140.0, 91.0, 90),
    # each clamp has its rail end in that rail's pour; the snubber in the pocket under DRIVE
    "D3": (164.8, PP_Y - 3.6, 270), "D4": (164.8, PP_Y + 3.6, 270),
    "R20": (160.0, PP_Y + 3.0, 180), "C10": (156.5, PP_Y + 3.0, 180),
    # the fuse row, the lamp across the fuse, the MOTOR terminal (DRIVE, behind the fuse)
    "F1": (160.0, FUSE_Y, 180),
    "R23": (164.5, 97.0, 270), "LED3": (160.0, 99.0, 180), "LED4": (160.0, 103.0, 0),
    "J4": (146.0, BOT_Y, 180),
    # the plant's track: its terminal, end resistors, decoupling; the POSITION loop
    "J5": (POS_X, BOT_Y, 180),
    # C3, C4 tap the track's ends far enough below R3's and R4's pads for the
    # junction dots, inside THE FADER'S TRACK box: R3 up 0.6 mm (C3's tap stays
    # clear of J5's "+"), C4's tap down 0.8 mm (R4's top pad keeps clear of the
    # dashed POSITION line at y 105)
    "R3": (POS_X + 5.0, 106.9, 270), "C3": (133.0, 109.4, 0),
    "R4": (POS_X - 5.0, 107.5, 90), "C4": (115.5, 110.2, 180),
    "TP8": (POS_X, 107.5, 0),
    # the POSITION follower and its jack, at the left under the TARGET block
    "U7": (U7X, U7Y, 0), "R25": (32.0, U7Y, 0), "J2": (5.7, 101.0, 180),
    # the extra probe loops: every op-amp output, and the bases
    "TP11": (146.0, 52.0, 90), "TP12": (U6X + 6.5, DRV_Y + 7.0, 90), "TP13": (29.0, U7Y + 7.0, 90),
    # DRIVE OUT: 1k from the DRIVE row to a jack on the bottom edge
    "R24": (112.5, 95.0, 270), "J3": (60.0, 114.3, 270),
    # power: in at the top edge, series diodes, bulk capacitors, lamps
    "J6": (138.0, 4.5, 0),
    "D1": (131.0, 11.6, 0), "D2": (148.5, 10.0, 270),
    "C11": (76.0, 17.8, 270), "C13": (83.0, 17.0, 270),
    "C12": (155.5, 18.0, 90), "C14": (148.5, 17.5, 90),
    "R26": (102.0, 17.0, 270), "LED1": (102.0, 22.0, 90),
    "R27": (163.5, 15.5, 90), "LED2": (163.5, 20.0, 270),
    # the rail clamps, beside the input diodes: D5 from the +15 V rail down to ground
    # (cathode up), D6 from the -15 V tie at D2 down to ground (cathode down)
    "D5": (130.5, 18.7, 270), "D6": (145.4, 17.3, 90),
    "TP9": (125.0, VP_Y, 90), "TP10": (167.0, 12.5, 90),
    # op-amp bypass: +15 hangs from the rail (or a flag) beside each V+ line, -15 under each triangle
    "C20": (U1X + 4.5, VP_Y + 3.0, 270), "C21": (U1X, A_Y + VM_CAP, 90),
    "C22": (U2X + 4.5, VP_Y + 3.0, 270), "C23": (U2X, A_Y + VM_CAP, 90),
    "C24": (U3X + 4.5, VP_Y + 3.0, 270), "C25": (U3X, A_Y + VM_CAP, 90),
    "C26": (U4X + 4.5, D_Y - 7.5, 0), "C27": (U4X, D_Y + VM_CAP, 90),
    "C28": (U5X + 4.5, I_Y - 7.0, 0), "C29": (U5X, I_Y + VM_CAP, 90),
    "C30": (U6X + 4.5, VP_Y + 3.0, 270), "C31": (U6X, DRV_Y + VM_CAP, 90),
    "C32": (U7X + 4.5, U7Y - 7.5, 0), "C33": (U7X, U7Y + VM_CAP, 90),
    "TP100": (40.0, 92.0, 0), "TP101": (42.0, 99.0, 0), "TP102": (50.0, 99.0, 0), "TP103": (118.0, 70.0, 0),
    "MH1": (4.0, 4.0, 0), "MH2": (166.0, 4.0, 0), "MH3": (6.0, 116.0, 0), "MH4": (166.0, 116.0, 0),
}

# ---------------------------------------------------------------- wires ----
W_SIG, W_RAIL = 0.35, 0.6
FBA, FBD, FBI, FBM = A_Y + FB, D_Y + 11.5, I_Y + 16.3, DRV_Y + 14.0   # the feedback rows (D's is higher: its trimmer and arc
# sit under it; I's lower: the film capacitor's 9.3 mm body has to clear U5's bypass and
# the dashed POSITION line at y 105)


def oa(ref, which):
    """A point on op-amp `ref`'s symbol: '+', '-', 'out', 'v+', 'v-'."""
    return (ref, {"+": "1", "-": "3", "out": "4", "v+": "5", "v-": "2"}[which])


WIRES = [
    # ---- +15 V: the rail along the top, the entry diode, the knob's end, the pour feed
    ("+15V", [(20.0, VP_Y), (143.0, VP_Y)], W_RAIL),
    ("+15V", [("D1", "1"), (129.0, VP_Y)], W_RAIL),
    ("+15V", [(143.0, VP_Y), (143.0, 29.2)], W_RAIL),          # into Q1's pour
    ("+15V", [("R1", "1"), (28.0, VP_Y)], W_SIG),
    ("+15V", [("C11", "1"), (76.0, VP_Y)], W_SIG), ("+15V", [("C13", "1"), (83.0, VP_Y)], W_SIG),
    ("+15V", [("R26", "1"), (102.0, VP_Y)], W_SIG),
    ("Net-(LED1-A)", [("R26", "2"), ("LED1", "2")], W_SIG),
    # ---- power entry and the -15 V corner
    ("/+15V_IN", [("J6", "1"), ("D1", "2")], W_RAIL),
    ("/-15V_IN", [("J6", "3"), (143.0, 6.5), (148.5, 6.5), ("D2", "1")], W_RAIL),
    ("-15V", [("D2", "2"), (148.5, 13.5), ("C14", "2")], W_RAIL),
    ("-15V", [(148.5, 12.5), (155.5, 12.5), (163.5, 12.5), (167.0, 12.5)], W_RAIL),
    ("-15V", [(163.5, 12.5), ("R27", "2")], W_SIG),
    ("-15V", [(155.5, 12.5), ("C12", "2")], W_SIG),
    ("Net-(LED2-K)", [("R27", "1"), ("LED2", "1")], W_SIG),
    ("+15V", [("D5", "1"), (130.5, VP_Y)], W_SIG),
    ("-15V", [("D6", "2"), (145.4, 13.5), (148.5, 13.5)], W_SIG),
    # ---- TARGET: knob, end resistors, decoupling, jack, source switch
    ("Net-(C1-Pad1)", [("RV1", "3"), (28.0, 31.5), ("R1", "2")], W_SIG),
    ("Net-(C1-Pad1)", [(28.0, 27.0), ("C1", "1")], W_SIG),
    ("Net-(C2-Pad2)", [("RV1", "1"), (24.0, 41.0), ("R2", "1")], W_SIG),
    ("Net-(C2-Pad2)", [(24.0, 41.0), ("C2", "2")], W_SIG),
    ("-15V", [("R2", "2"), (24.0, 50.0)], W_SIG),
    ("/KNOB", [("RV1", "2"), (35.0, 34.0), (35.0, 29.0), (45.0, 29.0), (45.0, 40.0), (42.25, 40.0), ("SW1", "1")], W_SIG),
    ("/TARGET IN", [("J1", "1"), (37.75, 60.0), ("SW1", "3")], W_SIG),
    ("/TARGET", [("SW1", "2"), (39.25, 43.0), (48.0, 43.0), (48.0, A_Y - OA_IN), ("R5", "1")], W_SIG),
    # ---- U1, the difference amplifier (unity): 4 x 100k; the LOOP switch feeds its - side
    ("Net-(U1-+)", [("R5", "2"), oa("U1", "+")], W_SIG),
    ("Net-(U1-+)", [(U1X - 7.2, A_Y - OA_IN), ("R6", "1")], W_SIG),
    ("/LOOP", [("SW2", "2"), (43.25, 60.0), (50.0, 60.0), (50.0, A_Y + OA_IN), ("R7", "1")], W_SIG),
    ("Net-(U1--)", [("R7", "2"), oa("U1", "-")], W_SIG),
    ("Net-(U1--)", [(U1X - 7.2, A_Y + OA_IN), (U1X - 7.2, FBA), ("R8", "1")], W_SIG),
    ("/ERROR", [oa("U1", "out"), (ERR_X, A_Y), (ERR_X, FBA), (ERR_X, D_Y + OA_IN), (ERR_X, I_Y + OA_IN)], W_SIG),
    ("/ERROR", [("R8", "2"), (ERR_X, FBA)], W_SIG),
    ("/ERROR", [(ERR_X, A_Y + OA_IN), ("R9", "1")], W_SIG),
    # ---- U2, the inverter
    ("Net-(U2--)", [("R9", "2"), oa("U2", "-")], W_SIG),
    ("Net-(U2--)", [(U2X - 7.2, A_Y + OA_IN), (U2X - 7.2, FBA), ("R10", "1")], W_SIG),
    ("/P", [oa("U2", "out"), (U2X + 7.2, A_Y), (104.0, A_Y), (104.0, A_Y + OA_IN), ("R11", "1")], W_SIG),
    ("/P", [(U2X + 7.2, A_Y), (U2X + 7.2, FBA), ("R10", "2")], W_SIG),
    # ---- U3, the summing amplifier; its - node is the SUM_X column the D and I stages feed
    ("Net-(U3--)", [("R11", "2"), oa("U3", "-")], W_SIG),
    ("Net-(U3--)", [(SUM_X, A_Y + OA_IN), (SUM_X, A_Y + 18.77), ("R14", "1")], W_SIG),
    ("Net-(U3--)", [(SUM_X, A_Y + 18.77), (SUM_X, D_Y - 6.0), ("R12", "2")], W_SIG),
    ("Net-(U3--)", [(SUM_X, D_Y - 6.0), (SUM_X, I_Y - 14.0), ("R13", "2")], W_SIG),
    ("Net-(R14-Pad2)", [("R14", "2"), ("RV2", "1")], W_SIG),
    ("/SUM", [oa("U3", "out"), (U3X + 7.2, A_Y), (U6X - 7.2, A_Y), (U6X - 7.2, DRV_Y - OA_IN), oa("U6", "+")], W_SIG),
    ("/SUM", [(U3X + 7.2, A_Y), (U3X + 7.2, A_Y + 18.77), ("RV2", "3")], W_SIG),
    # each trimmer's wiper is tied to its clockwise end (3) by a short wire under the body,
    # so the top of the trimmer is clear for the clockwise arc
    ("/SUM", [("RV2", "2"), (U3X + 3.54, A_Y + 16.23), ("RV2", "3")], W_SIG),
    # ---- the differentiator: ERROR into the switch, a capacitor per pole, 1k, U4, 1M || 470 pF
    ("/ERROR", [(ERR_X, D_Y + OA_IN), ("SW5", "2")], W_SIG),
    ("Net-(SW5-C)", [("SW5", "3"), (72.05, D_Y - 2.0), ("C6", "1")], W_SIG),
    ("Net-(SW5-A)", [("SW5", "1"), (72.05, D_Y + 9.0), ("C5", "1")], W_SIG),
    ("Net-(C5-Pad2)", [("C6", "2"), (82.0, D_Y - 2.0), (82.0, D_Y + 9.0), ("C5", "2")], W_SIG),
    ("Net-(C5-Pad2)", [(82.0, D_Y + OA_IN), ("R15", "1")], W_SIG),
    ("Net-(SW3-A)", [("R15", "2"), oa("U4", "-")], W_SIG),
    ("Net-(SW3-A)", [(U4X - 7.2, D_Y + OA_IN), (U4X - 7.2, FBD), ("C7", "1")], W_SIG),
    ("Net-(SW3-A)", [(U4X - 7.2, FBD), (U4X - 7.2, D_Y + 18.77), ("RV3", "1")], W_SIG),
    ("Net-(SW3-A)", [(U4X - 7.2, D_Y + 18.77), (U4X - 7.2, D_Y + 22.5), (104.05, D_Y + 22.5), ("SW3", "1")], W_SIG),
    ("/D", [oa("U4", "out"), (U4X + 7.2, D_Y), (U4X + 7.2, D_Y + 2.0), ("SW3", "2")], W_SIG),
    ("/D", [(U4X + 7.2, D_Y + 2.0), (U4X + 7.2, FBD), ("C7", "2")], W_SIG),
    ("/D", [(U4X + 7.2, FBD), (U4X + 7.2, D_Y + 18.77), ("RV3", "3")], W_SIG),
    ("/D", [("RV3", "2"), (U4X + 3.04, D_Y + 16.23), ("RV3", "3")], W_SIG),
    ("Net-(SW3-C)", [("SW3", "3"), (104.05, D_Y - 6.0), ("R12", "1")], W_SIG),
    ("+15V", [oa("U4", "v+"), (U4X + 1.14, D_Y - 7.5), ("C26", "1")], W_SIG),
    # ---- the integrator: 1k + 1M in, U5, 1 uF film across, the switch shorts it for reset
    ("/ERROR", [(ERR_X, I_Y + OA_IN), ("R17", "1")], W_SIG),
    ("Net-(R17-Pad2)", [("R17", "2"), (RV4X - 2.54, I_Y + OA_IN), ("RV4", "1")], W_SIG),
    ("Net-(SW4-A)", [("RV4", "3"), (84.0, I_Y + 7.27), (84.0, I_Y + OA_IN), oa("U5", "-")], W_SIG),
    ("Net-(SW4-A)", [("RV4", "2"), (RV4X + 2.54, I_Y + 4.73), ("RV4", "3")], W_SIG),
    ("Net-(SW4-A)", [(U5X - 7.2, I_Y + OA_IN), (U5X - 7.2, FBI), ("C8", "1")], W_SIG),
    # I OFF: on down from C8's input lead, under its body, and up to the switch
    ("Net-(SW4-A)", [("C8", "1"), (U5X - 7.8, I_Y + 22.3), (104.05, I_Y + 22.3), ("SW4", "1")], W_SIG),
    ("/I", [oa("U5", "out"), (U5X + 7.2, I_Y), (U5X + 7.2, I_Y + 2.0), ("SW4", "2")], W_SIG),
    ("/I", [(U5X + 7.2, I_Y + 2.0), ("C8", "2")], W_SIG),
    ("Net-(SW4-C)", [("SW4", "3"), (104.05, I_Y - 2.5), (105.5, I_Y - 2.5), (105.5, I_Y - 14.0), ("R13", "1")], W_SIG),
    ("+15V", [oa("U5", "v+"), (U5X + 1.14, I_Y - 7.0), ("C28", "1")], W_SIG),
    # ---- the motor driver: split feedback, 270 ohm, the push-pull, 1 ohm each, clamps
    ("Net-(U6--)", [oa("U6", "-"), (U6X - 7.2, DRV_Y + OA_IN), (U6X - 7.2, FBM), ("C9", "1")], W_SIG),
    ("Net-(U6--)", [(U6X - 7.2, FBM), ("R18", "1")], W_SIG),
    ("Net-(C9-Pad2)", [oa("U6", "out"), (U6X + 6.5, DRV_Y), ("R19", "1")], W_SIG),
    ("Net-(C9-Pad2)", [(U6X + 6.5, DRV_Y), (U6X + 6.5, FBM), ("C9", "2")], W_SIG),
    # BASES: up to Q1's base on the left; to Q2's, whose base is on the right (the
    # D2PAK cannot be mirrored), under Q2's emitter wire on the back (HOPS)
    ("/BASES", [("R19", "2"), (QX - 8.0, DRV_Y), (QX - 8.0, Q1Y + 7.0), ("Q1", "1")], W_SIG),
    ("/BASES", [(QX - 8.0, DRV_Y), (QX - 8.0, BH_Y), (QX - 4.7, BH_Y), (QX - 0.4, BH_Y),
                (QX + 7.5, BH_Y), (QX + 7.5, Q2Y - 7.0), ("Q2", "1")], W_SIG),
    ("Net-(Q1-E)", [("Q1", "3"), ("R21", "1")], W_RAIL),
    ("Net-(Q2-E)", [("Q2", "3"), ("R22", "2")], W_RAIL),
    # the push-pull's output, between the emitter resistors and the fuse: the
    # clamps and the snubber on it, no loop and no name; down the right edge to F1
    (PP_NET, [("R22", "1"), ("R21", "2"), (BUS_X, PP_Y), (BUS_X, FUSE_Y), ("F1", "1")], W_RAIL),
    (PP_NET, [("D3", "2"), (164.8, PP_Y), ("D4", "1")], W_SIG),
    (PP_NET, [("R20", "1"), (160.9125, PP_Y)], W_SIG),
    ("Net-(C10-Pad1)", [("R20", "2"), ("C10", "1")], W_SIG),
    # DRIVE, behind the fuse: the feedback, the DRIVE loop and DRIVE OUT along y 91
    # to the motor's lead
    ("/DRIVE", [("R18", "2"), (U6X - 7.2, 91.0), (MOT_X, 91.0), (MOT_X, FUSE_Y)], W_SIG),
    ("/DRIVE", [(U6X - 7.2, 91.0), (112.5, 91.0), ("R24", "1")], W_SIG),
    # DRIVE OUT under the integrator (its film capacitor reaches y 115.3) to the jack
    ("Net-(J3-In)", [("R24", "2"), (112.5, 118.3), (68.0, 118.3), (68.0, 112.5), (60.0, 112.5), ("J3", "1")], W_SIG),
    # ---- the fuse row: the PTC, the lamp across it, DRIVE to the motor's terminal
    (PP_NET, [(164.5, FUSE_Y), ("R23", "1")], W_SIG),
    ("Net-(LED3-K)", [("R23", "2"), (164.5, 99.0), ("LED3", "1")], W_SIG),
    ("Net-(LED3-K)", [(164.5, 99.0), (164.5, 103.0), ("LED4", "2")], W_SIG),
    ("/DRIVE", [("F1", "2"), (MOT_X, FUSE_Y), (MOT_X, BOT_Y), ("J4", "1")], W_RAIL),
    ("/DRIVE", [("LED3", "2"), (MOT_X, 99.0)], W_SIG),
    ("/DRIVE", [("LED4", "1"), (MOT_X, 103.0)], W_SIG),
    # ---- the plant's track: end resistors to the rails' flags, decoupling, the wiper
    ("/POT+", [("J5", "1"), ("R3", "2")], W_SIG),
    ("/POT+", [(POS_X + 5.0, 109.4), ("C3", "1")], W_SIG),
    ("+15V", [("R3", "1"), (POS_X + 5.0, 100.5)], W_SIG),
    ("/POT-", [("J5", "3"), ("R4", "1")], W_SIG),
    ("/POT-", [(POS_X - 5.0, 110.2), ("C4", "1")], W_SIG),
    ("-15V", [("R4", "2"), (POS_X - 5.0, 102.3)], W_SIG),
    ("/POSITION", [("J5", "2"), (POS_X, 105.0)], W_SIG),
    # ---- the POSITION follower and its jack (POSITION arrives on the back)
    ("/POSITION", [(12.0, U7Y - OA_IN), oa("U7", "+")], W_SIG),
    ("/POSITION", [(41.75, 64.0), ("SW2", "3")], W_SIG),
    ("Net-(U7--)", [oa("U7", "out"), (29.0, U7Y), ("R25", "1")], W_SIG),
    ("Net-(U7--)", [(29.0, U7Y), (29.0, U7Y + 12.0), (14.0, U7Y + 12.0), (14.0, U7Y + OA_IN), oa("U7", "-")], W_SIG),
    ("Net-(J2-In)", [("R25", "2"), (35.0, U7Y), (35.0, 101.0), ("J2", "1")], W_SIG),
    ("+15V", [oa("U7", "v+"), (U7X + 1.14, U7Y - 7.5), ("C32", "1")], W_SIG),
    # ---- the op-amps' supplies: V+ up to the rail with a bypass hanging beside it, V- flags
    ("+15V", [oa("U1", "v+"), (U1X + 1.14, VP_Y)], W_SIG), ("+15V", [("C20", "1"), (U1X + 4.5, VP_Y)], W_SIG),
    ("+15V", [oa("U2", "v+"), (U2X + 1.14, VP_Y)], W_SIG), ("+15V", [("C22", "1"), (U2X + 4.5, VP_Y)], W_SIG),
    ("+15V", [oa("U3", "v+"), (U3X + 1.14, VP_Y)], W_SIG), ("+15V", [("C24", "1"), (U3X + 4.5, VP_Y)], W_SIG),
    ("+15V", [oa("U6", "v+"), (U6X + 1.14, VP_Y)], W_SIG), ("+15V", [("C30", "1"), (U6X + 4.5, VP_Y)], W_SIG),
    ("-15V", [oa("U1", "v-"), ("C21", "2")], W_SIG), ("-15V", [oa("U2", "v-"), ("C23", "2")], W_SIG),
    ("-15V", [oa("U3", "v-"), ("C25", "2")], W_SIG), ("-15V", [oa("U4", "v-"), ("C27", "2")], W_SIG),
    ("-15V", [oa("U5", "v-"), ("C29", "2")], W_SIG), ("-15V", [oa("U6", "v-"), ("C31", "2")], W_SIG),
    ("-15V", [oa("U7", "v-"), ("C33", "2")], W_SIG),
]

# Segments that run on the back layer between two vias, under a crossing wire: (net, start, end).
HOPS = [("/BASES", (QX - 4.7, BH_Y), (QX - 0.4, BH_Y))]

# Copper on the back only: (net, [points], width, vias) with vias "both",
# "start", "end" or "none": a via at those ends (an end on a through-hole pad
# needs none).  The plane flows round it.  -15 V is a trunk just above the
# +15 V rail with a branch down to every flag; the lower stages' +15 V comes
# down from the push-pull's pour; POSITION runs back along the bottom.
BACK = [
    ("-15V", [(148.5, 13.5), (148.5, VM_TOP), (26.0, VM_TOP), (26.0, 90.0), (U7X, U7Y + OA_VM_DY)], W_RAIL, "both"),
    ("-15V", [(24.0, 50.0), (26.0, 50.0)], W_SIG, "start"),
    ("-15V", [(U1X, A_Y + OA_VM_DY), (U1X + 3.0, A_Y + OA_VM_DY), (U1X + 3.0, VM_TOP)], W_SIG, "start"),
    ("-15V", [(U2X, A_Y + OA_VM_DY), (91.0, A_Y + OA_VM_DY), (91.0, VM_TOP)], W_SIG, "start"),
    ("-15V", [(U5X, I_Y + OA_VM_DY), (VM_BR, I_Y + OA_VM_DY), (VM_BR, VM_TOP)], W_SIG, "start"),
    ("-15V", [(U4X, D_Y + OA_VM_DY), (VM_BR, D_Y + OA_VM_DY)], W_SIG, "start"),
    ("-15V", [(U3X, A_Y + OA_VM_DY), (U3X + 3.0, A_Y + OA_VM_DY), (U3X + 3.0, VM_TOP)], W_SIG, "start"),
    # Q2's pour (-15 V) is fed up the board's right edge, outside the heat's way;
    # U6's V- and the track's -15 V end come from that pour.  Nothing crosses
    # under the pours: the ground plane there is the push-pull's heatsink too.
    ("-15V", [(166.0, Q2Y - 7.0), (166.0, Q2Y - 5.0), (168.8, Q2Y - 5.0), (168.8, VM_TOP), (163.5, VM_TOP)], W_RAIL, "both"),
    ("-15V", [(U6X, DRV_Y + OA_VM_DY), (143.5, DRV_Y + OA_VM_DY), (143.5, 70.0)], W_SIG, "both"),
    ("-15V", [(POS_X - 5.0, 102.3), (149.6, 102.3), (149.6, 89.6)], W_SIG, "both"),     # clear of the QR code and its URL
    # the lower stages' +15 V: from the rail down the spine
    ("+15V", [(81.0, VP_Y), (81.0, 50.0), (VP_SP, 50.0), (VP_SP, D_Y - 7.5)], W_SIG, "start"),
    ("+15V", [(POS_X + 5.0, 100.5), (VP_SP, 100.5), (VP_SP, D_Y - 7.5), (U4X + 1.14, D_Y - 7.5)], W_SIG, "end"),
    ("+15V", [(VP_SP, I_Y - 7.0), (U5X + 1.14, I_Y - 7.0)], W_SIG, "end"),
    ("+15V", [(20.0, VP_Y), (20.0, U7Y - 7.5), (U7X + 1.14, U7Y - 7.5)], W_SIG, "both"),
    ("/POSITION", [(POS_X, 105.0), (46.0, 105.0), (46.0, 64.0), (41.75, 64.0)], W_SIG, "both"),
    ("/POSITION", [(46.0, 105.0), (12.0, 105.0), (12.0, U7Y - OA_IN)], W_SIG, "end"),
]
# Back runs of these nets are drawn on the front as dashed lines (a signal
# that goes round the back, as a sheet's net label does); the rest are flags.
DASHED_BACK = {"/POSITION"}
# More vias where one would carry a whole transistor's current: (net, x, y).
EXTRA_VIAS = [("-15V", 166.0, Q2Y - 6.0), ("-15V", 166.0, Q2Y - 5.0), ("-15V", 164.5, VM_TOP), ("-15V", 165.5, VM_TOP)]
# Flags where the back copper surfaces: (net, x, y[, dx, dy, justify]) for the name's place
FLAGS = [
    ("-15V", 24.0, 50.0), ("-15V", POS_X - 5.0, 102.3, 1.6, 0.45, "left"),   # its name low, clear of THE FADER'S TRACK
    ("+15V", U4X + 1.14, D_Y - 7.5, -1.6, 0.0, "right"), ("+15V", U5X + 1.14, I_Y - 7.0, -1.6, 0.0, "right"),
    ("+15V", U7X + 1.14, U7Y - 7.5, -1.6, 0.0, "right"), ("+15V", POS_X + 5.0, 100.5),
]

# Ground: a stub from the pad to a via (a point, or a path of points), the
# ground symbol drawn at the via pointing the way the last segment runs.
# An op-amp pad's stub starts where its lead leaves the triangle.
GND_STUBS = [
    (("C1", "2"), [(33.5, 27.0), (33.5, 30.0)]), (("C2", "1"), [(29.5, 41.0), (29.5, 44.0)]),
    (("R6", "2"), (U1X - 7.2, 24.5)), (("SW2", "1"), (46.25, 55.0)),
    (("U2", "1"), [(U2X - 7.2, A_Y - OA_IN), (U2X - 9.2, A_Y - OA_IN), (U2X - 9.2, A_Y - 1.5)]),
    (("U3", "1"), [(U3X - 7.2, A_Y - OA_IN), (U3X - 9.2, A_Y - OA_IN), (U3X - 9.2, A_Y - 1.5)]),
    (("U4", "1"), [(U4X - 7.2, D_Y - OA_IN), (U4X - 9.2, D_Y - OA_IN), (U4X - 9.2, D_Y - 1.5)]),
    # east as far as the triangle allows, clear of the "I" of RV4's arc label
    (("U5", "1"), [(U5X - 7.2, I_Y - OA_IN), (U5X - 8.15, I_Y - OA_IN), (U5X - 8.15, I_Y - 1.5)]),
    (("C20", "2"), (U1X + 4.5, VP_Y + 6.5)), (("C22", "2"), (U2X + 4.5, VP_Y + 6.5)),
    (("C24", "2"), (U3X + 4.5, VP_Y + 6.5)), (("C30", "2"), (U6X + 4.5, VP_Y + 6.5)),
    (("C26", "2"), [(U4X + 7.0, D_Y - 7.5), (U4X + 7.0, D_Y - 5.0)]),
    (("C28", "2"), [(U5X + 7.0, I_Y - 7.0), (U5X + 7.0, I_Y - 4.5)]),
    (("C32", "2"), [(U7X + 7.0, U7Y - 7.5), (U7X + 7.0, U7Y - 5.0)]),
    (("C21", "1"), (U1X, A_Y + VM_GND)), (("C23", "1"), (U2X, A_Y + VM_GND)), (("C25", "1"), (U3X, A_Y + VM_GND)),
    (("C27", "1"), (U4X, D_Y + VM_GND)), (("C29", "1"), (U5X, I_Y + VM_GND)), (("C31", "1"), (U6X, DRV_Y + VM_GND)),
    (("C33", "1"), (U7X, U7Y + VM_GND)),
    (("C10", "2"), (155.5875, PP_Y + 4.9)),
    (("C3", "2"), (133.95, 112.5)), (("C4", "2"), (114.55, 112.9)),
    (("C11", "2"), (76.0, 24.0)), (("C13", "2"), (83.0, 22.5)),
    (("C12", "1"), (155.5, 23.0)), (("C14", "1"), (148.5, 21.0)),
    (("LED1", "1"), (102.0, 25.5)), (("LED2", "2"), (163.5, 23.5)),
    (("D5", "2"), (130.5, 23.3)), (("D6", "1"), (145.4, 21.4)),
    (("J6", "2"), (138.0, 8.5)),
    (("J4", "2"), [(146.0, 110.5), (146.0, 108.5)]),
    (("TP100", "1"), (40.0, 95.0)), (("TP101", "1"), (42.0, 102.0)), (("TP102", "1"), (50.0, 102.0)), (("TP103", "1"), (118.0, 73.0)),
]
# Through-hole ground posts the plane reaches directly, with where to draw the symbol.
GND_MARKS = [(12.5, 61.5), (2.5, 108.3), (67.5, 112.5)]

# --------------------------------------------------------- silkscreen -----
OPAMPS = ["U1", "U2", "U3", "U4", "U5", "U6", "U7"]
TRANSISTORS = {"Q1": ("NPN", "left"), "Q2": ("PNP", "right")}
Q_CAPTION = {"Q1": (147.4, 34.6, "right", 0.9), "Q2": (147.4, 80.9, "right", 0.9)}
# Each transistor's heatsink: copper on its collector's net round the tab, as
# rectangles (x0, y0, x1, y1) that the board generator joins, less the
# symbol's circle; the fill keeps clear of everything else.  2 oz copper.
POURS = {
    "Q1": [(129.6, 28.6, 168.6, 45.3),          # above the base lead, the box's full width
           (129.6, 45.3, 145.4, 50.8),          # left of BASES, above U6
           (140.6, 50.8, 145.4, 56.6),          # down to R19
           (158.6, 45.3, 168.6, 58.25)],        # right of R21, round D3's cathode
    "Q2": [(129.6, 73.6, 166.6, 90.5),          # below U6's feedback, the box's full width
           (142.2, 66.7, 149.2, 73.6),          # between BASES and the circle
           (162.0, 59.6, 166.6, 73.6)],         # right of BASES, round D4's anode
}

# Free text: (x, y, text, size, thickness, justify, angle)
TEXTS = [
    # identity, in the band above the +15 V rail
    (75.0, 5.0, parts.BOARD_NAME.upper(), 2.4, 0.4, "center", 0),
    (75.0, 8.2, "Learning the Art of Electronics (Hayes & Horowitz), Lab 10L: a motorized fader held to a target", 1.0, 0.15, "center", 0),
    (75.0, 10.4, "board: Jason Gallicchio and Claude    rev " + parts.REV + "  " + parts.BOARD_DATE + "    " + parts.PROJECT_URL, 1.0, 0.15, "center", 0),
    (20.5, 12.3, "+15 V", 1.2, 0.2, "left", 0),
    (150.9, 10.6, "-15 V", 0.9, 0.18, "left", 0),
    (72.5, 16.2, "100uF", 0.8, 0.15, "right", 0), (72.5, 17.6, "C11", 0.8, 0.15, "right", 0),
    (84.6, 16.2, "C13", 0.8, 0.15, "left", 0), (84.6, 17.6, "100nF", 0.8, 0.15, "left", 0),
    (103.7, 22.0, "GREEN", 0.8, 0.15, "left", 0), (163.5, 26.4, "GREEN", 0.8, 0.15, "center", 0),
    (103.7, 16.3, "R26", 0.8, 0.15, "left", 0), (103.7, 17.7, "10k", 0.8, 0.15, "left", 0),
    (165.2, 16.2, "10k", 0.8, 0.15, "left", 0),
    (155.5, 26.4, "100uF", 0.8, 0.15, "center", 0), (148.5, 24.4, "100nF", 0.8, 0.15, "center", 0),
    (151.0, 7.4, "D1, D2: SS34", 0.8, 0.15, "left", 0),
    (151.0, 8.8, "D5, D6: SS34 clamps", 0.8, 0.15, "left", 0),
    (132.2, 9.1, "+15", 0.8, 0.15, "right", 0), (143.8, 9.1, "-15", 0.8, 0.15, "left", 0),
    (147.0, 4.0, "POWER ±15 V, 1 A", 1.0, 0.18, "left", 0),
    (147.0, 5.6, "both green lamps light", 0.8, 0.15, "left", 0),
    # the TARGET knob and jack
    (17.0, 20.3, "TARGET", 1.8, 0.3, "center", 0),
    (17.0, 22.2, "centre = 0 V, clockwise +", 0.8, 0.15, "center", 0),
    (12.5, 54.6, "TARGET IN", 1.2, 0.2, "left", 0),
    (12.5, 56.2, "±12 V max.  A square wave", 0.8, 0.15, "left", 0),
    (12.5, 57.6, "±3 V at 0.2 Hz replaces the knob", 0.8, 0.15, "left", 0),
    # the source switch, explained beside it
    (36.9, 39.1, "TARGET", 0.8, 0.15, "right", 0), (36.9, 40.4, "SOURCE", 0.8, 0.15, "right", 0),
    (36.9, 41.7, "1 = knob", 0.8, 0.15, "right", 0), (36.9, 43.0, "3 = jack", 0.8, 0.15, "right", 0),
    # the loop switch
    (44.0, 44.4, "LOOP", 0.9, 0.18, "center", 0),
    (44.0, 45.75, "3 = closed loop", 0.8, 0.15, "center", 0), (44.0, 47.05, "1 = open loop", 0.8, 0.15, "center", 0),
    # the gain trimmers
    (116.0, 56.2, "P GAIN", 0.8, 0.15, "center", 0),
    (90.6, 75.9, "D", 0.8, 0.15, "right", 0), (90.6, 77.1, "GAIN", 0.8, 0.15, "right", 0),
    (RV4X, 106.0, "I GAIN", 0.8, 0.15, "center", 0),
    (U5X + 7.2 - 7.5 + 11.2, FBI + 0.7, "film", 0.8, 0.15, "left", 0),        # under C8's value
    (U6X + 8.7, DRV_Y + 7.0, "U6 OUT", 0.8, 0.15, "center", 90),
    (31.2, U7Y + 7.0, "U7 OUT", 0.8, 0.15, "center", 90),
    (143.7, 52.0, "BASES", 0.8, 0.15, "center", 90),
    # the D and I switches
    (69.0, 62.6, "D CAPACITOR", 0.8, 0.15, "right", 0),
    (69.0, 64.0, "3 = 100 nF", 0.8, 0.15, "right", 0), (69.0, 65.4, "1 = 22 nF", 0.8, 0.15, "right", 0),
    (111.1, 58.4, "D IN / OFF", 0.8, 0.15, "left", 0),
    (111.1, 59.8, "3 = into the sum", 0.8, 0.15, "left", 0),
    (111.1, 61.2, "1 = off (shorted)", 0.8, 0.15, "left", 0),
    (111.1, 86.7, "I IN / OFF", 0.8, 0.15, "left", 0),
    (111.1, 88.1, "3 = into the sum", 0.8, 0.15, "left", 0),
    (111.1, 89.5, "1 = off (reset)", 0.8, 0.15, "left", 0),
    # the clamps, the fuse and its lamps
    (162.9, 54.0, "D3, D4", 0.8, 0.15, "right", 0), (162.9, 55.4, "SS34", 0.8, 0.15, "right", 0),
    (162.9, 56.8, "clamps", 0.8, 0.15, "right", 0),
    # the snubber in the pocket under DRIVE, one line each
    (156.8, PP_Y + 1.35, "C10 100nF", 0.8, 0.15, "center", 0), (160.0, PP_Y + 4.75, "R20 10R", 0.8, 0.15, "center", 0),
    # the push-pull's copper is its heatsink: a stall at a few volts heats it
    (147.4, 37.5, "HOT if the", 0.8, 0.15, "right", 0), (147.4, 38.9, "motor stalls", 0.8, 0.15, "right", 0),
    (147.4, 84.0, "HOT if the", 0.8, 0.15, "right", 0), (147.4, 85.4, "motor stalls", 0.8, 0.15, "right", 0),
    (152.5, 105.6, "MOTOR FUSE 0.35 A", 0.8, 0.15, "left", 0),
    (152.5, 107.0, "red = fuse open", 0.8, 0.15, "left", 0),
    # the jacks on the left and bottom edges
    (14.5, 99.7, "POSITION OUT", 1.0, 0.18, "left", 0),
    (53.8, 110.5, "DRIVE OUT", 1.0, 0.18, "right", 0),
    (53.8, 112.0, "1k in series", 0.8, 0.15, "right", 0),
    # the terminals' pins
    (120.6, 110.5, "-", 0.8, 0.15, "left", 0), (124.6, 110.5, "wiper", 0.8, 0.15, "left", 0), (129.8, 110.5, "+", 0.8, 0.15, "left", 0),
    (141.0, 110.5, "shield", 0.8, 0.15, "center", 0), (146.0, 110.5, "GND", 0.8, 0.15, "center", 0), (152.6, 110.5, "MOTOR", 0.8, 0.15, "left", 0),
    # a legend for the 14 bypass capacitors, which carry no names of their own
    (13.0, 66.5, "every op-amp has 100 nF from each", 0.8, 0.15, "left", 0),
    (13.0, 67.9, "supply pin to ground (C20-C33)", 0.8, 0.15, "left", 0),
]
LEGENDS = []

# Reference designators and values: ref -> ((ref dx, dy), (value dx, dy)) from the part.
# Horizontal parts get their names above and below; vertical ones to the right.
FIELD_AT = {}
for _ref, (_x, _y, _rot) in PLACE.items():
    if _ref[0] in "RCDL" and _ref[:2] != "LE":
        FIELD_AT[_ref] = ((0.0, -1.75), (0.0, 1.75)) if _rot in (0, 180) else ((1.7, -0.7), (1.7, 0.7))
FIELD_AT.update({
    "R3": ((1.7, -3.4), (1.7, -4.8)), "R4": ((-1.7, -3.4), (-1.7, -4.8)),
    "R21": ((-2.4, -0.7), (-2.4, 0.7)), "R22": ((-2.4, -0.7), (-2.4, 0.7)),
    "R19": ((0.0, -3.05), (0.0, -1.75)), "R6": ((1.7, -2.0), (1.7, -0.6)),
    "R12": ((0.0, -3.05), (0.0, -1.75)), "R13": ((0.0, -3.05), (0.0, -1.75)),
    "C3": (None, (0.0, -1.75)), "C4": (None, (0.0, -1.75)),
    "RV1": (None, (-3.5, 4.1)),
    "RV2": ((-4.3, -1.8), (-4.3, -0.5)), "RV3": ((-3.9, -1.2), (-3.9, 0.0)), "RV4": ((-4.3, 0.0), (-4.3, 1.3)),
    "F1": (None, (0.0, 2.7)),
    "R8": ((0.0, 1.75), (0.0, 3.05)), "R10": ((0.0, 1.75), (0.0, 3.05)), "R14": ((0.0, 1.75), (0.0, 3.05)),
    "C7": ((0.0, -3.05), (0.0, -1.75)), "C8": ((11.2, -2.1), (11.2, -0.7)),
    "C5": ((0.0, 1.75), (0.0, 3.05)), "C6": ((0.0, -3.05), (0.0, -1.75)),
})
# Parts whose reference or value is printed as free text instead, or not at all.
_BYPASS = {f"C{n}" for n in range(20, 34)}
HIDE_REF = _BYPASS | {"J1", "J2", "J3", "J4", "J5", "J6", "SW1", "SW2", "SW3", "SW4", "SW5",
                      "LED1", "LED2", "LED3", "LED4", "C11", "C13", "C12", "C14", "R26", "R27", "R23",
                      "D1", "D2", "D3", "D4", "D5", "D6", "F1", "R20", "C10"}
HIDE_VALUE = _BYPASS | {"J1", "J2", "J3", "J4", "J5", "J6", "SW1", "SW2", "SW3", "SW4", "SW5",
                        "LED1", "LED2", "LED3", "LED4", "C11", "C13", "C12", "C14", "R26", "R27", "R23",
                        "D1", "D2", "D3", "D4", "D5", "D6", "R20", "C10"}

# Each slide switch's ends numbered as its legend numbers them, in the
# footprint's own frame (pin 1 at -x, the actuator edge at +y): beyond the
# actuator edge at the two ends where that side is clear, past the shell pads
# along the slide where a wire runs beside the body.
_SW_SIDE = {"1": (-2.25, 2.45), "3": (2.25, 2.45)}
_SW_ENDS = {"1": (-4.95, 0.0), "3": (4.95, 0.0)}
SW_MARKS = {"SW1": _SW_SIDE, "SW2": _SW_ENDS, "SW5": {"1": (-2.25, 2.6), "3": (2.25, 2.6)},
            "SW3": _SW_ENDS, "SW4": {"1": (-4.95, 0.0), "3": (4.95, 0.6)}}

# Where each probe loop's name goes, relative to the loop: (dx, dy, justify); None = no name.
TP_LABEL = {
    "TP1": (-1.6, 0.0, "right"), "TP2": (2.6, 0.0, "left"), "TP3": (0.0, -3.0, "center"),
    "TP4": (-1.6, 0.0, "right"), "TP5": (-1.6, 0.0, "right"), "TP6": (2.6, 0.0, "left"),
    "TP7": (0.0, -3.0, "center"), "TP8": (0.0, -3.3, "center"), "TP9": None, "TP10": None,
    "TP11": None, "TP12": None, "TP13": None,
    "TP100": (2.6, 0.0, "left"), "TP101": None, "TP102": (2.6, 0.0, "left"), "TP103": (2.6, 0.0, "left"),
}

# Dashed boxes round the stages, named as the book names them:
# (x0, y0, x1, y1, [(title line, x, y[, size]), ...]); titles are short lines that dodge the wires.
BOXES = [
    (50.5, 18.5, 69.0, 50.8, [("DIFFERENCE", 51.0, 19.9, 0.85), ("AMPLIFIER x1", 51.0, 21.3, 0.85)]),
    (72.5, 26.0, 97.5, 50.8, [("INVERTER x-1", 73.0, 27.4, 0.85)]),
    (103.0, 26.0, 124.5, 57.0, [("SUMMING", 103.5, 27.4, 0.85), ("AMPLIFIER", 103.5, 28.8, 0.85)]),
    (71.0, 52.0, 109.5, 85.5, [("DIFFERENTIATOR", 71.5, 53.4, 0.85)]),
    (71.0, 86.0, 109.5, 117.3, [("INTEGRATOR", 71.5, 87.4, 0.85)]),
    (126.0, 28.2, 168.5, 92.5, [("MOTOR DRIVER", 126.5, 29.7, 0.8), ("gain 1", 126.5, 31.1, 0.8)]),
    (149.0, 92.8, 169.0, 109.0, []),
    (111.5, 99.3, 138.5, 111.4, [("THE FADER'S TRACK", 113.5, 101.2, 0.8)]),
    (10.5, 76.0, 38.0, 101.7, [("FOLLOWER", 30.2, 77.4, 0.85), ("x1", 30.2, 78.8, 0.85)]),
    (123.5, 1.5, 168.5, 27.2, []),
]

# Clockwise arcs.  Over each knob and trimmer a short arc runs from `a0` round
# to 12 o'clock and ends in an arrowhead pointing the way the shaft turns
# clockwise, with what that does printed beside it.  Bourns 3362: the wiper
# reaches terminal 3 turning clockwise (the data sheet's schematic), and every
# trimmer here is a rheostat between 1 and 2 with 3 tied to the wiper, so
# clockwise is always more resistance; what that does to the gain depends on
# where the resistance sits (P and D: feedback, more; I: input, less).  The
# ALPS knob: terminal 3 clockwise by the same convention (DESIGN_NOTES, "Not
# yet proven").  ref: (centre from the anchor in board mm, radius, start angle, label)
CW_ARCS = {
    "RV1": ((-7.5, -2.5), 10.0, 225, "\u2191TARGET"),         # the shaft, not the pins
    # r 5.0 from 238: the arc's start must clear the trimmer's own silk box (top at
    # 3.8 above the centre) by the 0.15 mm silk clearance, and the 10 o'clock end
    # would land on the wire that feeds terminal 1
    "RV2": ((0.0, 0.0), 5.0, 238, "\u2191R \u2191P"),
    "RV3": ((0.0, 0.0), 5.0, 238, "\u2191R \u2191D"),
    "RV4": ((0.0, 0.0), 5.0, 238, "\u2191R \u2193I"),
}

FIDUCIALS = [(12.0, 10.0), (12.0, 110.0), (158.0, 112.0)]
QR_AT, QR_MODULE = (133.0, 83.0), 0.6      # seen from the back: left of the text, clear of vias and holes
BACK_TITLE_AT = (85.0, 44.0)
# The back: what a student needs at the bench, one item to a line.  The text is
# mirrored, so a line starts at BACK_X and runs toward smaller board x; an
# entry is a string, or (indent, text), or (indent, text, indent2, text2) for a
# label with its options in a second column.  The column runs from x 70 to
# about 13 and from y 53 to 107: clear of the J1/J2 posts, the switch slots,
# the trimmers' pins and J3.
BACK_X, BACK_Y, BACK_PITCH, BACK_SIZE = 70.0, 52.6, 1.6, 0.9
_C2 = 17.0                                    # where a switch's options start
BACK_TEXT = [
    "LAB 10L: a PID loop holds a fader (motorized potentiometer) where TARGET says.",
    "",
    "POWER: +15 V, GND, -15 V on the POWER terminal, 1 A per rail.",
    (3, "Both green lamps light.  A reversed supply is blocked: the lamps stay dark."),
    "FADER (Bourns PSM01-082A-103B2): motor A to MOTOR, motor B to GND.",
    (3, "Track 1, 2, 3 to POT 1 (+), 2 (wiper), 3 (-): the numbers match."),
    (3, "Check with LOOP open: slide it by hand, POSITION is +7.7 V at the + end."),
    (3, "LOOP closed and the slider runs to an end and stays: swap the motor leads."),
    "INPUTS",
    (3, "TARGET knob: centre detent = 0 V, clockwise +, up to +/-6.4 V."),
    (3, "TARGET IN jack: a function generator, +/-12 V max."),
    (6, "Try +/-3 V: a 0.2 Hz square wave for steps, a 0.05 Hz triangle for stick-slip."),
    "OUTPUTS, each through 1k: for a scope, not a load",
    (3, "POSITION OUT: the fader's wiper, buffered.   DRIVE OUT: the motor drive."),
    "SWITCHES",
    (3, "TARGET SOURCE", _C2, "1 = the knob"),
    (_C2, "3 = the TARGET IN jack"),
    (3, "LOOP", _C2, "1 = open: no feedback; DRIVE = P GAIN x TARGET (+ D, I if in)"),
    (_C2 + 4, "P GAIN anticlockwise, D and I off: DRIVE = TARGET"),
    (_C2, "3 = closed: POSITION fed back, the loop holds TARGET"),
    (3, "D IN / OFF", _C2, "1 = off: the differentiator's output shorted"),
    (_C2, "3 = D into the sum"),
    (3, "D CAPACITOR", _C2, "1 = 22 nF, for this fader"),
    (_C2, "3 = 100 nF, for the book's slower rotary pot"),
    (3, "I IN / OFF", _C2, "1 = off: the 1 uF shorted, so I restarts from zero"),
    (_C2, "3 = I into the sum"),
    "TRIMMERS: clockwise = more resistance: more P, more D, but LESS I.",
    "START: every switch on 1.  P and D GAIN anticlockwise, I GAIN clockwise.",
    (3, "LOOP to 3: the slider follows the knob.  Raise P GAIN until it rings."),
    (3, "D IN, raise D GAIN: the ringing dies.  Lower P; I IN: the error goes to 0."),
    "WARNINGS",
    (3, "A short to GND opens the fuse in about a second (red lamps); it resets."),
    (3, "A stall may never open it: HOT copper reaches 90 C, so use the standoffs."),
    (3, "Never short MOTOR or DRIVE to a rail.  Power off to wire the fader."),
    (3, "Scope ground clips go on the GND loops only, never on a signal or a rail."),
]
