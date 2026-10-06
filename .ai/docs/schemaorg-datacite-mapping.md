# HydroShare DataCite and schema.org Mapping

This is a reference mapping of HydroShare's internal metadata model to schema.org JSON-LD and the DataCite vocabulary as rendered on public resource landing pages.

Primary code paths:

- Landing page JSON-LD: [hs_core/templates/pages/baseresource.html](../../hs_core/templates/pages/baseresource.html)
- Relation vocabulary and metadata model: [hs_core/models.py](../../hs_core/models.py)

## Summary

HydroShare now expresses the same resource metadata in two coordinated layers:

- The internal metadata model stores the canonical resource values and relation vocabulary.
- The landing page template renders those values as schema.org JSON-LD, using DataCite-compatible semantics where HydroShare stores a different internal term.

The mapping below groups the fields by intent so the relationship is easier to follow.

## Core Metadata Mapping

| HydroShare concept | Internal HydroShare field | schema.org field | DataCite intent |
| --- | --- | --- | --- |
| Title | `title` | `name` | Title |
| Abstract | `abstract` | `description` | Description |
| Keywords / subjects | subject list | `keywords` | Subject / keyword terms |
| Resource type | `cm.cached_metadata.type` | `additionalType` | ResourceType |
| Creator | `creator` (ordered by `order` field; plain JSON array, not `@list`-wrapped) | `creator` | Creator |
| Creator identifier | `creator[].identifiers` (e.g. ORCID) | `creator[].identifier`, `creator[].sameAs` | Creator identifier |
| Contact person (derived) | first creator by `order` — no dedicated contact field exists | appended `creator[]` entry with `roleName: "Contact"` — satisfies MetaDIG `resource.distributionContact.present`; see [schemaorg-improvements.md](schemaorg-improvements.md) | Not a stored field; derived at render time |
| Contact point | first creator by `order` | `contactPoint` (`@type: ContactPoint`) — indexed by Google Dataset Search; not evaluated by MetaDIG checks | Not a stored field; derived at render time |
| Contributor | `contributor` | `contributor` | Contributor |
| Alternate identifier | `identifier` | `identifier` | Alternate identifier |
| Rights statement / license | `rights` | `license` | Rights / license |
| Language | hardcoded `"en-US"` | `inLanguage` | Language |
| Funding | `fundingagency` | `funding` | Funding reference |
| Publication state | resource access state | `creativeWorkStatus`, `isAccessibleForFree`, `datePublished` | Publication / availability metadata |
| Creation date | `cm.created` | `dateCreated` | Date (Created) |
| Modification date | `cm.last_updated` | `dateModified` | Date (Updated) |
| File formats | `cm.metadata.formats.all` | `encodingFormat` | Format |
| Download / bag URL | bag URL or resource URL | `contentUrl` | Landing/download link |
| Publisher | `cm.cached_metadata.publisher` | `publisher` (`Organization`) | Publisher; only emitted for published resources |
| Schema version marker | n/a | `schemaVersion` | DataCite schema URI reference |
| Provider / catalog | n/a | `provider`, `includedInDataCatalog` | Repository / catalog context |

## Relation Mapping

HydroShare relation handling is the main place where the internal vocabulary and schema.org vocabulary diverge.

This relation layer is RDF-backed. In [hs_core/models.py](../../hs_core/models.py), the `Relation` model is annotated with `@rdf_terms(DC.relation)` and implements `rdf_triples()` and `ingest_rdf()`. That means HydroShare stores relation metadata as RDF-aware model data, then serializes it into the repository's XML/RDF structures and finally into schema.org JSON-LD on the landing page.

The important distinction is:

- HydroShare stores relations using its own metadata vocabulary in the model layer.
- The landing page translates a subset of those relations into schema.org properties.
- Some HydroShare relation terms are stored for internal or data-model reasons, but are not emitted as direct schema.org fields.

In practice, the divergence is not about losing information; it is about translating between a storage vocabulary and a web-facing vocabulary.

| HydroShare relation type | Internal HydroShare vocabulary | schema.org field in [hs_core/templates/pages/baseresource.html](../../hs_core/templates/pages/baseresource.html) | Notes |
| --- | --- | --- | --- |
| `isPartOf` | Supported | *(not emitted)* | Removed — caused schema.org validation errors |
| `hasPart` | Supported | *(not emitted)* | Removed — caused schema.org validation errors |
| `source` | Supported | *(not emitted)* | Removed — caused schema.org validation errors; was translated to `isBasedOn` |
| `isVersionOf` | Supported | *(not emitted)* | Removed — caused schema.org validation errors |
| `isReplacedBy` | Supported | *(not emitted)* | Removed — caused schema.org validation errors |
| `isDescribedBy` | Supported | *(not emitted)* | Removed — caused schema.org validation errors |
| `isReferencedBy` | Supported | *(not emitted)* | Removed — caused schema.org validation errors |
| `references` | Supported | *(not emitted)* | Removed — caused schema.org validation errors |
| `relation` | General relation wrapper | *(not emitted)* | Removed — caused schema.org validation errors |

### Where The Relation Mapping Diverges

The main divergence points are:

| Divergence point | HydroShare behavior | schema.org behavior |
| --- | --- | --- |
| Storage vocabulary vs rendering vocabulary | HydroShare stores `source` in the metadata model | schema.org uses `isBasedOn` in JSON-LD |
| Broader internal relation set | HydroShare supports additional relation types such as `isExecutedBy`, `isCreatedBy`, `conformsTo`, `hasFormat`, `isFormatOf`, `isRequiredBy`, `requires`, and `isSimilarTo` | The landing page only renders the relations with explicit schema.org equivalents that are wired into the template |
| Generic relation wrapper | HydroShare exposes a general `relation` element | schema.org flattens the relation values into `citation` and the specific relation fields above |

This means the mapping is partly one-to-one and partly translational. The code does not attempt to force every HydroShare relation into a schema.org property; it only emits the schema.org fields that have a clear semantic fit.

## Spatial And Temporal Coverage

These fields are important for discovery and are exposed on the landing page even though they are stored as HydroShare-specific coverage metadata.

| HydroShare concept | schema.org field | Notes |
| --- | --- | --- |
| Point coverage | `spatialCoverage` → `Place` → `geo` with `GeoCoordinates` | Nested under a `Place` object; uses `latitude` and `longitude` |
| Box coverage | `spatialCoverage` → `Place` → `geo` with `GeoShape` | Nested under a `Place` object; uses the bounding box as a space-separated `box` string in south west north east order |
| Temporal coverage | `temporalCoverage` | Rendered as `start/end` in the landing page |

The `geo` property is a sub-property of `spatialCoverage` and is not emitted as a top-level property. The correct structure is `spatialCoverage.geo`, not a bare `geo` at the Dataset root level.

## Distribution Metadata

The landing page emits two download-related objects that are not pure HydroShare metadata fields:

| schema.org field | Source | Notes |
| --- | --- | --- |
| `subjectOf` | Dublin Core metadata XML endpoint | `DataDownload` pointing to `hsapi/resource/{id}/scimeta/` with `encodingFormat: application/rdf+xml` |
| `distribution` | Bag download endpoint | `DataDownload` with `contentSize` (human-readable), `encodingFormat: application/zip`, `contentUrl`, and `dateModified` |
| `distribution.identifier` | `cm.bag_checksum` | For published resources only: an MD5 `PropertyValue` using the bag checksum stored in `extra_data`; unpublished resources receive a bare URL identifier only |

The `distribution.identifier` bag checksum is the only checksum exposed on the public landing page. Per-file checksums exist internally and via the REST API but are not included in the JSON-LD.

## Practical Takeaway

The main implementation pattern is:

- Store HydroShare metadata in the native model vocabulary.
- Map that vocabulary to schema.org JSON-LD in the landing page template.
- Preserve DataCite semantics where the HydroShare internal term differs, especially for relations such as `source` -> `isBasedOn`.

See [MetaDIG FAIR Suite Comparison](metadig-fair-suite-comparison.md) for a check-by-check comparison between the DataONE FAIR suite and HydroShare schema.org output.

For a full record of what changed in this PR and why, see [schemaorg-improvements.md](schemaorg-improvements.md).
