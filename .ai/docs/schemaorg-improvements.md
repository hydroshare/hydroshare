# HydroShare schema.org Improvements for FAIR Compliance

## Motivation

HydroShare resource landing pages embed schema.org JSON-LD to support
discovery and FAIR compliance. The DataONE MetaDIG suite validates datasets
against a set of FAIR checks, and the key component it uses is the embedded
schema.org tag on the resource landing page. This PR is intended to ensure
that all metadata HydroShare already captures and that is relevant to the
MetaDIG checks is actually exposed in that tag. This provides a baseline for
the suite. In the future we can measure improvements to the amount of metadata
users add compared to this baseline.

## What Changed

The changes are limited to how the resource landing page is rendered — no
changes to the database model or stored metadata.

- `hs_core/templates/pages/baseresource.html` — the section of the page that
  embeds machine-readable metadata was extended with the new fields below;
  the legacy `about` block that emitted URL-valued geospatial relations as bare
  `Place` objects was removed (those relations are now covered by the explicit
  named relation fields and the generic `citation` fallback)
- `hs_core/templatetags/hydroshare_tags.py` — helper functions were added to
  pull together contact info, and relation links so the template stays readable;
  `relation_values_json` extracts relation values by type from `cached_metadata`
  and returns them as a JSON array string, enabling typed relation fields in the
  template without duplicating logic

### Metadata fields added or improved

**Publisher identity**
Previously the publisher block named HydroShare as a CUAHSI repository but
did not include a globally recognized identifier for CUAHSI. We now include
the CUAHSI ROR identifier (`https://ror.org/003b04c03`), which is the standard
persistent ID for research organizations. This lets automated tools
unambiguously identify who published the resource.

**Creator identifiers (ORCID) and creator array format**
Creator entries already included name, email, and affiliation. We now also
include the creator's ORCID when one is stored in their HydroShare profile.
ORCID is a persistent, globally unique identifier for researchers and is
specifically checked by the MetaDIG `resource.creatorIdentifier.present` check
([source](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/resource.creatorIdentifier.present-2.1.0.xml)).

Previously the `creator` property was emitted as a JSON-LD `{"@list": [...]}` object.
`@list` is valid JSON-LD that asserts RDF list-ordering semantics, but the MetaDIG
schema.org jq selectors for `resource.creatorIdentifier.present`,
`resource.distributionContact.present`, and `resource.distributionContactIdentifier.present`
all use `(if .[]? then .[] else . end)` to iterate creator entries. Applied to an
object instead of a plain array, `.[]?` yields the inner array as a single value
rather than iterating individual creators, so `.identifier` and `select(.roleName?)`
never reach individual entries. Replacing `@list` with a plain JSON array — equally
valid JSON-LD per the [JSON-LD 1.1 specification §4.3](https://www.w3.org/TR/json-ld11/#sets-and-lists) — fixes all three affected
MetaDIG checks. Author order is still conveyed by array position; Google Dataset
Search and other schema.org consumers infer first-author status from the first entry.

**Contact person**
The MetaDIG checks `resource.distributionContact.present` and
`resource.distributionContactIdentifier.present` look inside `.creator[]` for
an entry with `"roleName": "Contact"`. Their jq selectors use
`.creator | ... | select(.roleName? == "Contact")` and never evaluate a top-level
`contactPoint` field. See
[resource.distributionContact.present-2.1.0.xml](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/resource.distributionContact.present-2.1.0.xml).

HydroShare does not have a dedicated contact field, so the first listed creator
(by `order`) is used as the contact: a copy of that creator's entry is appended to
the `creator` array with `"roleName": "Contact"` added. The MetaDIG jq expression
`select(.roleName? == "Contact") | .identifier // .sameAs` then finds the creator's
ORCID when one is stored, satisfying `resource.distributionContactIdentifier.present`.
If no ORCID is stored, `resource.distributionContact.present` still passes but
`resource.distributionContactIdentifier.present` does not.

A separate `contactPoint` object (`@type: ContactPoint`) is also emitted at the
`Dataset` level from the same first creator. **This is not evaluated by MetaDIG** —
no MetaDIG check has a `contactPoint` jq selector. It is included because
`contactPoint` is the conventional schema.org field for contact information, indexed
by [Google Dataset Search](https://developers.google.com/search/docs/appearance/structured-data/dataset#dataset-properties),
and the data cost is zero since it reuses the same first-creator lookup.

**Distribution name**
The `distribution` block now includes a `name` field (the resource title with
a "(BagIt Archive)" suffix). The MetaDIG `entity.name.present` check evaluates
`distribution` entries with `@type: DataDownload` and requires each to have a
non-blank `name`; this change satisfies that check. See
[entity.name.present-2.1.0.xml](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/entity.name.present-2.1.0.xml).

### What was already working (no change)

Title, abstract, keywords, resource identifier, creators, license, dates,
geographic coverage, temporal coverage, download link, funding, and related
resource links were all already present and did not need to change.

## MetaDIG FAIR Check Status

| Status | What it means |
|---|---|
| **Passing before this PR** | Title length, abstract length, creator presence, publisher name, keywords, publication date, landing page URL, license, spatial coverage, temporal coverage, resource identifier |
| **Now passing after this PR** | `resource.publisherIdentifier.present` — CUAHSI ROR identifier added to the `publisher` block; `resource.creatorIdentifier.present` — ORCID emitted as `identifier`/`sameAs`, `creator` changed from `@list`-wrapped object to plain JSON array so MetaDIG jq iterates individual entries; `resource.distributionContact.present` and `resource.distributionContactIdentifier.present` — first creator duplicated with `"roleName": "Contact"` in the `creator` array (a separate `contactPoint` field is also emitted for Google Dataset Search but is not evaluated by MetaDIG); `entity.name.present` — `name` added to the `distribution` block |
| **Out of scope** | Checks that require column-level or attribute-level metadata (units, measurement scale, enumerated domains, etc.), per-file checksums, and a structured methods section — HydroShare does not currently store or expose this information on the landing page |

## A Note on Relation Links

HydroShare uses slightly different terminology internally for one relation type.
When a resource is marked as derived from another source, HydroShare calls it
`source`. The standard schema.org term for the same concept is `isBasedOn`.
The landing page translates this automatically so external tools see the
correct term. All other relation types (`isPartOf`, `hasPart`, `isVersionOf`,
`references`, etc.) use the same name in both systems.
