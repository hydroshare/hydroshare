# MetaDIG Test Adaptation for Schema.org-Valid HydroShare Metadata

## Purpose

This note proposes how to adapt MetaDIG FAIR checks so they evaluate HydroShare metadata in a way that is consistent with valid schema.org JSON-LD.

Core principle:

1. Validate schema.org JSON-LD syntax and structure first.
2. Run FAIR semantic checks only if schema validation passes.
3. Mark FAIR-findability checks as not-applicable when schema syntax fails.

This avoids scoring metadata as FAIR-findable when search engines are unlikely to use it due to invalid schema.org markup.

## Related design notes

- [MetaDIG FAIR Suite Comparison](metadig-fair-suite-comparison.md)
- [HydroShare DataCite and schema.org Mapping](schemaorg-datacite-mapping.md)

## Proposed test gating

### Stage 1: Required schema.org gate

Fail fast if any of the following is true:

1. JSON-LD cannot be parsed.
2. JSON-LD graph is invalid for `Dataset` structure.
3. Required core fields are missing (`@type`, `@id` or `url`, `name`, `description`, `identifier`).

If Stage 1 fails, FAIR semantic checks should return not-applicable for web-discovery scoring.

### Stage 2: FAIR semantic checks (only after Stage 1 passes)

Run MetaDIG FAIR checks that measure metadata completeness and discoverability.

## Test mapping matrix

The table below maps each target check to HydroShare metadata sources and implementation status.

| MetaDIG test | Proposed schema.org-aligned expectation | HydroShare metadata source | Status |
| --- | --- | --- | --- |
| `schema.org syntax gate` (new) | JSON-LD parseable and schema-valid `Dataset` graph | Landing-page JSON-LD in `baseresource.html` | Satisfiable now |
| `resource.distributionContact.present` | Accept `contactPoint` when present; otherwise accept creator/contributor with public contact fields as evidence | Creator/contributor profile fields (`name`, `email`, `organization`, `homepage`, `phone`, identifiers) | Satisfiable with focused change (or relaxed test now) |
| `resource.distributionContactIdentifier.present` | Accept contact identifier from `contactPoint.identifier`; fallback to ORCID/profile URL evidence | Creator identifiers and profile URL | Satisfiable with focused change (or relaxed test now) |
| `provenance.trace.present` | Accept lineage evidence from `isBasedOn`, `citation`, `isPartOf`, `hasPart`, `dateCreated`, `dateModified` | Relation metadata + resource dates | Satisfiable now if test logic is updated |
| `provenance.sourceEntity.present` | Accept source lineage via `isBasedOn` and/or version lineage links | Relation types `source`, `isVersionOf` and emitted lineage links | Satisfiable now if test logic is updated |
| `entity.name.present` | Accept entity-level evidence from schema-valid part/distribution structures; do not require custom `entity` block | File/aggregation names exist in HydroShare metadata | Satisfiable with focused serializer changes |
| `entity.format.present` | Accept `encodingFormat` as format evidence at dataset/distribution level | `encodingFormat` from resource/file metadata | Satisfiable now (with schema-aligned expectation) |
| `entity.identifier.present` | Optional in strict schema profile unless consistent per-entity identifiers are emitted | Mostly resource-level identifiers today | Needs additional model/serialization work |
| `entity.identifierType.present` | Optional in strict schema profile unless typed per-entity identifiers are emitted | No consistent per-entity typed identifiers in current output | Needs additional model/serialization work |
| `resource.publisherIdentifier.present` | Accept explicit publisher identifier (`identifier` or `sameAs`, for example ROR) | Publisher object already emitted with `name` and `url` | Satisfiable with small change |
| `resource.methods.present` | Keep non-blocking unless a schema-valid methods mapping is implemented | No dedicated methods field in current landing-page schema | Out of current scope |
| `provenance.processStepCode.present` | Keep non-blocking profile check | No schema-mapped process step structure | Out of current scope |
| `entity.description.present` | Keep non-blocking unless consistent per-entity descriptions are emitted | Inconsistent file-level descriptions | Out of current scope |
| `entity.checksum.present` | Keep non-blocking for strict schema profile; current output has bag-level checksum only | Bag/resource checksum available; no per-file checksums in landing-page JSON-LD | Out of current scope |
| `entity.qualityDescription.present` | Keep non-blocking profile check | Not represented in landing-page JSON-LD | Out of current scope |

## Recommended policy changes for MetaDIG

1. Add a schema-validity prerequisite for web-discovery FAIR checks.
2. Split checks into:
   - strict schema.org profile (blocking)
   - FAIR compatibility profile (advisory or non-blocking until model support exists)
3. Redefine provenance checks around schema-valid lineage properties instead of non-standard tags.
4. Treat methods, process-step, and deep entity attribute checks as profile-specific and non-blocking for schema.org discovery compliance.

## Suggested rollout

1. Add Stage 1 schema gate.
2. Update provenance/contact/entity-format checks to schema-aligned pass criteria.
3. Reclassify out-of-scope checks to advisory.
4. Re-evaluate strictness after HydroShare adds dedicated contact and richer entity serialization.

## Practical takeaway

HydroShare can satisfy core schema-valid discoverability checks now, can satisfy several additional FAIR checks with targeted serializer updates, and should treat EML-style deep entity checks as a separate profile until broader metadata model support is added.
