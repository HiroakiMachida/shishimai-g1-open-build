# Validation status — simulation entry, not hardware qualified

This project is a reproducible Open Build simulation entry. **It has not passed the official submitted-container safety pipeline and is not ready for a physical G1.** No hardware run was performed.

## Custom MuJoCo task checks

The published controller/scene completed all 12 nominal 36-second episodes (seeds 1000–1011, independent joint-position perturbations within ±0.003 rad). The neutral controller stood but completed the dance in 0/12 episodes. Four separately reported 0.12-second lateral pushes, ±10/±20 N at 12 seconds, completed in 4/4 episodes.

- Worst active nominal pelvis tilt: 18.5295 degrees.
- Minimum actual joint-limit margin over all 24 active/neutral nominal episodes, sampled at every physics step: 0.05931 rad.
- Peak nominal per-joint speed/profile-limit ratio: 0.55369.
- No physical torque-limit exceedance was recorded in those episodes. Each observed requested PD demand was bounded to 82% of its public profile limit; physical motor effort limits were also present in the scene.
- Maximum active nominal horizontal displacement: **1.5453 m**. This is not a station-keeping policy. Balancing shuffles are allowed by the custom task definition.
- Video episode: seed 1000, 36 seconds, 1,800 controller calls, 9.0814-degree maximum pelvis tilt, 0.2157 m horizontal displacement.

These are builder-provided custom task checks, not Arena verification, official container safety clearance or hardware evidence. The raw episode and benchmark JSON files define the measurement protocol. Success means upright task completion under those narrow conditions, not broad reliability.

## Exact ARM64 package

`g1-runner.json` references the archived linux/arm64 image and its SHA-256. The image was built locally and its architecture/entrypoint were inspected. A network-isolated ARM64-emulated smoke test successfully imported the ROS interfaces and initialized/warmed the ONNX inference model. This only proves that initialization step.

Final controller source revision: `0b9b6feb90ef17b599deb8c561d01829831784cf`.

Final image archive SHA-256: `8e0cf0a51faa2d4f3a8cc22868b0af7945eeeceba10ea58841e1c7e98b1c4f5d`.

## Official kit attempts

All runs used the unmodified public kit at revision `e93c49267a7b6b905c6666c8c70668f8ee7ac397`, its safety/thrash checks enabled and the actual costume/task scene. The host was local x86-64 WSL/Docker with ARM64 emulation for the submitted controller.

1. `evidence/container-standing-attempt1/`: the earlier adapter's 60-second requested run accepted 347 commands and recorded handoff at 2.0 simulated seconds, then stopped on `observation_timeout` at 6.94 simulated seconds. It recorded a fall after the stop. The guard returned `review_required`; this is not a pass. This attempt used the earlier image/archive recorded in its attempt metadata.
2. `evidence/container-standing-attempt2/`: after making publication observation-driven, the launcher reported `mujoco plant response timed out` and did not produce a readable policy report. The guard returned `review_required`. This is incomplete evidence, not a controller safety pass.
3. `evidence/container-standing-attempt3/`: a retry of the exact final image stopped on `loop_progress` before any accepted command or policy handoff (0 simulated seconds, 0 commands). The guard again returned `review_required`.

The final submitted controller therefore has **no completed official standing test**. Counterfactual container starts were not run after these startup failures. The cause of those pre-handoff failures remains unresolved; the reports do not demonstrate a successful run of the final controller. Earlier evidence is preserved rather than replaced by the desktop task result.

## Required before any supervised physical attempt

Resolve the runner startup/timing failures, execute the exact published image for the full task with at least 10 simulated seconds after handoff, and complete the kit's counterfactuals with checks enabled. Require a genuine `simulation_checks_complete` report, control readiness and trace coverage. Then qualify the physical costume, its real inertia/mounting/clearance, joint/IMU calibration and stop behavior with the supervised runner. Keep hardware blocked until that separate qualification is complete.
