# Design GBU — Sources drawer usability (ARIA, founder-triggered)

- **Reviewer:** `ux-design` (ARIA) · mode `gbu` · trigger: founder — "search is very not
  intuitive; results should be in the bottom folder view"
- **Verdict on the shipped version:** **REVISE** — functional but violates its own mental model.
  Redesign (below) implemented same-session.

## GOOD (keep)

- Server-side folder browsing (the only honest way for a local web app), git-repo badges,
  dot-folders visible, LHS dock placement, bulk select, in-app confirms.

## BAD (the weaknesses — each with its fix)

1. **Two competing result surfaces.** The autocomplete dropdown floated OVER a folder list that
   shows near-identical rows — the user reads two answers to one question. → **ONE surface:**
   whatever you type drives the bottom folder view. The dropdown is deleted.
2. **One input, three unlabeled jobs** (manual path / completion / search) — no signal which
   mode you're in. → File-manager model: the input is a **location-and-filter bar**. Contains
   `/` → the list shows THAT folder (typing descends live, last segment prefix-filters); bare
   word → filters the current folder. The list always answers the input.
3. **Two verbs for one action** ("+ Add" button vs "+ use" rows). → One verb everywhere:
   **+ Add**. Rows add; the bar adds the current folder.
4. **You can't see where you are.** The path bar was truncated text, not navigation. →
   **Clickable breadcrumbs** — every segment jumps there — plus "＋ Add this folder".
5. **No dirty-state.** After toggling roots nothing says "Apply is needed" → the **Apply button
   glows** until the next ingest applies the changes.
6. **Roots rows carry no weight.** No note counts, disabled rows look identical. → per-root
   note counts from the live graph; disabled rows dim.

## UGLY (accepted)

- Prefix-filtering happens client-side over one directory listing (≤200 entries) — fine for a
  filesystem browser; server search-all-descendants is a non-goal (surprise + cost).
- `GET /fs/complete` stays for API compatibility/tests though the UI no longer uses it.

## Pattern recorded

**"The list answers the input"** — one query surface, one result surface, location = breadcrumb.
Applies to any future picker in SYNAPSE.
