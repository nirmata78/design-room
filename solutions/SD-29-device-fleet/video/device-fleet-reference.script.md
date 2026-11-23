# SD-29 Device-fleet control plane: reference solution (Staff L6/L7, compact cut)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: API=A-P-I SDK=S-D-K TB=terabytes PB=petabytes GB=gigabytes HTTP=H-T-T-P HTTPS=H-T-T-P-S ID=I-D IDs=I-Ds MQTT=M-Q-T-T mTLS=M-T-L-S TLS=T-L-S CDN=C-D-N EMQX=E-M-Q-X HSM=H-S-M PKI=P-K-I QoS=Q-O-S IoT=I-o-T TSDB=T-S-D-B URL=U-R-L CPU=C-P-U CPUs=C-P-Us GPU=G-P-U GPUs=G-P-Us Kafka=Kahf-kah ClickHouse=Click-House GCS=G-C-S MCAP=M-cap SHA-256=shaw-two-fifty-six DAG=dag Kueue=queue Bigtable=Big-table CI=C-I EM=E-M -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: Pushing configuration to devices sounds like a message queue. It's asked at Google, Amazon and Microsoft, and at every company with hardware in the field, because the devices are offline when you need them, untrusted, impossible to reach physically, and alive for seven years. A bad push is a fleet-wide outage with a schedule.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Design the control plane for a million devices in the field. Know their state, push configuration and software to them, and do it without bricking the fleet.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: The hook. Move fast: push to everyone in a day, and a bad image bricks a million devices. At a hundred and fifty dollars a truck roll, that's a hundred and fifty million dollars.
C: Move never, and seven years of devices run unpatched software. The design lives in the third box: move in waves that start with every kind of hardware, stop themselves on a bad signal, and devices that roll themselves back without anyone reaching them.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes.
[reveal: v-005]
[pause: 0.45]
N: Requirements: the strong answer asks how often devices are offline and what a bricked device costs.
[reveal: v-006]
[pause: 0.45]
N: Correctness: not commands to online devices, but desired against reported state, reconciled.
[reveal: v-007]
[pause: 0.45]
N: Safety: not a percentage watched by a person, but cohorts, an automatic halt, and devices that roll back on their own.
[reveal: v-008]
[pause: 0.45]
N: Depth: identity per device, signed images, jittered backoff, admission control.
[reveal: v-009]
[pause: 0.45]
N: Operations: convergence time and a version census, not the connected-device count.
[reveal: v-010]
[pause: 0.45]
C: And the rule for the round: design for the device you can't reach, not the one that's online.
[pause: 1.0]

[slide: v-011]
[pause: 0.7]
V: Never send a device a command. Publish a desired state it converges to whenever it can. Release in waves that halt themselves, and give every device a last known good it returns to on its own.
[pause: 1.6]

[slide: v-012]
[pause: 0.6]
C: The order I'll follow.
[reveal: v-013]
[pause: 0.45]
C: First, requirements, the dangerous numbers, and the theory: reconciliation, identity, waves, A-B partitions and backoff.
[reveal: v-014]
[pause: 0.45]
C: Then the interfaces and the data, three versions on one picture, every path, and three containers opened up.
[reveal: v-015]
[pause: 0.45]
C: Then six challenges, from a device that can't boot to a fleet that never converges.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-016]
[pause: 1.2]
C: The scale first, then five questions.
[pause: 1.8]

[slide: v-017]
[pause: 0.6]
C: The scale.
[reveal: v-018]
[pause: 0.45]
C: A million devices, a firmware release a month and about thirty configuration changes.
[reveal: v-019]
[pause: 0.45]
C: Each lives seven years in the field, and sends a health report every five minutes: about eight point six billion a month.
[reveal: v-020]
[pause: 0.45]
C: And the peak: a regional internet provider recovers, and two hundred thousand devices reconnect in the same minute.
[reveal: v-021]
[pause: 0.45]
C: Every number later starts from these.
[pause: 0.8]

[slide: v-022]
[pause: 0.6]
C: How often are devices offline?
[reveal: v-023]
[pause: 0.45]
I: Intermittently every day. Some for weeks.
C: Then nothing can depend on a device being online when we act. A device must catch up on its own.
[pause: 0.6]

[slide: v-024]
[pause: 0.6]
C: What does a device that won't boot cost us?
[reveal: v-025]
[pause: 0.45]
I: A truck roll: about a hundred and fifty dollars, and a day for the customer.
C: That sets the blast-radius budget for a release. A hundred devices is fifteen thousand dollars; a percent of the fleet is a million and a half.
[pause: 0.6]

[slide: v-026]
[pause: 0.6]
C: How different are the devices from each other?
[reveal: v-027]
[pause: 0.45]
I: Five hardware revisions, three cellular carriers, every region.
C: So a percentage isn't a sample. The first wave must contain every combination that can fail differently.
[pause: 0.6]

[slide: v-028]
[pause: 0.6]
C: Can we trust what a device sends?
[reveal: v-029]
[pause: 0.45]
I: No. Assume any device can be stolen and taken apart.
C: Identity per device, from manufacture, and a device can touch only its own state.
[pause: 0.6]

[slide: v-030]
[pause: 0.6]
C: What's in scope?
[reveal: v-031]
[pause: 0.45]
I: Configuration, firmware, state and health. Not the application data the devices produce.
C: That's the control plane. The data plane is someone else's pipeline, like question ninety-seven's.
[pause: 0.6]

[slide: v-032]
[pause: 0.6]
C: Four functional requirements.
[reveal: v-033]
[pause: 0.45]
C: One, know every device's reported state and health.
[reveal: v-034]
[pause: 0.45]
C: Two, configure a device or a cohort, and devices converge when they can.
[reveal: v-035]
[pause: 0.45]
C: Three, release signed firmware in waves, each soaked and compared before the next.
[reveal: v-036]
[pause: 0.45]
C: Four, stop: halt and revert a bad change automatically, including on devices that can't even boot it.
[pause: 0.8]

[slide: v-037]
[pause: 0.6]
C: The numbers.
[reveal: v-038]
[pause: 0.45]
C: At most a hundred devices harmed by any one release: fifteen thousand dollars.
[reveal: v-039]
[pause: 0.45]
C: Ninety-five percent of online devices on a new config within a day.
[reveal: v-040]
[pause: 0.45]
C: A full firmware release in about two weeks.
[reveal: v-041]
[pause: 0.45]
C: Three nines for the control plane, because devices don't need it to run.
[reveal: v-042]
[pause: 0.45]
C: If it's down, devices keep running their last good state. That's static stability.
[pause: 0.8]

[slide: v-043]
[pause: 0.6]
C: In scope: identity and sessions, desired and reported state, configurations, firmware waves and halts, the recovery on the device, and fleet health.
[reveal: v-044]
[pause: 0.45]
C: Out, on purpose: the application data the devices produce, manufacturing, running the P-K-I itself, billing, customer dashboards.
[reveal: v-045]
[pause: 0.45]
C: The data plane is a different system with a different budget. Question ninety-seven is its question.
[pause: 0.8]

[slide: v-046]
[pause: 1.3]
C: The context.
[reveal: v-047]
[pause: 0.45]
C: A million devices in the field, often offline, and a truck roll away.
[reveal: v-048]
[pause: 0.45]
C: The fleet platform, one box.
[reveal: v-049]
[pause: 0.45]
C: Operators change configuration and release firmware.
[reveal: v-050]
[pause: 0.45]
C: The factory P-K-I gives every device a key at manufacture.
[reveal: v-051]
[pause: 0.45]
C: And a C-D-N serves signed firmware images.
[pause: 1.1]

[slide: v-052]
[pause: 0.7]
V: The core is three things. A shadow of desired and reported state. A rollout that halts itself. And a device that recovers itself.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-053]
[pause: 1.2]
C: Numbers next, each from the scale line. Illustrative.
[pause: 1.8]

[slide: v-054]
[pause: 1.0]
C: Steady state.
[reveal: v-055]
[pause: 0.45]
C: A million devices every five minutes is about thirty-three hundred health reports a second, three megabytes a second. Small.
[reveal: v-056]
[pause: 0.45]
C: A million persistent connections at a hundred thousand per node is ten nodes; I'd run twenty.
[reveal: v-057]
[pause: 0.45]
C: And the shadow: four kilobytes per device is four gigabytes. One PostgreSQL with a standby.
[pause: 1.0]

[slide: v-058]
[pause: 1.0]
C: The dangerous numbers.
[reveal: v-059]
[pause: 0.45]
C: Two hundred thousand reconnects in a minute is thirty-three hundred a second. If they all retry at once, in five seconds, forty thousand a second, each a T-L-S handshake. That decides jitter and admission control.
[reveal: v-060]
[pause: 0.45]
C: A release: fifty megabytes to a million devices is fifty terabytes; with delta images, eight. A C-D-N, never the brokers.
[reveal: v-061]
[pause: 0.45]
C: Bricking one percent costs a million and a half dollars. So waves, with a blast-radius budget of a hundred devices.
[reveal: v-062]
[pause: 0.45]
C: And seven years of monthly releases is up to eighty-four versions in the field. The server must keep speaking every protocol it ever shipped.
[pause: 1.0]

[slide: v-063]
[pause: 1.0]
C: Identity has numbers too.
[reveal: v-064]
[pause: 0.45]
C: A million certificates valid for two years is about fourteen hundred renewals a day. They must renew themselves, over the session, without a person.
[reveal: v-065]
[pause: 0.45]
C: A device offline when its certificate expired comes back with an expired key. A grace window lets it renew; past that, a re-enrolment path signed with the factory key.
[reveal: v-066]
[pause: 0.45]
C: And a stolen device's key reaches only its own topics. Revoking one certificate changes nothing else.
[pause: 1.0]

[slide: v-067]
[pause: 1.3]
C: The release budget. Two days for waves zero and one, two for wave two, a day waiting for a person's approval, two for wave three, three for the rest: about ten days of fourteen.
C: The spare is for a halted wave, which is the normal case for one release in five, not an emergency.
[pause: 1.1]

[pause: 1.4]

## 3 Theory

[slide: v-068]
[pause: 1.2]
C: The theory: what makes this hard, beyond product names. Five mechanisms, the options, what will go wrong.
[pause: 1.8]

[slide: v-069]
[pause: 0.6]
C: What it is, and what it isn't.
[reveal: v-070]
[pause: 0.45]
V: Keeping a million unreachable, untrusted devices converging to a desired state, safely.
[reveal: v-071]
[pause: 0.45]
C: Not a message bus: a bus delivers to whoever is listening, and most devices aren't.
[reveal: v-072]
[pause: 0.45]
C: Not telemetry: health is only the signal for decisions here.
[reveal: v-073]
[pause: 0.45]
C: And not app deployment: a server can be replaced; a device must survive its own bad update.
[pause: 0.8]

[slide: v-074]
[pause: 0.6]
C: Safety.
[reveal: v-075]
[pause: 0.45]
V: S-one: no update leaves a device unable to boot a working image.
[reveal: v-076]
[pause: 0.45]
V: S-two: a device runs only signed images, and accepts only its own desired state.
[reveal: v-077]
[pause: 0.45]
V: S-three: a bad release reaches at most its first wave.
[reveal: v-078]
[pause: 0.45]
C: Liveness: L-one, every device that comes online converges to the latest desired state.
[reveal: v-079]
[pause: 0.45]
C: L-two, a good release finishes in about two weeks. Being too careful is also a failure.
[pause: 0.8]

[slide: v-080]
[pause: 0.6]
C: Mechanism one: desired and reported state, reconciled.
[reveal: v-081]
[pause: 0.45]
C: It protects L-one.
[reveal: v-082]
[pause: 0.45]
C: Each device has a versioned desired document and a reported one. The device pulls the latest desired state whenever it connects and applies all of it. A reconciler nudges devices whose reported version lags.
[reveal: v-083]
[pause: 0.45]
C: It rules out commands lost to offline devices, and replaying a queue of stale changes.
[reveal: v-084]
[pause: 0.45]
C: It costs this: the device must apply a whole state, not a delta.
[pause: 0.8]

[slide: v-085]
[pause: 0.6]
C: Mechanism two: identity per device, and signed images.
[reveal: v-086]
[pause: 0.45]
C: It protects S-two.
[reveal: v-087]
[pause: 0.45]
C: Each device gets a key pair at the factory, presents its certificate on every connection, and may touch only topics with its own I-D. Firmware is signed offline, and the device verifies the signature before writing it.
[reveal: v-088]
[pause: 0.45]
C: It rules out one stolen device reaching the others, and a compromised C-D-N installing code.
[reveal: v-089]
[pause: 0.45]
C: It costs a P-K-I and a signing ceremony.
[pause: 0.8]

[slide: v-090]
[pause: 0.6]
C: Mechanism three: waves by cohort, with an automatic halt.
[reveal: v-091]
[pause: 0.45]
C: It protects S-three, and L-two.
[reveal: v-092]
[pause: 0.45]
C: Release to a small wave that contains every hardware revision, region and carrier. Soak it, compare its health with a control group, and halt automatically when the difference is real.
[reveal: v-093]
[pause: 0.45]
C: It rules out a rare revision bricking at ten percent, and a person noticing too late.
[reveal: v-094]
[pause: 0.45]
C: It costs days of soak, and a statistic people must trust.
[pause: 0.8]

[slide: v-095]
[pause: 0.6]
C: Mechanism four, the crux of S-one: A-B partitions with a watchdog.
[reveal: v-096]
[pause: 0.45]
C: It protects S-one.
[reveal: v-097]
[pause: 0.45]
C: The new image goes into the inactive slot. The bootloader boots it with a try counter. The agent must confirm it's healthy, which includes reaching the server, before a hardware watchdog fires. If it doesn't, the counter runs out and the bootloader returns to the last good slot.
[reveal: v-098]
[pause: 0.45]
C: It rules out a crash loop that no server can reach.
[reveal: v-099]
[pause: 0.45]
C: It costs twice the flash, and a slower first boot.
[pause: 0.8]

[slide: v-100]
[pause: 0.6]
C: Mechanism five: jittered backoff and admission control.
[reveal: v-101]
[pause: 0.45]
C: It protects L-one and the control plane itself.
[reveal: v-102]
[pause: 0.45]
C: A device retries after a random delay up to a growing cap. Brokers admit new connections through a token bucket per node and answer later, with a hint, when it's empty.
[reveal: v-103]
[pause: 0.45]
C: It rules out two hundred thousand devices retrying in step and keeping the cluster down.
[reveal: v-104]
[pause: 0.45]
C: It costs a slower recovery for some devices.
[pause: 0.8]

[slide: v-105]
[pause: 1.3]
C: Mechanism four at protocol level.
[reveal: v-106]
[pause: 0.45]
C: The bootloader marks slot B to try, three tries left.
[reveal: v-107]
[pause: 0.45]
C: It boots version four point three.
[reveal: v-108]
[pause: 0.45]
C: The agent must confirm it's healthy within a hundred and twenty seconds.
[reveal: v-109]
[pause: 0.45]
C: It doesn't. The watchdog resets the device: two tries, one, none.
[reveal: v-110]
[pause: 0.45]
C: Tries exhausted: boot version four point two from slot A.
[reveal: v-111]
[pause: 0.45]
C: And report that it rolled back. No server was involved.
[pause: 1.1]

[slide: v-112]
[pause: 1.0]
C: One idea under mechanism one is worth its own slide: edge against level.
[reveal: v-113]
[pause: 0.45]
C: An edge-triggered system sends events: change the display to eco. A level-triggered one publishes state: the desired state is version eighteen.
[reveal: v-114]
[pause: 0.45]
C: A device offline for a week misses events, or replays a queue. With state, it reads eighteen when it returns.
[reveal: v-115]
[pause: 0.45]
C: A lost event is a lost change. A lost state message is caught by the next comparison.
[reveal: v-116]
[pause: 0.45]
C: And a duplicate event is applied twice unless you're careful; version eighteen twice is a no-op. That's why every loop in this design compares, then converges.
[pause: 1.0]

[slide: v-117]
[pause: 1.0]
C: Five ways.
[reveal: v-118]
[pause: 0.45]
C: A: the server pushes commands. A device offline at that moment misses them.
[reveal: v-119]
[pause: 0.45]
C: B: devices poll a configuration U-R-L. No versions, no reported state, no rollback.
[reveal: v-120]
[pause: 0.45]
C: C: a shadow and reconciliation, pushed to everyone at once. One bad image reaches the fleet in a day.
[reveal: v-121]
[pause: 0.45]
C: D: waves by percentage with a person watching. A rare hardware revision isn't in one percent, and people are slow.
[reveal: v-122]
[pause: 0.45]
C: E, which I pick: a shadow, waves by cohort with an automatic halt, and A-B partitions with a watchdog.
[reveal: v-123]
[pause: 0.45]
V: Converge when you can, release in steps that stop themselves, and recover without help.
[pause: 1.0]

[slide: v-124]
[pause: 1.0]
C: The failure catalogue.
[reveal: v-125]
[pause: 0.45]
C: One: a config that crashes the device on boot.
[reveal: v-126]
[pause: 0.45]
C: Two: a release that bricks one rare hardware revision.
[reveal: v-127]
[pause: 0.45]
C: Three: a device offline for six weeks and four changes.
[reveal: v-128]
[pause: 0.45]
C: Four: two hundred thousand reconnects in a minute.
[reveal: v-129]
[pause: 0.45]
C: Five: buffered telemetry arriving twice.
[reveal: v-130]
[pause: 0.45]
C: Six: every device connected, and the fleet not converging.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-131]
[pause: 1.2]
C: The interfaces, then the data.
[pause: 1.8]

[slide: v-132]
[pause: 1.0]
C: The desired document a device pulls, for F-R-two and three. It's the whole state, with a version, not a command.
C: Three lines matter. The version, so a device knows whether it's current. The image's hash and offline signature, which the device checks before writing anything. And the minimum firmware the configuration needs, so a device on an old image doesn't apply a config it can't run.
[pause: 1.0]

[slide: v-133]
[pause: 1.0]
C: The reported document, for F-R-one. What the device runs: version, firmware and active slot.
C: The lines that matter. The config it applied. What it rejected, and why, which is how the rollout controller learns about a crash loop it could never see. And a sequence and epoch, so a resend is recognised as one.
[pause: 1.0]

[slide: v-134]
[pause: 1.0]
C: Three more.
[reveal: v-135]
[pause: 0.45]
C: Reported state, from each device: what it applied, what it runs, and what it rejected.
[reveal: v-136]
[pause: 0.45]
C: Desired state for a cohort, from an operator, with if-match on the version, so two operators can't overwrite each other.
[reveal: v-137]
[pause: 0.45]
C: And a release: an image and a wave plan. Halting doesn't need a call; the controller does it.
[pause: 1.0]

[slide: v-138]
[pause: 1.3]
C: The conceptual model.
[reveal: v-139]
[pause: 0.45]
C: A device, with its hardware revision.
[reveal: v-140]
[pause: 0.45]
C: In a cohort.
[reveal: v-141]
[pause: 0.45]
C: A device wants a desired document: a weak entity, identified by the device and a version.
[reveal: v-142]
[pause: 0.45]
C: And reports a reported document, also versioned.
[reveal: v-143]
[pause: 0.45]
C: Releases target cohorts.
[reveal: v-144]
[pause: 0.45]
C: And ship one signed image.
[pause: 1.1]

[slide: v-145]
[pause: 1.3]
C: The physical tables.
[reveal: v-146]
[pause: 0.45]
C: Device: cohort, hardware revision, desired and reported versions. Drift is desired version greater than reported.
[reveal: v-147]
[pause: 0.45]
C: Desired documents, append-only, so a rollback is writing an old document as a new version.
[reveal: v-148]
[pause: 0.45]
C: Releases, owned by the rollout controller.
[reveal: v-149]
[pause: 0.45]
C: Waves: soak, compare, continue or halt.
[reveal: v-150]
[pause: 0.45]
C: Reported documents, including what the device rejected.
[reveal: v-151]
[pause: 0.45]
C: And telemetry in the time-series store, labelled by cohort, never by device.
[pause: 1.1]

[pause: 1.4]

## 5 High-level design

[slide: v-152]
[pause: 1.2]
C: The design in three versions, on one picture that only changes by deltas.
[pause: 1.8]

[slide: v-153]
[pause: 1.3]
C: Version one.
[reveal: v-154]
[pause: 0.45]
C: A device agent on every device.
[reveal: v-155]
[pause: 0.45]
C: Connected to a device gateway, an MQTT broker, over mutual T-L-S.
[reveal: v-156]
[pause: 0.45]
C: Reported state lands in a shadow store; desired state is read from it.
[reveal: v-157]
[pause: 0.45]
C: A fleet A-P-I writes desired state.
[reveal: v-158]
[pause: 0.45]
C: For operators. The objection: a device offline when the change happens only gets it if it asks, and nothing tells us how healthy anything is.
[pause: 1.1]

[slide: v-159]
[pause: 1.3]
C: Version two.
[reveal: v-160]
[pause: 0.45]
C: Version one, carried.
[reveal: v-161]
[pause: 0.45]
C: New, a reconciler: it finds devices whose reported version lags, and nudges them.
[reveal: v-162]
[pause: 0.45]
C: New, telemetry: health summaries every five minutes.
[reveal: v-163]
[pause: 0.45]
C: New, a metrics store, labelled by cohort. The objection: a firmware release still goes to everyone at once.
[pause: 1.1]

[slide: v-164]
[pause: 1.3]
C: Version three.
[reveal: v-165]
[pause: 0.45]
C: Version two, carried.
[reveal: v-166]
[pause: 0.45]
C: New, a rollout controller: it writes desired firmware wave by wave, and reads each wave's health against a control.
[reveal: v-167]
[pause: 0.45]
C: New, an image C-D-N: devices fetch signed images there, never through the brokers. This is the baseline.
[pause: 1.1]

[slide: v-168]
[pause: 1.0]
C: The containers.
[reveal: v-169]
[pause: 0.45]
C: The device agent: applying the whole state, the A-B slots and the watchdog. A million of them.
[reveal: v-170]
[pause: 0.45]
C: The gateway: sessions, identity, and desired-state reads. Twenty nodes.
[reveal: v-171]
[pause: 0.45]
C: The shadow store: desired and reported, versioned. Four gigabytes.
[reveal: v-172]
[pause: 0.45]
C: The reconciler: finds drift and nudges it, gently, spread over minutes.
[reveal: v-173]
[pause: 0.45]
C: The rollout controller: waves, soak, compare, halt.
[reveal: v-174]
[pause: 0.45]
C: And telemetry and metrics: health, by cohort.
[pause: 1.0]

[slide: v-175]
[pause: 1.3]
C: A configuration change, numbered.
[reveal: v-176]
[pause: 0.45]
C: One: the operator changes it.
[reveal: v-177]
[pause: 0.45]
C: Two: the A-P-I writes desired version eighteen, if seventeen.
[reveal: v-178]
[pause: 0.45]
C: Three: the reconciler finds the drift.
[reveal: v-179]
[pause: 0.45]
C: Four: it nudges the gateway, spread over ten minutes.
[reveal: v-180]
[pause: 0.45]
C: Five: the device reads desired state.
[reveal: v-181]
[pause: 0.45]
C: Six: it reports version eighteen applied.
[pause: 1.1]

[slide: v-182]
[pause: 1.3]
C: A release, numbered.
[reveal: v-183]
[pause: 0.45]
C: One: the operator starts it.
[reveal: v-184]
[pause: 0.45]
C: Two: the controller writes desired firmware for wave one.
[reveal: v-185]
[pause: 0.45]
C: Three: devices in the wave read it.
[reveal: v-186]
[pause: 0.45]
C: Four: they fetch the signed image from the C-D-N.
[reveal: v-187]
[pause: 0.45]
C: Five: they report health.
[reveal: v-188]
[pause: 0.45]
C: Six: by cohort and wave.
[reveal: v-189]
[pause: 0.45]
C: Seven: the controller compares the wave with the control, and continues or halts.
[pause: 1.1]

[slide: v-190]
[pause: 1.3]
C: Know, as a sequence.
[reveal: v-191]
[pause: 0.45]
C: The agent reports: firmware four point two, config seventeen.
[reveal: v-192]
[pause: 0.45]
C: Into the shadow, as reported version seventeen.
[reveal: v-193]
[pause: 0.45]
C: Every five minutes a health summary, with a sequence number.
[reveal: v-194]
[pause: 0.45]
C: Into Kafka, keyed by device.
[reveal: v-195]
[pause: 0.45]
C: A repeated sequence is dropped. Challenge five.
[pause: 1.1]

[slide: v-196]
[pause: 1.3]
C: Configure, as a sequence.
[reveal: v-197]
[pause: 0.45]
C: The operator writes version eighteen for a cohort, if the current one is seventeen.
[reveal: v-198]
[pause: 0.45]
C: The reconciler finds rows where desired is ahead of reported.
[reveal: v-199]
[pause: 0.45]
C: It nudges forty thousand devices, spread over ten minutes.
[reveal: v-200]
[pause: 0.45]
C: A device asks for desired state, saying it has seventeen.
[reveal: v-201]
[pause: 0.45]
C: It gets eighteen.
[reveal: v-202]
[pause: 0.45]
C: It applies it, and if that fails, keeps seventeen.
[reveal: v-203]
[pause: 0.45]
C: And reports eighteen.
[pause: 1.1]

[slide: v-204]
[pause: 1.3]
C: Release, as a sequence.
[reveal: v-205]
[pause: 0.45]
C: Wave one: a thousand devices, every hardware revision, firmware four point three.
[reveal: v-206]
[pause: 0.45]
C: A device fetches the image by range, and verifies the signature and hash.
[reveal: v-207]
[pause: 0.45]
C: Writes slot B, reboots into it, and has a hundred and twenty seconds to confirm health.
[reveal: v-208]
[pause: 0.45]
C: It reports four point three, healthy.
[reveal: v-209]
[pause: 0.45]
C: After a day, the wave is compared with a control.
[reveal: v-210]
[pause: 0.45]
C: Crashes point two one percent against point two zero: the next wave.
[pause: 1.1]

[slide: v-211]
[pause: 1.0]
C: Before the stop sequence, what a halt costs, because it decides who is allowed to make it.
[reveal: v-212]
[pause: 0.45]
C: A false halt costs a day of soak and a person reading a report. The controller halts on its own; a person resumes.
[reveal: v-213]
[pause: 0.45]
C: A real halt in wave one costs at most fifty devices, and they revert by themselves.
[reveal: v-214]
[pause: 0.45]
C: No halt, with a bad release at ten percent, is up to a hundred thousand devices: fifteen million dollars if they brick. So stopping never waits for a person.
[pause: 1.0]

[slide: v-215]
[pause: 1.3]
C: Stop, as a sequence.
[reveal: v-216]
[pause: 0.45]
C: Wave two reconnects three times as often as the control.
[reveal: v-217]
[pause: 0.45]
C: The halt rule fires: no new devices get the release.
[reveal: v-218]
[pause: 0.45]
C: Wave two's desired firmware goes back to four point two, as a new version.
[reveal: v-219]
[pause: 0.45]
C: Devices read it.
[reveal: v-220]
[pause: 0.45]
C: And slot A still holds four point two: switch and reboot. Nobody was paged to make that happen; somebody was paged to look at it.
[pause: 1.1]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-221]
[pause: 1.2]
C: One level down: what each box runs on, three containers opened up, and what I rejected.
[pause: 1.8]

[slide: v-222]
[pause: 1.3]
C: The same view, with technologies.
[reveal: v-223]
[pause: 0.45]
C: The agent: C, on the device, with A-B slots and a watchdog.
[reveal: v-224]
[pause: 0.45]
C: The gateway: an E-M-Q-X cluster speaking MQTT five over mutual T-L-S.
[reveal: v-225]
[pause: 0.45]
C: The shadow store: PostgreSQL.
[reveal: v-226]
[pause: 0.45]
C: The reconciler: a Go service.
[reveal: v-227]
[pause: 0.45]
C: The rollout controller: a Go service.
[reveal: v-228]
[pause: 0.45]
C: Telemetry: Kafka.
[reveal: v-229]
[pause: 0.45]
C: Metrics: Victoria Metrics, by cohort.
[pause: 1.1]

[slide: v-230]
[pause: 1.3]
C: Inside the device agent.
[reveal: v-231]
[pause: 0.45]
C: The gateway.
[reveal: v-232]
[pause: 0.45]
C: The MQTT client, with jittered backoff and session resume.
[reveal: v-233]
[pause: 0.45]
C: A kill switch on a separate, minimal path: a signed instruction it will act on even if everything else is broken.
[reveal: v-234]
[pause: 0.45]
C: A telemetry buffer: store and forward, a sequence number per message.
[reveal: v-235]
[pause: 0.45]
C: The config applier: latest version wins.
[reveal: v-236]
[pause: 0.45]
C: The updater fetches from the C-D-N, verifies, and writes the inactive slot.
[reveal: v-237]
[pause: 0.45]
C: The bootloader with its try counter.
[reveal: v-238]
[pause: 0.45]
C: The watchdog: a hardware timer.
[reveal: v-239]
[pause: 0.45]
C: And the two slots. Challenges one, three and five live here.
[pause: 1.1]

[slide: v-240]
[pause: 1.3]
C: Inside the rollout controller.
[reveal: v-241]
[pause: 0.45]
C: A release from the fleet A-P-I.
[reveal: v-242]
[pause: 0.45]
C: The release plan: waves of point one, one, ten and a hundred percent.
[reveal: v-243]
[pause: 0.45]
C: The cohort picker: every hardware revision, region and carrier in the early waves.
[reveal: v-244]
[pause: 0.45]
C: The wave scheduler, with soak timers.
[reveal: v-245]
[pause: 0.45]
C: An approval gate: a person before ten percent.
[reveal: v-246]
[pause: 0.45]
C: The health comparer, wave against control, from the metrics store.
[reveal: v-247]
[pause: 0.45]
C: The halt rule: stop, then revert.
[reveal: v-248]
[pause: 0.45]
C: Writing the shadow store. Challenge two lives here.
[pause: 1.1]

[slide: v-249]
[pause: 1.3]
C: Inside the gateway.
[reveal: v-250]
[pause: 0.45]
C: Devices.
[reveal: v-251]
[pause: 0.45]
C: The T-L-S terminator checks a certificate per device.
[reveal: v-252]
[pause: 0.45]
C: Admission control: a token bucket per node.
[reveal: v-253]
[pause: 0.45]
C: Sessions that survive seven days of disconnection.
[reveal: v-254]
[pause: 0.45]
C: A desired-state cache keyed by version: a current device costs one comparison.
[reveal: v-255]
[pause: 0.45]
C: A bridge to Kafka.
[reveal: v-256]
[pause: 0.45]
C: And the shadow store behind it. Challenge four lives here.
[pause: 1.1]

[slide: v-257]
[pause: 1.0]
C: About 100,000 connections per node, 20 nodes. Each device presents its factory certificate; topics are scoped to its own ID.
[reveal: v-258]
[pause: 0.45]
C: Why: A small, battery-friendly protocol with persistent sessions and a device identity checked at the handshake.
[reveal: v-259]
[pause: 0.45]
C: Rejected: HTTP polling. Every device polls whether or not anything changed.
[reveal: v-260]
[pause: 0.45]
C: Kafka on devices. A server-side log, not a device protocol.
[pause: 1.0]

[slide: v-261]
[pause: 1.0]
C: One row per device: desired and reported JSON with versions. Writers use WHERE desired_v = $read.
[reveal: v-262]
[pause: 0.45]
C: Why: 1 M rows of a few kilobytes is small.
[reveal: v-263]
[pause: 0.45]
C: Rejected: Redis. A lost write is a device told something nobody can see.
[reveal: v-264]
[pause: 0.45]
C: A replayed change log. Six weeks offline means four obsolete configs.
[pause: 1.0]

[slide: v-265]
[pause: 1.0]
C: The desired document names the URL, size, SHA-256 and an offline signature. The agent fetches by range, resumes, and verifies before writing.
[reveal: v-266]
[pause: 0.45]
C: Why: 50 TB per release must not cross the gateway.
[reveal: v-267]
[pause: 0.45]
C: Rejected: Images through the brokers. 50 TB crowds out every control message.
[reveal: v-268]
[pause: 0.45]
C: Trusting TLS to the CDN. TLS proves the server, not the image.
[pause: 1.0]

[slide: v-269]
[pause: 1.0]
C: Summaries every 5 minutes with a per-device sequence; repeats dropped; metrics labelled by cohort, firmware and wave.
[reveal: v-270]
[pause: 0.45]
C: Why: Rollout decisions compare cohorts and waves.
[reveal: v-271]
[pause: 0.45]
C: Rejected: Device ID as a label. 1 M series per metric.
[reveal: v-272]
[pause: 0.45]
C: Scraping devices. Behind NAT and often offline.
[pause: 1.0]

[slide: v-273]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
[reveal: v-274]
[pause: 0.45]
C: Device gateway: EMQX (MQTT 5), mTLS. Not HTTP polling, Kafka. Light sessions; identity at the handshake.
[reveal: v-275]
[pause: 0.45]
C: Shadow store: PostgreSQL. Not Redis, a change log replayed. Latest desired; versioned compare-and-set.
[reveal: v-276]
[pause: 0.45]
C: Firmware delivery: CDN + signed images. Not via brokers, TLS only. The device verifies what it runs.
[reveal: v-277]
[pause: 0.45]
C: Telemetry: Kafka to VictoriaMetrics. Not device labels, scraping. Cohort labels; per-device seq dedup.
[reveal: v-278]
[pause: 0.45]
N: Naming a product is not the signal. Naming the property that rules out its rival is. Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[pause: 1.4]

## 5.2 When you don't need all this

[slide: v-279]
[pause: 1.2]
C: Before I break it: a small fleet needs much less.
[pause: 1.8]

[slide: v-280]
[pause: 1.3]
C: The alternate path, on version three.
[reveal: v-281]
[pause: 0.45]
C: The reconciler goes.
[reveal: v-282]
[pause: 0.45]
C: And the rollout controller.
[reveal: v-283]
[pause: 0.45]
C: Instead, a managed I-o-T service holds the shadows, devices poll desired state hourly, and a release is three manual steps watched by a person.
[reveal: v-284]
[pause: 0.45]
C: What it gives up: automatic halts, cohorts built from strata, and convergence measured rather than hoped for. The A-B slots and the watchdog stay: those I'd never skip.
[pause: 1.1]

[slide: v-285]
[pause: 0.7]
C: Where's the line? Bricking one percent of five thousand devices is fifty truck rolls, seven and a half thousand dollars. Of a million, a million and a half.
V: Below about ten thousand devices, I'd ship a managed service and manual waves, and keep the A-B slots and the watchdog no matter what.
[pause: 1.6]

[pause: 1.4]

## 6 Bridge

[slide: v-286]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-287]
[pause: 1.3]
C: Version three, with the places it breaks.
[reveal: v-288]
[pause: 0.45]
C: The device agent: a config that crashes it on boot. Challenge one.
[reveal: v-289]
[pause: 0.45]
C: The rollout controller: a release that bricks one rare revision. Challenge two.
[reveal: v-290]
[pause: 0.45]
C: The shadow store: a device back after six weeks and four changes. Challenge three.
[reveal: v-291]
[pause: 0.45]
C: The gateway: two hundred thousand reconnects in a minute. Challenge four.
[reveal: v-292]
[pause: 0.45]
C: And telemetry: duplicates and a cardinality trap. Challenge five. Then, how would we know?
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-293]
[pause: 1.2]
C: Six challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks inside the container, the fix one level down, then the push on the fix itself, and what I would say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: A config that crashes the device

[slide: v-294]
[pause: 1.2]
N: Challenge one is the crux: the device you can no longer reach.
[pause: 1.8]

[slide: v-295]
[pause: 0.6]
I: You push a config that crashes the device on boot. It's now offline. What saves you?
[pause: 2.0]

[slide: v-296]
[pause: 1.3]
C: Inside the agent.
[reveal: v-297]
[pause: 0.45]
C: The config applier is marked.
[reveal: v-298]
[pause: 0.45]
C: The naive answer: push a rollback.
[reveal: v-299]
[pause: 0.45]
C: But the applier applied version eighteen and rebooted into a crash loop. The device never connects long enough to hear anything.
[pause: 1.1]

[slide: v-300]
[pause: 1.0]
C: The trace.
[reveal: v-301]
[pause: 0.45]
C: Nine o'clock, config eighteen to ten thousand devices in a store cohort.
[reveal: v-302]
[pause: 0.45]
C: Hardware revision three has no such display mode, and its driver crashes on boot.
[reveal: v-303]
[pause: 0.45]
C: Crash, reboot, crash. No connection, so no rollback.
[reveal: v-304]
[pause: 0.45]
C: Ten thousand truck rolls: a million and a half dollars.
[reveal: v-305]
[pause: 0.45]
C: Every server-side fix needs the device to connect, which is exactly what it can't do.
[pause: 1.0]

[slide: v-306]
[pause: 1.3]
C: The fix.
[reveal: v-307]
[pause: 0.45]
C: The bootloader.
[reveal: v-308]
[pause: 0.45]
C: And the slots.
[reveal: v-309]
[pause: 0.45]
C: One level down. A new config, like a new image, is pending until confirmed. The bootloader boots it with a try counter of three. The agent confirms only after it has reconnected and reported healthy, because a device that boots but can't talk to us is not healthy. Three failed boots, and the bootloader restores config seventeen and the image in slot A, and the device reports that it rejected eighteen.
[reveal: v-310]
[pause: 0.45]
C: It covers crash loops, hangs and a broken network stack. Not hardware damage.
[reveal: v-311]
[pause: 0.45]
C: Rejected: a server-side rollback command. A device that crashes on boot never connects to receive it.
[pause: 1.1]

[slide: v-312]
[pause: 1.3]
C: As a sequence.
[reveal: v-313]
[pause: 0.45]
C: Config eighteen arrives.
[reveal: v-314]
[pause: 0.45]
C: Applied as pending, then a reboot to take it.
[reveal: v-315]
[pause: 0.45]
C: The boot crashes; the watchdog resets; tries two, one, none.
[reveal: v-316]
[pause: 0.45]
C: Revert to config seventeen and the firmware in slot A.
[reveal: v-317]
[pause: 0.45]
C: And the report: rejected eighteen, crash loop. The rollout controller sees that within minutes.
[pause: 1.1]

[slide: v-318]
[pause: 1.0]
C: What exactly does the agent confirm? Healthy means still controllable, so four checks within a hundred and twenty seconds of boot.
[reveal: v-319]
[pause: 0.45]
C: The application process is up. The obvious one.
[reveal: v-320]
[pause: 0.45]
C: The network stack has an address. A device that boots offline can't be helped.
[reveal: v-321]
[pause: 0.45]
C: The gateway accepted our certificate. A broken T-L-S library is a brick with a power light.
[reveal: v-322]
[pause: 0.45]
C: And desired state was fetched and reported back: a full round trip. An agent that can't be updated again is the worst possible outcome, so it's the last thing checked before the new image becomes the last known good.
[pause: 1.0]

[slide: v-323]
[pause: 0.6]
I: The new firmware boots fine, but its agent has a bug: it never applies the next desired state.
[pause: 1.5]

[slide: v-324]
[pause: 0.6]
C: First, confirming means the device can still be updated: the confirmation needs a full round trip, fetching desired state and reporting it. A deaf agent never confirms, so it reverts.
[reveal: v-325]
[pause: 0.45]
C: Second, a kill switch below the agent: a tiny recovery client in the bootloader polls one signed U-R-L once a day, and acts on revert to slot A.
[reveal: v-326]
[pause: 0.45]
C: The honest limit: a bug that passes both and fails later needs the next release. That's why releases go in waves.
[pause: 0.8]

[slide: v-327]
[pause: 0.7]
V: If asked, I'd say: I'd never rely on a server to rescue a device. New configs and images are pending until the agent confirms, after a full round trip to us, within a watchdog deadline. Three failed boots and the bootloader returns to the last known good on its own, and a signed recovery path sits below the agent.
[pause: 1.0]
N: That fix creates the next question: the device recovers. How many devices have to go through that?
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: The rare revision

[slide: v-328]
[pause: 1.2]
N: Challenge two: the second half of the crux, the blast radius.
[pause: 1.8]

[slide: v-329]
[pause: 0.6]
I: You release to one percent first. It looks fine. At ten percent, one hardware revision starts bricking. What went wrong?
[pause: 2.0]

[slide: v-330]
[pause: 1.3]
C: Inside the rollout controller.
[reveal: v-331]
[pause: 0.45]
C: The cohort picker is marked.
[reveal: v-332]
[pause: 0.45]
C: The naive answer: one percent, then ten, then everyone, and someone watches.
[reveal: v-333]
[pause: 0.45]
C: A random one percent of the fleet. Hardware revision five is point three percent of devices, so about thirty of them were in it, and that day they were offline.
[pause: 1.1]

[slide: v-334]
[pause: 1.0]
C: The trace.
[reveal: v-335]
[pause: 0.45]
C: Monday, wave one: ten thousand random devices, thirty of them revision five, all offline.
[reveal: v-336]
[pause: 0.45]
C: Tuesday, the crash rate is flat, and a person approves ten percent.
[reveal: v-337]
[pause: 0.45]
C: Wednesday, three hundred revision-five devices brick. Their old bootloader has no watchdog.
[reveal: v-338]
[pause: 0.45]
C: Three hundred visits, three times the budget.
[reveal: v-339]
[pause: 0.45]
C: Two errors: a sample by percentage, and a person reading an average.
[pause: 1.0]

[slide: v-340]
[pause: 1.3]
C: The fix.
[reveal: v-341]
[pause: 0.45]
C: The cohort picker.
[reveal: v-342]
[pause: 0.45]
C: And the halt rule.
[reveal: v-343]
[pause: 0.45]
C: One level down. Wave one isn't a percentage; it's at least fifty online devices from every combination of hardware revision, region and carrier, chosen from devices seen in the last day. Each combination is compared with its own control group for twenty-four hours, and the halt is automatic when the interval for crashes, reconnects or battery drain excludes zero.
[reveal: v-344]
[pause: 0.45]
C: It covers rare hardware, regional networks and quiet failures. Not a slow leak over weeks; that needs the census in challenge six.
[reveal: v-345]
[pause: 0.45]
C: Rejected: rolling out to a percentage. One percent is mostly the most common hardware; the rare revision that bricks may not be in it at all.
[pause: 1.1]

[slide: v-346]
[pause: 1.3]
C: The waves. Wave zero: a hundred internal devices. Wave one: a thousand, every hardware revision. Wave two: ten thousand, every region too. Wave three: a hundred thousand, after a person approves. Then the rest. Each soaks for a day and is compared with a control.
C: And at every wave the same halt rule: if crashes, reconnects or battery are worse than the control beyond the interval, stop, and revert the wave as a new version of desired state. The person approves going faster. Nobody has to approve stopping.
[pause: 1.1]

[slide: v-347]
[pause: 1.0]
C: What a thousand-device wave can actually see.
[reveal: v-348]
[pause: 0.45]
C: Normal crashes at point two percent a day: about two in a thousand. That's the baseline.
[reveal: v-349]
[pause: 0.45]
C: A five-times regression: ten crashes against two expected. A day's soak sees it.
[reveal: v-350]
[pause: 0.45]
C: A one-and-a-half-times regression: three against two. Invisible at a thousand; it needs ten thousand devices or a week. That's what wave two is for.
[reveal: v-351]
[pause: 0.45]
C: And bricking at any rate is visible, because the halt counts watchdog reverts and devices that stop reporting, not only crashes.
[pause: 1.0]

[slide: v-352]
[pause: 0.6]
I: Halts keep firing on noise, and releases take six weeks.
[pause: 1.5]

[slide: v-353]
[pause: 0.6]
C: Halt on intervals, not thresholds, and put more devices per cell to narrow them. Noise stops firing.
[reveal: v-354]
[pause: 0.45]
C: And a halt pauses rather than kills. A person can resume with a recorded reason. False halts cost a day; a missed real one costs a fleet.
[pause: 0.8]

[slide: v-355]
[pause: 0.7]
V: If asked, I'd say: a percentage isn't a sample. Wave one has every hardware revision, region and carrier in it, each compared with its own control for a day, and the halt is automatic when an interval excludes zero. A person approves going faster; nobody needs to approve stopping.
[pause: 1.0]
N: That fix creates the next question: the waves assume devices are online. Many aren't.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: Six weeks offline

[slide: v-356]
[pause: 1.2]
N: Challenge three: the device that comes back.
[pause: 1.8]

[slide: v-357]
[pause: 0.6]
I: A device has been offline for six weeks, and four config changes happened. What does it do when it reconnects?
[pause: 2.0]

[slide: v-358]
[pause: 1.3]
C: Inside the agent.
[reveal: v-359]
[pause: 0.45]
C: The config applier is marked.
[reveal: v-360]
[pause: 0.45]
C: The naive answer: queue the four changes, deliver them in order.
[reveal: v-361]
[pause: 0.45]
C: Then the applier works through fifteen, sixteen and seventeen to reach eighteen: three obsolete states, and one of them needs firmware the device doesn't have.
[pause: 1.1]

[slide: v-362]
[pause: 1.0]
C: The trace.
[reveal: v-363]
[pause: 0.45]
C: Week zero, a device on firmware four point zero, config fourteen, goes offline.
[reveal: v-364]
[pause: 0.45]
C: Over five weeks, four configs; one needs firmware four point one.
[reveal: v-365]
[pause: 0.45]
C: In week six it reconnects, and a queue delivers fifteen through eighteen.
[reveal: v-366]
[pause: 0.45]
C: Sixteen fails on the old firmware, the queue blocks, and seventeen and eighteen never apply.
[reveal: v-367]
[pause: 0.45]
C: What it needed was one document: the latest desired state, and the firmware that requires.
[pause: 1.0]

[slide: v-368]
[pause: 1.3]
C: The fix.
[reveal: v-369]
[pause: 0.45]
C: The config applier.
[reveal: v-370]
[pause: 0.45]
C: One level down. The device reads one desired document, version eighteen, and applies the whole of it. If eighteen needs firmware four point one or later, the reconciler serves the firmware step first, through the normal wave the device belongs to, then eighteen. Applying the same version twice is a no-op, so a nudge sent twice does nothing.
[reveal: v-371]
[pause: 0.45]
C: It covers any absence and any number of changes. Not changes that must happen in sequence; those are migrations, and the firmware owns them.
[reveal: v-372]
[pause: 0.45]
C: Rejected: replaying every queued change in order. A device offline for six weeks applies four obsolete configs to reach the fifth.
[pause: 1.1]

[slide: v-373]
[pause: 1.0]
C: The agent's loop, level-triggered. Line two: one document, the latest. Line four: if it needs newer firmware, report what it's blocked on, and wait for the firmware wave. Line seven: confirm only after a healthy round trip, otherwise revert. Nothing in the loop depends on what happened while it was away.
[pause: 1.0]

[slide: v-374]
[pause: 0.6]
I: The device's clock is wrong after six weeks without power.
[pause: 1.5]

[slide: v-375]
[pause: 0.6]
C: Nothing compares times. Desired and reported state compare versions, so a clock in nineteen seventy changes no decision.
[reveal: v-376]
[pause: 0.45]
C: And the gateway stamps receipt time from its own clock, with a grace window for certificate validity, so a device with a dead clock can still connect and fix it.
[pause: 0.8]

[slide: v-377]
[pause: 0.7]
V: If asked, I'd say: a device never replays history. It reads one desired document, the latest, applies all of it, and reports the version. If that needs newer firmware, it reports what it's blocked on, and the firmware wave comes first. Versions order everything; the device's clock orders nothing.
[pause: 1.0]
N: That fix creates the next question: what if a lot of devices come back at once?
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: The reconnect storm

[slide: v-378]
[pause: 1.2]
N: Challenge four: overload, caused by the fleet recovering.
[pause: 1.8]

[slide: v-379]
[pause: 0.6]
I: A regional internet provider comes back, and two hundred thousand devices reconnect in the same minute. What happens to your control plane?
[pause: 2.0]

[slide: v-380]
[pause: 1.3]
C: Inside the gateway.
[reveal: v-381]
[pause: 0.45]
C: Admission is marked.
[reveal: v-382]
[pause: 0.45]
C: The naive answer: brokers autoscale.
[reveal: v-383]
[pause: 0.45]
C: Autoscaling takes minutes. Admission accepts everyone at once: forty thousand T-L-S handshakes a second, timeouts, and every device retries on the same fixed schedule.
[pause: 1.1]

[slide: v-384]
[pause: 1.0]
C: The trace.
[reveal: v-385]
[pause: 0.45]
C: At two, the provider recovers and two hundred thousand devices try to connect.
[reveal: v-386]
[pause: 0.45]
C: Five seconds in, forty thousand handshakes a second; brokers saturate; half time out.
[reveal: v-387]
[pause: 0.45]
C: Every device retries after exactly ten seconds: the same storm again.
[reveal: v-388]
[pause: 0.45]
C: Twenty minutes later it's still down.
[reveal: v-389]
[pause: 0.45]
C: The cause ended at two o'clock. The retries are now the outage.
[pause: 1.0]

[slide: v-390]
[pause: 1.3]
C: The fix.
[reveal: v-391]
[pause: 0.45]
C: Admission.
[reveal: v-392]
[pause: 0.45]
C: And the desired-state cache.
[reveal: v-393]
[pause: 0.45]
C: One level down. Devices back off with full jitter: wait a random time between zero and a cap that doubles with each failure, so retries spread out instead of lining up. Each node admits through a token bucket, two thousand connections a second, and refuses the rest with a retry-after hint the agent honours. And a device that's already current costs one version comparison in the cache, not a database read.
[reveal: v-394]
[pause: 0.45]
C: It covers storms after outages, deploys and power cuts. Not a broker that's simply too small.
[reveal: v-395]
[pause: 0.45]
C: Rejected: immediate reconnect with a fixed retry. Two hundred thousand devices retry in step, and the brokers never recover.
[pause: 1.1]

[slide: v-396]
[pause: 1.0]
C: What jitter buys, in numbers.
[reveal: v-397]
[pause: 0.45]
C: A fixed ten-second retry: forty thousand connects a second, again every ten seconds. The brokers never recover.
[reveal: v-398]
[pause: 0.45]
C: Exponential backoff without jitter still sends everyone at two seconds, four, eight: the storms get rarer, not smaller.
[reveal: v-399]
[pause: 0.45]
C: Full jitter with a fifteen-minute cap spreads two hundred thousand devices across the window: by the tail, around two hundred and twenty a second, far inside twenty nodes at two thousand each. Devices come back over minutes, and the control plane stays up the whole time.
[pause: 1.0]

[slide: v-400]
[pause: 1.0]
C: The backoff in pseudocode. Line three: a cap that doubles, up to fifteen minutes. Line four: sleep a random fraction of it, the full jitter, so two hundred thousand devices spread over the window. Line six: if the broker says retry after, obey it, with a little jitter of its own.
[pause: 1.0]

[slide: v-401]
[pause: 0.6]
I: The devices that reconnect all ask for desired state, and the shadow database melts.
[pause: 1.5]

[slide: v-402]
[pause: 0.6]
C: Most reconnecting devices are already current. The device sends its applied version, the gateway compares it with a cached version per cohort, and answers current.
[reveal: v-403]
[pause: 0.45]
C: Only devices that are actually behind read their document from the database. After a short outage, that's almost none.
[pause: 0.8]

[slide: v-404]
[pause: 0.7]
V: If asked, I'd say: a recovering fleet must not become the next outage. Devices back off with full jitter and obey a retry-after, each broker admits through a token bucket, and a reconnecting device that's already current costs one cached version compare, not a database read.
[pause: 1.0]
N: That fix creates the next question: those devices also bring weeks of buffered telemetry.
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Telemetry, twice

[slide: v-405]
[pause: 1.2]
N: Challenge five: the health signals the rollout decides on.
[pause: 1.8]

[slide: v-406]
[pause: 0.6]
I: Devices buffer health reports while offline and send them on reconnect. Some arrive twice. And someone labels the crash metric by device I-D. What happens to your rollout decisions?
[pause: 2.0]

[slide: v-407]
[pause: 1.3]
C: Inside the agent.
[reveal: v-408]
[pause: 0.45]
C: The telemetry buffer is marked.
[reveal: v-409]
[pause: 0.45]
C: The naive answer: MQTT's highest quality of service delivers exactly once.
[reveal: v-410]
[pause: 0.45]
C: Within one session. The buffer resends after a reboot, which is a new session, so the crash reports count twice.
[pause: 1.1]

[slide: v-411]
[pause: 1.0]
C: The trace.
[reveal: v-412]
[pause: 0.45]
C: Tuesday night, wave-two devices crash once each: the normal rate.
[reveal: v-413]
[pause: 0.45]
C: Wednesday morning they flush their buffers, and half flush twice after rebooting mid-upload.
[reveal: v-414]
[pause: 0.45]
C: The wave's crash rate looks one and a half times the control, and the halt fires on duplicates.
[reveal: v-415]
[pause: 0.45]
C: And the device-I-D label made a million series, so the metrics store answers in minutes.
[reveal: v-416]
[pause: 0.45]
C: Duplicates that look like failures, and labels that make the signal unreadable.
[pause: 1.0]

[slide: v-417]
[pause: 1.3]
C: The fix.
[reveal: v-418]
[pause: 0.45]
C: The telemetry buffer.
[reveal: v-419]
[pause: 0.45]
C: One level down. Each report carries the device I-D and a sequence number from a counter kept in flash, so it survives reboots. The consumer keeps the last sequence per device, a million entries, and drops anything not newer. Metrics carry cohort, firmware and wave labels; per-device data goes to the lake, where it's a row, not a series.
[reveal: v-420]
[pause: 0.45]
C: It covers resends across sessions and reboots. Not a device whose flash was wiped: its counter restarts with a new epoch number in front.
[reveal: v-421]
[pause: 0.45]
C: Rejected: exactly-once from the broker. Its highest quality of service covers one session; a device replaying its buffer after a reboot is a new session.
[pause: 1.1]

[slide: v-422]
[pause: 1.0]
C: The consumer in pseudocode. Line three: anything not newer than the last epoch and sequence for this device is dropped. Line five: the labels are cohort, firmware and wave, never the device. Line seven: the per-device record goes to the lake, for the engineer who needs one device's story.
[pause: 1.0]

[slide: v-423]
[pause: 0.6]
I: A wave of a thousand devices. Is a crash rate of point three percent against point two real?
[pause: 1.5]

[slide: v-424]
[pause: 0.6]
C: Count, don't guess. Three crashes against two expected is noise, and the interval says so. Soak longer or widen the cell.
[reveal: v-425]
[pause: 0.45]
C: Use leading signals: reconnects and watchdog reverts move before crashes do.
[reveal: v-426]
[pause: 0.45]
C: And the honest limit: a failure rarer than one in a thousand a day can't be seen in a thousand devices. That's what the bigger waves are for.
[pause: 0.8]

[slide: v-427]
[pause: 0.7]
V: If asked, I'd say: telemetry decides rollouts, so it must be right. Every report carries a device sequence from flash, the consumer drops anything not newer, and metrics are labelled by cohort, firmware and wave, never by device. Per-device data goes to the lake instead.
[pause: 1.0]
N: That fix creates the last question: how would you know the fleet is actually where you think it is?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: Connected is not converged

[slide: v-428]
[pause: 1.2]
N: Challenge six is observability of a fleet, not of servers.
[pause: 1.8]

[slide: v-429]
[pause: 0.6]
I: The dashboard says ninety-eight percent of devices are connected and healthy. A customer says their devices still run last year's firmware. How would you have known?
[pause: 2.0]

[slide: v-430]
[pause: 1.3]
C: The gateway, telemetry, metrics and the shadow store.
[reveal: v-431]
[pause: 0.45]
C: The metrics store is marked.
[reveal: v-432]
[pause: 0.45]
C: The naive answer: ninety-eight percent connected.
[reveal: v-433]
[pause: 0.45]
C: The metrics count connections. Nothing compares what devices report with what we told them to be.
[pause: 1.1]

[slide: v-434]
[pause: 1.0]
C: The trace.
[reveal: v-435]
[pause: 0.45]
C: March, release four point one to everyone.
[reveal: v-436]
[pause: 0.45]
C: One retail cohort, on old bootloaders, reports blocked on a prerequisite version.
[reveal: v-437]
[pause: 0.45]
C: For nine months it's connected, sends health, and never converges. No alert.
[reveal: v-438]
[pause: 0.45]
C: In December the customer notices first.
[reveal: v-439]
[pause: 0.45]
C: Connected and healthy: true, and beside the point.
[pause: 1.0]

[slide: v-440]
[pause: 1.3]
C: The fix changes the design: version four. Version three, carried.
[reveal: v-441]
[pause: 0.45]
C: New: a fleet census, reading the shadow store and the metrics, every hour.
[pause: 1.1]

[slide: v-442]
[pause: 0.6]
C: One level down, four measures.
[reveal: v-443]
[pause: 0.45]
C: A census: devices by firmware, config, cohort and hardware, every hour. The version tail is a table, not a guess.
[reveal: v-444]
[pause: 0.45]
C: Convergence: from a desired change to ninety-five percent of online devices reporting it. Ours stalled at ninety-four for nine months.
[reveal: v-445]
[pause: 0.45]
C: Blocked and rejected: devices reporting blocked on, or rejected, by cohort. That one would have fired in March.
[reveal: v-446]
[pause: 0.45]
C: Unseen: devices not seen for seven, thirty or ninety days. Lost, stolen, or in a drawer.
[reveal: v-447]
[pause: 0.45]
C: Rejected: dashboards of connected devices. A device that connects but runs the wrong firmware looks exactly healthy.
[pause: 0.8]

[slide: v-448]
[pause: 1.0]
C: And read them in pairs.
[reveal: v-449]
[pause: 0.45]
C: Convergence stalls with blocked-on rising: a missing prerequisite. Serve the firmware step.
[reveal: v-450]
[pause: 0.45]
C: Convergence stalls with rejections rising: the change fails on some hardware. Halt it.
[reveal: v-451]
[pause: 0.45]
C: Reconnects up in one wave only: the release. In every wave on one carrier: the network.
[reveal: v-452]
[pause: 0.45]
C: The same pair, the other way round: every wave, one carrier, means the carrier, and the release can continue.
[reveal: v-453]
[pause: 0.45]
C: And watchdog reverts on one hardware revision: a driver bug. Halt that cell.
[pause: 1.0]

[slide: v-454]
[pause: 1.0]
C: And the fleet's service levels.
[reveal: v-455]
[pause: 0.45]
C: Online devices on the desired config within a day: at least ninety-five percent.
[reveal: v-456]
[pause: 0.45]
C: Devices harmed per release: at most a hundred.
[reveal: v-457]
[pause: 0.45]
C: Watchdog reverts: measured and alerted per cell.
[reveal: v-458]
[pause: 0.45]
C: Devices unseen for thirty days: watched, against the customer's contract.
[reveal: v-459]
[pause: 0.45]
C: And the control plane at three nines, because devices keep running without it.
[pause: 1.0]

[slide: v-460]
[pause: 0.7]
V: If asked, I'd say: I'd watch convergence, not connection. An hourly census by firmware, config, cohort and hardware; the time for a change to reach ninety-five percent of online devices; devices reporting blocked or rejected; and devices we haven't seen in weeks. Connected and healthy can be true for a device that's nine months behind.
[pause: 1.6]

[pause: 1.4]

## 8 Recap

[slide: v-461]
[pause: 1.2]
C: The recap.
[pause: 1.8]

[slide: v-462]
[pause: 1.3]
C: Version four.
[reveal: v-463]
[pause: 0.45]
C: The agent: A-B slots and the watchdog.
[reveal: v-464]
[pause: 0.45]
C: The gateway: identity per device, and admission with backoff.
[reveal: v-465]
[pause: 0.45]
C: The shadow store: desired and reported.
[reveal: v-466]
[pause: 0.45]
C: The reconciler: convergence, gently.
[reveal: v-467]
[pause: 0.45]
C: The rollout controller: waves by cohort that halt themselves.
[reveal: v-468]
[pause: 0.45]
C: And the census, which tells us where the fleet really is.
[pause: 1.1]

[slide: v-469]
[pause: 0.6]
C: One sentence per path.
[reveal: v-470]
[pause: 0.45]
C: Know: devices report versions and health, aggregated by cohort and deduplicated by sequence.
[reveal: v-471]
[pause: 0.45]
C: Configure: an operator writes a versioned desired document, and devices converge to the latest when they can.
[reveal: v-472]
[pause: 0.45]
C: Release: signed images, waves by cohort, each compared with a control, and a halt that needs no person.
[reveal: v-473]
[pause: 0.45]
C: Stop: devices revert on their own, and the controller reverts desired state as a new version.
[pause: 0.8]

[slide: v-474]
[pause: 1.0]
N: The mistakes that cost most.
[reveal: v-475]
[pause: 0.45]
N: Commands pushed to online devices. Instead, desired state, pulled and reconciled.
[reveal: v-476]
[pause: 0.45]
N: A server-side rollback for a crash loop. Instead, A-B slots and a watchdog.
[reveal: v-477]
[pause: 0.45]
N: Rolling out to a percentage. Instead, strata and an automatic halt.
[reveal: v-478]
[pause: 0.45]
N: Replaying queued changes. Instead, latest wins.
[reveal: v-479]
[pause: 0.45]
N: Immediate, fixed retries. Instead, full jitter and admission control.
[reveal: v-480]
[pause: 0.45]
N: Counting connected devices. Instead, a census and convergence time.
[pause: 1.0]

[slide: v-481]
[pause: 0.7]
V: Publish a desired state, never a command. Release in waves that halt themselves. And let every device return to its last known good without help.
[pause: 1.0]
C: Thanks for watching. The written design is linked below.
[pause: 1.6]
