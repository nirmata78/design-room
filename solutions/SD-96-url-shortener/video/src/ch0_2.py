from dsl import *
P = "[+]"

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Design a URL shortener", [
 "C: A U-R-L shortener is the question everyone has drawn. A hash, a table, a cache. Interviewers still ask it at every level, because the grade is not on the table. It is on three places where the simple answer quietly fails."])

qs("Interviewer · the prompt", "“Design a URL shortener: a long URL goes in, a short link comes out, and anyone who opens the short link is redirected.”", [
 "I: Design a U-R-L shortener. A long U-R-L goes in, a short link comes out, and anyone who opens the short link is redirected.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "Three places where the simple answer fails", "tension",
      chip=chips("unique without a lock", "one viral key", "a takedown in 5 min")), [
 "C: Here is the hook. First, two servers must never hand out the same code, and they must not ask each other on every create. Second, one link can go viral: forty thousand clicks a second on one key, and a read-heavy system becomes a single hot spot.",
 "C: Third, the things beside the redirect. Click counts and phishing takedowns both fight the caching that makes the redirect fast. This picture is the whole tension: every layer that answers closer to the user is faster and cheaper, and harder to count or to take back."])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Shorten and redirect”, no numbers", "Read to write ratio, lifetime, aliases, analytics and the takedown time, asked first"],
  ["<b>Correctness</b>", "Hash the URL, take six characters; check, then insert", "Code length from arithmetic; ranges or random with retry; the key constraint decides"],
  ["<b>Trade-offs</b>", "“Use a cache and a NoSQL store”", "Named technologies against named alternatives; 301 against 302 as a product decision"],
  ["<b>Depth</b>", "Stops at “add a cache”", "Hot key: in-process cache and single flight; codes that cannot be walked; takedown through every copy"],
  ["<b>Operations</b>", "CPU and error rate", "A create-then-follow probe, hit rate against store reads, takedown time as an SLI"]], "bt sm sig") +
  grade("The redirect is the product. Everything else must stand beside it, never in front of it.")), [
 "N: Five axes. I'll fill them in one at a time.", P,
 "N: Requirements. The weak answer is shorten and redirect, with no numbers. The strong one asks the read to write ratio, the lifetime, aliases, analytics and the takedown time first.", P,
 "N: Correctness. Hashing and truncating, or checking and then inserting, is weak. The strong answer derives the code length and lets a key constraint decide a collision.", P,
 "N: Trade-offs. Use a cache and a NoSQL store is a slogan. The strong answer names a technology, names what it rejected, and says why.", "[+2]",
 "N: Depth: what one viral key does to one cache shard. And operations: probes and pairs of metrics, not C-P-U.", P,
 "C: And one rule I'll keep for the whole round: the redirect is the product. Everything else stands beside it, never in front of it."])

key("The thesis", "A read path with a write path attached: codes <em>unique</em> without a lock, <em>unguessable</em> without a lookup, a redirect that is <em>one memory read</em>, and nothing standing between the click and the answer.", [
 "V: A U-R-L shortener is a read path with a write path attached. Make codes unique without a lock per create, and unguessable without a lookup. Keep the redirect to one memory read. And let nothing, not counting, not abuse, not analytics, stand between the click and the answer.", "[pause: 1.0]"])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:6pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  cards(("", "First", "Requirements and scope, with the system in context. Numbers. A theory chapter with the mechanisms at work."),
        ("grn", "Then", "API and data. A design in three versions, the container view, every flow as a sequence, then every component one level deep, with its technology."),
        ("red", "Most of the time", "Eight challenges that break the design. A build cost. A recap."), cols=3)), [
 "C: The order.", P,
 "C: First, requirements and scope, with the system in its context. Numbers. And a theory chapter where each mechanism is shown at work.", P,
 "C: Then the A-P-I and the data, a design in three versions, the container view, every flow as a sequence, and every component one level deep, with the technology I would use and the ones I would not.", P,
 "C: Then most of the time goes to eight challenges that break it, where each fix creates the next question. A build cost, and a recap."])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "Ask first. Cut on purpose. Put numbers on it.", [
 "C: Six questions before I draw anything. Each answer moves the design."])

def clar(n, q, a, ask, ans, so):
    S(f'<div class="who">Clarifying question {n} of 6</div><div class="qq">{q}</div><div class="ans">{a}</div>',
      ["C: " + ask, P, "I: " + ans, "C: " + so], cls="qs")

clar(1, "How many links, and how many clicks?", "100 million new links a month. 10 billion redirects a month. A viral link can take 40,000 clicks a second.",
     "How many links, and how many clicks?", "A hundred million new links a month. Ten billion redirects a month. And a viral link can take forty thousand clicks a second.",
     "A hundred to one, reads to writes. And the peak is not many keys, it is one key. That last number will get its own challenge.")
clar(2, "How long does a link live?", "Forever by default. The creator can set an optional expiry.",
     "How long does a link live?", "Forever by default. The creator can set an optional expiry date.",
     "Forever means the code space has to last for years, so I'll size it over ten. And printed links never go away, which makes the code format a one-way door.")
clar(3, "Custom aliases?", "Yes, for paying users. First come, first served.",
     "Can users choose their own alias?", "Yes, paying users can. First come, first served.",
     "First come, first served is a uniqueness race between two customers. Somebody has to decide who was first, and it should not be my application code.")
clar(4, "What analytics?", "Clicks per link by day and by country, shown to the owner. Not billed today; product may bill per click later.",
     "What do owners see about their clicks?", "Clicks per link, by day and by country, in a dashboard. Not billed today. Product may want to bill per click later.",
     "Not billed means I may lose a tiny fraction and say so. Billed later means that decision is not permanent. Challenge six.")
clar(5, "What about abuse?", "Phishing and malware links exist. Legal wants a reported link dead everywhere within five minutes.",
     "What about abuse?", "Phishing and malware links exist. Legal wants a reported link dead everywhere within five minutes.",
     "Everywhere is the hard word. Every cache that holds the answer is a copy I have to reach. Challenge five.")
clar(6, "Who calls us?", "Browsers following links, and integrators creating links in bulk through an API.",
     "Who calls the service?", "Browsers following links. And integrators who create links in bulk through an A-P-I.",
     "Bulk creators retry, so create must be idempotent, and they need a rate limit per key. Two lines on the A-P-I slide.")

S(plain("Requirements · functional", "Four things the system must do", cards(
  ("", "FR1 · Create", "Long URL in, short link out. Optional alias and expiry. A retried request gets the same answer."),
  ("grn", "FR2 · Redirect", "A request for a code gets the long URL as a redirect, or a not-found or gone page."),
  ("amb", "FR3 · Count", "Clicks per link per day per country, visible to the owner within minutes."),
  ("red", "FR4 · Withdraw", "The owner deletes, or trust and safety blocks, a link. It stops redirecting everywhere within five minutes."))), [
 "C: Four functional requirements.", P,
 "C: One, create: a long U-R-L in, a short link out, with an optional alias and expiry, and a retried request gets the same answer.", P,
 "C: Two, redirect: a code gets the long U-R-L, or a not-found or gone page.", P,
 "C: Three, count: clicks per link per day per country, within minutes.", P,
 "C: Four, withdraw: the owner deletes, or trust and safety blocks, and it stops working everywhere within five minutes. Each of these gets a numbered flow and a sequence later."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile blue"><b>20 ms</b><span>redirect p99 at the server</span></div>'
  '<div class="tile blue"><b>99.99 %</b><span>redirect availability</span></div>'
  '<div class="tile"><b>200 ms</b><span>create p99, 99.9 %</span></div>'
  '<div class="tile red"><b>5 min</b><span>takedown, at every layer</span></div></div>' +
  line("Counts may lag by minutes and may lose a tiny, measured fraction, until clicks are billed.", "a")), [
 "C: The numbers, and they are initial targets, not measurements.", P,
 "C: A redirect under twenty milliseconds at the ninety-ninth percentile, measured at the server.", P,
 "C: Four nines of redirect availability.", P,
 "C: Create under two hundred milliseconds, three nines, because creating is less urgent than following.", P,
 "C: A takedown effective everywhere within five minutes.", P,
 "C: And counts may lag by minutes and may lose a tiny, measured fraction, until clicks are billed."])

S(plain("Requirements · scope", "In, and out on purpose", cards(
  ("grn", "In scope", "Create, redirect, custom aliases, expiry, counts by day and country, takedown, a bulk API with a rate limit per key."),
  ("red", "Out, on purpose", "The malware classifier itself (a service we call). Accounts and billing. QR codes (a picture of the same link). Link-in-bio pages. Editing a link's target.")) +
  line("Editing a target is a takedown plus a create, as far as every cache is concerned.", "")), [
 P, "C: In scope: create, redirect, aliases, expiry, counts, takedowns, and a bulk A-P-I with a rate limit per key.", P,
 "C: Out, on purpose. The malware classifier itself: I call it, I don't build it. Accounts and billing. Q-R codes, which are just a picture of the same link. Link-in-bio pages.", P,
 "C: And editing a link's target, which I'd say aloud: for every cache, an edit is a takedown plus a create, so it rides on challenge five."])

S(dia("Architecture · C4 level 1 · context", "The system in its context, before any boxes inside it", "c4-context",
      cap="Figure 1.1 — C4 system context: who uses the shortener, and the one system it depends on"), [
 "C: Before any boxes inside it, the system in its context. This is C-four level one: people and other systems, nothing internal.", P,
 "C: First, visitors. They follow a short link from anywhere, an email, a printed flyer, a chat, and they get a three-oh-two. This is ninety-nine percent of the traffic.", P,
 "C: In the middle, the shortener, one box for now: codes, redirects, counts and takedowns.", P,
 "C: Link owners create links through the A-P-I, alone or in bulk, and read their click statistics.", P,
 "C: Trust and safety block phishing and malware links, through a console or an A-P-I. Their five-minute bar is a requirement on everything inside the box.", P,
 "C: And one external system: a U-R-L classifier we call on create, to ask whether a U-R-L is known-bad. Notice what is not on this picture: nothing external sits on the redirect path. That is a decision, and I'll defend it."], cls="dia")

key("The core", "The core is three things: a <em>code generator</em> that never collides, a <em>redirect path</em> that is one memory read, and a <em>side path</em> for counting and withdrawal that never sits in front of it.", [
 "V: The core is three things. A code generator that never collides. A redirect path that is one memory read. And a side path for counting and withdrawal that never sits in front of the redirect.", "[pause: 0.8]",
 "N: Notice the candidate named the core and drew the context before any internals. That is the scoping signal."])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Each number as arithmetic, with what it decides", [
 "C: Numbers next, each as arithmetic, each with the decision it drives. I'll label them: given, derived or illustrative."])

S(plain("Estimates · traffic", "Writes are tiny; the peak is one key", table(["Number", "Arithmetic", "Label", "Decides"], [
  ["Creates", "10⁸ ÷ (30 × 86,400 s) ≈ <b>40/s</b>, peak ×10 = <b>400/s</b>", "derived", "Throughput is easy; uniqueness is the problem"],
  ["Redirects", "10¹⁰ ÷ 2.6 × 10⁶ s ≈ <b>4,000/s</b>", "derived", "Read to write 100 : 1; optimise the read"],
  ["Viral peak", "<b>40,000/s</b> on one code", "given", "A hot key, not a big fleet"]])), [
 "C: Traffic, three rows.", P,
 "C: A hundred million creates a month, divided by about two point six million seconds, is about forty a second, and say ten times that at peak: four hundred. That is nothing. One database could take it. So the hard part of create is uniqueness, not throughput.", P,
 "C: Ten billion redirects a month is about four thousand a second. Reads to writes, a hundred to one.", P,
 "C: And the peak the interviewer gave me is forty thousand a second on one code. The peak is one key, which is a very different problem from a big fleet."])

S(dia("Estimates · the code space", "Six characters or seven?", "codespace", chip=chips("62 symbols: a–z A–Z 0–9", "1.2 × 10¹⁰ links in ten years")), [
 "C: How long must a code be? A hundred million a month, times twelve, times ten years, is one point two times ten to the ten links. The alphabet is sixty-two symbols: lower case, upper case and digits.",
 "C: Six characters give sixty-two to the sixth, about five point seven times ten to the ten. Only four point seven times the links I need, and random codes would collide long before that. Seven characters give three point five times ten to the twelve, about two hundred and ninety times. Seven it is.",
 "C: And with random codes, at the end of year ten, a new code hits an existing one with probability links over space: about a third of a percent. Small enough that a retry on conflict is fine."])

S(plain("Estimates · storage and memory", "The data is small; the hot set fits in RAM", table(["Number", "Arithmetic", "Label", "Decides"], [
  ["Storage", "1.2 × 10¹⁰ × ~500 B ≈ <b>6 TB</b>, × 3 replicas = 18 TB", "illustrative", "A sharded store, easily; not the hard part"],
  ["Hot set", "2 % of links take 90 % of clicks: 2 × 10⁸ × 500 B ≈ <b>100 GB</b>", "illustrative, to measure", "A few cache nodes hold it"],
  ["Store reads", "4,000/s × 1 % miss ≈ <b>40/s</b>; cold cache: up to 4,000/s", "derived", "The store is off the hot path, until the cache is cold"]])), [
 "C: Storage and memory.", P,
 "C: One point two times ten to the ten links at about five hundred bytes each, with the U-R-L, the owner, dates and index overhead, is six terabytes, eighteen with three replicas. Not the hard part.", P,
 "C: The hot set. If two percent of links take ninety percent of clicks, that's two hundred million links, about a hundred gigabytes. A few cache nodes. This number is illustrative, and the first thing I'd measure.", P,
 "C: So the store sees misses only: four thousand a second times a one percent miss rate is forty a second. Except when the cache is cold, after a restart, when it can see all four thousand. Keep that for challenge three."])

S(plain("Estimates · coordination and side paths", "Small numbers that shape the design", table(["Number", "Arithmetic", "Label", "Decides"], [
  ["Range leases", "400 creates/s ÷ 1,000 per lease = <b>0.4 leases/s</b>", "derived", "The allocator can be a small consistent store"],
  ["Click events", "4,000/s × ~200 B ≈ <b>0.8 MB/s</b>, ≈ 70 GB a day", "illustrative", "A log and an aggregator, not a counter on the row"],
  ["One hot shard", "40,000/s on one cache shard, plus its other keys", "derived", "Its tail becomes every viral click's tail"]])), [
 "C: Three small numbers that shape the design.", P,
 "C: If each create server leases a thousand I-Ds at a time, four hundred creates a second is less than one lease every two seconds. So the allocator can be a small, strongly consistent store.", P,
 "C: Click events: four thousand a second, two hundred bytes each, under a megabyte a second, seventy gigabytes a day. A log and an aggregator, not a counter on the link row.", P,
 "C: And one viral key at forty thousand a second lands on one cache shard. The shard can take it, but its queue and its tail become every viral click's tail."])

S(dia("Estimates · the latency budget", "Twenty milliseconds, with room for one miss", "budget", chip=chips("initial target", "at the server")), [
 "C: The latency budget at the server. A cache lookup, about a millisecond. On a miss, the link store, about five. Parsing, writing the response and emitting the click event, about one more. Seven milliseconds in the worst case with a miss, against twenty.",
 "C: That spare is room for one miss. It is not room for a synchronous write of a click counter, or a call to a classifier on the redirect path. The budget says what may never be added."])

S(plain("Estimates · the takedown budget", "Five minutes is a sum of lifetimes", cards(
  ("", "Status and shared cache", "Written and deleted directly by the takedown: seconds."),
  ("amb", "In-process caches", "Dropped by an event; if the event is lost, a 60 s TTL ends it."),
  ("red", "Edge", "Purged by API; if that fails, a 60 s cache time ends it."), cols=3) +
  line("Every layer's lifetime has to fit inside five minutes, summed along the worst path.", "a")), [
 "C: The takedown budget. Five minutes is not a hope, it is a sum.", P,
 "C: The status write and the shared cache delete are done directly by the takedown, in seconds.", P,
 "C: Each redirect server's in-process cache is dropped by an event, and if that event is lost, a sixty-second lifetime ends it.", P,
 "C: The edge is purged by its A-P-I, and if that fails, a sixty-second cache time ends it.", P,
 "C: The rule: every layer's lifetime fits inside five minutes, summed along the worst path. I'll come back to it with numbers in challenge five."])
