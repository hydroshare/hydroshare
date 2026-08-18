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
  embeds machine-readable metadata was extended with the new fields below
- `hs_core/templatetags/hydroshare_tags.py` — helper functions were added to
  pull together file lists, contact info, and relation links so the template
  stays readable

### Metadata fields added or improved

**Publisher identity**
Previously the publisher block named HydroShare as a CUAHSI repository but
did not include a globally recognized identifier for CUAHSI. We now include
the CUAHSI ROR identifier (`https://ror.org/003b04c03`), which is the standard
persistent ID for research organizations. This lets automated tools
unambiguously identify who published the resource.

**Creator identifiers (ORCID)**
Creator entries already included name, email, and affiliation. We now also
include the creator's ORCID when one is stored in their HydroShare profile.
ORCID is a persistent, globally unique identifier for researchers and is
specifically checked by MetaDIG.

**Contact person**
MetaDIG checks whether a resource has a named point of contact — someone
responsible for the data. HydroShare does not have a separate "contact" field,
so we derive this from the first listed creator: their name, email,
affiliation, ORCID, and profile URL. This is emitted as a structured contact
block in the metadata.

**Provenance — lineage history**
If a resource links to related resources (e.g. it is derived from another
dataset, is a new version of an older one, or is part of a collection), those
links are now collected and exposed as a lineage trail. This tells tools and
users where the data came from and how it relates to other resources.

**Provenance — source resource**
A specific subset of the lineage: if the resource was directly derived from or
supersedes another resource, that parent/prior resource is called out
explicitly as the "source entity". If no such link exists the field is omitted.

**File list with names and formats**
Each file in the resource is now listed individually in the metadata, with its
filename and file type (e.g. `text/csv`, `image/tiff`). Previously only a
single zip-archive download link was described. This lets MetaDIG verify that
the dataset contains named entities with known formats.

### What was already working (no change)

Title, abstract, keywords, resource identifier, creators, license, dates,
geographic coverage, temporal coverage, download link, funding, and related
resource links were all already present and did not need to change.

## MetaDIG FAIR Check Status

| Status | What it means |
|---|---|
| **Passing before this PR** | Title length, abstract length, creator presence, publisher name, keywords, publication date, landing page URL, license, spatial coverage, temporal coverage, resource identifier |
| **Now passing after this PR** | Publisher has a recognized identifier (ROR), creators have persistent identifiers (ORCID), a contact person is identified, provenance/lineage links are present, files are listed with names and formats |
| **Out of scope** | Checks that require column-level or attribute-level metadata (units, measurement scale, enumerated domains, etc.), per-file checksums, and a structured methods section — HydroShare does not currently store or expose this information on the landing page |

## A Note on Relation Links

HydroShare uses slightly different terminology internally for one relation type.
When a resource is marked as derived from another source, HydroShare calls it
`source`. The standard schema.org term for the same concept is `isBasedOn`.
The landing page translates this automatically so external tools see the
correct term. All other relation types (`isPartOf`, `hasPart`, `isVersionOf`,
`references`, etc.) use the same name in both systems.
