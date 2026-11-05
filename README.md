# SHISHIMAI v2 — Dynamic Festival Dance

獅子舞を、大きな全身の動きで。

A free-standing Unitree G1 performs a 36-second lion-dance-inspired routine: a greeting bow, overhead reaches, sweeping looks, alternating paw gestures, a festival fan and a final blessing. The dynamic edition replaces the restrained first demonstration with substantially larger motor-driven movements and a full-frame 1080p presentation.

Created by Hiroaki Machida, with coding-agent assistance, for [HIM Open Build Challenge](https://arena.himrobotics.com/challenges/open-build). [Dynamic v2 Arena entry](https://arena.himrobotics.com/uploads/source_468d0f1ae2776057b8e7). [Original v1](https://arena.himrobotics.com/uploads/source_54b57ede9b7ae5bd29cd).

## What changed

Measured from the two published demonstration trajectories; v1 uses seed 1000, v2 uses the disclosed successful seed 1008. See `evidence/motion-comparison.json`.

| Measured motion | v1 | Dynamic v2 |
| --- | ---: | ---: |
| Waist/head left-to-right range | 39.6 deg | 110.4 deg |
| Shoulder pitch range | about 41 deg | about 120 deg |
| Hand vertical range relative to pelvis | 0.12 m | 0.80 m |
| Presentation | 720p, large text panel | 1080p, full-frame tracking view |

The new controller adds analytical gravity feedforward for the waist and arms, using the known robot/costume masses, measured joints and pelvis quaternion. Its calculation is independently checked against MuJoCo's rigid-body gravity terms. This supports the large upper-body poses without adding any force to the floating base.

## Actual control and physics

- Floating G1 pelvis; 29 joint actuators, gravity and ground contact. No weld, mocap body, external support force or scripted root motion.
- `policy.py` provides `reset()` and `act(observation) -> {q,dq,kp,kd,tau}` in the public HIM motor order. Control is 50 Hz; physics is 500 Hz.
- Inputs are joint positions/velocities, pelvis quaternion wxyz and body-frame gyro. No contact oracle, external object state or world/base translation enters the policy.
- NVIDIA's unchanged pretrained GR00T WholeBodyControl Balance model supplies leg targets. Scripted choreography supplies waist/arm targets; `kinematics.py` supplies gravity feedforward. No new model was trained.
- Public HIM profile gains and effort/position limits are used. Position targets are projected into 82% of the current total PD-plus-feedforward effort budget.
- The original lion mask and karakusa cloak are a rigid, torso-mounted 0.45 kg costume. There is no simulated hand grasp, articulated jaw or fabric dynamics. Costume/stage decoration has no collision geometry; robot-to-floor contact is physical.

## Reproduce

Use Python 3.10 or 3.11 and the pinned dependencies.

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
bash run.sh
```

On Windows, activate the corresponding Python environment, install the requirements and run `run.ps1`.

`run.sh` checks the controller contract and independent gravity calculation, evaluates all active/neutral starts and stress trials, then renders the successful **seed-1008** episode. It refuses to render a failed demonstration. The benchmark reports failures; it does not assert that this WIP routine succeeds on every start.

```sh
python3 tests/test_policy.py
python3 tests/test_policy.py --benchmark
python3 run.py --seed 1008 --render
python3 run.py --seed 1008 --neutral
```

`scene.xml`, all assets and the balance model are included. `python3 build_scene.py` regenerates the scene, original costume, texture and exported `assets/g1_dynamics.json`. On headless Linux, configure an EGL or OSMesa OpenGL context for rendering. `video_v2.py` is the full-frame renderer; `video.py` supplies the shared font/audio helpers and retains the original layout implementation.

## Results and important failures

The stricter v2 task requires 36 seconds upright, pelvis height above 0.55 m, tilt below 0.4 rad, waist yaw/pitch ranges above 1.57/0.30 rad, both shoulder pitch ranges above 1.57 rad and both hand vertical ranges above 0.65 m.

- **Dynamic task: 9/12**, seeds 1000–1011 with independent initial joint perturbations within ±0.003 rad.
- **Neutral: 0/12** under the same dynamic task definition.
- **Brief lateral-push stress trials: 2/4**, ±10/±20 N for 0.12 s at 12 seconds.
- Seeds **1001, 1009 and 1011 failed** the dynamic task. Some failed runs include low pelvis height, joint-limit excursions or a fall. This is an intentionally disclosed WIP limitation, not a fully robust policy.
- The shown successful seed 1008 has 8.18 deg maximum pelvis tilt, 0.214 m net horizontal displacement and a positive 0.0832 rad minimum joint-limit margin.

The custom task was made substantially more demanding than v1. The v1 success count must not be carried over as a v2 reliability claim. All episodes, including failures, are retained in `evidence/benchmark.json`. This remains a demonstration of large controlled motion with limited robustness, not a hardware safety pass.

The full-frame video is a continuous real-time rendering of the evaluated seed-1008 state trajectory. The camera tracks actual root XY with fixed viewing angle/distance and displays root offset. Titles, progress and original synthesized percussion are editorial additions. The renderer cannot change the recorded physical outcome.

## Runner and qualification status

`runner/` includes a linux/arm64 ROS 2 Foxy image and adapter for the public HIM safety interface. It reads `/safety/policy_observation` and `/safety/policy_state`, obtains a checker-issued session, publishes all 29 command slots to `/safety/precheck`, and stops on abort/stale telemetry. It never publishes motor topics. Required sensors are `joint_state` and `imu`.

`g1-runner.json` identifies the exact public image archive and SHA-256. The image includes the same complete controller, model and gravity data. ROS Foxy uses Python 3.8, NumPy 1.24.4 and ONNX Runtime 1.16.3; desktop versions are pinned separately. Platform/runtime differences need their own validation.

```sh
docker buildx build --platform linux/arm64 --load -f runner/Dockerfile -t shishimai-g1:submission-v2 .
docker save shishimai-g1:submission-v2 -o submission.tar
bash runner/check_with_official_kit.sh /path/to/g1-builder-kit
```

**No physical G1 run or hardware approval exists.** Read `SAFETY_REPORT.md` for the exact v2 container attempt and historical v1 reports. A metadata inspection, model warmup or desktop success is not an official container safety pass. The physical costume, real inertia/mounting, sensor calibration, broader starts and stop behavior still require supervised qualification.

## Credits

G1 model: MuJoCo Menagerie commit `8161bba264d7fa7c99ca301e91e7fb44737676ad`, via HIM builder kit revision `e93c49267a7b6b905c6666c8c70668f8ee7ac397`. NVIDIA Balance model: GR00T WholeBodyControl commit `b042411fae38ee4d1af9aac82a37a1f8d14d6dd0`. Robot/model/font licenses and exact notices are retained; see `THIRD_PARTY_NOTICES.md`.

Original contributions include choreography/composite control, analytical gravity compensation, costume geometry and karakusa texture, festival stage, task harness, video/audio, ROS adapter and artifact packaging. The cloth is a visual approximation and the dance is culturally inspired choreography, not a recording or retargeting of a traditional performer.

