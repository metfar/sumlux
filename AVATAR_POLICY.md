# Σlux — Avatar distribution policy

Date: 2026-09-22

## Public distribution (implemented in 0.1.0a2)

- The public avatar is the green, videogame-style Lumen character.
- Public assets: `sumlux/assets/Lumen-OpenPets.zip` and its corresponding `spritesheet.png`, plus its `pet.json`.
- The private Lumen Delicate artwork is not included in public source packages, wheels, or release archives.
- The runtime does not automatically load fallback sprites from a pre-existing `build/` directory or an installed private asset bundle.

## Release check

Before publishing a public archive, inspect the **generated artifact** and assert that it contains no private avatar assets, no stale `build/` tree, and no previously built wheels.
