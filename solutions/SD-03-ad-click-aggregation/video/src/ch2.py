from dsl import *
P = "[+]"

# ───────────────────────── 2 · back-of-the-envelope ─────────────────────────
chapter(2, "Estimates", 1, "Each number from the scale line, and the constraint it forces", [
 "C: Numbers next. Each starts from the scale line, and each ends in a constraint on the design: what it rules out, and what it forces. They are illustrative, not anyone's real figures."])

S(plain("Estimates · traffic", "Ten million a second, thirty at the peak", table(["Number", "From", "Arithmetic", "Forces"], [
  ["Events", "monthly volume", "2.5 × 10¹³ ÷ 2.6 × 10⁶ s ≈ <b>10 M/s</b>; × 3 = <b>30 M/s</b>", "a partitioned log; no database write per event"],
  ["Clicks", "monthly volume", "2.5 × 10¹¹ ÷ 2.6 × 10⁶ s ≈ <b>100 k/s</b>; peak 300 k/s", "the same pipeline; a billable click keyed by its impression"],
  ["Bandwidth", "peak", "30 M × 200 B = <b>6 GB/s</b>; × 3 replicas = 18 GB/s", "about 1,024 partitions and 80 brokers"]])), [
 "C: Traffic, from the monthly volumes.", P,
 "C: Twenty-five trillion impressions over two point six million seconds is about ten million a second. Three times that in the evening: thirty million a second. No database takes a write per event at that rate. That rules out a counter per event, and forces a partitioned log.", P,
 "C: Clicks are a hundredth of that: a hundred thousand a second, three hundred thousand at peak. They ride the same pipeline, and a billable click is keyed by the impression it came from, so a double-click bills once.", P,
 "C: At two hundred bytes an event, the peak is six gigabytes a second, eighteen with three replicas. About a thousand partitions and eighty brokers: illustrative, but it sets the order of magnitude."])

S(plain("Estimates · storage and state", "Days in the log, months in the lake, minutes in memory", table(["Number", "From", "Arithmetic", "Forces"], [
  ["Log, 3 days", "average", "2 GB/s × 259,200 s ≈ 520 TB; ÷ 4 compressed × 3 ≈ <b>390 TB</b>", "brokers keep 3 days; older replays read the lake"],
  ["Lake", "volume, retention", "2.5 × 10¹³ × 25 B ≈ <b>0.6 PB</b> a month; × 6 ≈ 3.8 PB", "object storage, partitioned by event hour"],
  ["Dedup state", "peak", "30 M/s × 600 s = 1.8 × 10¹⁰ IDs × 40 B ≈ <b>0.7 TB</b>", "keyed state over 512 tasks, not one Redis set"]])), [
 "C: Where the bytes live.", P,
 "C: Three days of log at the two-gigabyte average is five hundred and twenty terabytes; compressed and replicated, about three hundred and ninety. So brokers keep three days, and a replay older than that has to read somewhere else.", P,
 "C: That somewhere is a lake: about twenty-five bytes an event in columns, point six petabytes a month, three point eight for six months. Object storage, by event hour.", P,
 "C: And dedup. Ten minutes of event IDs at the peak is eighteen billion IDs, about point seven terabytes. Spread over five hundred and twelve stream tasks, one point four gigabytes each. In one Redis set it would be eighteen billion keys on one shard's thread. That rules Redis out for dedup."])

S(plain("Estimates · the hot ad and the money", "Two numbers that decide the hard parts", table(["Number", "From", "Arithmetic", "Forces"], [
  ["Hot ad", "the peak", "2 M/s on one key; one task does ~300 k updates/s", "combine before the shuffle: 512 partial sums a second"],
  ["Duplicates", "monthly clicks", "0.3 % retried × 2.5 × 10¹¹ = 7.5 × 10⁸ clicks × $0.50 ≈ <b>$375 M</b> a month", "dedup is the crux, not an optimisation"]])), [
 "C: Two numbers that decide the hard parts.", P,
 "C: The hot ad: two million impressions a second on one key, against roughly three hundred thousand updates a second for one stream task. Keyed by ad, one task drowns, and more machines don't help a single key. That forces combining before the shuffle.", P,
 "C: And the money. If three tenths of a percent of click batches are retried, that's seven hundred and fifty million duplicate clicks a month. At fifty cents a click, about three hundred and seventy-five million dollars of overbilling. Illustrative, but it says dedup is the crux of this question, not an optimisation."])

S(dia("Estimates · the freshness budget", "Ten seconds, from an impression to the dashboard", "budget", chip=chips("initial target", "worst case"),
      cap="The freshness budget, worst case, against the 10 s target"), [
 "C: The freshness budget, worst case. One second of batching in the SDK. Half a second through the collector and the log. Two seconds for the stream job's early results. A second to insert, a second to query. About five and a half seconds against ten.",
 "C: The spare is for a slow minute, not for a synchronous call. And it forces early results every two seconds, rather than waiting for a minute to close."])
