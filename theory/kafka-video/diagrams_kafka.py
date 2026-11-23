#!/usr/bin/env python3
"""Figures of the Kafka course. Run: python3 theory/kafka-video/diagrams_kafka.py [name ...] -> svg/k-*.svg
Blue = normal path, red = failure, green = the repaired path, amber = warning, grey = background."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "video"))
import dg
from dg import *
dg.OUT = pathlib.Path(__file__).resolve().parent / "svg"


def cells(x, y, labels, w=74, h=58, fill=None, col=BLUE, size=21):
    out = []
    for i, l in enumerate(labels):
        out.append(rect(x + i * w, y, w, h, fill or FILL[col], col, 2, 3))
        out.append(text(x + i * w + w / 2, y + h / 2 + 8, l, size, INK, "middle", 700))
    return "".join(out)


def place():
    b = [panel(560, 70, 480, 520, "blue", "Kafka: the shared, durable log")]
    for i, (n, c) in enumerate((("orders.order-events.v1", BLUE), ("payments.payment-events.v1", BLUE), ("catalog.price-changes.v1", BLUE))):
        b.append(box(590, 150 + i * 135, 420, 90, n, c, size=23))
    for i, n in enumerate(("Checkout", "Payments", "Catalog")):
        y = 150 + i * 135
        b.append(box(90, y, 250, 90, n, GREY, size=25)); b.append(arrow(342, y + 45, 586, y + 45, "append", BLUE, 3))
    for i, n in enumerate(("Fulfilment", "Search index", "Analytics", "Notifications")):
        y = 95 + i * 122
        b.append(box(1260, y, 280, 90, n, GREEN, size=25)); b.append(arrow(1042, 330, 1256, y + 45, "", GREEN, 3))
    b.append(text(1150, 625, "each reads at its own pace", 23, GREEN, "middle", 700))
    b.append(text(215, 625, "writers do not know the readers", 23, BLUE, "middle", 700))
    return svg(1600, 650, b)


def anatomy():
    b = [title(40, 46, "Topic: orders.order-events.v1", 28)]
    x0 = 230
    for k, n in enumerate((10, 8, 11)):
        y = 110 + k * 118
        b.append(text(x0 - 24, y + 38, f"Partition {k}", 25, INK, "end", 700))
        b.append(cells(x0, y, [str(i) for i in range(n)], 80, 62))
        b.append(arrow(1290, y + 31, x0 + n * 80 + 8, y + 31, "", BLUE, 3.5))
    b.append(box(1300, 190, 250, 130, ["Producer", "appends at", "the end"], BLUE, size=23))
    x = x0 + 7.5 * 80
    b.append(line(x, 472, x, 410, GREEN, 3.5, "", True))
    x2 = x0 + 2.5 * 80
    b.append(line(x2, 472, x2, 410, AMBER, 3.5, "", True))
    b.append(text(x, 505, "fulfilment group at offset 7", 24, GREEN, "middle", 800))
    b.append(text(x2, 505, "analytics group at offset 2", 24, AMBER, "middle", 800))
    b.append(text(800, 580, "Order holds inside one partition. Reading deletes nothing. Each group keeps its own position.", 25, MUTED, "middle", 600))
    return svg(1600, 620, b)


def sync_event():
    b = [panel(20, 20, 770, 610, "red", ""), panel(810, 20, 770, 610, "green", "")]
    b += [title(405, 70, "Request and response", 29, INK, "middle"), title(1195, 70, "Event on a log", 29, INK, "middle")]
    b.append(box(60, 150, 200, 100, "Checkout", BLUE, size=24)); b.append(box(310, 150, 200, 100, "Payments", BLUE, size=24)); b.append(box(560, 150, 190, 100, "Email", RED, size=24))
    b.append(arrow(262, 200, 306, 200, "", BLUE, 3.5)); b.append(arrow(512, 200, 556, 200, "", RED, 3.5)); b.append(cross(655, 130, 18))
    b.append(mtext(405, 340, ["Email is down, so the call fails,", "and the failure travels back", "to the customer at checkout."], 25, RED, "middle", 700))
    b.append(mtext(405, 520, ["The caller waits for everyone.", "Availability multiplies down the chain."], 24, MUTED, "middle", 600))
    b.append(box(850, 150, 200, 100, "Checkout", BLUE, size=24)); b.append(box(1100, 150, 200, 100, "Log", GREEN, size=24)); b.append(box(1350, 150, 190, 100, "Email", RED, size=24))
    b.append(arrow(1052, 200, 1096, 200, "", GREEN, 3.5)); b.append(arrow(1302, 200, 1346, 200, "", GREY, 3.5, "9 7")); b.append(cross(1445, 130, 18))
    b.append(mtext(1195, 340, ["Email is down. The order is taken.", "Email catches up from its offset", "when it comes back."], 25, GREEN, "middle", 700))
    b.append(mtext(1195, 520, ["Decoupled in time. Still coupled by", "the schema of the event."], 24, MUTED, "middle", 600))
    return svg(1600, 650, b)


def replicate():
    x0, cw = 590, 76
    b = [box(30, 245, 210, 110, ["Producer", "acks = all"], BLUE, size=23)]
    rows = [("Broker 1 · leader", 9, BLUE), ("Broker 2 · follower", 9, BLUE), ("Broker 3 · follower", 7, BLUE)]
    for k, (lab, n, c) in enumerate(rows):
        y = 110 + k * 135
        b.append(text(x0 - 16, y + 38, lab, 23, INK, "end", 700))
        b.append(cells(x0, y, [str(100 + i) for i in range(n)], cw, 62, size=20))
    hw = x0 + 7 * cw
    b.append(line(hw, 82, hw, 455, RED, 4, "10 7"))
    b.append(text(hw, 66, "high watermark", 25, RED, "middle", 800))
    b.append(arrow(242, 275, 330, 160, "", BLUE, 3.5))
    b.append(text(x0 + 9 * cw + 28, 148, "newest writes", 23, BLUE, "start", 700))
    b.append(text(x0 + 9 * cw + 28, 415, "still fetching", 23, AMBER, "start", 700))
    b.append(box(120, 500, 560, 100, ["Consumers read only below", "the high watermark"], GREEN, size=24, first_bold=False))
    b.append(box(760, 500, 760, 100, ["The producer is acknowledged once every", "in-sync replica holds the record"], BLUE, size=24, first_bold=False))
    return svg(1600, 630, b)


def groups():
    b = [title(40, 46, "One topic, two independent consumer groups", 28)]
    ys = [100, 215, 330, 445]
    for i, y in enumerate(ys):
        b.append(box(660, y, 280, 84, f"Partition {i}", BLUE, size=24))
    b.append(panel(30, 90, 460, 450, "green", "Group: fulfilment"))
    b.append(box(90, 150, 330, 120, ["Consumer A", "partitions 0 and 1"], GREEN, size=23)); b.append(box(90, 370, 330, 120, ["Consumer B", "partitions 2 and 3"], GREEN, size=23))
    for y, sy in ((142, 210), (257, 210), (372, 430), (487, 430)):
        b.append(arrow(656, y, 424, sy, "", GREEN, 3))
    b.append(panel(1110, 90, 460, 450, "amber", "Group: analytics"))
    b.append(box(1170, 245, 340, 130, ["Consumer C", "all four partitions"], AMBER, size=23))
    for y in (142, 257, 372, 487):
        b.append(arrow(944, y, 1166, 310, "", AMBER, 3))
    b.append(text(800, 590, "Inside a group, one partition has one reader. So partitions cap a group's parallelism.", 25, MUTED, "middle", 600))
    return svg(1600, 620, b)


def decide():
    qs = [("Does the caller need the answer now?", "Request and response", "gRPC or HTTP", BLUE),
          ("Do several teams need the same facts, or a replay?", "Kafka", "a durable, replayable log", GREEN),
          ("Is it work to do once per item, with retries or delays?", "A task queue", "or Kafka share groups", AMBER)]
    b = []
    for i, (q, a, s, c) in enumerate(qs):
        y = 40 + i * 180
        b.append(box(60, y, 800, 120, q, GREY, size=26, weight=700))
        b.append(arrow(862, y + 60, 1088, y + 60, "yes", c, 3.5, size=25, weight=800))
        b.append(box(1092, y, 450, 120, [a, s], c, size=26))
        if i < 2:
            b.append(arrow(460, y + 122, 460, y + 176, "no", INK, 3.5, size=25, weight=800))
    b.append(arrow(460, 522, 460, 580, "no", INK, 3.5, size=25, weight=800))
    b.append(box(60, 584, 800, 90, "A database table is probably enough", GREY, size=26, weight=700))
    return svg(1600, 700, b)


def split_race():
    b = [panel(20, 20, 770, 630, "red", ""), panel(810, 20, 770, 630, "green", "")]
    b += [title(405, 70, "One topic per event type", 29, RED, "middle"), title(1195, 70, "One topic per ordering domain", 29, GREEN, "middle")]
    for i, (n, l) in enumerate((("order-created", "lag 40 s"), ("order-paid", "lag 9 s"), ("order-shipped", "lag 1 s"))):
        y = 125 + i * 108
        b.append(box(55, y, 290, 80, n, BLUE, size=23)); b.append(arrow(347, y + 40, 515, 285, "", GREY, 3)); b.append(text(200, y + 102, l, 21, MUTED, "middle", 600))
    b.append(box(520, 225, 235, 120, ["Fulfilment", "consumer"], AMBER, size=23))
    b.append(text(405, 505, "Arrives:  shipped, paid, created", 28, RED, "middle", 800))
    b.append(mtext(405, 560, ["Three topics, three lags.", "Nothing orders one against another."], 24, MUTED, "middle", 600))
    b.append(text(850, 165, "orders.order-events.v1 · key = order_id", 24, INK, "start", 700))
    b.append(cells(850, 200, ["created", "paid", "shipped"], 225, 90, size=26))
    b.append(arrow(1195, 295, 1195, 385, "", GREEN, 3.5)); b.append(box(1075, 390, 240, 90, "Fulfilment", GREEN, size=24))
    b.append(text(1195, 550, "Arrives:  created, paid, shipped", 28, GREEN, "middle", 800))
    b.append(text(1195, 600, "A type field tells them apart.", 24, MUTED, "middle", 600))
    return svg(1600, 670, b)


def key_hash():
    b = []
    rows = [("order-9814", 17, BLUE, 120), ("order-9814", 17, BLUE, 270), ("order-2207", 3, GREEN, 420)]
    for key, p, c, y in rows:
        b.append(box(50, y, 280, 96, ["key", key], c, size=23, first_bold=False))
        b.append(arrow(332, y + 48, 470, y + 48, "", c, 3.5))
        b.append(box(474, y, 300, 96, "hash(key)", GREY, size=25))
        b.append(arrow(776, y + 48, 910, y + 48, "", c, 3.5))
        b.append(box(914, y, 250, 96, "mod 48", GREY, size=25))
        b.append(arrow(1166, y + 48, 1300, y + 48, "", c, 3.5))
        b.append(box(1304, y, 250, 96, f"partition {p}", c, size=25))
    b.append(text(800, 70, "The producer picks the partition. The same key always lands in the same one, while the count stays at 48.", 26, INK, "middle", 700))
    b.append(text(800, 585, "Same key, same partition, same order. Different keys have no order between them.", 25, MUTED, "middle", 600))
    return svg(1600, 620, b)


def bars(x0, y0, h, vals, w, gap, col, top=1000):
    out = []
    for i, v in enumerate(vals):
        bh = h * v / top; c = RED if v > 500 else col
        out.append(rect(x0 + i * (w + gap), y0 - bh, w, bh, FILL[c], c, 2.5, 3))
    return "".join(out)


def hot_key():
    b = [panel(20, 20, 770, 620, "red", ""), panel(810, 20, 770, 620, "green", "")]
    b += [title(405, 70, "key = seller_id", 29, RED, "middle"), title(1195, 70, "key = order_id", 29, GREEN, "middle")]
    y0, h = 540, 400
    b.append(bars(80, y0, h, [960, 310, 180, 240, 150, 290, 200, 330, 170, 260, 220, 190], 44, 12, BLUE))
    b.append(bars(870, y0, h, [250, 255, 245, 250, 248, 252, 250, 246, 254, 250, 249, 251], 44, 12, GREEN))
    for x in (60, 850):
        b.append(line(x, y0, x + 700, y0, INK, 2.5))
        b.append(line(x, y0 - h / 2, x + 700, y0 - h / 2, RED, 3, "10 7"))
        b.append(text(x + 700, y0 - h / 2 - 12, "one consumer: 500 per second", 22, RED, "end", 700, halo=True))
    b.append(text(150, y0 - h * 0.96 - 12, "960 per second", 24, RED, "start", 800, halo=True))
    b.append(text(1195, y0 - h / 4 - 95 + 40, "about 250 per second each", 24, GREEN, "middle", 800, halo=True))
    b.append(text(405, 595, "One big seller: a partition that never catches up", 24, RED, "middle", 700))
    b.append(text(1195, 595, "Many small keys: an even spread", 24, GREEN, "middle", 700))
    return svg(1600, 660, b)


def resize():
    b = [title(40, 50, "Key hash = 17. Add partitions, and the key moves.", 29)]
    b.append(panel(40, 90, 730, 400, "grey", "Before: 4 partitions")); b.append(panel(830, 90, 730, 400, "amber", "After: 6 partitions"))
    for i in range(4):
        c = RED if i == 1 else BLUE
        b.append(box(70, 145 + i * 82, 150, 64, f"P{i}", c, size=23))
    b.append(cells(240, 145 + 82, ["e1", "e2", "e3", "e4"], 90, 64, col=RED))
    b.append(text(420, 325, "unread backlog", 23, RED, "middle", 700))
    b.append(text(400, 460, "17 mod 4 = 1", 26, INK, "middle", 800))
    for i in range(6):
        c = GREEN if i == 5 else (RED if i == 1 else BLUE)
        b.append(box(860, 135 + i * 54, 130, 46, f"P{i}", c, size=21))
    b.append(cells(1010, 135 + 54, ["e1", "e2", "e3", "e4"], 70, 46, col=RED, size=20))
    b.append(cells(1010, 135 + 270, ["e5", "e6"], 70, 46, col=GREEN, size=20))
    b.append(text(1180, 450 - 16, "17 mod 6 = 5", 26, INK, "start", 800))
    b.append(text(800, 545, "e5 and e6 can be read before e1 to e4. The order for this key is broken.", 28, RED, "middle", 800))
    b.append(text(800, 595, "Over-provision up front, or migrate to a new topic.", 25, MUTED, "middle", 600))
    return svg(1600, 620, b)


def rf_states():
    st = [("3 of 3 in sync", "Writes succeed", "Normal", GREEN, 3), ("2 of 3 in sync", "Writes still succeed", "No spare left", AMBER, 2), ("1 of 3 in sync", "Writes are rejected", "Reads continue, nothing acknowledged is lost", RED, 1)]
    b = [text(800, 50, "Replication factor 3 with min.insync.replicas = 2 and acks = all", 28, INK, "middle", 800)]
    for i, (h, a, s, c, n) in enumerate(st):
        x = 40 + i * 515
        b.append(rect(x, 90, 490, 480, FILL[c], c, 3, 14))
        b.append(text(x + 245, 145, h, 29, INK, "middle", 800))
        for k in range(3):
            up = k < n; bx = x + 45 + k * 140
            b.append(box(bx, 190, 120, 100, f"B{k + 1}", GREEN if up else GREY, size=25))
            if not up: b.append(cross(bx + 60, 240, 26))
        b.append(text(x + 245, 375, a, 30, c if c != AMBER else INK, "middle", 800))
        b.append(mtext(x + 245, 435, ([s] if len(s) < 30 else ["Reads continue. Nothing", "acknowledged is lost."]), 25, INK, "middle", 500))
    b.append(text(800, 615, "The default for min.insync.replicas is 1. Set it to 2 yourself.", 27, RED, "middle", 800))
    return svg(1600, 640, b)


def sizing():
    rows = [("Disk", 5, BLUE, "25.9 TB ÷ 6 TB per broker"), ("Writes", 3, GREY, "90 MB/s ÷ 30 MB/s per broker"), ("Network out", 3, GREY, "150 MB/s ÷ 60 MB/s per broker")]
    b = [text(40, 50, "Brokers needed by each limit (the budgets per broker are illustrative: measure yours)", 26, INK, "start", 700)]
    x0, u = 300, 150
    for i, (n, v, c, why) in enumerate(rows):
        y = 90 + i * 100
        b.append(text(x0 - 20, y + 50, n, 27, INK, "end", 700))
        b.append(rect(x0, y, v * u, 76, FILL[c], c, 2.5, 6)); b.append(text(x0 + v * u - 22, y + 50, str(v), 32, INK, "end", 800))
        b.append(text(x0 + v * u + 24, y + 48, why, 24, MUTED, "start", 600))
    y = 400
    b.append(line(60, y - 14, 1540, y - 14, GREY, 2))
    b.append(text(x0 - 20, y + 54, "Design", 27, INK, "end", 700))
    b.append(rect(x0, y, 5 * u, 80, FILL[BLUE], BLUE, 2.5, 6)); b.append(text(x0 + 5 * u / 2, y + 52, "largest limit: 5", 28, INK, "middle", 800))
    b.append(rect(x0 + 5 * u, y, u, 80, FILL[GREEN], GREEN, 2.5, 6)); b.append(text(x0 + 5.5 * u, y + 52, "+1", 30, GREEN, "middle", 800))
    b.append(text(x0 + 6 * u + 28, y + 52, "6 brokers, 2 per zone", 30, GREEN, "start", 800))
    b.append(text(800, 560, "The spare is what lets you lose a broker, or restart one, and still have room to work.", 26, MUTED, "middle", 600))
    return svg(1600, 600, b)


def zones():
    b = []
    pl = [("Leader", BLUE), ("Follower", GREEN), ("Follower", GREEN)]
    for z in range(3):
        x = 30 + z * 525
        b.append(panel(x, 30, 490, 520, "grey", f"Zone {'ABC'[z]}", size=25))
        b.append(box(x + 30, 85, 430, 80, "Controller", AMBER, size=25))
        for k in range(2):
            b.append(box(x + 25 + k * 225, 195, 215, 90, f"Broker {z * 2 + k + 1}", BLUE, size=24))
        n, c = pl[z]
        b.append(box(x + 25, 335, 440, 80, f"Partition 0 · {n}", c, size=24))
        b.append(mtext(x + 245, 460, ["one replica per zone"] if z == 1 else [""], 23, MUTED, "middle", 600))
    b.append(text(800, 600, "Lose a zone: two replicas and two of three controllers survive, so writes continue.", 27, GREEN, "middle", 800))
    return svg(1600, 630, b)


def tiered():
    b = [panel(20, 20, 770, 570, "blue", ""), panel(810, 20, 770, 570, "green", "")]
    b += [title(405, 70, "Tiered storage", 29, INK, "middle"), title(1195, 70, "Rebuilding a lost broker", 29, INK, "middle")]
    b.append(box(70, 130, 280, 150, ["Broker disk", "last 1 day", "fast, replicated"], BLUE, size=24))
    b.append(box(440, 130, 300, 150, ["Object storage", "the other 6 days", "cheap per terabyte"], GREEN, size=24))
    b.append(arrow(352, 205, 436, 205, "", GREEN, 3.5))
    b.append(mtext(405, 370, ["Same topic, same offsets.", "Old segments move out,", "and consumers read them transparently."], 25, INK, "middle", 500))
    b.append(mtext(405, 530, ["Not for compacted topics."], 25, RED, "middle", 700))
    u = 62
    b.append(text(860, 170, "7 days on local disk: 3 TB to copy", 25, INK, "start", 700))
    b.append(rect(860, 190, 8.3 * u, 70, FILL[RED], RED, 2.5, 6)); b.append(text(860 + 8.3 * u + 20, 235, "about 8 h", 34, RED, "start", 800))
    b.append(text(860, 340, "1 day on local disk: 0.43 TB to copy", 25, INK, "start", 700))
    b.append(rect(860, 360, 1.19 * u, 70, FILL[GREEN], GREEN, 2.5, 6)); b.append(text(860 + 1.19 * u + 20, 405, "about 70 min", 34, GREEN, "start", 800))
    b.append(text(1195, 530, "Copy throttled to 100 MB/s", 24, MUTED, "middle", 600))
    return svg(1600, 610, b)


def dual_write():
    b = [panel(20, 20, 770, 620, "red", ""), panel(810, 20, 770, 620, "green", "")]
    b += [title(405, 70, "Dual write", 29, RED, "middle"), title(1195, 70, "Outbox", 29, GREEN, "middle")]
    b.append(box(280, 120, 250, 90, "Order service", BLUE, size=24))
    b.append(box(60, 340, 260, 100, "Database", BLUE, size=24)); b.append(box(490, 340, 260, 100, "Kafka", GREY, size=24))
    b.append(arrow(340, 212, 200, 336, "", GREEN, 3.5)); b.append(text(150, 275, "1. commit", 24, GREEN, "middle", 800))
    b.append(arrow(470, 212, 620, 336, "", RED, 3.5, "9 7")); b.append(text(680, 275, "2. publish", 24, RED, "middle", 800)); b.append(cross(545, 274, 22))
    b.append(mtext(405, 520, ["A crash between the two steps:", "the order exists, and nobody hears of it."], 26, RED, "middle", 700))
    b.append(box(1070, 105, 250, 80, "Order service", BLUE, size=24))
    b.append(rect(850, 225, 690, 170, "#fff", GREEN, 3, 10, "10 7")); b.append(text(1195, 258, "one database transaction", 23, GREEN, "middle", 800))
    b.append(box(885, 280, 290, 90, "orders", GREEN, size=25)); b.append(box(1215, 280, 290, 90, "outbox", GREEN, size=25))
    b.append(arrow(1195, 187, 1195, 222, "", GREEN, 3.5))
    b.append(box(1215, 455, 290, 80, "Relay or CDC", AMBER, size=24)); b.append(arrow(1360, 397, 1360, 451, "", AMBER, 3.5))
    b.append(box(885, 455, 240, 80, "Kafka", BLUE, size=24)); b.append(arrow(1213, 495, 1129, 495, "", BLUE, 3.5))
    b.append(text(1195, 600, "At least once, and never lost.", 26, GREEN, "middle", 800))
    return svg(1600, 660, b)


def eos():
    b = [rect(40, 60, 1010, 400, FILL[GREEN], GREEN, 3, 14, "12 8"), text(545, 105, "Kafka transaction: exactly once, inside this box", 28, GREEN, "middle", 800)]
    b.append(box(80, 180, 240, 110, "Input topic", BLUE, size=25)); b.append(box(420, 180, 250, 110, "Processor", GREEN, size=25)); b.append(box(770, 150, 240, 90, "Output topic", BLUE, size=24)); b.append(box(770, 300, 240, 110, "Consumer offset", BLUE, size=24))
    b.append(arrow(322, 235, 416, 235, "", BLUE, 3.5)); b.append(arrow(672, 215, 766, 195, "", GREEN, 3.5)); b.append(arrow(672, 260, 766, 350, "", GREEN, 3.5))
    b.append(text(545, 435, "output and offset commit together, or not at all", 24, GREEN, "middle", 700))
    b.append(box(1220, 90, 330, 90, "Your database", AMBER, size=25)); b.append(box(1220, 215, 330, 90, "Card network", AMBER, size=25)); b.append(box(1220, 340, 330, 90, "Email provider", AMBER, size=25))
    for y in (135, 260, 385): b.append(arrow(1052, 260, 1216, y, "", RED, 3.5, "9 7"))
    b.append(text(800, 530, "Outside the box, delivery is at least once. The receiver removes the duplicate.", 28, RED, "middle", 800))
    b.append(text(800, 580, "Idempotency key, unique constraint, or an upsert keyed by a stable event ID.", 25, MUTED, "middle", 600))
    return svg(1600, 610, b)


def retry():
    b = [box(50, 200, 280, 110, "orders topic", BLUE, size=26), box(470, 200, 280, 110, "Consumer", GREEN, size=26), box(1250, 200, 300, 110, "Done", GREEN, size=26)]
    b.append(arrow(332, 255, 466, 255, "", BLUE, 3.5)); b.append(arrow(752, 255, 1246, 255, "success", GREEN, 3.5, size=25, weight=700))
    b.append(box(470, 420, 280, 110, ["retry topic", "with a delay"], AMBER, size=25))
    b.append(arrow(570, 312, 570, 416, "", AMBER, 3.5)); b.append(text(555, 372, "transient error", 23, AMBER, "end", 700, halo=True))
    b.append(arrow(660, 416, 660, 314, "", AMBER, 3.5)); b.append(text(676, 372, "try again", 23, AMBER, "start", 700, halo=True))
    b.append(box(1000, 420, 300, 110, ["dead-letter topic", "alert, inspect, replay"], RED, size=24))
    b.append(arrow(752, 475, 996, 475, "attempts used up", RED, 3.5, size=23, weight=700))
    b.append(text(800, 80, "Without a way out, one bad record blocks its partition forever", 29, RED, "middle", 800))
    b.append(text(800, 610, "A retry topic gives up order for that key. If order matters, park every later event of the key too.", 25, MUTED, "middle", 600))
    return svg(1600, 640, b)


def compaction():
    x0, w = 120, 150
    before = [("A", "1"), ("B", "1"), ("A", "2"), ("C", "1"), ("B", "2"), ("A", "3"), ("C", "∅"), ("B", "3")]
    keep = {3, 4, 5, 6, 7}
    b = [text(x0, 60, "Before compaction", 28, INK, "start", 800)]
    def row(y, on):
        out = []
        for i, (k, v) in enumerate(before):
            x = x0 + i * w
            if i not in on: continue
            c = RED if v == "∅" else BLUE
            out.append(rect(x, y, w - 12, 86, FILL[c], c, 2.5, 6)); out.append(text(x + (w - 12) / 2, y + 54, f"{k} = {v}", 28, INK, "middle", 800))
            out.append(text(x + (w - 12) / 2, y + 116, str(i), 22, MUTED, "middle", 600))
        return "".join(out)
    b.append(row(85, set(range(8))))
    b.append(text(x0, 290, "After compaction", 28, INK, "start", 800)); b.append(row(315, keep))
    for i in range(3):
        b.append(rect(x0 + i * w, 315, w - 12, 86, "#fff", GREY, 2, 6, "8 6")); b.append(text(x0 + i * w + (w - 12) / 2, 366, "removed", 21, MUTED, "middle", 600))
    sx = x0 + 6 * w - 6
    b.append(line(sx, 70, sx, 450, AMBER, 3.5, "10 7")); b.append(text(sx + 12, 470, "active segment: not compacted yet", 23, AMBER, "start", 800)); b.append(text(sx - 12, 470, "older segments", 23, MUTED, "end", 700))
    b.append(text(800, 545, "Offsets never change, and order is kept. So B = 2 survives until the segment with B = 3 is cleaned.", 25, INK, "middle", 600))
    b.append(text(800, 590, "∅ is a tombstone: a key with a null value, which deletes C for good after a retention period.", 25, RED, "middle", 600))
    return svg(1600, 620, b)


def cqrs():
    b = [box(30, 250, 220, 110, "Write API", BLUE, size=25), box(310, 250, 220, 110, ["PostgreSQL", "source of truth"], BLUE, size=23), box(590, 250, 160, 110, "CDC", AMBER, size=25), box(810, 240, 220, 130, ["Kafka", "change log"], GREEN, size=26)]
    b.append(arrow(252, 305, 306, 305, "", BLUE, 3.5)); b.append(arrow(532, 305, 586, 305, "", AMBER, 3.5)); b.append(arrow(752, 305, 806, 305, "", GREEN, 3.5))
    for i, (n, q) in enumerate((("Elasticsearch", "search"), ("Redis", "lookup by key"), ("Iceberg tables", "analytics"))):
        y = 60 + i * 190
        b.append(box(1120, y, 260, 110, [n, q], GREEN, size=23)); b.append(arrow(1032, 305, 1116, y + 55, "", GREEN, 3))
        b.append(box(1440, y + 12, 130, 86, "Reads", GREY, size=23)); b.append(arrow(1438, y + 55, 1384, y + 55, "", GREY, 3))
    b.append(text(560, 480, "Each read model can be deleted and rebuilt from the log.", 27, GREEN, "middle", 800))
    b.append(text(560, 530, "The price: read models lag behind the write.", 25, MUTED, "middle", 600))
    return svg(1600, 620, b)


def no_cas():
    b = [panel(20, 20, 770, 610, "red", ""), panel(810, 20, 770, 610, "green", "")]
    b += [title(405, 70, "Append to a log", 29, RED, "middle"), title(1195, 70, "Conditional write in a database", 29, GREEN, "middle")]
    b.append(box(60, 130, 170, 80, "Client 1", BLUE, size=23)); b.append(box(60, 280, 170, 80, "Client 2", BLUE, size=23))
    b.append(arrow(232, 170, 396, 220, "seat 12A", BLUE, 3)); b.append(arrow(232, 320, 396, 270, "seat 12A", BLUE, 3, above=-30))
    b.append(cells(400, 210, ["12A", "12A"], 170, 80, col=RED, size=26))
    b.append(tick(485, 180)); b.append(tick(655, 180))
    b.append(mtext(405, 450, ["Both appends succeed.", "A log has no check on current state."], 26, RED, "middle", 700))
    b.append(box(850, 130, 170, 80, "Client 1", BLUE, size=23)); b.append(box(850, 280, 170, 80, "Client 2", BLUE, size=23))
    b.append(box(1250, 190, 290, 110, ["seats", "UNIQUE (seat)"], GREEN, size=24))
    b.append(arrow(1022, 170, 1246, 225, "", GREEN, 3)); b.append(tick(1135, 165))
    b.append(arrow(1022, 320, 1246, 270, "", RED, 3)); b.append(cross(1135, 325))
    b.append(mtext(1195, 450, ["The second write is rejected.", "Decide here, then publish the fact."], 26, GREEN, "middle", 700))
    return svg(1600, 650, b)


def share():
    b = [panel(20, 20, 770, 600, "blue", ""), panel(810, 20, 770, 600, "green", "")]
    b += [title(405, 70, "Consumer group", 29, INK, "middle"), title(1195, 70, "Share group", 29, INK, "middle")]
    b.append(cells(90, 130, ["1", "2", "3", "4", "5", "6", "7", "8"], 78, 66))
    b.append(box(255, 300, 300, 100, "Consumer A", BLUE, size=25)); b.append(arrow(405, 200, 405, 296, "", BLUE, 3.5))
    b.append(box(255, 445, 300, 70, "Consumer B: idle", GREY, size=23))
    b.append(mtext(405, 565, ["One reader per partition. Order kept."], 25, BLUE, "middle", 700))
    b.append(cells(880, 130, ["1", "2", "3", "4", "5", "6", "7", "8"], 78, 66, col=GREEN))
    for i in range(3):
        x = 850 + i * 240
        b.append(box(x, 320, 210, 100, f"Consumer {'ABC'[i]}", GREEN, size=24)); b.append(arrow(1195, 200, x + 105, 316, "", GREEN, 3))
    b.append(text(1195, 475, "accept · release · reject, per record", 26, GREEN, "middle", 800))
    b.append(mtext(1195, 545, ["More readers than partitions.", "No order across deliveries."], 25, INK, "middle", 600))
    return svg(1600, 640, b)


def reference():
    b = [box(30, 60, 220, 90, "Order service", BLUE, size=24), box(30, 220, 220, 110, ["PostgreSQL", "orders + outbox"], BLUE, size=23), box(30, 410, 220, 90, "CDC relay", AMBER, size=24)]
    b.append(arrow(140, 152, 140, 216, "", BLUE, 3.5)); b.append(arrow(140, 332, 140, 406, "", AMBER, 3.5))
    b.append(path("M252,455 L370,455 L370,300 L396,300", BLUE, 3.5, "", True))
    b.append(panel(400, 30, 660, 500, "blue", "Kafka · 6 brokers, 3 zones, 3 controllers"))
    b.append(box(430, 85, 600, 120, ["orders.order-events.v1", "48 partitions · key = order_id"], BLUE, size=24))
    b.append(box(430, 225, 600, 110, ["RF 3 · min in-sync 2 · acks = all", "7 days retention, 1 day on local disk"], GREY, size=23, first_bold=False))
    b.append(box(430, 355, 285, 100, ["retry topic", "with a delay"], AMBER, size=22)); b.append(box(745, 355, 285, 100, ["dead-letter topic", "alert on any"], RED, size=22))
    b.append(text(730, 505, "Schemas: backward-compatible, checked in CI", 23, MUTED, "middle", 700))
    for i, (n, s) in enumerate((("Fulfilment", "dedupes by event ID"), ("Search indexer", "upsert by order ID"), ("Analytics", "Iceberg tables"), ("Notifications", "idempotency key"))):
        y = 40 + i * 125
        b.append(box(1230, y, 340, 100, [n, s], GREEN, size=23)); b.append(arrow(1062, 280, 1226, y + 50, "", GREEN, 3))
    b.append(box(400, 555, 660, 70, "Object storage: tiered log segments", GREY, size=23)); b.append(arrow(730, 532, 730, 552, "", GREY, 3))
    return svg(1600, 650, b)


FIGS = {"k-place": place, "k-anatomy": anatomy, "k-sync-event": sync_event, "k-replicate": replicate, "k-groups": groups, "k-decide": decide,
        "k-split-race": split_race, "k-key-hash": key_hash, "k-hot-key": hot_key, "k-resize": resize, "k-rf-states": rf_states, "k-sizing": sizing,
        "k-zones": zones, "k-tiered": tiered, "k-dual-write": dual_write, "k-eos": eos, "k-retry": retry, "k-compaction": compaction,
        "k-cqrs": cqrs, "k-no-cas": no_cas, "k-share": share, "k-reference": reference}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
