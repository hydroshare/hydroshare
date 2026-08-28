# MetaDIG FAIR Suite Comparison

This note compares the DataONE `metadig-checks` FAIR suite with the schema.org JSON-LD HydroShare emits on public resource landing pages.

The key point is that MetaDIG checks are written against EML-style metadata completeness, while HydroShare exposes a schema.org landing page. That means some checks map cleanly, some map partially, and some are outside schema.org entirely.

## Recommended Test Adaptation Plan

For an implementation-focused plan that maps each candidate MetaDIG check to schema.org-aligned expectations and HydroShare metadata sources, see:

- [MetaDIG Test Adaptation for Schema.org-Valid HydroShare Metadata](metadig-schemaorg-test-adaptation.md)

That companion note defines a two-stage validation strategy:

1. schema.org syntax/structure gate first
2. FAIR semantic checks only after schema-valid metadata is confirmed

| MetaDIG FAIR check | HydroShare / schema.org coverage | Notes |
| --- | --- | --- |
| `metadata.identifier.present` / `metadata.identifier.resolvable` | `identifier`, landing page URL, `contentUrl` | Strong overlap for discoverability and resolvable identifiers |
| `resource.titleLength.sufficient` | `name` | Direct mapping for the title content check |
| `resource.abstractLength.sufficient` | `description` | Direct mapping for descriptive summary content |
| `resource.creator.present` / `resource.creatorIdentifier.present` | `creator` | Creator name maps directly; identifier coverage is partial unless an ORCID or equivalent is present |
| `resource.keywords.present` / `dataset.keywords.minimum-2.0.0` | `keywords` | Direct mapping for keyword presence; controlled vocabulary support is partial |
| `resource.publicationDate.present` / `resource.publicationDate.timeframe` | `datePublished` and `dateAccepted` | Strong overlap for published resources |
| `resource.landingPage.present` | `url`, `contentUrl`, `subjectOf` | Direct support for a landing page plus downloadable content |
| `resource.license.present` | `license` | Direct mapping |
| `resource.accessControlRules.present` | `creativeWorkStatus`, `isAccessibleForFree` | Partial overlap; HydroShare expresses publication/access state rather than the full EML access-control vocabulary |
| `resource.publisher.present` / `resource.publisherIdentifier.present` | `publisher`, `provider`, `includedInDataCatalog` | Implemented for published resources; the template emits a full `Organization` object with `@type`, `@id`, `name`, and `url` sourced dynamically from `cm.cached_metadata.publisher`. No explicit ROR identifier property is emitted — `@id` carries the publisher URL. `resource.publisherIdentifier.present` via a dedicated identifier field remains partial. |
| `resource.distributionContact.present` / `resource.distributionContactIdentifier.present` | not fully represented in schema.org output | Treat this as the main person responsible for the content. Use an explicit contact record if it exists, otherwise use the first author record and its public profile fields |
| `resource.spatialExtent.present` / `geographic.description.present` | `spatialCoverage.geo` | Direct overlap for point and box coverage; descriptive geographic text is partial |
| `resource.temporalExtent.present` | `temporalCoverage` | Direct overlap |
| `resource.methods.present` | out of scope for the current schema.org landing page | HydroShare does not expose a dedicated methods field that can be mapped cleanly today |
| `provenance.trace.present` / `provenance.sourceEntity.present` | not satisfiable with the current schema.org implementation | The MetaDIG checks for these require PROV-O terms (`prov:wasGeneratedBy` and `prov:wasDerivedFrom`) in the JSON-LD graph — not schema.org relation fields such as `isBasedOn`. Satisfying them would require embedding a separate PROV-O vocabulary in the schema.org `@context`, which is outside the current scope. See [provenance.trace.present-2.0.0.xml](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/provenance.trace.present-2.0.0.xml) and [provenance.sourceEntity.present-2.0.0.xml](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/provenance.sourceEntity.present-2.0.0.xml). |
| `provenance.processStepCode.present` | not represented in the landing page JSON-LD | Outside the scope of the current schema.org mapping |
| `entity.identifier.present` / `entity.identifierType.present` | out of scope for the current schema.org landing page | HydroShare only has resource-level identifiers, not identifiers for each file or aggregation |
| `entity.name.present` | `distribution.name` | The check (v2.1.0) evaluates `.distribution[]` entries with `@type: DataDownload` and requires each to have a non-blank `name`. Adding `name` to the existing `distribution` block satisfies this check without per-file serialization. See [entity.name.present-2.1.0.xml](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/entity.name.present-2.1.0.xml). |
| `entity.description.present` | not represented at the attribute/entity level | `entity.description` is inconsistent across files and is outside the scope of the current schema.org mapping |
| `entity.format.present` / `entity.format.nonproprietary` | `encodingFormat` | Partial overlap; file format is exposed, but non-proprietary validation is not encoded in schema.org |
| `entity.checksum.present` | out of scope for the current schema.org landing page | HydroShare exposes a bag/resource checksum for published resources, but not per-file checksums on the public landing page |
| `entity.attributeDefinition.present` / `entity.attributeUnits.present` / `entity.attributeMeasurementScale.present` | not represented in the landing page JSON-LD | Attribute-level completeness is outside the current schema.org mapping |
| `entity.qualityDescription.present` | not represented in the landing page JSON-LD | Out of scope for the current schema.org landing page |

For the DataONE FAIR suite, the practical status is:

- **Direct**: identifier, title, abstract, creator, keywords, publication date, landing page, license, spatial coverage, temporal coverage.
- **Partial**: access rules, distribution contact, controlled keywords, provenance, entity identifiers, bag/resource checksum, file formats.
- **Missing from schema.org output**: metadata/distribution contacts, methods/process steps, provenance detail, and attribute/entity-level completeness checks.

So the practical interpretation is:

- HydroShare schema.org metadata should satisfy the **discovery-oriented** part of the MetaDIG FAIR suite.
- MetaDIG still adds value for **EML-specific completeness** and **data-structure quality** checks.
- Schema.org is a useful public-facing layer, but it is not a full replacement for the MetaDIG FAIR assessment model.

## Validations HydroShare Does Not Fully Satisfy Yet, But Could Implement

The checks below are the best candidates for future HydroShare work because they are either already represented in HydroShare metadata somewhere, or they could be added without changing the overall DataONE/MetaDIG model.

| MetaDIG FAIR check | Why it is currently incomplete | Practical HydroShare implementation path |
| --- | --- | --- |
| `resource.distributionContact.present` / `resource.distributionContactIdentifier.present` | The landing page does not emit a dedicated `contactPoint` object today; contact data only exists through creator/profile metadata | Emit schema.org `contactPoint` from an explicit contact record when available, otherwise from the first creator profile, and populate `name`, `email`, `affiliation`, `identifier`, `url`, `telephone`, and `sameAs` |
| `resource.publisherIdentifier.present` | `publisher` is already emitted with `name` and `url`; no dedicated identifier property (e.g. ROR) is currently included | Add an explicit `identifier` or `sameAs` on the `publisher` object pointing to the ROR URL for CUAHSI |
| `resource.methods.present` | Methods text is not exposed as a dedicated landing page field | No clear schema.org mapping exists in the current landing page model |
| `provenance.trace.present` | The landing page has relations and dates, but not a structured provenance object | Build a provenance structure that captures the full lineage history using `source`, `isPartOf`, `hasPart`, version links, and publication dates |
| `provenance.sourceEntity.present` | Source relationships exist as generic relations, but not as explicit provenance fields | Derive the schema.org `sourceEntity` tag from HydroShare relation metadata such as `source` or `isVersionOf`, and point it at the previous version or parent resource. If there is no earlier version or parent, leave `sourceEntity` absent |
| `provenance.processStepCode.present` | not represented in the landing page JSON-LD | Outside the scope of the current schema.org mapping |
| `entity.identifier.present` / `entity.identifierType.present` | out of scope for the current schema.org landing page | HydroShare only has resource-level identifiers, not identifiers for each file or aggregation |
| `entity.name.present` | `distribution.name` | The check evaluates `distribution` entries with `@type: DataDownload`. Adding a `name` field to the existing distribution block (e.g. `"<title> (BagIt Archive)"`) is sufficient. Per-file serialization is not required and not evaluated by the check. See [entity.name.present-2.1.0.xml](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/entity.name.present-2.1.0.xml). |
| `entity.description.present` | Entity-level descriptions are not rendered consistently on the landing page today | Treat `entity.description` as out of scope unless a resource type exposes consistent file-level description metadata |
| `entity.format.present` | Derived from extension or file metadata | HydroShare captures file format in DataCite and file-level metadata; the schema.org `encodingFormat` value should be derived from that same source. This scales well for many files because every file already has a type, but a resource with 1,000 files would still make the landing-page JSON-LD large if we emitted fully expanded per-file entries |
| `entity.checksum.present` | out of scope for the current schema.org landing page | HydroShare only exposes a bag/resource checksum on the public landing page, not per-file checksums |
| `entity.qualityDescription.present` | Quality-control notes are not represented in the public JSON-LD today | Out of scope for the current schema.org landing page |

These are the most plausible gaps to close because they are aligned with metadata HydroShare either already stores or can reasonably extend without changing the core schema.org landing page pattern.

## Checks That Are Likely Outside The Current Scope

Some MetaDIG validations are important, but they are not good candidates for near-term schema.org work because they require a deeper EML-style model or attribute-level semantics that HydroShare does not currently expose on the landing page.

- `entity.attributeDefinition.present`
- `entity.attributeUnits.present`
- `entity.attributeMeasurementScale.present`
- `entity.attributeStorageType.present`
- `entity.attributePrecision.present`
- `entity.attributeEnumeratedDomains.present`
- `entity.attributeDomain.present`
- `entity.attributeNames.unique`
- `entity.attributeName.differs`
- `entity.attributeCoverageContentType.present`
- `resource.methods.present`
- `entity.qualityDescription.present`

`resource.methods.present` is also outside the current schema.org layer because HydroShare does not expose a dedicated methods field on the landing page today.

`provenance.trace.present` and `provenance.sourceEntity.present` are outside the current schema.org layer because the MetaDIG checks for these require W3C PROV Ontology terms (`prov:wasGeneratedBy` and `prov:wasDerivedFrom`) that are not part of the schema.org vocabulary. Satisfying them would require embedding PROV-O in the JSON-LD `@context`, which is a separate decision from the current schema.org implementation. See [provenance.trace.present-2.0.0.xml](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/provenance.trace.present-2.0.0.xml) and [provenance.sourceEntity.present-2.0.0.xml](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/provenance.sourceEntity.present-2.0.0.xml).

These checks are more about tabular/model-level metadata curation than about the public discovery layer, so they would need broader entity metadata support rather than a small schema.org extension.

## Implementation Priority Summary

If the goal is to improve HydroShare so it passes more of the DataONE FAIR checks for public resources with embedded schema.org, the most practical grouping is:

| Priority | MetaDIG FAIR checks | Why |
| --- | --- | --- |
| Achievable now | `metadata.identifier.present`, `metadata.identifier.resolvable`, `resource.titleLength.sufficient`, `resource.abstractLength.sufficient`, `resource.creator.present`, `resource.publisher.present`, `resource.publisherIdentifier.present` (published resources only), `resource.keywords.present`, `resource.publicationDate.present`, `resource.landingPage.present`, `resource.license.present`, `resource.spatialExtent.present`, `resource.temporalExtent.present` | These are already exposed in HydroShare metadata or schema.org JSON-LD, so they are the closest fit to the current implementation |
| Achievable with work | `resource.creatorIdentifier.present`, `resource.distributionContact.present`, `resource.distributionContactIdentifier.present`, `entity.format.present` | `entity.format` is already captured in DataCite, but the schema.org `encodingFormat` output still needs to be derived from the same source; the rest are plausible because HydroShare already stores some of the needed metadata, or could add a narrow new public representation without redesigning the whole model |
| Outside current scope | `provenance.trace.present`, `provenance.sourceEntity.present`, `entity.attributeDefinition.present`, `entity.attributeUnits.present`, `entity.attributeMeasurementScale.present`, `entity.attributeStorageType.present`, `entity.attributePrecision.present`, `entity.attributeEnumeratedDomains.present`, `entity.attributeDomain.present`, `entity.attributeNames.unique`, `entity.attributeName.differs`, `entity.attributeCoverageContentType.present` | The provenance checks require PROV-O terms (`prov:wasGeneratedBy`, `prov:wasDerivedFrom`) that are outside the schema.org vocabulary; the attribute checks require deeper EML-style tabular metadata support |

The shortest version is: HydroShare can already cover the discovery checks, can plausibly add a number of contact/provenance/entity checks, and would need a broader metadata model to satisfy the attribute-level EML checks.

## Pass / Needs-Work / Out-of-Scope Matrix

This matrix is a stricter operational view of the same checks.

| Status | MetaDIG FAIR checks | Interpretation |
| --- | --- | --- |
| Pass now | `metadata.identifier.present`, `metadata.identifier.resolvable`, `resource.titleLength.sufficient`, `resource.abstractLength.sufficient`, `resource.creator.present`, `resource.publisher.present`, `resource.publisherIdentifier.present` (published resources only), `resource.keywords.present`, `resource.publicationDate.present`, `resource.landingPage.present`, `resource.license.present`, `resource.spatialExtent.present`, `resource.temporalExtent.present` | HydroShare already exposes these in the current resource model or schema.org output |
| Needs work | `resource.creatorIdentifier.present`, `resource.distributionContact.present`, `resource.distributionContactIdentifier.present`, `entity.format.present` | `entity.format` is captured in DataCite, but the schema.org mapping still needs to be emitted from that source; the other checks are realistic additions because HydroShare already stores some of the needed information, or could expose it with a focused metadata extension |
| Out of scope for current schema.org layer | `provenance.trace.present`, `provenance.sourceEntity.present`, `entity.attributeDefinition.present`, `entity.attributeUnits.present`, `entity.attributeMeasurementScale.present`, `entity.attributeStorageType.present`, `entity.attributePrecision.present`, `entity.attributeEnumeratedDomains.present`, `entity.attributeDomain.present`, `entity.attributeNames.unique`, `entity.attributeName.differs`, `entity.attributeCoverageContentType.present` | The provenance checks require PROV-O terms (`prov:wasGeneratedBy`, `prov:wasDerivedFrom`) that are not part of the schema.org vocabulary; the attribute checks need richer tabular metadata support |

The practical takeaway is that the biggest near-term gains are contact metadata and entity-level formats. The provenance checks require PROV-O vocabulary that is outside schema.org, and the attribute-level checks are a separate modeling problem.

## How To Map The Needs-Work Checks To HydroShare Metadata

The checks in the "Needs work" bucket can be implemented by using the metadata HydroShare already stores, plus a few focused extensions to the landing page JSON-LD and entity metadata serialization.

| MetaDIG FAIR check | HydroShare metadata source | Suggested mapping approach |
| --- | --- | --- |
| `resource.creatorIdentifier.present` | creator records | Emit an `identifier` value for each creator when ORCID or another persistent identifier is available |
| `resource.publisherIdentifier.present` | `cm.cached_metadata.publisher` | `resource.publisher.present` is already satisfied; add an explicit `identifier` or `sameAs` with the ROR URL to satisfy `resource.publisherIdentifier.present` |
| `resource.distributionContact.present` / `resource.distributionContactIdentifier.present` | contact metadata or first author profile | Emit `contactPoint` from an explicit contact source when available; otherwise use the first creator profile and map its public contact fields |
| `resource.methods.present` | resource methods / description metadata | No clear schema.org mapping exists in the current landing page model |
| `provenance.trace.present` | Not applicable — requires PROV-O | The check's schema.org JSON-path looks for `prov:wasGeneratedBy` ([source](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/provenance.trace.present-2.0.0.xml)), a W3C PROV Ontology term outside the schema.org vocabulary. Out of scope for the current implementation. |
| `provenance.sourceEntity.present` | Not applicable — requires PROV-O | The check's schema.org JSON-path looks for `prov:wasDerivedFrom` ([source](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/provenance.sourceEntity.present-2.0.0.xml)), a W3C PROV Ontology term outside the schema.org vocabulary. Out of scope for the current implementation. |
| `provenance.processStepCode.present` | methods / provenance metadata | No clear schema.org mapping exists in the current landing page model |
| `entity.identifier.present` / `entity.identifierType.present` | out of scope for the current schema.org landing page | HydroShare only has resource-level identifiers, not identifiers for each file or aggregation |
| `entity.name.present` | `distribution.name` | The check evaluates `distribution` entries with `@type: DataDownload` and requires a non-blank `name` on each. Adding `name` to the existing distribution block is sufficient; per-file serialization is not evaluated. See [entity.name.present-2.1.0.xml](https://github.com/NCEAS/metadig-checks/blob/main/src/checks/entity.name.present-2.1.0.xml). |
| `entity.description.present` | file-level metadata | Treat `entity.description` as out of scope unless a file type exposes consistent description metadata for every file |
| `entity.format.present` | Derived from extension or file metadata | HydroShare captures file format in DataCite and file-level metadata; the schema.org `encodingFormat` value should be derived from that same source. This scales better than richer per-file metadata because every file already has a type, but a resource with 1,000 files would still make the landing-page JSON-LD large if we emitted fully expanded per-file entries |
| `entity.checksum.present` | out of scope for the current schema.org landing page | HydroShare only exposes a bag/resource checksum on the public landing page, not per-file checksums |
| `entity.qualityDescription.present` | resource methods, QA/QC notes, file-specific metadata | Out of scope for the current schema.org landing page |

### Suggested implementation order

1. **Add creator identifiers first.** These are the easiest to wire because HydroShare already stores creator records, and the gain for FAIR validation is immediate. Publisher name and URL are already emitted; a dedicated publisher identifier (e.g. ROR) is the remaining gap.
2. **Add contact metadata next.** `distributionContact` should become a `contactPoint` emitted from the explicit contact source or first creator profile.
3. **Add entity-level identifiers, names, formats, and checksums.** This requires iterating over the resource’s files or aggregations, but it is still a focused metadata serialization task.
4. **Leave attribute-level and provenance checks for later.** Attribute checks need column/attribute semantics outside the current schema.org layer. Provenance checks (`provenance.trace.present`, `provenance.sourceEntity.present`) require PROV-O terms (`prov:wasGeneratedBy`, `prov:wasDerivedFrom`) that are not part of the schema.org vocabulary and are out of scope for the current implementation.

### Practical rule of thumb

If the needed information already exists in one of these places, it is a good candidate for implementation:

- `cm.cached_metadata`
- relation metadata
- file or aggregation metadata
- bag or file checksum data
- existing resource history or publication state

If the check depends on per-column semantics, units, measurement scale, or enumerated domains, it is probably beyond the current schema.org layer and should stay in the out-of-scope group for now.

### Implementation plan

**Quick wins**

- `resource.creatorIdentifier.present`
- `resource.distributionContact.present` / `resource.distributionContactIdentifier.present`

These are the easiest to justify because they build on existing resource-level metadata and mostly need better serialization.

**Medium effort**

- `entity.format.present`

`entity.description.present` is also outside the current schema.org layer because HydroShare does not expose a consistent description for every file in a resource.

`entity.checksum.present` is also outside the current schema.org layer because HydroShare only has a bag/resource checksum, not per-file checksums.

These require iterating over resource relations or entities and emitting a richer public metadata structure, but they still fit the current landing-page pattern.

**Future work**

- `entity.attributeDefinition.present`
- `entity.attributeUnits.present`
- `entity.attributeMeasurementScale.present`
- `entity.attributeStorageType.present`
- `entity.attributePrecision.present`
- `entity.attributeEnumeratedDomains.present`
- `entity.attributeDomain.present`
- `entity.attributeNames.unique`
- `entity.attributeName.differs`
- `entity.attributeCoverageContentType.present`

These need attribute-level metadata that HydroShare does not currently expose as part of the public schema.org layer.