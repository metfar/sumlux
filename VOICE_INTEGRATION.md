# Σlux 0.1.0a3 — phonem integration (2026-09-22)

- External toolkit: phonem 1.6.0 / pronounce 0.6.1, GNU/Linux.
- Public edition continues to ship only green Lumen; no private Delicate asset.
- Existing preferred Uruguayan study profile `es-uy` delegates to the installed `~/.config/phonem/pronounce.json`, not an invented Uruguayan Piper model.
- In provided phonem distribution `es-uy` maps to `es_AR-daniela-high`, `length_scale=2.0`, `volume=1.0`, `extra_pauses=false`, validation `user-tested`. The user's installed config takes precedence over the distribution template.
- UTF-8 text -> phonem IPA -> pronounce Piper WAV -> ffplay; no `shell=True` or unsanitized shell pipes.
- No bundled phonem or Piper models; Σlux must be able to coexist with pre-existing installation and original profile tuning.
- Implemented: switchable phonem/eSpeak, preview, asynchronous playback, GUI PATH fallback, config persisted, unit tests.
- Pending: on-screen error reporting after worker failure, cancellation/interrupt, automatic avatar mouth animation, profile catalog, STT, real Linux/XFCE auditory test.
