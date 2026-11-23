# Diagram index

Drawn by `diagrams_sre.py` into `svg/`. Illustrative numbers are labelled on the figure.

| Episode | Slide | Figure | Slide title |
|---|---|---|---|
| 1 | 4 | `e01-ops-scaling.svg` | Operations that scales with load, against operations that does not |
| 1 | 10 | `e01-request-life.svg` | One request through an example service |
| 2 | 9 | `e02-budget-burndown.svg` | A quarter of budget, spent by incidents and releases |
| 3 | 2 | `e03-empty-set.svg` | The empty list that meant everything |
| 3 | 9 | `e03-automation-ladder.svg` | Where automation lives, from no automation to none needed |
| 4 | 11 | `e04-alert-path.svg` | From a counter in a process to a page on a phone |
| 4 | 15 | `e04-hierarchy.svg` | Monitoring that follows the shape of the service |
| 5 | 6 | `e05-pipeline.svg` | From a commit to a fleet, with the gates between |
| 6 | 8 | `e06-troubleshoot-loop.svg` | Hypothesise, test, learn, and repeat |
| 7 | 7 | `e07-incident-roles.svg` | Roles in a managed incident |
| 7 | 18 | `e07-incident-timeline.svg` | One incident, and the numbers a manager should track |
| 8 | 5 | `e08-test-ladder.svg` | From a unit test to a probe in production |
| 8 | 11 | `e08-intent.svg` | Intent-based capacity planning |
| 9 | 4 | `e09-lb-layers.svg` | Four steps from a name to a task |
| 9 | 9 | `e09-subset-load.svg` | Three hundred clients, three hundred backends |
| 9 | 12 | `e09-lame-duck.svg` | Draining a task without dropping a request |
| 10 | 2 | `e10-goodput.svg` | Goodput collapses when load passes capacity |
| 10 | 7 | `e10-retry-amp.svg` | Three layers, each trying three times: twenty-seven at the bottom |
| 10 | 14 | `e10-throttle.svg` | Reject locally before the backend has to |
| 10 | 17 | `e10-deadline.svg` | A deadline is a budget handed down the call tree |
| 10 | 21 | `e10-metastable.svg` | Metastable failure: the loop that outlives the trigger |
| 11 | 2 | `e11-split-brain.svg` | Case study one: the split brain |
| 11 | 7 | `e11-rsm.svg` | A replicated state machine |
| 11 | 11 | `e11-paxos-phases.svg` | Two phases: ask for a promise, then ask for acceptance |
| 11 | 13 | `e11-paxos-recovery.svg` | A later proposer is forced to repeat it |
| 11 | 15 | `e11-paxos-slots.svg` | Multi-Paxos: elect once, then one round trip per slot |
| 11 | 20 | `e11-write-latency.svg` | Commit waits for the nearest majority |
| 12 | 5 | `e12-cron-launch.svg` | The two synchronisation points of a launch |
| 12 | 10 | `e12-moire.svg` | Three periodic pipelines that overlap |
| 12 | 13 | `e12-workflow.svg` | Leases and uniquely named output |
| 13 | 7 | `e13-layers.svg` | A deleted object's journey |
| 13 | 10 | `e13-restore-time.svg` | Restore time at a fixed bandwidth |
| 14 | 2 | `e14-santa.svg` | A service meets Santa |
| 15 | 13 | `e15-engagement.svg` | From late review to built-in reliability |
| 16 | 7 | `e16-course-map.svg` | Sixteen episodes in five layers |
| 16 | 10 | `e16-ai-serving.svg` | The same ideas applied to a model-serving system |
