# SHISHIMAI — The Lion, Reawakened

獅子舞を、Unitree G1の全身制御で。

A free-standing Unitree G1 performs a 36-second Japanese lion-dance-inspired routine: awakening, a greeting bow, left/right mie, rhythmic head shakes and a final blessing. An original red lacquer-style mask, white mane and green karakusa-pattern cloak turn the standard humanoid into a single-performer shishi. The robot's waist supplies the expressive head movement without adding a neck motor.

Created for [HIM Robotics Open Build Challenge](https://arena.himrobotics.com/challenges/open-build), deadline November 15, 2026, 11:59 PM ET. Entrant: Hiroaki Machida. Developed with coding-agent assistance.

## What actually runs

- Real MuJoCo gravity, contact and 29 joint actuators. Floating pelvis, no weld, mocap body, scripted root motion or support force.
- `policy.py`: `reset()` and `act(observation) -> {q,dq,kp,kd,tau}`. All outputs have 29 slots in the public HIM G1 motor order. The policy runs at 50 Hz and physics at 500 Hz.
- The observation contains joint positions/velocities, pelvis quaternion wxyz and body-frame gyro. The controller never receives world position, floor contact, camera images or future simulator state.
- Scripted waist/arm choreography is combined with the **unchanged, pretrained NVIDIA GR00T WholeBodyControl Balance ONNX** for the 12 leg targets. No model was trained for this project. The network's waist outputs are replaced by choreography; IMU heading feedback also adjusts hip yaw. This is a composite controller, not a newly learned dance policy.
- Public HIM profile gains, position limits and torque limits are used. Each position target is projected into 82% of the current PD demand budget. Legs may respond quickly; the artistic upper-body targets are rate limited.
- The 0.45 kg costume is a rigid torso-mounted prop with explicit inertia. It is **not held by a simulated grasp**. The cloak is a rigid visual mesh with no fabric dynamics or collision. Robot-to-floor contact remains enabled; the costume has no collision geometry.

## Reproduce

Python 3.10 or 3.11 is recommended. Install the pinned dependencies:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
bash run.sh
```

Windows: activate a Python 3.10/3.11 environment, install the same requirements and run `powershell -ExecutionPolicy Bypass -File run.ps1`.

`run.sh` checks the policy contract, runs the seeded task/neutral comparisons and generates `result.mp4` from the evaluated seed-1000 trajectory. On headless Linux, use `MUJOCO_GL=egl` with a compatible GPU driver, or `MUJOCO_GL=osmesa` with Mesa installed. Rendering requires an OpenGL context. The checked-in `scene.xml`, assets and model make no runtime network requests.

Quick evaluation without rendering:

```sh
python3 run.py --seed 1000
python3 run.py --seed 1000 --neutral
```

To regenerate the original costume and stage from code, run `python3 build_scene.py`. The published scene is already included. Video typography uses the bundled OFL-licensed Zen Old Mincho font. Percussion is synthesized procedurally by `video.py`; it is original sound design, not a recording of a traditional performance.

## Evidence and task definition

`evidence/benchmark.json` is the authoritative custom task report. Each episode lasts 36 seconds. Task success requires the pelvis to remain above 0.55 m, tilt to remain below 0.4 rad, and the measured **waist** yaw/pitch ranges to exceed 0.45/0.12 rad. Both the active and neutral policies use identical seeded starts and the same learned standing controller. Neutral disables the choreography, so standing alone does not pass.

The nominal protocol uses seeds 1000–1011 with independent joint-position perturbations uniformly sampled within ±0.003 rad. This is a small reset perturbation, not broad domain randomization. Four additional ±10/±20 N sideways pushes, applied for 0.12 s at 12 s, are reported separately as stress characterization; their outcomes do not change the nominal task definition.

The video is a continuous real-time rendering of the saved successful episode. The renderer replays actual evaluated joint/base states; it cannot change the outcome. Titles, the progress bar and audio are editorial additions. Frame indices map directly to simulation time, and the camera stays fixed so physical motion remains visible.

Inspect `evidence/episode.json`, `evidence/benchmark.json`, `evidence/video-check.json`, `evidence/provenance.json` and any included `evidence/container-*` reports. Custom task tests, official container screening and physical qualification are distinct.

## Robot-runner package

`runner/` contains a ROS 2 Foxy safety-interface adapter and a linux/arm64 Dockerfile. It reads `/safety/policy_observation` and `/safety/policy_state`, requests a checker session, publishes all 29 command slots to `/safety/precheck`, uses increasing sequences and the current observation ID, and stops publication on abort or stale telemetry. It never writes to Unitree motor topics. Initial commands hold the measured pose until the host reports `control_ready`.

The standard joint/IMU interface is sufficient; no camera, external tracker or base-position source is required. The costume is an additional physical requirement: a real prop, its mounting, true mass/inertia, clearance and thermal effects require separate engineering and qualification.

Build with:

```sh
docker buildx build --platform linux/arm64 --load -f runner/Dockerfile -t shishimai-g1:submission-v1 .
docker save shishimai-g1:submission-v1 -o submission.tar
```

The ROS Foxy image uses Python 3.8, NumPy 1.24.4 and ONNX Runtime 1.16.3; the desktop evaluation uses the pinned versions in `requirements.txt`. The controller source and ONNX bytes are the same; runtime/platform differences require their own container test.

Use the [official G1 builder kit](https://arena.himrobotics.com/policy-contracts/g1-builder-kit-e93c492-v1.zip) at revision `e93c49267a7b6b905c6666c8c70668f8ee7ac397`. Copy `submission.tar` and this complete scene/assets under `containers/upload/`, then run:

```sh
bash sim.sh --seconds 60 --scene containers/upload/environment/scene.xml --output containers/sim/output/standing
bash sim.sh --seconds 60 --scene containers/upload/environment/scene.xml --counterfactuals --output containers/sim/output/counterfactuals
```

No hardware deployment is authorized by this project. A container build is not a safety pass. Read `SAFETY_REPORT.md` and the actual reports for the exact validation status.

## Limitations

This is simulation-only. The dance is scripted and uses a third-party learned balance component. Foot shuffling/drift is possible; the task measures upright completion rather than station keeping. Initial-state perturbations and disturbances are narrow. Self-contact uses the supplied simplified model. The 36-second artistic demonstration does not prove hour-long stability, sensor robustness, costume mechanics, fabric safety or hardware readiness. Real G1 execution needs supervised qualification of the exact container and physical prop.

## Provenance and credits

The G1 geometry comes from MuJoCo Menagerie commit `8161bba264d7fa7c99ca301e91e7fb44737676ad`, via the public HIM builder kit. Unitree's notices are preserved in `assets/g1/third_party/unitree_g1/`. The NVIDIA model is from GR00T WholeBodyControl commit `b042411fae38ee4d1af9aac82a37a1f8d14d6dd0`; its exact digest and NVIDIA Open Model License are included in `models/`. The policy's observation packing follows the public HIM balance adapter and NVIDIA's Gear WBC contract.

Original work: choreography/composite controller, costume geometry and karakusa texture, festival stage, task harness, video design/audio, ROS adapter and packaging. See `THIRD_PARTY_NOTICES.md` for the boundaries between these contributions and third-party assets.
