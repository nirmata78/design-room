# Episode 13 · Data integrity, what you read is what you wrote

Reader transcript generated from `src/ch13.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 13 of 16 · Priority 1 — Data integrity: what you read is what you wrote   `[th]`
> Why replication is not a backup, what a recovery system looks like, and how to find corruption before your users do.
**COACH:** Episode thirteen. Data integrity is the longest topic in this course, and it is about the failure that ends companies: losing or corrupting what people entrusted to you. It is also where the course's two big ideas meet. Reliability is a promise to users, and recovery is only real if you have practised it.
**SAY THIS:** Nobody wants backups. They want restores.
*[pause: 0.8]*


## 13.0 Why this decides interviews

### Slide 2 · The opening story — Same data, two kinds of outage   `[cards · c2]`
> red Unavailable for days :: A provider whose users could not reach their mail for over a week. Later the data was recovered. By then, users had already moved away.
> red Lost :: The data is gone. Trust is gone with it.
> > To a user, loss, corruption and long unavailability look the same.
**COACH:** Start with a story of an email provider whose users lost access to their mail for more than a week. Later it turned out that the data was not lost after all, it had only been unavailable. By then it did not matter. Users had already moved away. The lesson is that to a user, data loss, data corruption and extended unavailability are indistinguishable. So when we say data integrity, we mean the whole promise: what you read is what you wrote, and it is there when you ask.

### Slide 3 · What this episode covers — Data integrity   `[panel · note]`
> Data integrity: what you read is what you wrote. It is must-read for the design-room reliability part.
**COACH:** This episode covers data integrity. It is must read for the reliability part of the design-room course.


## 13.1 What the target is

### Slide 4 · The objective — Integrity is the means, availability is the goal   `[table · sm]`
> Idea | The position
> Recovery system, not a backup system | The deliverable is the ability to restore, with a measured time
> "Too long" for data to be unavailable | 24 hours is a sensible starting threshold for productivity apps, after a four-day recovery in a real incident taught them four days is too long
> Backups versus archives | An archive stores; a backup is designed for restoring
> Replication | Protects against site loss, but is not recoverability: it copies mistakes at once
> > A line to remember: "No one really wants to make backups; what people really want are restores."
**COACH:** The objective, in one line. Build a recovery system, not a backup system: the deliverable is the ability to restore, with a measured time. Decide how long is too long for data to be unavailable. After a real recovery that took four days, twenty-four hours is a sensible starting threshold for productivity applications. Know the difference between an archive and a backup: a backup is designed for restoring. And understand that replication is not recoverability. It protects against losing a site, and it copies a bad write to every replica within seconds.

### Slide 5 · One level down — The twenty-four ways to lose data   `[table · sm]`
> Dimension | Values | Count
> Root cause | User action · Operator error · Application bug · Infrastructure defect · Hardware fault · Site catastrophe | 6
> Scope | Wide, many entities · Narrow, a few entities | 2
> Rate | Big bang, sudden · Creeping, slow | 2
> > 6 × 2 × 2 = 24 combinations. No single defence covers all of them.
**COACH:** One level down: how you lose data. Classify it along three dimensions. Root cause, with six values: a user action, an operator error, an application bug, an infrastructure defect, a hardware fault, or a site catastrophe. Scope: wide, affecting many, or narrow, affecting a few. And rate: a big bang, or creeping slowly. Six times two times two is twenty-four combinations, and no single defence covers them all. That is why you layer them.

### Slide 6 · The line to say — Replication copies mistakes. Only a restore you have rehearsed counts as protection.   `[th]`
**SAY THIS:** Replication protects you from a machine dying. It does not protect you from a bug, because it copies the bug everywhere, quickly. Only a tested restore protects you from that.
*[pause: 0.8]*


## 13.2 Three layers of defence

### Slide 7 · Defence in depth — A deleted object's journey   `[dia]`
*Diagram:* `svg/e13-layers.svg`
**COACH:** The design is layers, and the picture shows an object's journey. The first layer is soft deletion. When data is deleted, it is marked as deleted and kept, hidden, for a limited time, before it is destroyed. Application bugs account for the vast majority of data loss, so the ability to undelete for a limited time becomes the primary line of defence. The second layer is backups, with recovery methods, including point-in-time recovery.
**COACH:** The third layer is early detection: regular validation that finds problems before users do. Across all three runs replication, useful in some cases, but not something recovery plans should rely upon.

### Slide 8 · One level down — What each layer catches, and what it misses   `[table · sm]`
> Layer | Catches | Misses
> Soft deletion | Application and operator bugs that delete or overwrite | Anything noticed after the retention window, or storage-level corruption
> Backups with point-in-time recovery | Larger losses, older damage | Anything between backups; slow to restore at scale
> Validation (early detection) | Corruption and runaway deletion, while the other layers can still help | Nothing, if it runs too late or looks at too little
> Replication | Site loss, hardware faults | Every logical error: it replicates the mistake
> > Early detection is what makes the other layers useful: a restore point is only any good if you notice in time.
**COACH:** What each layer catches, and what it misses. Soft deletion catches application and operator bugs that delete or overwrite, and misses anything noticed after the retention window. Backups with point-in-time recovery catch larger and older losses, and are slow to restore at scale. Validation catches corruption and runaway deletion while the other layers can still help. And replication catches site loss and hardware faults, and misses every logical error, because it replicates the mistake. Early detection is what makes the other layers useful, because a restore point is only good if you notice in time.

### Slide 9 · The line to say — Early detection makes the other layers usable.   `[th]`
**SAY THIS:** Early detection is what makes the other layers usable. A restore point only helps if you notice in time.
*[pause: 0.8]*

### Slide 10 · Why scale changes the answer — Restore time at a fixed bandwidth   `[dia]`
*Diagram:* `svg/e13-restore-time.svg`
**COACH:** One terabyte versus one exabyte is not just a bigger backup. Here is the arithmetic. Suppose you can restore at ten gigabytes a second. One terabyte takes under two minutes. One petabyte takes about twenty-eight hours, which is already beyond a twenty-four hour objective. One exabyte takes more than three years. The numbers are illustrative, but the lesson is general.
**COACH:** Restore time grows with size, and you cannot meet a recovery objective by buying more backup. You need to shard the data, restore in parallel, restore only what is affected, and keep recent and critical data on the fastest path.

### Slide 11 · Recovery objectives — Two numbers to agree before the incident   `[table · sm]`
> Term | Meaning | Set by
> Recovery point objective | How much recent data you can afford to lose | Backup frequency, log shipping
> Recovery time objective | How long until the data is usable again | Restore speed, size, practice
> > A daily backup means a recovery point of up to 24 hours. If that is too much, back up the log, not just snapshots.
**COACH:** Two numbers to agree before the incident. The recovery point objective is how much recent data you can afford to lose, and it is set by backup frequency and log shipping. The recovery time objective is how long until the data is usable again, and it is set by restore speed, size and practice. A daily backup means a recovery point of up to twenty-four hours. If that is too much, back up the log, not just snapshots, so you can replay to a chosen moment.


## 13.3 Early detection

### Slide 12 · The line to say — Restore time grows with size.   `[th]`
**SAY THIS:** Restore time grows with the size of the data, so a recovery objective is an engineering problem, not a purchase.
*[pause: 0.8]*

### Slide 13 · Validation — Out-of-band checks that find what monitoring cannot   `[table · sm]`
> Check | How | Finds
> Referential integrity across stores | A separate job compares references in one store to objects in another | Orphaned or missing data
> Checksums on read and at rest | Verify on every read, and scrub on a schedule | Silent corruption
> Counts and rates | Alert on a sudden fall in rows, or a spike in deletions | Runaway deletion
> Independent validators | Pipelines that do not share code with the writers | Bugs the writer cannot see
> > "Out of band" means the check does not use the same path as the thing it checks.
**COACH:** Early detection is validation that runs out of band: it does not use the same path as the thing it checks. A job compares references in one store to objects in another, and finds orphaned or missing data. Checksums are verified on read and scrubbed on a schedule, which finds silent corruption. Counts and rates alert on a sudden fall in rows or a spike in deletions, which finds runaway deletion, a bug that deletes more and more. And independent validators, which do not share code with the writers, find bugs the writer cannot see.

### Slide 14 · The line to say — Validation must not share a path with what it checks.   `[th]`
**SAY THIS:** A check that shares its path with the thing it checks will fail with it. Validate out of band.
*[pause: 0.8]*

### Slide 15 · Two case studies — What the layers did in practice   `[cards · c2]`
> grn Gmail, 2011 :: A significant amount of user data disappeared despite many safeguards. The offline backup system was used for its largest ever restore. It worked partly because similar restores had been simulated many times before.
> amb Music, 2012 :: A user reported tracks that skipped. Engineers traced it to missing references and a runaway deletion bug. Recovery meant reading data from thousands of tapes. The follow-up: monitor deletion rates to catch such bugs before users notice.
> > In both, rehearsal mattered. In the second, detection came late, from a user.
**COACH:** Two case studies. In Gmail in two thousand eleven, a significant amount of user data disappeared despite many safeguards. The offline backup system was used for its largest ever restore. It worked partly because similar restores had been simulated many times before.
**COACH:** In the music service in two thousand twelve, a user reported that tracks were being skipped. Engineers traced it to missing references, and then to a runaway deletion bug. Recovery meant reading data from thousands of offline tapes, which raises its own logistics questions. The follow-up was monitoring and alerting on large-scale deletions, to catch such bugs before users notice. In that story the problem was found late, by a user, and that is exactly what early detection is for.

### Slide 16 · The trap — Backups you have never restored   `[panel · trap]`
> A backup that has never been restored is a hypothesis.
> Restore regularly, from the real backup files, in an environment the size of the real thing, and check the result with the validators.
> Measure the time, and publish it. If it breaks the objective, that is an incident, before the incident.
**ASIDE:** The trap is backups you have never restored. A backup that has never been restored is a hypothesis. Restore regularly, from the real files, in an environment the size of the real thing, and check the result with the validators. Measure the time, and publish it. If it breaks the objective, treat that as an incident now, before the real one.


## 13.4 Then and now

### Slide 17 · Since 2016 — The threat model widened, the tools improved   `[panel · now]`
> Ransomware and malicious deletion are now a main scenario: keep backups immutable and in a separate account or trust boundary, so a compromised credential cannot erase them.
> Point-in-time recovery, object versioning and retention locks are standard storage features, but check that they are turned on, and tested.
> Privacy law adds a tension: soft deletion must be bounded, and a hard delete must really happen. Document the window.
> End-to-end checksums and scrubbing are common in storage systems, and erasure coding replaced much simple replication for cold data.
**ASIDE:** What has changed since 2016? The threat model widened. Ransomware and malicious deletion are now a main scenario, so keep backups immutable and in a separate account or trust boundary, so that a compromised credential cannot erase them. Point-in-time recovery, object versioning and retention locks are standard storage features, but check that they are switched on, and tested. Privacy law adds a tension: soft deletion must be bounded, and a hard delete must really happen, so document the window. And end-to-end checksums and scrubbing are common, with erasure coding in place of simple replication for cold data.


## 13.5 Probe drills

### Slide 18 · Interviewer probe — We replicate across three regions. Why do we need backups?   `[probe]`
**INTERVIEWER:** We replicate across three regions. Why do we need backups?
*A strong answer on screen:*
> - Replication copies a bad write or a deletion to all copies, within seconds
> - It protects against hardware or site loss, not logic errors or malicious acts
> - Backups give an older, separate copy to restore from
> - Plus soft deletion and validation to notice early
**CANDIDATE:** Because replication copies mistakes. A bad write or a deletion reaches all three regions in seconds. Replication protects against hardware or site loss, not against a bug or a malicious act. A backup is an older, separate copy that can be restored to a point before the damage. And I add soft deletion for fast undo, and validation to notice early enough that a restore point still exists.

### Slide 19 · Interviewer probe — An application bug has been silently corrupting a field for two days. What do you do?   `[probe]`
**INTERVIEWER:** An application bug has been silently corrupting a field for two days. What do you do?
*A strong answer on screen:*
> - Stop it: fix or disable the bug, freeze the bad path
> - Find the blast radius: which records, which time range
> - Restore the affected records to a point in time, or recompute from the source of truth
> - Reconcile with changes since: this is the hard part
> - Add a validator so it cannot return silently
**CANDIDATE:** First stop the damage: fix or disable the bug. Then find the blast radius, which records and which time range, using the logs. Then repair: restore the affected records to a point before the corruption, or recompute them from a source of truth. The hard part is reconciling with legitimate changes made since. And finally, add a validator that would have caught it, so it cannot happen silently again.

### Slide 20 · Interviewer probe — How would you test that your backups work?   `[probe]`
**INTERVIEWER:** How would you test that your backups work?
*A strong answer on screen:*
> - Restore them, on a schedule, into a test environment
> - Check the restored data with the same validators used in production
> - Measure the restore time against the objective
> - Include the human steps: access, keys, runbooks
> - Record failures as incidents
**CANDIDATE:** By restoring them, regularly, on a schedule, into a test environment. I check the restored data with the same validators that run in production, and I measure the restore time against the objective. I include the human steps: who has access, where the keys are, which runbook to follow. And any failure is recorded as an incident, and fixed.


## 13.6 Where this shows up

### Slide 21 · Where this shows up — Read, watch and build next   `[list]`
> ~ Design-room course part 13 covers reliability patterns, including reconciliation and disaster recovery, and part 7 covers storage.
> - Episode 11: the consensus state that holds metadata
> - Episode 14: launches that must not lose data
> - Google's SRE books: the chapter on data integrity, with the Gmail case study
> - Also: the reliability pillar of your cloud provider's architecture framework
**COACH:** Next steps. Part thirteen of the design-room course covers reliability patterns, including reconciliation and disaster recovery, and part seven covers storage. Episode eleven covered the consensus state that holds metadata, and episode fourteen is about launches that must not lose data. Google's free S-R-E books cover it, especially the Gmail case study, and the reliability guidance of your cloud provider's architecture framework.

