# Semantic Negative Space in Deterministic Validators

Use this when a validator repair introduces a parser or structured-tree traversal.

## Durable lesson

Syntactically parsing more cases can still create semantic false positives. A validator must inspect the active surface named by its contract, not every node exposed by the parser.

## Required probe matrix

For HTML attribute/metadata validators, test:

- quoted, single-quoted, and unquoted attributes;
- reordered and mixed-case attributes;
- named, decimal, hexadecimal, and literal character forms;
- commented-out markup;
- inert `<template>` content;
- active document/head placement;
- missing and irrelevant attributes.

Nodes under `template.content` are inert document-fragment content. Recursively traversing that subtree can misclassify inactive declarations as active browser metadata.

## Review disagreement rule

A passing reviewer does not rebut a concrete failing reproduction it did not attempt. When two independent lanes disagree:

1. freeze both exact artifacts at the same head;
2. identify the precise untested dimension;
3. require an Integration Auditor to reproduce the disputed input independently;
4. compare implementation behavior with browser/runtime semantics and the governing contract;
5. adjudicate from the reproduction rather than averaging verdicts;
6. apply the smallest semantic fix plus one full-path regression;
7. rerun exact-head proof after any code/docs/test change.

## Scope discipline

Keep finite validators finite. A parser replacement should close the named bypass without becoming a general language or DOM framework. Update comments/docs to describe active semantics accurately, and test inert controls so future hardening cannot widen scope silently.
