# Convergence plan — documentation and repo hygiene

**Type:** status and work plan. Non-normative. The binding rules are
[`agent-workflow.md`](../../../freetheplatform/_docs/agent-workflow.md) and the
ownership rule in
[`freetheplatform/_docs/README.md`](../../../freetheplatform/_docs/README.md).

**Every row landed on 2026-09-25.** DH-1 through DH-7 and DH-9 here; DH-8, the
three `deprecated_*` documents, in [`dead-code.md`](dead-code.md) DC-10, which
owned it.

What is left in this file is not work. It is a boundary decision other plans
lean on, and four findings the rows did not carry. Delete it once
[`README.md`](README.md) and [`testing.md`](testing.md) stop linking here.

## What the survey did not anticipate

Recorded because the next person to audit this repository will hit the same
thing, and because two of these changed the shape of the work.

**Three subsystems had been removed from the code and left standing in the
prose.** Not drifted — removed. There is no `Store` model, no store grouping,
no IGA support and no GS1 prefix scrape, and `Price` is keyed
`(product, company)` with one row per chain. The survey counted six broken
links and four stale files; the real number was eight of the eleven documents
audited, and almost every stale claim traced back to one of those three
removals.

**`store_grouping.md` could not be written.** The plan asked for it on the
grounds that the README headlined it as one of the two most interesting pieces
of engineering in the codebase. The clustering system it describes no longer
exists, so there was nothing to document; the README's second slot went to
[`optimization.md`](../optimization.md) instead, which is a live subsystem and
arguably the actual product. `gs1.md` went the same way: the prefix-inference
idea the README invited contributions to was removed along with the rest of
the GS1 code.

**`_docs/TESTING.md` §4 described a fixture that does not exist.** No root
`conftest.py`, no `drf_request_factory`, anywhere in the repository. Worth
knowing that a document can be wrong about its own subject and still read as
authoritative for a year.

**The translation-table fetch is not ETag-cached.** Four documents said it was.
The server sets an `ETag`; the client never sends `If-None-Match`, and two
tests in `scraping/tests/util_tests/test_python_file_downloader.py` pin exactly
that. This is the one correction that is a live performance fact rather than a
documentation defect: a 10MB table is re-downloaded on every scrape run.

## The strategy boundary

splitcart depends on `@freetheplatform/web-security` and on nothing else from
that repository — in particular not the `freetheplatform` Python package. Being
almost entirely outside the shared-package graph is the root of several gaps in
the other plans rather than a separate problem.

Verdicts on each shared capability, applying strategy.md's tests:

| Capability                     | Verdict       | Reason                                                                               |
| ------------------------------ | ------------- | ------------------------------------------------------------------------------------ |
| `web-security` CSP + sanitiser | **adopt now** | splitcart emits no CSP at all. Cheapest real security win available.                 |
| Security bounds table          | **adopt now** | Closes a live blind spot; see [`forms.md`](forms.md) FM-4.                           |
| Auth / cookie-JWT sessions     | adopt later   | Large migration with a live blast radius — [`auth-migration.md`](auth-migration.md). |
| Component registry             | adopt later   | Blocked on tokens — [`registry.md`](registry.md).                                    |
| Messaging / email              | stays local   | No shared need demonstrated.                                                         |
| Search Console reporting       | adopt later   | No measurement plumbing here yet.                                                    |
