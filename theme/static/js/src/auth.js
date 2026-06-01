import { isPmtilesProtocolRegistered, setPmtilesProtocolRegistered, REF_DIVIDES_PMTILES_URL, REF_FLOWPATHS_PMTILES_URL, COMMUNITY_HF_DIVIDES, COMMUNITY_HF_FLOWPATHS } from "./config.js";
function createCredentialedPmtilesSource(url) {
    return {
    getKey() {
        return url;
    },
    async getBytes(offset, length, signal, etag) {
        const headers = new Headers();
        headers.set('range', `bytes=${offset}-${offset + length - 1}`);

        const resp = await fetch(url, {
        signal,
        headers,
        credentials: 'include',
        });

        const newEtag = resp.headers.get('Etag') || undefined;
        if (resp.status === 416 || (etag && newEtag && newEtag !== etag)) {
        throw new pmtiles.EtagMismatch(`Server returned non-matching ETag ${etag}`);
        }
        if (resp.status >= 300) {
        throw new Error(`Bad response code: ${resp.status}`);
        }

        const contentLength = resp.headers.get('Content-Length');
        if (resp.status === 200 && (!contentLength || +contentLength > length)) {
        throw new Error('Server returned no content-length header or content-length exceeding request. Check that your storage backend supports HTTP Byte Serving.');
        }

        return {
        data: await resp.arrayBuffer(),
        etag: newEtag,
        cacheControl: resp.headers.get('Cache-Control') || undefined,
        expires: resp.headers.get('Expires') || undefined,
        };
    },
    };
}

export function ensurePmtilesProtocol() {
    if (isPmtilesProtocolRegistered()) return;

    const protocol = new pmtiles.Protocol({ metadata: true });
    protocol.add(new pmtiles.PMTiles(createCredentialedPmtilesSource(REF_FLOWPATHS_PMTILES_URL)));
    protocol.add(new pmtiles.PMTiles(createCredentialedPmtilesSource(REF_DIVIDES_PMTILES_URL)));
    protocol.add(new pmtiles.PMTiles(createCredentialedPmtilesSource(COMMUNITY_HF_FLOWPATHS)));
    protocol.add(new pmtiles.PMTiles(createCredentialedPmtilesSource(COMMUNITY_HF_DIVIDES)));

    maplibregl.addProtocol('pmtiles', protocol.tile);
    setPmtilesProtocolRegistered(true);
}