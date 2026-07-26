---
name: inquiry-form-formspree
description: Wire up the Femme Events inquiry form to Formspree backend with proper React patterns.
version: 1.0.0
---

# Inquiry Form - Formspree Integration

## Overview

The Femme Events inquiry form (`src/components/Inquiry.tsx`) submits to Formspree, a no-code form backend service. The form collects: first/last name, email, event date, guest count, venue checkbox + name, and a message.

## Setup

1. Sign up at https://formspree.io (free = 50 submissions/month)
2. Create a new form, set notification email to `Karan@FemmeEvents.com`
3. Copy the endpoint URL (format: `https://formspree.io/f/{form-id}`)
4. Add to `.env` at repo root: `VITE_FORMSPREE_ENDPOINT=https://formspree.io/f/{form-id}`
5. Restart dev server

## Required Implementation Pattern

```ts
async function handleSubmit(e: FormEvent<HTMLFormElement>) {
  e.preventDefault();

  // Capture form element BEFORE any await — React nullifies currentTarget after yield
  const form = e.currentTarget;
  const formData = new FormData(form);
  // ... build data object ...

  const res = await fetch(FORM_ACTION, { method: "POST", ... });

  if (res.ok) {
    form.reset(); // safe — captured reference, not e.currentTarget
  }
}
```

## Common Bugs (ALREADY FIXED — but watch for regressions)

### Bug 1: `e.currentTarget.reset()` crashes after `await`
React nullifies `currentTarget` once the event handler yields control (any `await`). Always capture `const form = e.currentTarget` before the `await`, then use `form.reset()`.

### Bug 2: Animation state management for error banner
Don't use `<motion.div>` with `exit` animations for error banners unless wrapped in `<AnimatePresence>`. Simpler: just conditionally render a plain `<div>`:
```tsx
{state === "error" && (
  <div className="...">error message</div>
)}
```

### Bug 3: Preserve `motion.form` scroll animation
The original form had `whileInView` scroll-in animation. When adding `onSubmit`, keep `motion.form` (it forwards all HTML props). Don't downgrade to plain `<form>`.

## Form Component States

- **idle**: Form fields visible, button says "Send Inquiry"
- **loading**: Fields disabled, button shows spinner + "Sending..."
- **success**: Entire form replaced with confirmation panel
- **error**: Inline error banner appears above form fields, form stays editable

## Related Issues
- Issue #8: Wire up inquiry form to submission backend
- Issue #35: Set up Formspree endpoint (one-time config)
- PR #34: Main PR for this feature