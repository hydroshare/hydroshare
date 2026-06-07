# HydroShare DataCite and schema.org Mapping

This note summarizes the HydroShare code changes that align the internal metadata model with schema.org JSON-LD and the DataCite vocabulary.

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
| Creator | `creator` | `creator` | Creator |
| Contributor | `contributor` | `contributor` | Contributor |
| Alternate identifier | `identifier` | `identifier` | Alternate identifier |
| Rights statement / license | `rights` | `license` | Rights / license |
| Language | `language` | `inLanguage` | Language |
| Funding | `fundingagency` | `funding` | Funding reference |
| Publication state | resource access state | `creativeWorkStatus`, `isAccessibleForFree`, `datePublished`, `dateAccepted` | Publication / availability metadata |
| Download / bag URL | bag URL or resource URL | `contentUrl` | Landing/download link |
| Schema version marker | n/a | `schemaVersion` | DataCite schema version reference |
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
| `isPartOf` | Supported | `isPartOf` | Direct mapping |
| `hasPart` | Supported | `hasPart` | Direct mapping |
| `source` | Supported | `isBasedOn` | HydroShare stores `source`, schema.org renders it as `isBasedOn` |
| `isVersionOf` | Supported | `isVersionOf` | Direct mapping |
| `isReplacedBy` | Supported | `isReplacedBy` | Direct mapping |
| `isDescribedBy` | Supported | `isDescribedBy` | Direct mapping |
| `isReferencedBy` | Supported | `isReferencedBy` | Direct mapping |
| `references` | Supported | `references` | Direct mapping |
| `relation` | General relation wrapper | `citation` | The landing page also emits a generic citation list of relation values |

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
| Point coverage | `spatialCoverage.geo` with `GeoCoordinates` | Uses latitude and longitude |
| Box coverage | `spatialCoverage.geo` with `GeoShape` | Uses the bounding box |
| Temporal coverage | `temporalCoverage` | Rendered as `start/end` in the landing page |

## Practical Takeaway

The main implementation pattern is:

- Store HydroShare metadata in the native model vocabulary.
- Map that vocabulary to schema.org JSON-LD in the landing page template.
- Preserve DataCite semantics where the HydroShare internal term differs, especially for relations such as `source` -> `isBasedOn`.

## What Changed In HydroShare

The code changes that enabled the mapping were concentrated in two places:

- [hs_core/models.py](../../hs_core/models.py) defines the supported relation vocabulary and makes HydroShare relation terms available as first-class metadata elements.
- [hs_core/templates/pages/baseresource.html](../../hs_core/templates/pages/baseresource.html) translates those stored values into schema.org JSON-LD, including creator, contributor, spatial coverage, temporal coverage, relations, rights, funding, and content URL fields.

That separation is what allows HydroShare to keep an internal metadata model that is practical for the application while still emitting web-friendly schema.org markup with DataCite-aligned meaning.
