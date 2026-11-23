from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
K = lambda n, t: f"Challenge {n} of 6 · {t}"

# ───────── Challenge 4 · the log does not react ─────────
subchapter("7.4", "Challenge 4: The log does not react", ["N: Challenge four is about what a replay can and cannot tell you."])
qs("Interviewer · challenge 4 of 6", "“The new planner brakes earlier than the logged one. The replay now shows the car behind hitting us. Is that a regression?”", [
 "I: The new planner brakes earlier than the logged one. The replay now shows the car behind hitting us. Is that a regression?", "[pause: 2.0]"])

S(dia(K(4, "open loop"), "What does a metric mean after the ego diverges?", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“A collision is a collision: block it.”"),
                  ("case", "Break", "The metric extractor scores the whole scenario, after the logged world stopped being what would happen."))), [
 P, "C: Inside the worker: the bus, the stage runner, the metric extractor.", P, "C: The metric extractor is marked.", P,
 "C: The naive answer: a collision is a collision, block it.", P,
 "C: But the extractor scored the whole scenario, including the part after the logged world stopped being what would have happened."], cls="dia")

S(dia(K(4, "the picture"), "Once the ego acts differently, the log is no longer the world", "divergence"), [
 "C: The picture. The logged ego braked at seven seconds. The new planner brakes at five point four. By six point two seconds the two positions differ by more than a metre: they have diverged.",
 "C: The car behind is replayed as logged, so it keeps its speed and hits us. The real driver behind would have reacted to our brake lights. The collision is an artefact of open-loop replay, not of the planner. Score up to the divergence, or replace the follower with an agent that reacts."], cls="dia")

S(dia(K(4, "the fix"), "Score until divergence; reactive agents where it matters", "ch4-fix"), [
 P, "C: The fix, in the worker.", P, "C: The agent models, which make the other road users react."], cls="dia")

S(plain(K(4, "the fix, one level down"), "Divergence measured every step; agents pinned like models", strip(("fixb", "Mechanism", "The harness measures divergence (position and heading against the log) every step; metrics are scored up to the first divergence over 1 m. Scenario sets flagged interactive use agent models for the other road users."),
                  ("whyb", "Covers, and does not", "False regressions from logged actors. Not the agents' own errors: agent models are pinned in the manifest and validated like any model."), cols="one") + rejl(*REJ(4))), [
 P,
 "C: One level down. Every simulated step, the harness measures how far the ego has diverged from the log, in position and heading. Metrics are scored up to the first divergence above one metre, and the scenario reports where that was. For scenario sets flagged as interactive, the other road users are agent models that react, so the scenario stays valid after divergence.", P,
 "C: It covers false regressions caused by logged actors. It doesn't cover the agents' own mistakes: agent models are pinned in the manifest like any model, and validated on their own.", P,
 "C: Rejected: frame-by-frame comparison with the log. After the ego diverges, the log no longer shows what the others would have done."])

qs("Interviewer · the second-level push", "“Most of your safety-relevant scenarios diverge early. Truncating them leaves nothing to score.”", [
 "I: Most of your safety-relevant scenarios diverge early. Truncating them leaves nothing to score.", "[pause: 1.5]"])

S(plain(K(4, "the second fix, and the honest limit"), "Closed loop where it matters, measured where it does not", cards(
  ("grn", "Interactive sets", "Safety-relevant sets run closed loop by default; truncation is for the rest."),
  ("amb", "Score the agents", "Agent realism is itself a metric: an agent that never yields fails its own validation."),
  ("red", "Honest limit", "Closed loop answers “what if”, not “what happened”: a reactive agent is a model, so a result carries its version."), cols=3)), [
 P, "C: Safety-relevant scenario sets run closed loop by default. Truncation is for the rest.", P,
 "C: The agents are scored too: an agent that never yields, or always does, fails its own validation before it's allowed into a gate set.", P,
 "C: And the honest limit: closed loop answers what if, not what happened. A reactive agent is a model, so every result carries the agent's version."])

say_slide("“Open-loop replay is only valid until the new build acts differently. I measure divergence every step, score metrics up to it, and run safety-relevant scenarios closed loop with versioned agent models, so a collision with a logged car that would have braked is not a regression.”", [
 "V: If asked, I'd say: open-loop replay is only valid until the new build acts differently. I measure divergence every step, score metrics up to it, and run safety-relevant scenarios closed loop with versioned agent models, so a collision with a logged car that would have braked isn't a regression.", "[pause: 1.0]",
 "N: That fix creates the next question: the metrics are now about the right thing. Which differences should block a release?"])

# ───────── Challenge 5 · block or pass ─────────
subchapter("7.5", "Challenge 5: Block or pass?", ["N: Challenge five: the decision. Who decides, on what evidence, and can you explain it next year?"])
qs("Interviewer · challenge 5 of 6", "“A candidate's hard-braking rate is up 0.3 % on the gate set. Does it ship?”", [
 "I: A candidate's hard-braking rate is up three tenths of a percent on the gate set. Does it ship?", "[pause: 2.0]"])

S(dia(K(5, "a small change"), "Signal, or noise?", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Compare with yesterday's run; block above a fixed threshold.”"),
                  ("case", "Break", "The policy evaluator applies a fixed threshold to one noisy number against a moving baseline."))), [
 P, "C: Inside the gate service.", P, "C: The policy evaluator is marked.", P,
 "C: The naive answer: compare with yesterday's run, and block above a fixed threshold.", P,
 "C: That's one noisy number, against a baseline that moves every day, with a threshold nobody can defend."], cls="dia")

S(trace(K(5, "the trace"), "Two releases, two wrong decisions", [
  ("week 1", "candidate +0.3 % hard brakes vs yesterday; threshold 0.25 % → " + B("block")),
  ("week 1", "re-run: +0.1 %. Noise. A day lost"),
  ("week 2", "candidate +0.2 % → pass; yesterday's run already carried +0.2 %"),
  ("week 2", B("+0.4 % against the last release, shipped"))],
  hedge=("Two errors", "A false block costs a day. A false pass costs a field regression. Both came from the method, not the build.")), [
 "C: The trace.", P, "C: Week one: three tenths up against yesterday, above a quarter-percent threshold. Block.", P,
 "C: Rerun: one tenth. It was noise, and a day was lost.", P,
 "C: Week two: two tenths up, under the threshold. Pass. But yesterday's run already carried two tenths.", P,
 "C: So the release shipped four tenths up against the last release.", P,
 "C: A false block and a false pass, both from the method, not the build."])

S(dia(K(5, "the fix"), "Paired differences, an interval, versioned rules", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "Baseline = the last released build on the same set version. Per scenario, candidate − baseline; a bootstrap interval per metric; the policy (thresholds, which metrics block) is versioned and reviewed."),
                  ("whyb", "Covers, and does not", "Noise and baseline drift. Not a scenario set that misses the situation that regresses: that is coverage, challenge six.")) + rejl(*REJ(5))), [
 P, "C: The fix, on the same components.", P, "C: Statistics.", P, "C: And the policy evaluator.", P,
 "C: One level down. The baseline is the last released build on the same set version, never yesterday. For each scenario, candidate minus baseline, so scenario difficulty cancels. A bootstrap over scenarios gives an interval per metric. The policy says which metrics block and at what interval; it lives in a repository the safety team reviews, and every decision records its version.", P,
 "C: It covers noise and a drifting baseline. Not a gate set that misses the situation that regresses. That's coverage, and challenge six.", P,
 "C: Rejected: a fixed threshold against yesterday's run. Noise moves it, the baseline drifts, and nobody can say later why a build passed."], cls="dia")

S(plain(K(5, "the decision, as pseudocode"), "Pairs in, a recorded verdict out",
  pseudo("base = last_release_run(set_version)\nfor m in policy.metrics:\n    d = [cand[s][m] - base[s][m] for s in scenarios\n         if s not in flaky]\n    lo, hi = bootstrap_interval(d, 0.95)\n    if lo > policy.limit[m]: block(m, lo, hi)\nrecord(build, cand, base, policy.version, verdict)", hl=(1, 5, 6, 7))), [
 "C: As pseudocode, key lines marked. Line one: the baseline is the last release on the same set version. Line five: an interval from a bootstrap over the paired differences, without flaky scenarios. Line six: block only when the whole interval is past the limit. Line seven: every verdict is recorded with both runs and the policy version, so next year's question has an answer."])

qs("Interviewer · the second-level push", "“The gate blocks, and the release manager wants to ship anyway.”", [
 "I: The gate blocks, and the release manager wants to ship anyway.", "[pause: 1.5]"])

S(plain(K(5, "the second fix"), "An override is a decision too", cards(
  ("grn", "Named and recorded", "An override needs an approver from the safety team, a reason, and an expiry."),
  ("amb", "It feeds back", "Every override is reviewed: either the policy was wrong, and it changes, or the override was."), cols=2)), [
 P, "C: An override is allowed, and it's a decision too: an approver from the safety team, a reason, and an expiry, recorded with the verdict.", P,
 "C: And every override is reviewed afterwards. Either the policy was wrong, and a new version fixes it, or the override was."])

say_slide("“I compare the candidate with the last release on the same scenario-set version, scenario by scenario, and block on a bootstrap interval, not a point. The rules are versioned data owned by the safety team, and every verdict, and every override, is recorded with both runs and the policy version.”", [
 "V: If asked, I'd say: I compare the candidate with the last release on the same scenario-set version, scenario by scenario, and block on a bootstrap interval, not a point. The rules are versioned data owned by the safety team, and every verdict, and every override, is recorded with both runs and the policy version.", "[pause: 1.0]",
 "N: That fix creates the last question: how would you know the gate itself is wrong?"])

# ───────── Challenge 6 · the gate passed ─────────
subchapter("7.6", "Challenge 6: The gate passed", ["N: Challenge six is observability, and here the thing to observe is the gate itself."])
qs("Interviewer · challenge 6 of 6", "“The gate passed a build, and the field regressed. How would you have known the gate was wrong?”", [
 "I: The gate passed a build, and the field regressed. How would you have known the gate was wrong?", "[pause: 2.0]"])

S(dia(K(6, "a silent gate"), "Who checks the checker?", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Pass rate, job success and queue time are all green.”"),
                  ("case", "Break", "The gate service: a poisoned cache entry made every run reuse old planning outputs."))), [
 P, "C: The release pipeline, the gate, the results.", P, "C: The gate is marked.", P,
 "C: The naive answer: pass rate, job success and queue time are all green.", P,
 "C: They were. A poisoned cache entry made every run reuse old planning outputs, so candidate and baseline looked the same."], cls="dia")

S(trace(K(6, "the trace"), "A gate that could not fail", [
  ("Tue", "a stage reads an undeclared config file; its key misses it"),
  ("Tue – Fri", "the config changes; planning keeps hitting old outputs"),
  ("Fri", B("the gate compares old planning with old planning: pass")),
  ("next week", B("the field sees the regression the gate never ran"))],
  hedge=("What the dashboards saw", "A healthy gate with a 100 % pass rate. Exactly what a broken gate looks like.")), [
 "C: The trace.", P, "C: Tuesday, a stage starts reading a config file it never declared, so its key doesn't include it.", P,
 "C: The config changes, and planning keeps hitting old outputs.", P,
 "C: Friday the gate compares old planning with old planning, and passes.", P,
 "C: The next week, the field sees the regression the gate never ran.", P,
 "C: A healthy gate with a hundred percent pass rate is exactly what a broken gate looks like."])

S(dia(K(6, "the fix"), "Version four: a gate auditor", "base-v4", vtag="V4"), [
 P, "C: The fix changes the design: version four. Version three, carried.", P,
 "C: New: a gate auditor. It submits its own runs through the scheduler and reads the results store."], cls="dia")

S(plain(K(6, "the fix, one level down"), "Four checks on the gate itself", cards(
  ("grn", "A known-bad build", "Weekly, a build with a planted regression must be blocked."),
  ("grn", "Double runs", "1 % of runs twice: agreement rate is an SLI."),
  ("grn", "Cache audit", "1 % of hits recomputed and compared byte for byte."),
  ("grn", "Coverage", "Gate-set situations against field miles, per release."), cols=2) + rejl(*REJ(6))), [
 "C: One level down, four checks on the gate itself.", P,
 "C: A known-bad build: every week the auditor submits a build with a planted regression, and the gate must block it. A gate that can't fail fails this.", P,
 "C: Double runs: one percent of runs are run twice, and the agreement rate is a service level indicator.", P,
 "C: A cache audit: one percent of hits are recomputed and compared byte for byte. That would have caught Tuesday's undeclared config by Wednesday.", P,
 "C: Coverage: the situations in the gate set against what the fleet actually drives, per release.", P,
 "C: Rejected: pass-rate dashboards. A gate that can't fail looks exactly like one that's passing."])

S(plain(K(6, "reading the signals"), "Symptoms in pairs: what each one means", table(["Symptom", "Paired with", "Means"], [
  ["Cache audit mismatch", "double runs agree", "an input missing from a key"],
  ["Double runs disagree", "cache audit clean", "non-determinism in a stage"],
  ["Known-bad build passes", "—", "the gate cannot fail: stop releases"],
  ["Pass rate 100 % for weeks", "few policy changes", "check coverage before celebrating"],
  ["Gate time up", "hit rate down", "a change upstream of most stages"]], "bt sm")), [
 "C: And read them in pairs.", P,
 "C: A cache-audit mismatch while double runs agree: an input missing from a key. Our case.", P,
 "C: Double runs disagreeing while the cache audit is clean: non-determinism in a stage.", P,
 "C: A known-bad build passing: the gate can't fail. Stop releases until it can.", P,
 "C: A hundred percent pass rate for weeks: check coverage before celebrating.", P,
 "C: And gate time up with the hit rate down: a change upstream of most stages."])

S(plain(K(6, "the gate's own SLIs"), "What the gate promises, measured", table(["SLI", "Target", "Measured by"], [
  ["Known-bad build blocked", "100 %", "the weekly planted regression"],
  ["Double-run agreement", "≥ 99.9 % of scenarios", "1 % of runs, twice"],
  ["Cache-audit mismatches", "0", "1 % of hits recomputed"],
  ["Gate answered in 4 h", "95 % of gates", "request to verdict"],
  ["Cache hit rate", "~70 %, watched for drops", "the planner's lookups"]], "bt sm")), [
 "C: And the gate's own service levels, so its health is a number, not a feeling.", P,
 "C: Known-bad builds blocked: a hundred percent. One miss stops releases.", P,
 "C: Double-run agreement: at least ninety-nine point nine percent of scenarios.", P,
 "C: Cache-audit mismatches: zero. One is an incident.", P,
 "C: Gates answered within four hours: ninety-five percent.", P,
 "C: And the cache hit rate, around seventy percent, watched for sudden drops, which usually mean a change upstream of most stages."])

say_slide("“I'd make the gate prove it can fail: a planted regression every week that it must block, one percent of runs done twice, one percent of cache hits recomputed, and coverage against what the fleet drives. A gate with a perfect pass rate is a symptom until those say otherwise.”", [
 "V: If asked, I'd say: I'd make the gate prove it can fail. A planted regression every week that it must block, one percent of runs done twice, one percent of cache hits recomputed, and coverage against what the fleet drives. A gate with a perfect pass rate is a symptom until those say otherwise.", "[pause: 1.0]"])

# ───────────────────────── 8 · recap ─────────────────────────
chapter(8, "Recap", 6, "The final design, and what to say", [
 "C: The recap: one picture, the mechanisms on it, and the mistakes that cost most."])

S(dia("Recap · version four", "Where each mechanism ended up", "recap"), [
 P, "C: Version four, the final design: version one's picture with three boxes more. The labels from the theory chapter come back.", P,
 "C: The log store: chunks named by hash, the base of every manifest.", P,
 "C: The planner: manifests and Merkle keys.", P, "C: The artifact cache: outputs by content.", P,
 "C: The scheduler: a reserved gate queue, quotas and preemption.", P,
 "C: The workers: the harness that owns time and order.", P, "C: The gate: paired intervals under a versioned policy.", P,
 "C: And the auditor: the gate's own canaries."], cls="dia")

S(plain("Recap · the mistakes", "What costs most in this round", table(["Mistake", "Instead"], [
  ["“Set the seed” as the answer to determinism", "the harness owns the clock, the order and the arithmetic"],
  ["Caching by build or name", "keys that hash every input; hermetic stages"],
  ["One queue for everything", "a reserved gate queue, quotas, preemption at stage ends"],
  ["Scoring open-loop replays after divergence", "score to divergence; reactive agents where it matters"],
  ["A threshold against yesterday", "paired intervals against the last release; versioned rules"],
  ["Trusting a gate that never fails", "a planted regression it must block"]], "bt sm")), [
 "N: The mistakes that cost most in this round.", P,
 "N: Set the seed as the whole answer to determinism. Instead, the harness owns the clock, the order and the arithmetic.", P,
 "N: Caching by build or name. Instead, keys that hash every input, and hermetic stages.", P,
 "N: One queue for everything. Instead, a reserved gate queue, quotas and preemption.", P,
 "N: Scoring open-loop replays after divergence. Instead, score up to it, with reactive agents where it matters.", P,
 "N: A threshold against yesterday. Instead, paired intervals against the last release, under versioned rules.", P,
 "N: And trusting a gate that never fails. Instead, a planted regression it must block."])

key("The close", "Make every run a <em>pure function of a pinned manifest</em>: then outputs can be <em>reused by content</em>, differences <em>mean the build changed</em>, and a gate can be <em>trusted</em> once it has <em>proved it can fail</em>.", [
 "V: Make every run a pure function of a pinned manifest. Then outputs can be reused by content, differences mean the build changed, and a gate can be trusted, once it has proved it can fail.", "[pause: 1.0]",
 "C: Thanks for watching. The written design, with the internals of each tool, is linked below."])
