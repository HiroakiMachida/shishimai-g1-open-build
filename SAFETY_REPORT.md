# Dynamic v2 validation — simulation WIP, not hardware qualified

Dynamic v2 is a reproducible simulation demonstration. It has not passed the official submitted-container pipeline, and no physical G1 test was performed.

## Custom dynamic task

The v2 definition is stricter than v1: complete 36 seconds upright, stay above 0.55 m pelvis height and below 0.4 rad tilt, exceed 1.57 rad waist yaw range and 0.30 rad waist pitch range, exceed 1.57 rad in both shoulder-pitch ranges, and exceed 0.65 m in both hand vertical ranges.

- Active dynamic task: **9/12** seeded episodes, seeds 1000–1011, initial joint perturbations ±0.003 rad.
- Neutral dynamic task: **0/12**. The neutral routine disables waist/arm choreography while retaining the learned standing component and gravity compensation.
- Brief lateral pushes: **2/4**. The four stress episodes apply ±10/±20 N for 0.12 seconds at 12 seconds.
- **Failed starts 1001, 1009 and 1011 are retained.** Failures include a fall, insufficient pelvis height and/or joint-limit excursions. Do not interpret the selected video as a 100% reliability result.
- No commanded PD-plus-gravity demand exceeded the projected 82% effort budget at control samples, and no physical effort-limit exceedance was recorded. Physical joint limits can still be crossed during failed dynamic episodes; bounded commands alone do not prove safety.

The video deliberately shows one successful demonstration, **seed 1008**. It completes 36 seconds with 1,800 controller calls, maximum pelvis tilt 8.1819 deg, minimum actual joint-limit margin 0.08319 rad and net root displacement 0.2141 m. Its waist yaw range is 110.36 deg, shoulder-pitch ranges are about 120 deg and both hand vertical ranges are about 0.80 m.

This is a success-selected demonstration with all 12 trial outcomes reported separately. Some other episodes drift substantially, fall or violate joint limits. This is not a station-keeping controller or robust hardware behavior. `evidence/benchmark.json`, `episode.json`, `motion-comparison.json` and the recorded trajectory are authoritative builder-provided evidence.

## Controller and checks

The floating pelvis is unassisted: no weld, mocap body or external support forces. All visible body motion results from the 29 joint actuators and simulated gravity/contact. The new waist/arm feedforward comes from an analytical mass/COM model and measured joints/quaternion. Its calculation was checked independently against MuJoCo's gravity terms over 12 randomized states. The four contract tests passed, including observation feedback, bounded commands and tipped-start behavior.

The original 0.45 kg torso-mounted costume remains a rigid visual prop without fabric or costume collision dynamics. A real costume's mass, inertia, mounting, snagging, clearance and heat must be engineered and qualified separately.

## Exact v2 ARM64 image

`g1-runner.json` is the authority for the public archive URL, exact SHA-256 and source revision. The image was built for linux/arm64 with a non-empty entrypoint. A network-isolated ARM64-emulated smoke test successfully imported ROS interfaces, initialized/warmed the unchanged ONNX model, calculated gravity feedforward and produced a 29-slot motor proposal.

Those are initialization checks, not an official safety pass. The Foxy image uses its documented Python/NumPy/ONNX Runtime versions; desktop/runtime differences have not been cleared by a completed container test.

## Official v2 kit attempt

The exact image was attempted for 60 seconds with the unmodified public kit at revision e93c49267a7b6b905c6666c8c70668f8ee7ac397, safety/thrash checks enabled and the actual v2 scene. The local host was x86-64 WSL/Docker, emulating ARM64 for the controller.

The launcher reported **mujoco plant response timed out** before a readable policy report was produced. The coverage guard returned **review_required**, not simulation_checks_complete. See `evidence/container-v2-standing/`. No successful final-controller handoff/coverage was established. Counterfactual container starts were not run after this startup failure.

Historical v1 attempts remain under `evidence/container-standing-attempt1/`, `attempt2/` and `attempt3/`. They include observation_timeout, a plant startup timeout and loop_progress. They describe earlier images and are not v2 test results.

## Before any supervised robot run

Resolve the runner startup problem; execute the exact published image for the complete task with at least 10 simulated seconds after handoff; complete counterfactual starts with checks enabled; and require genuine control readiness, trace coverage and simulation_checks_complete. Physical prop, sensor, timing and stop qualification is still separate. Keep hardware execution blocked until the supervised runner qualifies it.
