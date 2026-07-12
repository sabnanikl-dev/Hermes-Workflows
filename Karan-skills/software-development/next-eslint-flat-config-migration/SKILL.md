---
name: next-eslint-flat-config-migration
description: Fix Next.js lint failures when migrating from `next lint` to ESLint CLI with ESLint 9 flat config. Covers CommonJS-vs-ESM issues, unsupported `extends`, and using FlatCompat with `eslint-config-next`.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [nextjs, eslint, flat-config, ci, debugging, migration]
    related_skills: [systematic-debugging]
---

# Next.js ESLint 9 Flat Config Migration

Use this when a Next.js repo starts failing CI after switching from `next lint` to `eslint .`, especially with errors like:
- `next lint is deprecated`
- `module is not defined in ES module scope`
- `A config object is using the "extends" key, which is not supported in flat config system`

## Root cause pattern

These failures usually mean the repo is **half-migrated**:
1. `package.json` now runs `eslint .`
2. config file is named `eslint.config.mjs` (flat-config entrypoint)
3. but the file contents still use old `.eslintrc` conventions:
   - `module.exports`
   - `extends: [...]`

That combination breaks under ESLint 9.

## Key rules

1. `.mjs` files must use ESM syntax:
   - use `export default`
   - never use `module.exports`
2. Flat config does **not** support `extends` inside config objects.
3. If consuming legacy shareable configs like `next/core-web-vitals` or `next/typescript`, bridge them with `FlatCompat`.
4. Verify by running `pnpm lint` locally before pushing.

## Fix procedure

### 1) Check scripts

In `package.json`, replace deprecated scripts:

```json
"lint": "eslint .",
"lint:fix": "eslint . --fix"
```

### 2) Install compat bridge

```bash
pnpm add -D @eslint/eslintrc
```

### 3) Rewrite `eslint.config.mjs`

Use this working pattern:

```js
import { FlatCompat } from '@eslint/eslintrc'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const compat = new FlatCompat({
  baseDirectory: __dirname,
})

const config = [
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  {
    ignores: ['.next/**', 'out/**', 'build/**', 'next-env.d.ts'],
  },
  {
    rules: {
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'import/no-default-export': 'off',
      'import/no-anonymous-default-export': 'warn',
      '@next/next/no-img-element': 'warn',
      'prefer-const': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
        },
      ],
    },
  },
]

export default config
```

## What not to do

### Wrong for `.mjs`

```js
module.exports = [ ... ]
```

This causes:
- `ReferenceError: module is not defined in ES module scope`

### Wrong for flat config

```js
export default [
  {
    extends: ['next/core-web-vitals', 'next/typescript'],
  },
]
```

This causes:
- `A config object is using the "extends" key, which is not supported in flat config system`

## Investigation notes

If unsure whether the installed Next config is still legacy-style, inspect:

```bash
read_file node_modules/eslint-config-next/core-web-vitals.js
read_file node_modules/eslint-config-next/index.js
```

If those files export legacy objects with `extends`, use `FlatCompat`.

## Verification checklist

Run:

```bash
pnpm lint
```

Expected result:
- exit code 0
- no ESLint loader/config errors

Then commit and push. After push, verify the remote PR contains the fix commit before reporting success.

## Pitfalls

- Do not assume `eslint-config-next` ships flat-config-ready objects in the installed version.
- Do not stop after fixing `module.exports` → `export default`; the next error may still be legacy `extends`.
- If `pnpm/action-setup` is also in CI, avoid duplicating pnpm version in both workflow YAML and `packageManager`.

## When this skill applies

Use this for Next.js 15/16 repos where CI breaks during lint migration and the project already has:
- `eslint@9`
- `eslint.config.mjs`
- `eslint-config-next`
- a move away from `next lint`
