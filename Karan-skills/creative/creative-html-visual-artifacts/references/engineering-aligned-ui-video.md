# Engineering-aligned scripted UI videos

Use when a user wants an end-to-end app/process video but the source is an engineering design or static concept rather than an implemented app.

## Truth boundary

- Retrieve the canonical design and original scenario before storyboarding; a meeting brief alone may omit critical invariants.
- Distinguish **recording a real app** from **rendering a scripted UI simulation**. When the app does not exist, keep a persistent on-screen simulation / fictional-data / not-live banner and state this in narration and handoff.
- A local video prototype is not permission to build/deploy the production product or connect real/client data.
- Trace each scene to source sections. Preserve exact baseline fixtures; label what-if branches separately and return explicitly to the main scenario. Never blend original recommendations, later overrides, approvals and publication into one state.
- Use source-defined error identifiers only when presenting them as API codes. Human UI messages can use ordinary words instead of invented uppercase codes.

## Artifact pattern

Keep the video, editable storyboard, self-contained HTML visual source, narration transcript, actual synthetic export and verification sidecars under the established project artifact directory. Preserve original design/brief bytes. This is a reusable project media asset, not automatically new wiki/business policy.

1. Write `storyboard.json`: stable scene ID, title, role, evidence mode, concise caption, narration, source-section refs and exact visual-state transitions.
2. Build standalone HTML with `window.renderScene(index, progress)` for deterministic state, cursor, click-ring and typed-text rendering. No network dependencies or real account actions. Offer silent play/pause/next/back controls for the source handoff and hide transport in recording mode.
3. Use a fixed 16:9 stage such as 1600×900. Reserve a chapter/caption region. Keep role/mode visible and primary app text readable; this should look like using the proposed app, not lecture slides.
4. Generate narration and measure actual clip durations. On macOS, local `say -v Samantha -r 170 -f scene.txt -o scene.aiff` is an available offline option. Native `afinfo` reports duration even for AIFC variants that Python `aifc` rejects. Pad/resample with a tested ffmpeg and derive frame counts from measured audio, not guessed words-per-minute.
5. Start an owned ephemeral localhost server and an isolated Chrome profile. Use local CDP/WebSocket when the browser tool cannot access localhost. Verify HTTP readiness and scene API, then capture actual rendered images. Never use the user's logged-in Chrome profile for local media rendering.
6. Include narrated holds for readability. Capture cursor/action transitions at a reasonable sample rate, reusing the same actual browser image during holds. Encode at a playback-compatible frame rate. Be explicit that this is a scripted visualization, not a continuous recording of a functioning backend.
7. Pipe JPEG browser captures to ffmpeg image2pipe; mux narration to H.264/yuv420p + AAC MP4 with `+faststart` and chapter metadata. Audio and timeline frame counts should reconcile.

## Practical runtime pitfalls

- Exercise `ffmpeg -version` before starting work. A command existing on PATH does not prove its linked libraries are available. If Homebrew ffmpeg/ffprobe aborts on a missing dylib, do not mutate system packages casually. An already installed `imageio_ffmpeg.get_ffmpeg_exe()` can supply an isolated tested binary.
- Foreground and background terminals may resolve different `python3` executables. Resolve `sys.executable` where dependencies were tested and use that exact executable for background render commands. Do not infer the interpreter from OS or user memory.
- Capture-every-frame can be unnecessarily slow. Narrated holds plus short smooth transitions retain actual browser visuals while avoiding thousands of identical CDP screenshots. Keep the render finite and report active process identity; stop owned browser/server/encoder resources after failure and success.

## Acceptance

- Independently review storyboard/source fidelity before calling the video design-aligned.
- Capture every scene at representative before/mid/after states and inspect contact sheet plus native-resolution critical frames.
- **Check the app content against the reserved app-area bottom, not just viewport bounds.** Text below a fixed chapter bar may have a valid in-viewport box but be invisible. Check small provenance cards, final notices and error messages specifically.
- Do not render missing/stale evidence with the same green success styling as valid evidence.
- Exercise the source HTML's actual play/pause/next/back/keyboard controls. Check role-specific visible projections and key simulated rejection/approval/publication states, while labeling these UI checks—not backend/security proof.
- If the video shows a CSV preview, make it match the actual synthetic export. Mark a partial-column preview as such and preserve final revision/assignment identity and override reasons.
- Decode the entire encoded video and audio, check actual size/duration/codec/frame rate/audio presence, sample an actual encoded frame from every chapter, and compare those against browser references. Nonzero file size or an ffmpeg exit alone is not sufficient.
- Bind the final MP4, HTML, storyboard, timing, narration and governing source with hashes. Reviews bind exact candidate bytes; verify returned reviewer artifacts yourself.
- Deliver the actual MP4 through chat media convention. Briefly name duration, coverage and simulation limitation. Keep editable sources discoverable without flooding the user with QA files.
