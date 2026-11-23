from dsl import *
from stack import REJ, say_text
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
def rej(n):
    t, w = REJ(n); return rejl(t, w)
def rejsay(n):
    t, w = REJ(n); return "C: Rejected: " + say_text(t) + ". " + say_text(w[0].upper() + w[1:])

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 5, "It works. Where does it break first?", [
 "V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Six challenges, six places on the same picture", "map", chip=chips("each fix creates the next question")), [
 P, "C: Version four, with the places it will break marked one at a time.", P,
 "C: The adapter, where a call times out. Challenge one.", P,
 "C: The A-P-I, where retries arrive together. Challenge two.", P,
 "C: The outbox relay, where a crash splits a commit from its event. Challenge three.", P,
 "C: The balance projector, and the database behind it: the hot merchant, and a million one-time accounts. Challenge four.", P,
 "C: Reconciliation, where the outside world disagrees with us, and a bad release. Challenge five.", P,
 "C: And finance operations, who find out last. Challenge six: how would we know first?"], cls="dia")

chapter(7, "Challenges", 5, "Six ways to break it, and what survives", [
 "C: Six challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks inside the container, the fix one level down, the push on the fix itself, and what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 6 · {t}"

# ───────── Challenge 1 · the bank timed out ─────────
subchapter("7.1", "Challenge 1: The bank timed out", ["N: Challenge one, the crux. The processor does not answer, and we do not know whether the customer paid."])
qs("Interviewer · challenge 1 of 6", "“You call the processor. It times out. You don't know whether the customer was charged. Walk me through the next ten minutes, and the next ten days.”", [
 "I: You call the processor. It times out. You don't know whether the customer was charged. Walk me through the next ten minutes, and the next ten days.", "[pause: 2.0]"])

S(dia(K(1, "the timeout"), "What does a timeout mean?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Mark it failed and let the client retry.” Or: “Retry it ourselves until it works.”"),
                  ("case", "Break", "The port maps a timeout to a decline. A timeout is not an answer: either guess is sometimes wrong."))), [
 P, "C: The payment service, opened up: the attempt, the port, the adapter and the processor.", P,
 "C: The processor port is marked.", P,
 "C: The naive answers: mark it failed and let the client retry, or retry it ourselves until it works.", P,
 "C: Then the port maps a timeout to a decline. But a timeout is not an answer. It means the request may or may not have arrived, and may or may not have been approved."], cls="dia")

S(trace(K(1, "the trace"), "Two holds for one purchase", [
  ("10:00:00.000", "attempt p-7731/1 sent, 1,050"),
  ("10:00:01.900", "our deadline: no answer; the naive design marks it " + B("failed")),
  ("10:00:02.400", "the processor approves p-7731/1"),
  ("10:00:05.000", "the checkout retries as p-7744: approved; " + B("two holds of 1,050 on one card"))],
  hedge=("Label the numbers", "Illustrative. The shape is real: an approval that arrives after the deadline, and a retry that is a new payment.")), [
 "C: The trace.", P, "C: The attempt is sent at ten o'clock.", P,
 "C: At one point nine seconds there is no answer, and the naive design marks it failed.", P,
 "C: Half a second later the processor approves it.", P,
 "C: At five seconds the checkout retries, as a new payment, which is approved. Two holds on one card for one purchase.", P,
 "C: The numbers are illustrative. The shape is real: approvals do arrive after deadlines."])

S(dia(K(1, "the fix"), "Unknown is a state, and an inquiry ends it", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "Attempt row commits before the call → UNKNOWN by conditional update → inquiry by our reference.")) + rej(1)), [
 P, "C: The fix, on the same view.", P, "C: The state machine.", P, "C: The attempt writer.", P, "C: And the inquiry job.", P,
 "C: One level down. The attempt row, with our reference, commits before the call. At the deadline the state moves from auth pending to unknown, in a conditional update that names the state it expects, and the client gets pending. The inquiry asks the processor about that reference after five seconds, thirty seconds, two minutes.", 
 "C: It covers every retry: the same key gets the same pending, and the same reference is one movement at the processor. It does not cover a processor that has no inquiry. Then the settlement file is the arbiter, a day late.", P,
 rejsay(1)], cls="dia")

S(dia(K(1, "sequence"), "The next ten minutes", "seq-timeout"), [
 "C: As a sequence.", P, "C: Authorise, with reference p-seventy-seven thirty-one, slash one.", P,
 "C: The deadline passes.", P, "C: The payment becomes unknown, and pending is the answer, to this request and to any retry with the same key.", P,
 "C: The inquiry asks for the status of that reference.", P, "C: Approved, at two point four seconds.", P,
 "C: The job moves it to authorised, posts the entries and the outbox event.", P,
 "C: The two other exits: not found after the processor's safe window means declined, and a new attempt is safe. And an approval we no longer want is reversed by the same reference."], cls="dia")

qs("Interviewer · the second-level push", "“The processor's inquiry endpoint is down too. Actually, the whole processor is down for an hour.”", [
 "I: The processor's inquiry endpoint is down too. Actually, the whole processor is down for an hour.", "[pause: 2.0]"])

S(plain(K(1, "the second fix, and the honest limit"), "Fail over only what definitely failed", cards(
  ("grn", "A breaker per processor", "Stop new attempts to a processor that is down; new payments go to a second one, if the contract allows."),
  ("red", "Never fail over an unknown", "An unknown sent elsewhere is two possible charges. Unknowns wait, age, and show on a dashboard."),
  ("amb", "The honest limit", "No inquiry and no idempotent references: only the file resolves it, a day late. Choose processors for it."), cols=3)), [
 P, "C: A circuit breaker per processor stops new attempts going to one that is down, and new payments go to a second processor, if the contracts allow.", P,
 "C: But never an unknown. An unknown sent to a second processor is two possible charges. Unknowns wait, age, and show on a dashboard, and the merchant sees pending.", P,
 "C: The honest limit: a processor with neither inquiry nor idempotent references can only be resolved by the settlement file, a day late. That is a reason to choose processors, and I'd say so to whoever negotiates the contracts."])

say_slide("“A timeout is an unknown, not a failure. I commit the attempt before calling out, move the payment to unknown, answer pending, and an inquiry job asks the processor by our own reference until it knows. Retries carry the same reference, so they can't become a second charge, and the settlement file is the final arbiter.”", [
 "V: If asked, I'd say: a timeout is an unknown, not a failure. I commit the attempt before calling out, move the payment to unknown, answer pending, and an inquiry job asks the processor by our own reference until it knows. Retries carry the same reference, so they can't become a second charge, and the settlement file is the final arbiter.", "[pause: 1.0]",
 "N: That fix leans on retries being harmless. Are they?"])

# ───────── Challenge 2 · three retries at once ─────────
subchapter("7.2", "Challenge 2: Three retries at once", ["N: Challenge two. The same payment arrives three times in three milliseconds: how does only one of them count?"])
qs("Interviewer · challenge 2 of 6", "“The client sends the same payment three times, concurrently, with the same idempotency key. Then once more, same key, different amount. What happens?”", [
 "I: The client sends the same payment three times, concurrently, with the same idempotency key. Then once more, same key, different amount. What happens?", "[pause: 2.0]"])

S(dia(K(2, "concurrent retries"), "Who decides which request counts?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“We check whether the key exists before processing.”"),
                  ("case", "Break", "Check, then act, on three servers: each check sees nothing, each acts."))), [
 P, "C: The payments A-P-I, the idempotency guard, the state machine, and the database.", P,
 "C: The guard is marked.", P, "C: The naive answer: check whether the key exists before processing.", P,
 "C: Three requests land on three servers, and each one checks, finds nothing, and charges. A check followed by an act is a race, however fast the check is."], cls="dia")

S(trace(K(2, "the trace"), "Three authorisations, and a changed amount", [
  ("10:00:00.001", "R1, key k-91, 1,050, server A: SELECT → none"),
  ("10:00:00.002", "R2, key k-91, 1,050, server B: SELECT → none"),
  ("10:00:00.003", "R3, key k-91, 1,050, server C: SELECT → none; " + B("three authorisations of 1,050")),
  ("10:05:00", "R4, key k-91, " + B("2,050") + ": return the old answer, or charge again?")]), [
 "C: The trace.", P, "C: Request one, key k-ninety-one, server A: it selects, and finds none.", P,
 "C: Request two, one millisecond later, server B: none.", P,
 "C: Request three, server C: none. Three authorisations go out.", P,
 "C: Five minutes later a fourth request arrives with the same key and a different amount. Returning the stored answer would hide the client's bug. Executing it would charge again. Neither is right."])

S(dia(K(2, "the fix"), "Insert the key first, and let the constraint decide", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "Unique insert of the key with a request hash, in the payment's transaction; the loser reads the row.")) + rej(2)), [
 P, "C: The fix, on the same view.", P, "C: The guard.", P, "C: And the key row it writes.", P,
 "C: Insert the key first, unique per client, with a hash of the request, in the same transaction that creates the payment. Only one insert can win. The others fail the constraint and read the row: processing gets a four-oh-nine, done gets the stored response, and a different hash gets a four twenty-two.", 
 "C: It covers concurrent and later retries for seven days. It does not cover a client that mints a new key per retry. That is a client bug.", P,
 rejsay(2)], cls="dia")

S(plain(K(2, "the code"), "Insert or read, in eleven lines", pseudo(
 "begin transaction\n  try insert key(client, key, hash, 'processing')\n       create payment AUTH_PENDING   # same transaction\n  on unique violation:\n    row = read key(client, key)\n    if row.hash != hash: return 422   # changed request\n    if row.status == 'processing': return 409\n    return row.stored_response   # never re-executed\ncommit", hl=(2, 6, 8)) +
  strip(("whyb", "Why it works", "The result is returned, not re-executed; a changed request under an old key is reported, not hidden."), cols="one")), [
 "C: In pseudocode. Inside one transaction, try to insert the key and create the payment.",
 "C: On a unique violation, read the row. A different hash is a reused key: four twenty-two. Processing: four-oh-nine. Otherwise return the stored response, never re-executed.", P,
 "C: The result is returned, not re-executed, and a changed request under an old key is reported, not hidden."])

S(dia(K(2, "sequence"), "One wins; the others read", "seq-idem"), [
 "C: As a sequence.", P, "C: Request one and request two, two milliseconds apart.", P,
 "C: Request one's insert succeeds: processing, with payment p-seventy-seven thirty-one.", P,
 "C: Request two's insert hits the unique violation.", P, "C: It reads the row: processing, hash h-one.", P, "C: So it gets four-oh-nine.", P,
 "C: Later the same request finds done, and the same hash, and gets the stored response.", "[+2]",
 "C: And the changed amount has a different hash: four twenty-two."], cls="dia")

qs("Interviewer · the second-level push", "“The server that won crashes after the processor approved, but before it wrote ‘done’.”", [
 "I: The server that won crashes after the processor approved, but before it wrote done.", "[pause: 2.0]"])

S(plain(K(2, "the second fix"), "A stuck “processing” row is just an unknown", cards(
  ("grn", "The rows say how far it got", "Key: processing, with the payment ID. Payment: AUTH_PENDING, with the attempt reference. That is exactly an unknown outcome."),
  ("grn", "Sweep, then inquire", "A processing row older than a minute goes to recovery: challenge one's inquiry, by reference."), cols=2) +
  line("Keys live seven days. The contract says a retry after that is a new payment.", "a")), [
 P, "C: The rows say exactly how far it got. The key says processing, with the payment I-D. The payment says auth pending, with the attempt's reference. That is an unknown outcome.", P,
 "C: Challenge one already handles it: a sweeper sends any processing row older than a minute to the inquiry.", P,
 "C: One contract term: keys live seven days, and a retry after that is a new payment."])

say_slide("“The idempotency key is inserted first, with a unique constraint, in the same transaction that creates the payment. One request wins; the others get ‘in progress’ or the stored answer. A different body under the same key is a client bug, so I reject it instead of hiding it. And a crash in the middle is just an unknown outcome, which I already handle.”", [
 "V: If asked, I'd say: the idempotency key is inserted first, with a unique constraint, in the same transaction that creates the payment. One request wins; the others get in progress or the stored answer. A different body under the same key is a client bug, so I reject it instead of hiding it. And a crash in the middle is just an unknown outcome, which I already handle.", "[pause: 1.0]",
 "N: Inside the database it is now safe. What about everything outside it?"])

# ───────── Challenge 3 · a crash between the ledger and the event ─────────
subchapter("7.3", "Challenge 3: A crash between the ledger and the event", ["N: Challenge three. The payment is committed, and the process dies before anyone is told."])
qs("Interviewer · challenge 3 of 6", "“Your service commits the payment, then crashes before telling the merchant. What state are you in?”", [
 "I: Your service commits the payment, then crashes before telling the merchant. What state are you in?", "[pause: 2.0]"])

S(dia(K(3, "two writes"), "Commit, then publish", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Publish right after the commit.”"),
                  ("case", "Break", "Two writes, no shared transaction."))), [
 P, "C: The container view: the service, the database, the relay and the webhook sender.", P,
 "C: The service is marked: it writes to the database, then publishes.", P,
 "C: The naive answer: publish right after the commit, crashes are rare.", P,
 "C: But that is a second write, to a second system, with no shared transaction. Whichever order you choose, a crash between them loses something."], cls="dia")

S(trace(K(3, "the trace"), "Charged, and nothing shipped", [
  ("11:20:00.010", "commit: p-8102 CAPTURED, entries written"),
  ("11:20:00.012", B("process killed by a deploy") + ": no event"),
  ("11:20 onward", "the merchant's order system waits; " + B("nothing ships")),
  ("reverse order", "publish first, then the commit fails: " + B("goods ship for an unpaid order"))]), [
 "C: The trace.", P, "C: The capture commits.", P, "C: Two milliseconds later a deploy kills the process, and no event is sent.", P,
 "C: The merchant's order system waits, and nothing ships: the customer has paid for nothing.", P,
 "C: Reverse the order, publish first, and a failed commit ships goods for an unpaid order. Rare is not the same as never, at ten thousand a second."])

S(dia(K(3, "the fix"), "The event is a row in the same transaction, read from the log", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "Outbox row in the same transaction; Debezium reads the log in commit order, at least once.")) + rej(3)), [
 P, "C: The fix, on the ledger database's component view.", P, "C: The outbox table, in the same transaction.", P, "C: And the replication slot.", P,
 "C: One level down. The outbox row commits with the state and the entries. Debezium reads the write-ahead log through a replication slot, so it sees only committed rows, in commit order, and publishes each to Kafka keyed by merchant. Delivery is at least once.", 
 "C: It covers a crash between the commit and the publish. It does not remove duplicates, so consumers deduplicate by event I-D.", P,
 rejsay(3)], cls="dia")

S(dia(K(3, "sequence"), "Nothing is lost at the crash", "seq-outbox"), [
 "C: As a sequence. This is also requirement three, notify.", P, "C: One transaction: captured, entries, the outbox row e-five-five-one.", P,
 "C: The process is killed right there. Nothing is lost: the row is committed.", P,
 "C: Debezium reads the log from its slot position, in commit order.", P, "C: It publishes e-five-five-one, keyed by merchant.", P,
 "C: Kafka delivers it to the webhook sender.", P, "C: Which posts it, signed, retried with backoff.", P,
 "C: If the merchant sees it twice, it has already seen that event I-D and ignores the second."], cls="dia")

qs("Interviewer · the second-level push", "“Debezium has been stopped for a day. Or the connector is stuck on one bad record.”", [
 "I: Debezium has been stopped for a day. Or the connector is stuck on one bad record.", "[pause: 2.0]"])

S(plain(K(3, "the second fix, and the honest limit"), "A stalled reader holds the database's log", cards(
  ("red", "What it costs", "The slot keeps log for the reader; a reader stopped for a day can fill the primary's disk."),
  ("grn", "Alert and cap", "Alert on slot lag in bytes and outbox age; cap retained log. A lost slot is rebuilt from the outbox table."),
  ("amb", "Or poll", "Below about 1,000 events a second, poll: no slot to babysit. That is the alternate path."), cols=3)), [
 P, "C: The cost of reading the log is that the slot keeps log for the reader. A reader stopped for a day can fill the primary's disk. That is the one new way this design can hurt the database.", P,
 "C: So: alert on slot lag in bytes and on outbox age, and cap how much log the database keeps. If a slot is invalidated, it is rebuilt from the outbox table itself, which still holds the unpublished rows.", P,
 "C: And below about a thousand events a second I would not run change capture at all. A polling relay has no slot to look after. That was the alternate path."])

say_slide("“I never write to two systems and hope. The event is a row in the same transaction as the state change, and change capture publishes it at least once, in commit order. Consumers de-duplicate by event ID, and the merchant can always ask us for the state directly. The cost I watch is the replication slot.”", [
 "V: If asked, I'd say: I never write to two systems and hope. The event is a row in the same transaction as the state change, and change capture publishes it at least once, in commit order. Consumers de-duplicate by event I-D, and the merchant can always ask us for the state directly. The cost I watch is the replication slot.", "[pause: 1.0]",
 "N: One transaction per payment works. Until a thousand of them want the same row."])
