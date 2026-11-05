# Third-party notices

## Unitree G1 and MuJoCo Menagerie

Source: https://github.com/google-deepmind/mujoco_menagerie/tree/8161bba264d7fa7c99ca301e91e7fb44737676ad/unitree_g1

The robot geometry, meshes, physical description and original scene elements retain Unitree Robotics' BSD-3-Clause-style license in `assets/g1/third_party/unitree_g1/LICENSE`. The Menagerie repository is Apache-2.0, while the robot assets retain the Unitree notice. The original MJCF received from the public HIM kit is retained as `assets/g1/g1_original.xml`; `scene.xml` adds the original costume/stage and applies the public HIM profile's effort limits.

## NVIDIA GR00T WholeBodyControl Balance model

Source: https://github.com/NVlabs/GR00T-WholeBodyControl

Revision: `b042411fae38ee4d1af9aac82a37a1f8d14d6dd0`.

`models/balance.onnx` is unchanged and retains the **NVIDIA Open Model License Agreement**, last modified October 24, 2025, reproduced in full as `models/LICENSE`. This model is not covered by this project's MIT license. Exact SHA-256: `f645da599d4ca3d29ed273c8f4712620bb680d34977469ca3aeabe5bb9631c18`.

## HIM public G1 builder kit

Source: https://arena.himrobotics.com/policy-contracts/g1-builder-kit-e93c492-v1.zip

Revision: `e93c49267a7b6b905c6666c8c70668f8ee7ac397`.

`vendor/him/balance_policy.py`, `vendor/him/hardware_constants.py`, `assets/g1_profile.json` and `runner/him_safety_interfaces/` are copied from this simulation-oriented public kit. These files and their existing package notices retain their upstream terms; this project's MIT grant applies to original contributions only. The complete original kit is downloadable from the link above. Its repository/asset fingerprints are recorded in `evidence/provenance.json`. No hardware launcher, motor transport, account configuration or session data is distributed.

## Zen Old Mincho font

Source: https://github.com/google/fonts/tree/main/ofl/zenoldmincho

`assets/fonts/ZenOldMincho-Regular.ttf` is supplied under the SIL Open Font License 1.1, reproduced as `assets/fonts/OFL.txt`. No font modifications were made.

## Runtime dependencies

MuJoCo, NumPy, ONNX Runtime, Pillow, imageio and imageio-ffmpeg retain their own licenses. Container runtime components retain their upstream licenses, including ROS 2, Ubuntu and the inference runtime. Dependency code is installed from its public distribution and is not relicensed by this project.
