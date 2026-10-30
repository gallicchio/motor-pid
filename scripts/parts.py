"""Single source of truth for every part: value, footprint, LCSC code, notes.

The schematic, the BOM, the CPL, the cost estimate and the silkscreen legends
are all generated from this table, so there is exactly one place to change a
part.  Stock figures are what JLCPCB's parts API returned on the date given;
`scripts/jlc_api.py <code>` re-queries them, and the release refuses to build
when a code's description no longer matches the value and package here.
"""

REV = "A"
BOARD_DATE = "2026-10-29"
BOARD_NAME = "PID Motor Control Loop"
PROJECT_URL = "github.com/gallicchio/motor-pid"   # the git remote of this checkout
STOCK_DATE = "2026-10-24"

# The plant: the motorized slide potentiometer the lab owns.
# Bourns PSM01-082A-103B2 (PSP01-082A-103B2: the same in a metal-framed body);
# the motor numbers are Jason's bench measurements of 2026-10-26.
FADER = dict(
    name="Bourns PSM01-082A-103B2 (100 mm motorized slide pot, 10k, taper B2)",
    pot_ohms=10e3, travel_mm=100.0, linear_mm=80.0,       # B2: linear from 10 % to 90 % of the travel
    motor_v_rated=10.0, motor_v_range=(6.0, 11.0),
    motor_r_ohm=14.0,                                     # 0.36 A stalled at 5 V (18 ohm on an ohmmeter)
    motor_i_break_a=0.18, motor_i_running_a=0.16,         # 2-3 V to break loose; 0.16 A running at 3 V
    pins=dict(motor_plus="A", motor_minus="B", pot_plus="1", wiper="2", pot_minus="3"),   # A + moves the lever toward 1
)

# lcsc       : JLCPCB / LCSC order code
# jlc_type   : "basic" | "preferred" | "extended"  (Extended = per-part setup fee)
# process    : "SMT" | "THT"
# stock      : stock seen at JLCPCB on STOCK_DATE
# alt        : drop-in alternates, checked to share the footprint
PARTS = {
    # ---- the op-amp: the book's LM358, one amplifier per package ------------
    "OPAMP": dict(
        value="LM321", mpn="LM321MFX/NOPB", lcsc="C9405", jlc_type="extended",
        process="SMT", stock=193397, price=0.1578,
        footprint="Package_TO_SOT_SMD:SOT-23-5",
        symbol="Amplifier_Operational:LM321",
        desc="LM321 (TI): the single-amplifier LM358, SOT-23-5, 3-32 V, 1 MHz, 0.4 V/us, "
             "inputs to V- and to V+ - 1.5 V, no phase reversal (the book: 'not 411'). "
             "One package per triangle so the silkscreen is the schematic",
        alt=["LM321DTR (XBLW) / C18723612 (398k, $0.03)",
             "LM321MF (UTC) / C668208 (391k, $0.04)"]),
    # ---- the motor driver's power pair: the book's MJE3055 / MJE2955 in D2PAK
    # D2PAK, not DPAK: a stall at a few volts of DRIVE puts up to 3.7 W in one of
    # them for as long as the 0.35 A fuse holds (DESIGN_NOTES, "A stall at a few
    # volts").  RthJC 2.5 C/W against the DPAK's 6.25, on a ~30 x 18 mm pour of
    # 2 oz copper: about 120 C at the junction (sim/thermal.py --board).
    "NPN_PWR": dict(
        value="MJB44H11", mpn="MJB44H11T4G", lcsc="C233689", jlc_type="extended",
        process="SMT", stock=1458, price=1.2244,
        footprint="Package_TO_SOT_SMD:TO-263-2",
        symbol="Transistor_BJT:Q_NPN_BCE",
        desc="10 A 80 V 50 W NPN, D2PAK (1 = B, 2 = C on the tab, 3 = E): the upper half of "
             "the motor driver's push-pull.  Its tab is the +15 V rail; the copper round "
             "it is its heatsink",
        alt=["MJB44H11G / C80690 (355)", "MJB44H11T4-A (ST) / C2802057 (708)"]),
    "PNP_PWR": dict(
        value="MJB45H11", mpn="MJB45H11T4G", lcsc="C154570", jlc_type="extended",
        process="SMT", stock=486, price=1.1573,
        footprint="Package_TO_SOT_SMD:TO-263-2",
        symbol="Transistor_BJT:Q_PNP_BCE",
        desc="10 A 80 V 50 W PNP, D2PAK: the lower half of the push-pull, tab on the -15 V rail",
        alt=["MJB45H11G / C463327 (151)"]),
    # ---- passives: 0805 so a student can probe and rework them -------------
    "R_0805": dict(footprint="Resistor_SMD:R_0805_2012Metric", process="SMT",
                   symbol="Device:R_US"),
    "R_1206": dict(footprint="Resistor_SMD:R_1206_3216Metric", process="SMT",
                   symbol="Device:R_US"),
    "R_2512": dict(footprint="Resistor_SMD:R_2512_6332Metric", process="SMT",
                   symbol="Device:R_US"),
    "C_0805": dict(footprint="Capacitor_SMD:C_0805_2012Metric", process="SMT",
                   symbol="Device:C"),
    # ---- the bulk capacitors on the motor's rails ----------------------------
    "CBULK": dict(
        value="100uF", mpn="JVJ25V100M6x5", lcsc="C46550402", jlc_type="extended",
        process="SMT", stock=200110, price=0.0423,
        footprint="Capacitor_SMD:CP_Elec_6.3x5.4",
        symbol="Device:C_Polarized_US",
        desc="100 uF 25 V aluminium electrolytic, SMD 6.3 x 5.4 mm, one per rail at the "
             "motor driver: the motor draws 0.8 A pulses through a metre of bench lead",
        alt=["RST100UF25V004 / C4747964 (196k)", "RVT25V100M6X5 / C47023107 (141k)"]),
    # ---- the integrator's capacitor: a filter-grade film ---------------------
    # Polypropylene keeps its value whatever the voltage across it (an X5R 10 uF
    # loses much of it at the integrator's few volts), leaks next to nothing
    # and soaks up little charge: Panasonic's own recommendation for the 450 V
    # ECW-F is "active filter circuit".  1 uF, not the book's 7.5: with the 1M
    # trimmer, RC runs from 1 ms to 1 s across the whole turn, and 1 s is the
    # slowest I this fader needs (sim/pid_sim.py).
    "CFILM": dict(
        value="1uF", mpn="ECWF2W105JA", lcsc="C242107", jlc_type="extended",
        process="THT", stock=2052, price=0.3259,
        footprint="motorpid:C_Film_Panasonic_ECWF_L18.1mm_W9.3mm_P15.00mm",
        symbol="Device:C",
        desc="1 uF 5 % metallized polypropylene film, 450 V, Panasonic ECW-F, 18.1 x 9.3 mm, "
             "leads on 15 mm: the integrator's capacitor, C8",
        alt=["C352S105J62C000 (Faratronic) / C401331 (3757, $0.22, 15 mm)",
             "ECWFE2W105J / C178481 (987, $0.58)"]),
    # ---- the target knob -----------------------------------------------------
    "POT_KNOB": dict(
        value="10k", mpn="RK09K1130A70", lcsc="C351173", jlc_type="extended",
        process="THT", stock=6351, price=0.5335,
        footprint="Potentiometer_THT:Potentiometer_Alps_RK09K_Single_Vertical",
        symbol="Device:R_Potentiometer_US",
        desc="ALPS RK09K 9 mm vertical potentiometer, 10 k linear, 30 mm knurled knob "
             "shaft with a centre detent: TARGET.  The detent is 0 V",
        alt=["RK09K1130AAU / C202373 (20 mm flat shaft, no detent)",
             "RK09K1130AP5 / C470295 (15 mm screwdriver shaft)"]),
    # ---- the three gain trimmers: the book's 'R substitution box' and '1M pot'
    "TRIM": dict(
        value="1M", mpn="3362P-1-105", lcsc="C118945", jlc_type="extended",
        process="THT", stock=1113, price=0.1585,
        footprint="motorpid:Potentiometer_Bourns_3362P_Vertical",
        symbol="Device:R_Potentiometer_Trim_US",
        desc="3362P 1 M single-turn cermet trimmer (BOCHEN's, Bourns' pattern and pinout: the "
             "wiper reaches 3 turning clockwise), top adjust: P GAIN, D GAIN "
             "and I GAIN.  JLCPCB stocks no 1 M potentiometer with a shaft, so these "
             "take a screwdriver; the slot shows the setting",
        alt=["3362P-1-105LF (Bourns) / C111656 (1278 in stock, $0.41)"]),
    # ---- the five selectors: SPDT slide switches ----------------------------
    "SW": dict(
        value="SW_SPDT", mpn="MSK12C02", lcsc="C431540", jlc_type="extended",
        process="SMT", stock=194273, price=0.0544,
        footprint="motorpid:SW_SPDT_Shouhan_MSK12C02",
        symbol="Switch:SW_SPDT",
        desc="SPDT slide switch, SMD, 2 = common; the knob slides toward the pin it "
             "connects.  TARGET source, LOOP, D, I and the D capacitor",
        alt=["MSK12C02-HB / C431541 (78k, black knob)", "MSK12C02-SZ / C2681568 (26k)"]),
    # ---- connectors ----------------------------------------------------------
    "BNC": dict(
        value="BNC", mpn="BNC-KYWE-295-W4-N", lcsc="C41416668", jlc_type="extended",
        process="THT", stock=215, price=1.2929,
        footprint="motorpid:BNC_KYWE_RightAngle",
        symbol="Connector:Conn_Coaxial",
        desc="50 ohm BNC jack, right angle, 4 ground posts on 8x8 mm (the op-amp "
             "board's jack: JLCPCB rotation +90 read off a real preview)",
        alt=["HL2-BNC-KYWE / C48606310 (107 in stock)",
             "MLD-BNC-KYWE-L29.5 / C52766468 (12 in stock)"]),
    "TERM3": dict(
        value="Screw_Terminal_01x03", mpn="KF301-5.0-3P", lcsc="C474882",
        jlc_type="extended", process="THT", stock=28051, price=0.1396,
        footprint="motorpid:TerminalBlock_KF301_1x03_P5.00mm",
        symbol="Connector:Screw_Terminal_01x03",
        desc="3-way 5.0 mm screw terminal block, blue: MOTOR, POT and POWER all use the "
             "same block so one order code covers the three"),
    # ---- probe loops: a 2.54 mm loop a scope hook grabs -----------------------
    "TP": dict(
        value="", mpn="RH-5019", lcsc="C5199800", jlc_type="extended",
        process="SMT", stock=101462, price=0.0966,
        footprint="motorpid:TestPoint_Loop_RH-5019",
        symbol="Connector:TestPoint",
        desc="SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): "
             "a scope probe's hook or a mini-grabber clips onto it",
        alt=["RH-5015 / C5199798 (276k): the smaller 2.7 x 1.0 mm loop, same idea"]),
    # ---- protection ----------------------------------------------------------
    "DSCH": dict(
        value="SS34", mpn="SS34", lcsc="C8678", jlc_type="basic",
        process="SMT", stock=3642483, price=0.0351,
        footprint="Diode_SMD:D_SMA", symbol="Device:D_Schottky",
        desc="3 A 40 V Schottky, SMA.  Two in series with the supplies (a reversed bench "
             "supply does nothing) and two clamping the motor node to the rails (the "
             "motor's inductive kick when a brush breaks contact)",
        alt=["SS34 / C115205 (67k)", "SS34A / C211775 (100k)"]),
    # LUTE (not Littelfuse) 1812L035 in its 60 V grade: a short of DRIVE to a rail
    # leaves about 29.6 V across the open fuse, which is the 30 V grade's limit.
    # Hold 0.35 A, trip 0.70 A: a dead short (2 A) opens it in about a second (the
    # data sheet's typical curve), but a full-drive stall (0.56-0.64 A, less with a
    # warm motor or the fuse's own 1.7 ohm) sits between hold and trip and takes a
    # minute or more, or never, cold.  A smaller part does not fix that: the 0.30 A
    # one's own resistance pulls the stall back to its 0.60 A trip, and a 0.20 A one
    # would trip on the gain-100 ringing (0.19 A rms).  The pours, not the fuse,
    # carry the stall (sim/thermal.py --board); review round 1, 2026-10-27.
    "PTC": dict(
        value="0.35A", mpn="1812L035/60GR", lcsc="C18198330", jlc_type="extended",
        process="SMT", stock=9170, price=0.0667,
        footprint="Fuse:Fuse_1812_4532Metric", symbol="Device:Polyfuse",
        desc="LUTE resettable fuse between the push-pull and DRIVE: 0.35 A hold, 0.7 A trip, 60 V, "
             "0.2-1.7 ohm.  Opens a short of DRIVE (2 A) in about a second and resets when the "
             "drive stops; a full-drive stall (about 0.6 A) sits between hold and trip and may "
             "take a minute or more.  The loop's running current is 50-190 mA rms even when it "
             "rings (sim/pid_sim.py)",
        alt=["1812L035/30GR / C18198328 (40k, 30 V: at its limit in a short to a rail)"]),
    "LED": dict(
        value="GREEN", mpn="KT-0805G", lcsc="C2297", jlc_type="basic",
        process="SMT", stock=2420908, price=0.0164,
        footprint="LED_SMD:LED_0805_2012Metric", symbol="Device:LED",
        desc="green 0805 LED, one per rail, 1.2 mA through 10k: rails at a glance "
             "(JLCPCB rotation 0 on KiCad's LED_0805, read in GPiBridge's preview)"),
    "LED_R": dict(
        value="RED", mpn="NCD0805R1", lcsc="C84256", jlc_type="basic",
        process="SMT", stock=3082781, price=0.0135,
        footprint="LED_SMD:LED_0805_2012Metric", symbol="Device:LED",
        desc="red 0805 LED, two anti-parallel across the fuse with 1k: lights only "
             "when the fuse has tripped (more than 2 V across it), either polarity"),
    # ---- nothing to buy -----------------------------------------------------
    "MH": dict(value="", process="THT", in_bom=False,
               footprint="MountingHole:MountingHole_3.2mm_M3",
               symbol="Mechanical:MountingHole",
               desc="M3 mounting hole, one per corner"),
}

# Resistor and capacitor order codes, keyed by the value printed on the sheet.
PASSIVES = {
    "100k":  dict(lcsc="C149504", mpn="0805W8F1003T5E", jlc_type="basic",
                  price=0.0059, stock=3369385, note="the error amplifier's four"),
    "10k":   dict(lcsc="C17414", mpn="0805W8F1002T5E", jlc_type="basic",
                  price=0.0034, stock=54265030),
    "1k":    dict(lcsc="C17513", mpn="0805W8F1001T5E", jlc_type="basic",
                  price=0.0035, stock=43108325),
    "1k_1206": dict(lcsc="C4410", mpn="1206W4F1001T5E", jlc_type="basic",
                    price=0.0085, stock=1945919, note="1206, 0.25 W: the series resistors to the BNC outputs"),
    "6.8k":  dict(lcsc="C17772", mpn="0805W8F6801T5E", jlc_type="basic",
                  price=0.0029, stock=567224, note="the target knob's end resistors: +/-6.4 V"),
    "4.7k":  dict(lcsc="C17673", mpn="0805W8F4701T5E", jlc_type="basic",
                  price=0.0051, stock=4750437, note="the motor pot's end resistors: +/-7.7 V"),
    "270R":  dict(lcsc="C17590", mpn="0805W8F2700T5E", jlc_type="preferred",
                  price=0.0070, stock=352205, note="the push-pull's base resistor, the book's 270"),
    "10R":   dict(lcsc="C17415", mpn="0805W8F100JT5E", jlc_type="basic",
                  price=0.0040, stock=5960192, note="the motor snubber, the book's 10 ohm"),
    "1R":    dict(lcsc="C3000711", mpn="FRC2512J1R0TS", jlc_type="extended",
                  price=0.0313, stock=73941, note="2512, 1 W: the push-pull's emitter resistors; 1 V per ampere of motor current across either"),
    "100nF": dict(lcsc="C49678", mpn="CC0805KRX7R9BB104", jlc_type="basic",
                  price=0.0205, stock=22485395, note="X7R 50V 0805"),
    "22nF":  dict(lcsc="C1729", mpn="CL21B223KBANNNC", jlc_type="basic",
                  price=0.0084, stock=478982, note="X7R 50V 0805: the D capacitor for the slide pot"),
    "470pF": dict(lcsc="C1743", mpn="0805B471K500NT", jlc_type="basic",
                  price=0.0075, stock=438251, note="X7R 50V 0805: rolls the differentiator off"),
    "330nF": dict(lcsc="C1740", mpn="0805B334K500NT", jlc_type="preferred",
                  price=0.0207, stock=103724, note="X7R 50V 0805: the driver's split feedback, the book's 0.33 uF"),
    "10uF":  dict(lcsc="C15850", mpn="CL21A106KAYNNNE", jlc_type="basic",
                  price=0.0426, stock=9137411, note="X5R 25V 0805: the pot's end decoupling"),
}

# --------------------------------------------------------- JLCPCB rotations
# JLCPCB places from its own drawing of each part, and for some parts that
# drawing is turned from KiCad's footprint, or has its origin elsewhere.
# (degrees counter-clockwise to ADD to the KiCad rotation, (dx, dy) in mm to
# ADD to the CPL point in the footprint's own unrotated frame with y UP, as the
# CPL's is (KiCad's footprint y runs down: a shift toward a footprint's -y is
# +dy here), how known, note).
# "read": seen in a JLCPCB "Confirm Parts Placement" preview on a real order.
# "predicted": from fitting their land pattern on ours by pin number
# (scripts/check_rotations.py, which also lays their drawing where the upload
# CPL puts it); listed in PLACEMENT_CHECKS.txt for the order day.
JLC_ROTATION = {
    "C41416668": (90, (0, 0), "read", "BNC-KYWE-295-W4-N: Lorenz board rev A/B preview, built and working"),
    "C9405": (180, (0, 0), "predicted", "SOT-23-5: their pad 1 at (+1.3,+0.95), KiCad's at (-1.14,-0.95); "
                                        "+180 was read on 59 SOT-23-5 placements on the GPSDO board"),
    "C233689": (180, (-2.45, 0), "predicted", "D2PAK: their pins at +x, KiCad's TO-263-2 at -x; turned, their "
                                               "pins land 2.45 mm from KiCad's origin toward the pins (the tabs differ)"),
    "C154570": (180, (-2.45, 0), "predicted", "D2PAK, the same drawing as the NPN"),
    "C431540": (0, (0, 0.25), "predicted", "MSK12C02: pins along x in both drawings, pin 1 at -x; their origin "
                                           "0.25 mm from ours toward the terminals (check_rotations.py; their "
                                           "terminals are 2.25 mm from the posts, Shouhan's land pattern 1.95)"),
    "C351173": (270, (3.5, -2.5), "predicted", "RK09K: their pins along +x at the body's bottom edge, pin 1 at -x, the "
                                               "posts above; turned 270, the pins land on KiCad's (overlay of easyeda "
                                               "C351173: 0.00 mm); their origin is the body's middle, 3.5 mm from the "
                                               "pins toward the posts.  Their posts are 10 mm apart, ALPS's slots 8.8: "
                                               "the preview shows each post 0.6 mm off its slot (review round 1)"),
    "C118945": (0, (0, 0), "predicted", "3362P: their pads 1/3 at y=+1.27 and 2 at y=-1.27, as drawn here"),
    "C2297": (0, (0, 0), "read", "KT-0805G on KiCad's LED_0805: GPiBridge rev A preview, cathode at pad 1"),
    "C84256": (0, (0, 0), "read", "NCD0805R1 on KiCad's LED_0805: GPiBridge rev A preview, cathode at pad 1"),
    "C8678": (0, (0, 0), "predicted", "SS34 SMA: cathode (pad 1) at -x in both drawings"),
    "C18198330": (0, (0, 0), "predicted", "1812 fuse: two pads along x, not polarised"),
    "C242107": (0, (0, 0), "predicted", "ECWF2W105JA: two leads on 15 mm along x, origin the body's middle "
                                        "in both drawings (easyeda CAP-TH_L18.1-W9.3-P15.00-D0.8); not polarised"),
    "C46550402": (0, (0, 0), "predicted", "SMD electrolytic: pads along x, pad 1 (+) at -x in both drawings"),
    "C474882": (180, (0, 0), "predicted", "KF301-3P: pins along x at -5/0/+5 in both drawings; EasyEDA draws the "
                                          "wire-entry arrows on +y, the body 3.7 mm that way and 4.0 the other; "
                                          "ours face -y (the board edge): the pin row is symmetric, so +180 turns "
                                          "only the body (the op-amp board's review round 1)"),
    "C5199800": (0, (0, 0), "predicted", "RH-5019 test loop: one 4.0 x 2.2 pad, as drawn here; the loop lies along x"),
    "C3000711": (0, (0, 0), "predicted", "2512: pads along x, not polarised"),
}
