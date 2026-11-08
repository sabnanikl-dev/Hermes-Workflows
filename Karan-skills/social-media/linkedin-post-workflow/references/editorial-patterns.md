# Editorial patterns and source anchors

Examples illustrate voice and reasoning; do not repeat them as boilerplate. Project evidence and publishing state remain in their project files.

## Effective patterns

**Concrete opening**
> My AI assistant lives in a Telegram conversation. But I care just as much about what happens behind that conversation.

A familiar experience with a reason to keep reading. Avoid unearned “This changed everything” claims.

**Personal thesis**
> For me, it’s the ability to shape the system around how I work.

Develop with project context, reusable instructions, review standards and approval boundaries. Explain the benefit, not merely a preference for open source.

**A feature translated into value**
> When we figure out a useful process, we can save it as a reusable skill instead of starting over in the next conversation.

A saved procedure is context for future work, not model retraining or guaranteed perfect memory.

**Purpose-based distinction**
> A project repository holds the work. The second brain connects the knowledge around that work.

When differentiating two of Karan's own systems (e.g. project repository vs. second brain), distinguish by purpose — deliver this project vs. carry learning forward — and acknowledge honest overlap rather than claiming a technology-exclusive boundary.

**Honest tradeoff**
> Running the agent on my computer also doesn’t mean everything stays local: cloud models still receive the context sent to them.

Connect privacy to specific data/access decisions and acknowledge maintenance. Do not claim self-hosting is universally safer.

**Clear conclusion**
> For me, a personal AI assistant should fit how I work—and let me decide what it can access, what it should remember, and when it needs to ask first.

Joins personalization, privacy and control in language a novice understands.

## Failure modes

- **Résumé disguised as a post:** listing projects/frameworks without a useful lesson. Select one workflow and explain a transferable decision.
- **Abstract enterprise analogy:** “You don’t need an enterprise IT department to ask where your data goes” needed explanation. State directly what the individual should understand/control. Enterprise governance can supply practical questions, but should not obscure the point.
- **False feature exclusivity:** do not claim only Hermes remembers things, uses tools or works in the background. Check competitors; differentiate flexibility and tradeoffs.
- **Manufactured proof:** a realistic-looking fake Telegram exchange remains illustrative. Prefer actual media and label mockups. Never infer achieved metrics from a simulated exchange.
- **Confusing intent with results:** a clip ending with “I’ll merge it” shows intent after approval, not a verified merge. Limit the description to what footage establishes unless additional evidence exists.
- **Revision drift:** do not let a requested security paragraph erase the customization thesis Karan liked. Preserve accepted parts and edit the targeted portion.
- **Agent without a home:** describing a specialist agent (e.g. Karan's DevOps engineer) through its permissions alone left readers unclear on what it is, and centering the tool (OpenRig) instead was also rejected. Karan wants the storyline to be the real project being built (e.g. "how I'm using OpenRig to build Lead Distro"): the project and its delivery flow lead, the tool is the how, and individual agents appear as members of that flow. Ground in the repo's conventions/PR history. One storyline per post; cut side agents that dilute it. Confirm client permission before naming a client-owned product. For OpenRig/team posts, Karan wants the team itself (seat locations, jobs, communication channels, task flow, approvals) — not the product's slice plan or build progress. Ground in `~/.openrig/specs/*/CULTURE.md`, rig specs and hosts.yaml.
- **Example crowding the takeaway:** when the concrete example needs more explanation than the lesson it proves, compress it to its supporting role (what was researched, tried, learned) and let the central benefit lead. A post that spends more words explaining the example than the takeaway becomes a post about the example.

## Series angles to adapt

- Personalized assistant via messaging: useful context and tools behind a familiar interface.
- Project brief: what the AI must not guess; give readers a usable brief.
- Where not to use AI: predictable automation versus interpretation.
- Claude Code builds/Codex reviews: separate creation from checking, with tests and human acceptance.
- Skills: make corrections reusable and inspectable.
- Profiles: responsibilities, context and permissions rather than a theatrical AI org chart.
- Product case study: business requirements through small testable features; label unfinished work.
- Build-versus-adopt retrospective: retrieve the actual reason for a switch rather than inventing frustration, failure or superiority.

## Bounded continuity locators

Existing workspace: `/Users/creator/projects/consultancy/linkedin-review-2026-10-24/`.

Read only relevant exact artifacts:
- `linkedin-series-plan.md`: proposed series, not a current publishing ledger.
- `linkedin-post-01-video-draft.txt`: approved caption/voice example.
- `linkedin-post-01-verified.json`: publication verification locator.
- `client-product-evidence.md`, `agentic-portfolio-evidence.md`, `lead-distro-delivery-evidence.md`: dated evidence audits, not current runtime truth.

Source paths/private evidence URLs are internal, not public copy. If artifacts move, retrieve their current canonical owner instead of turning this reference into a stale status tracker.
