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

## Proposed Distribution Contact Mapping

HydroShare does not currently expose a first-class `distributionContact` metadata element on the landing page. In MetaDIG terms, this field is best understood as the main person responsible for the content. The implementation should therefore build a schema.org contact object from the same profile-backed fields used for authors.

Recommended source order:

1. An explicit distribution-contact record, if HydroShare ever stores one.
2. The first creator / first author record.
3. The public creator profile fields for that record.

This is a semantic mapping, not an existing stored field. If HydroShare needs to satisfy a check that specifically looks for `resource.distributionContact.present`, the implementation should render a schema.org `contactPoint` object, or an equivalent contact structure, from the selected source record. The object should carry the public contact name, email, affiliation, identifier, homepage, phone, and profile URL when available.

This makes the mapping deterministic and keeps the fallback aligned with the MetaDIG intent.

The best current source is the creator/contact data already emitted in the landing page JSON-LD author block in [hs_core/templates/pages/baseresource.html](../../hs_core/templates/pages/baseresource.html). That block already includes profile-derived name, email, organization, identifiers, homepage, phone, and profile URL.

| Proposed `distributionContact` field | Likely HydroShare source | Notes |
| --- | --- | --- |
| `name` | creator full name / profile display name | Use the public profile name when available |
| `email` | `author.email` | Already present in the landing page author object |
| `affiliation` / organization | `author.organization` | Comes from the user profile organization field |
| `identifier` | `author.identifiers` | Can carry ORCID or other public identifiers |
| `url` / homepage | `author.homepage` | Use the profile or personal website if present |
| `telephone` | `author.phone` | Use the public phone value from the profile |
| `sameAs` / profile URL | `author.profileUrl` | Useful if the profile page itself should be treated as the contact landing page |

Code-generation rule:

- Use `contactPoint` as the primary schema.org property.
- Populate `name`, `email`, `affiliation`, `identifier`, `url`, and `telephone` from the chosen contact source.
- Use the first author only as the fallback source when no explicit contact exists.
- Do not infer contact responsibility from author order unless the fallback path is needed.

Implementation recipe:

1. Select the contact source in this order: explicit contact record, first creator record, public profile for that person.
2. Build a schema.org `ContactPoint` object from that source.
3. Map `name`, `email`, `affiliation`, `identifier`, `url`, `telephone`, and `sameAs` from the selected source.
4. Emit the object as `contactPoint` in the landing page JSON-LD.
5. Keep the output deterministic so the same resource always produces the same contact object.

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

See [MetaDIG FAIR Suite Comparison](metadig-fair-suite-comparison.md) for a check-by-check comparison between the DataONE FAIR suite and HydroShare schema.org output.

## What Changed In HydroShare

The code changes that enabled the mapping were concentrated in two places:

- [hs_core/models.py](../../hs_core/models.py) defines the supported relation vocabulary and makes HydroShare relation terms available as first-class metadata elements.
- [hs_core/templates/pages/baseresource.html](../../hs_core/templates/pages/baseresource.html) translates those stored values into schema.org JSON-LD, including creator, contributor, spatial coverage, temporal coverage, relations, rights, funding, and content URL fields.

That separation is what allows HydroShare to keep an internal metadata model that is practical for the application while still emitting web-friendly schema.org markup with DataCite-aligned meaning.
