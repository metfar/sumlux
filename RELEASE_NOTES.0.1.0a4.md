# Σlux 0.1.0a4 — Names and chat keyboard

- The **Enviar** button is now the default in chat. Focus returns to the chat input when opened and after replies; Enter sends, not “Modelo y voz…”.
- One-time, optional preferred-name prompt on the next launch for new and old installations; persisted at `$XDG_CONFIG_HOME/sum/lux.toml`.
- Name and optional TTS-only phonetic form can be edited in Preferences; the voice preview uses these fields. Example: displayed `William` and spoken `Uiliam`.
- The configured name is supplied to the model in its system message. It does not change old chat history; no personal name is bundled as a default.
- Public green avatar only; previous configured phonem/es-uy profiles, chat database, and local XDG preferences are preserved.
- No bundled private artwork or model/voice files. No stale build trees or wheels in the release archive.

Qt's live keyboard and phonem playback require a check on the target XFCE machine.
