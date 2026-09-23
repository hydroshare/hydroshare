# Research: Add HydroShare User as Author in the Atlas Edit Form

**Date:** 2026-08-27  
**Scope:** Feasibility of selecting a HydroShare user from the `/user-autocomplete/` endpoint and pre-populating a new Author entry in the schema-generated edit form.

---

## Background

The original Django resource landing page has long supported picking a HydroShare user from a Select2 dropdown (populated by `/user-autocomplete/`) when adding an author. The user's profile data — name, organization, email, ORCID — is then copied into the resource metadata.

The Atlas edit page (`edit-dataset.vue`) replaces this with a schema-generated form driven by cznet-vue-core / JSONForms. The Authors field is a `cz-field-modal` backed by an `ArrayLayoutRenderer`. We want to offer the same "pick a HydroShare user" shortcut while keeping manual entry working as it does today.

---

## System Inventory

### 1. The `/user-autocomplete/` endpoint

**Location:** `hs_core/autocomplete_light_registry.py`, registered in `hydroshare/urls.py`

**Implementation:** `UserAutocompleteView(autocomplete.Select2QuerySetView)` from django-autocomplete-light (DAL).

**Request:** `GET /user-autocomplete/?q=<query>`

**Response format** (Select2/DAL standard):
```json
{
  "results": [
    { "id": "123", "text": "Jane Q. Smith, CUAHSI (jsmith)" },
    ...
  ],
  "pagination": { "more": false }
}
```
- `id` — Django `User.pk` (integer, returned as string by DAL)
- `text` — constructed by `get_result_label`: `"FirstName MiddleName LastName, Organization (username)"`

**Search fields:** `username`, `first_name`, `last_name` (case-insensitive contains)

**Authentication:** Required — the endpoint is only accessible to logged-in users (DAL default; confirmed by tracking logs showing `user_type` in all request records).

**Existing usage in Vue app:** `cd.manage-access.vue` already calls this endpoint identically using a debounced `v-autocomplete` (`no-filter`, `hide-no-data`, `return-object`). The pattern is proven and in production.

### 2. What user profile data is available

`UserProfile` (in `hs_core/models.py`) stores:
| Field | Notes |
|---|---|
| `user.first_name`, `user.last_name` | Django auth fields |
| `userprofile.middle_name` | Optional |
| `userprofile.organization` | Maps to Creator `affiliation.name` |
| `userprofile.identifiers` | HStoreField — `{'ORCID': 'https://orcid.org/0000-...', 'ResearchGateID': ...}` |
| `user.email` | Maps to Creator `email` |

The ORCID value in `identifiers['ORCID']` is stored as a full URI (`https://orcid.org/...`).

> **Note:** The Creator/Contributor schema's `identifier` field is changing (see [Schema Dependency](#schema-dependency) below). In the current schema it is a bare ORCID string; after the planned change it will be an array of `PersonIdentifier` objects using the full URI as `value`. The frontend construction logic should target the new schema.

`get_access_object()` already assembles most of this into a dict that is used by the manage-access feature.

### 3. The Creator/Contributor JSON schema

```json
"Creator": {
  "additionalProperties": true,
  "properties": {
    "@type": { "const": "Person" },
    "name":  { "type": "string" },
    "email": { "anyOf": [{"format": "email"}, {"type": "null"}] },
    "identifier": {
      "pattern": "\\b\\d{4}-\\d{4}-\\d{4}-\\d{3}[0-9X]\\b",
      "description": "ORCID identifier"
    },
    "affiliation": { "$ref": "#/$defs/Affiliation" }
  },
  "required": ["name"]
}
```

Key observation: `additionalProperties: true` means we can store extra fields (e.g., `hydroshare_user_id`) on a Creator object without breaking schema validation.

### 4. How the Authors field is rendered

`edit-dataset.vue` renders:
```
cz-field-modal (scope="#/properties/creator")
  └── #summary slot (chip list + edit icon) — fully consumer-controlled
      CzField → ArrayLayoutRenderer → v-expansion-panels (one per author)
          └── dispatch-renderer → [AnyOfRenderer? / branch layouts]
```

The `data` ref (`ref<Record<string, any>>`) holds the live form data. `data.creator` is the array being edited.

`CzFieldModal` passes `options` straight through to `CzField`, which passes them to the underlying renderer. The `#summary` slot is rendered *outside* the dialog and is entirely in consumer code.

### 5. cznet-vue-core extensibility

`CzFormComposed` hardcodes its renderer list:
```ts
const renderers = Object.freeze([...CzRenderers]);
```
There is **no prop or plugin mechanism** to inject custom renderers from outside. The library would need to be modified to support that.

However, the library does **not** need to be involved at all for the "import from user" use case. The `data` ref is owned by `edit-dataset.vue`. Adding an author is simply pushing an object onto `data.creator`:
```ts
data.value.creator = [...(data.value.creator ?? []), newCreator];
```
JSONForms picks up the change reactively because `data` is a `ref`.

---

## Feasibility Assessment

### Is it feasible without modifying cznet-vue-core?
**Yes.** The `data` ref is fully accessible in `edit-dataset.vue`. Inserting a new Creator object into `data.creator` causes the form to re-render with the new item pre-populated. No library changes are needed.

### Is it feasible without a new backend endpoint?
**Yes — an existing endpoint is sufficient.** `GET /hsapi/userDetails/<user_identifier>/` (registered in `hydroshare/urls.py` at line 202) routes to `hsapi_get_user` → `get_user_or_group_data` (`hs_core/views/__init__.py`, line 2500). It accepts a username, email, or numeric user id (the DAL autocomplete returns `id` = `User.pk`, so this works directly).

The response includes exactly what is needed:
```json
{
  "name": "Jane Smith",
  "email": "jsmith@example.edu",
  "organization": "CUAHSI",
  "identifiers": { "ORCID": "https://orcid.org/0000-0001-2345-6789" },
  "url": "https://www.hydroshare.org/user/123/",
  "address": "...",
  "phone": "...",
  "website": "..."
}
```
The `url` field is assembled by `hydroshare.utils.current_site_url()` so it is domain-aware. The `identifiers` dict may contain other keys beyond ORCID (e.g., `ResearchGateID`).

**No new backend endpoint is needed.**

---

## Recommended Approach

### Architecture

A “Find HydroShare user” button placed **inside the Authors array editor modal, next to the existing “Add” button**. This is Option A: adding a `customActions` mechanism to `ArrayLayoutRenderer` in cznet-vue-core.

**Why inside the modal (not in the `#summary` slot):**
The button needs to live in the same context as the existing “Add Creator” button so the UX is cohesive — the user is already in author-management mode when the modal is open. Putting it in the `#summary` chip row is technically easier but contextually awkward.

**The `customActions` mechanism (implemented, cznet-vue-core change) — AS BUILT, differs from the original plan below:**
The first pass used `options.customActions: Array<{ label, icon?, handler: () => void }>`, with `ArrayLayoutRenderer` calling `action.handler()` directly. That doesn't work as a general library feature: `handler` is a live function reference, which can only exist when the uischema is built in code (as it is here) — a plain JSON uischema (per the [JSONForms uischema spec](https://jsonforms.io/docs/uischema/)) can't serialize a function. It also happened to only work by accident here for an unrelated reason: `ArrayLayoutRenderer` is resolved dynamically by JsonForms' internal dispatch mechanism and is never placed directly in any consumer's template, so a plain Vue `$emit` from it has nowhere to land — no template tag exists to attach a `@custom-action` listener to.

The implemented design instead:
1. `options.customActions` is plain, JSON-serializable data: `Array<{ id: string; label: string; icon?: string }>`.
2. `ArrayLayoutRenderer.vue` renders a `<v-btn>` per entry; clicking one calls an **injected** function (`inject('cz-custom-action')`, exposed as `this.customActionHandler`) with `(action.id, { path: this.control.path })`. `provide`/`inject` is used specifically because it crosses the dynamic-dispatch boundary that a template `@listener` cannot — this is the same reasoning `cz-field-modal.vue` already uses to re-provide the `jsonforms` context across Vuetify's dialog teleport.
3. `cz-field-modal.vue` (`setup()`) calls `provide('cz-custom-action', (id, ctx) => emit('custom-action', id, ctx))` — this is the bridge: it receives the call via inject (crossing the dynamic part), then re-emits it as a normal Vue `custom-action` event on `<cz-field-modal>` itself, which **is** written directly in `edit-dataset.vue`'s template, so a plain `@custom-action="..."` listener there works.
4. `edit-dataset.vue` listens for `@custom-action` on each `cz-field-modal` (Authors and Contributors each get their own listener, so there's no need to disambiguate via `ctx.path`) and dispatches on `id === "findUser"` to open the search dialog for the right field.
5. On selection → call `GET /hsapi/userDetails/<user_id>/` → construct Creator/Contributor object → push onto `data.creator` / `data.contributor`.
6. The modal closes, and the new chip appears in the summary area immediately (reactive).
7. The user can then open the normal author edit modal to adjust any pre-filled fields.

### UX Sketch

```
┌───────────────────────────────────────────────────────┐
│ Authors                                              │
│  ───────────────────────────────────────────────────  │
│  1.  Jane Smith              [expand ▾] [del]       │
│  [+ Add author]  [🔍 Find HydroShare user]          │
└───────────────────────────────────────────────────────┘
```

The “Find HydroShare user” button renders via the `customActions` mechanism next to the existing “Add author” button at the bottom of the `ArrayLayoutRenderer`.

### Backend endpoint

No new endpoint needed. Use the existing:
```
GET /hsapi/userDetails/<user_id>/
```
This calls `get_user_or_group_data` (line 2500, `hs_core/views/__init__.py`) which already returns `name`, `email`, `organization`, `identifiers` (including `ORCID` as a full URI), and `url` (the user's HydroShare profile URL, domain-aware).

### Frontend construction of Creator object

Using the new `PersonIdentifier`-based schema (see [Schema Dependency](#schema-dependency)):

```ts
async function importFromHsUser(userId: number) {
  const resp = await fetch(`/hsapi/userDetails/${userId}/`);
  if (!resp.ok) throw new Error("Failed to fetch user info");
  const info = await resp.json();

  const identifier = [];
  if (info.identifiers?.ORCID) {
    identifier.push({ "@type": "PropertyValue", propertyID: "ORCID", value: info.identifiers.ORCID });
  }
  // info.url is e.g. "https://www.hydroshare.org/user/123/"
  identifier.push({ "@type": "PropertyValue", propertyID: "HydroShareID", value: info.url });

  const creator: Record<string, any> = {
    "@type": "Person",
    name: info.name,
  };
  if (info.email) creator.email = info.email;
  if (identifier.length) creator.identifier = identifier;
  if (info.organization) {
    creator.affiliation = { "@type": "Organization", name: info.organization };
  }

  data.value.creator = [...(data.value.creator ?? []), creator];
}
```

---

## Schema Dependency

This work depends on a **planned but out-of-scope schema change** to `Creator`, `Contributor`, and `Provider` in `resource_edit_schema.json` (and the corresponding `scientific_dataset_json_schema.json`).

**Current schema** — `identifier` is a single bare ORCID string:
```json
"identifier": {
  "type": "string",
  "pattern": "\\b\\d{4}-\\d{4}-\\d{4}-\\d{3}[0-9X]\\b",
  "description": "ORCID identifier for creator."
}
```

**Planned schema** — `identifier` becomes an array of a constrained `PersonIdentifier` type:
```json
"identifier": {
  "type": "array",
  "items": { "$ref": "#/definitions/PersonIdentifier" }
}
```
Where `PersonIdentifier` is a new definition (distinct from the general `PropertyValue`) with only three fields — `@type` (const `"PropertyValue"`), `propertyID`, and `value` — and `additionalProperties: false`. This prevents the form from rendering the full `PropertyValue` field set (maxValue, minValue, unitCode, etc.) when editing identifiers.

The general `PropertyValue` definition already exists in the schema and is used elsewhere (e.g., `Place.additionalProperty`). `PersonIdentifier` is a purposely constrained variant for person-level identifier use.

Example valid `identifier` value after the change:
```json
[
  { "@type": "PropertyValue", "propertyID": "ORCID", "value": "https://orcid.org/0000-0001-2345-6789" },
  { "@type": "PropertyValue", "propertyID": "HydroShareID", "value": "https://www.hydroshare.org/user/123/" }
]
```

Note that the ORCID is stored as the **full URI** in the new schema, matching what `UserProfile.identifiers['ORCID']` stores — no stripping needed.

This schema change must be merged before (or alongside) this feature PR. The frontend construction sketch above already targets the new schema.

---

## Where the Search UI Renders (and Why the Library Is Involved)

This deserves explicit treatment because it's easy to assume the schema-generated form controls where all inputs appear. It doesn't, for this feature.

### The ownership boundary

`CzFieldModal` renders two distinct zones:

1. **The `#summary` slot** — rendered *by `edit-dataset.vue`* as a consumer-provided scoped slot. The library passes slot props but the HTML is entirely consumer code.
2. **The dialog body** — rendered by the library; contains `CzField` → `ArrayLayoutRenderer`. We have no slot into the dialog body.

The "Find HydroShare user" button is placed in zone 2, inside the `ArrayLayoutRenderer`, using the new `customActions` mechanism. The user search dialog (`v-dialog`) is declared in `edit-dataset.vue` but *opened by a handler registered via `customActions`*.

### Concrete render tree

```
edit-dataset.vue template
│
├── <cz-field-modal scope="#/properties/creator" ...>
│     ├── #summary slot (chip list only — existing)
│     └── dialog body (library-rendered)
│           └── ArrayLayoutRenderer
│                 ├── expansion panels (one per author)
│                 ├── [+ Add author]          ← existing hardcoded button
│                 └── [🔍 Find HydroShare user] ← new, via customActions
│                       clicking calls the injected `cz-custom-action` handler
│                       (provided by cz-field-modal.vue), which re-emits it as
│                       this element's `custom-action` event
│                       → edit-dataset.vue's @custom-action listener
│                       → onArrayCustomAction(id, 'creator') → hsUserDialogOpen = true
│
└── <cd-find-hydroshare-user v-model="hsUserDialogOpen" @select="onHsUserSelected">
      (own component; owns the v-dialog, search UI, import fetch, and
      iframe-viewport-alignment logic — see cd.find-hydroshare-user.vue)
      └── <v-card>
            ├── <v-autocomplete>             ← plain Vuetify
            │     calls /user-autocomplete/?q=...
            │     same pattern as cd.manage-access.vue
            └── [Add] button
                  → fetch /hsapi/userDetails/<id>/
                  → emit('select', person)
                  → edit-dataset.vue pushes onto data.creator/data.contributor
                  → close dialog
```

### Required cznet-vue-core change (as built)

`ArrayLayoutRenderer.vue` had a hardcoded Add button with no extension point. The implemented change:
- Read `appliedOptions.customActions` — plain data, `Array<{ id: string; label: string; icon?: string }>`
- Render one `<v-btn>` per entry alongside the existing Add button
- On click, call the function injected under the `cz-custom-action` key (`inject('cz-custom-action')`) with `(action.id, { path: this.control.path })`
- `cz-field-modal.vue` provides that function (`provide('cz-custom-action', (id, ctx) => emit('custom-action', id, ctx))`), re-surfacing it as a normal `custom-action` component event that a consumer can listen for directly on `<cz-field-modal>`

This is a small, non-breaking additive change, and (unlike the earlier handler-based draft) works for uischemas authored as plain JSON, not just ones built in code — `customActions` is JSON-serializable, and the actual behavior lives in the consumer's `@custom-action` listener rather than in the options object.

### What the library handles automatically after insertion

After `data.creator.push(newCreator)` is called:
- JSONForms detects the `data` change (reactive `ref`)
- `ArrayLayoutRenderer` re-renders with a new expansion panel for the new item
- The `#summary` chip list re-renders with the new entry

The library handles the *editing* experience for the newly added item inside its own modal; it is not involved in the *discovery* flow.

---

## Open Questions / Decisions Needed

1. ~~**Where does the "Find HS user" button live?**~~ **Resolved:** Inside the array editor modal, next to "Add author", via `customActions` in `ArrayLayoutRenderer`. Requires a small cznet-vue-core change.

2. **Should the same affordance appear for Contributors?**
   Yes — same pattern applies. `contributorOptions` has the same structure as `creatorOptions` and can use the identical `customActions` mechanism.

3. **What happens to the pre-filled fields if the user edits them?**
   Nothing special — once inserted into `data.creator`, the object is a plain JS object with no live link to the HydroShare user. Manual edits work normally.  This matches the existing landing page behavior where you can edit an author's info after adding via HydroShare user.

4. **Should we store `hydroshare_user_id` on the Creator object?**
   The `HydroShareID` `PersonIdentifier` entry (containing the user's profile URL) already serves as an implicit link. Storing a separate `hydroshare_user_id` integer is redundant and adds schema noise. Recommendation: don't.

5. ~~**ORCID URI vs bare identifier**~~ **Resolved by schema change:** The new `PersonIdentifier`-based schema stores the full URI as `value`. No stripping needed. `UserProfile.identifiers['ORCID']` maps directly to `value`.

---

## Summary

| Factor | Assessment |
|---|---|
| Feasible? | ✅ Yes |
| Existing precedent in codebase? | ✅ Yes — `cd.manage-access.vue` uses the identical autocomplete pattern |
| New backend code required? | ✅ None — existing `/hsapi/userDetails/<id>/` is sufficient |
| cznet-vue-core change required? | ⚠️ Yes — small additive change to `ArrayLayoutRenderer.vue` to support `customActions` |
| Schema change required? | ⚠️ Yes — `Creator`/`Contributor`/`Provider` `identifier` field changing to `PersonIdentifier` array (out of scope, must land first) |
| Risk to existing manual entry flow? | ✅ None — completely additive |
| Complexity | Low–medium |
| Estimated touchpoints | `cznet-vue-core/ArrayLayoutRenderer.vue`, `edit-dataset.vue`, `resource_edit_schema.json`, `scientific_dataset_json_schema.json` |

---

## Implementation Plan

### Prerequisites (separate PRs, must land first)

- [ ] **Schema change** — update `Creator`, `Contributor`, and `Provider` `identifier` field in `resource_edit_schema.json` and `scientific_dataset_json_schema.json`:
  - Add `PersonIdentifier` definition (`@type`, `propertyID`, `value` only; `additionalProperties: false`)
  - Change `identifier` from `{type: string, pattern: ...}` to `{type: array, items: {$ref: PersonIdentifier}}`

### Step 1 — cznet-vue-core: add `customActions` to `ArrayLayoutRenderer` ✅ IMPLEMENTED (design revised from original plan)

The original plan (handler functions called directly by `ArrayLayoutRenderer`) was replaced after review: functions aren't valid JSON-uischema data, and — separately — `ArrayLayoutRenderer` is never placed in a consumer's template (JsonForms mounts it dynamically via `<dispatch-renderer>`), so it has no template tag for a plain `$emit` to reach. The as-built design uses `provide`/`inject` to cross that dynamic-dispatch boundary, then a normal Vue emit for the final hop into the consumer's template — see [Where the Search UI Renders](#where-the-search-ui-renders-and-why-the-library-is-involved) above for the full reasoning.

**Files:** `src/renderers/layouts/ArrayLayoutRenderer.vue`, `src/components/cz.field-modal.vue`

- `ArrayLayoutRenderer.vue`:
  - `customActions` computed: `appliedOptions.customActions || []`, typed as `Array<{ id: string; label: string; icon?: string }>` (plain data, no functions)
  - `inject: { customActionHandler: { from: 'cz-custom-action', default: null } }`
  - Renders a `<v-btn>` per entry in the button row alongside Add; `@click="fireCustomAction(action)"`
  - `fireCustomAction(action)` calls `this.customActionHandler?.(action.id, { path: this.control.path })`
- `cz.field-modal.vue`:
  - `emits: ['custom-action']`
  - In `setup(props, { emit })`: `provide('cz-custom-action', (id, ctx) => emit('custom-action', id, ctx))`
  - No changes needed to `CzField` or any other component
- Rebuild: `nvm use 22 && npm run build` in `/Users/callie/src/cznet-vue-core/` (memory note: earlier guidance said `nvm use 18`; corrected to `22`, which matches `package.json`'s `engines.node: "^24.3.0"` compatibility range used in practice)

### Step 2 — `edit-dataset.vue` + `cd.find-hydroshare-user.vue`: search dialog wired via `@custom-action` ✅ IMPLEMENTED (extracted into its own component)

The dialog was initially inlined directly in `edit-dataset.vue`, then extracted into its own component (`cd.find-hydroshare-user.vue`, mirroring the existing `cd.manage-access.vue` pattern) once it became clear the file was accumulating unrelated dialog/search/fetch logic.

**File:** `discovery-atlas/frontend/src/components/landing-page/cd.find-hydroshare-user.vue`
- Owns: the `v-autocomplete` search against `/user-autocomplete/?q=...` (300ms debounce, same pattern as `cd.manage-access.vue`), the import fetch (`GET /hsapi/userDetails/<user_id>/`), Creator/Contributor object construction (name, email, affiliation, `identifier` array with ORCID + HydroShareID `PersonIdentifier` entries), and the iframe-viewport-alignment fix (same technique as `cd.manage-access.vue`'s `alignDialogToParentViewport`, plus restoring the parent's scroll position on close so the page doesn't end up scrolled past Authors).
- Props: `modelValue: boolean` (dialog open/closed). Emits: `update:modelValue`, `select` (with the constructed person object).
- The confirm button is labeled **"Add"**, not "Import" (per review feedback).

**File:** `discovery-atlas/frontend/src/components/landing-page/edit-dataset.vue`
1. `creatorOptions` / `contributorOptions` each get `customActions: [{ id: "findUser", label: "Find HydroShare user", icon: "mdi-account-search" }]` — plain data, no handler function.
2. Each of the Authors/Contributors `<cz-field-modal>` elements gets its own listener: `@custom-action="(id) => onArrayCustomAction(id, 'creator' | 'contributor')"`. Because each modal is wired individually, there's no need to disambiguate targets via the emitted `ctx.path` — the closure already knows which field it's for.
3. `onArrayCustomAction(id, target)` opens the dialog (`hsUserDialogOpen = true`, `hsUserDialogTarget = target`) when `id === "findUser"`.
4. `<cd-find-hydroshare-user v-model="hsUserDialogOpen" @select="onHsUserSelected" />` is placed once in the template; `onHsUserSelected(person)` pushes onto `data.value[hsUserDialogTarget.value]`.
