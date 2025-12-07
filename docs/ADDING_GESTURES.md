# Adding New Gestures

Use this checklist to create and expose a new gesture in the WebSocket API.

## Steps
1) Open `robot_gestures.py`.
2) Add a method on `GestureController` (e.g., `def wave_right(self):`).
   - Use existing methods as a template.
   - Keep blocking `time.sleep` short (≤0.5s) to avoid WebSocket ping timeouts.
   - For simulation-only testing, keep the `if not MOTORS_AVAILABLE` branch informative.
3) If you need new targets, extend `LIMITS` near the top (e.g., add a new key or new positions under an existing motor).
4) Register the gesture in `GESTURES` at the bottom:
   ```python
   GESTURES = {
       # ...existing
       "wave_right": gesture_controller.wave_right,
   }
   ```
5) Restart the server so the registry reloads.
6) Call it from a client:
   - WebSocket payload: `{ "action": "gesture", "gesture": "wave_right" }`
   - CLI client: `python robot_client.py --gesture wave_right`

## Tips
- Motors: Head uses `head_motors.move(motor_name, position, speed)`. Torso uses `torso_motors.arm_move(name, position, step)`. See comments in `robot_gestures.py`.
- Safety: Keep eyelids open when eyeball is not centered to avoid collision (see `motion_tests_run.py` notes).
- Simulation: Without hardware, the methods print `[SIMULATION] ...` but still return success so you can test end-to-end.
- Timing: For multi-step gestures, use small sleeps between moves (0.1–0.5s) instead of large delays to keep the server responsive.
- Calibration: If hardware changes, recalibrate the numeric positions in `LIMITS` before adding new gestures.
