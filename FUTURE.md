# Future Improvements

## Spectacle `_anim.tla` generation

Generate a `Spec_anim.tla` file compatible with [Spectacle](https://github.com/will62794/spectacle) as an alternative to the HTML playground. Uses the SVG module to define visuals in TLA+ itself. Two triggers: offer it as an option alongside the HTML playground for users who prefer Spectacle's native UI, and auto-generate it as a fallback when the state space exceeds the playground threshold (>50K states) instead of just suggesting the user open their `.tla` in Spectacle directly.
