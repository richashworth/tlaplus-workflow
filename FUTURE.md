# Future Improvements

## Spectacle `_anim.tla` generation

Offer an alternative to the domain-specific HTML playground: generate a `Spec_anim.tla` file compatible with [Spectacle](https://github.com/will62794/spectacle). Uses the SVG module to define visuals in TLA+ itself. Useful for TLA+ power users who prefer exploring specs in Spectacle's native UI.

## Spectacle fallback for large state spaces

When the state graph exceeds the playground threshold (>50K states), automatically generate a `Spec_anim.tla` file for Spectacle instead of building the HTML playground. Currently we just suggest the user open their `.tla` in Spectacle directly — this would provide a better experience with pre-configured visuals.

## Contribute invariant checking to Spectacle

Spectacle's JS interpreter can evaluate arbitrary TLA+ expressions but doesn't evaluate invariants in the UI. Contributing this upstream would make Spectacle useful as a standalone verification tool, not just an explorer.
