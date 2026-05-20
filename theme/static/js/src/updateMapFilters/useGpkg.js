import { log } from "../config.js";
function _ensureBytes(v) {
    if (v instanceof Uint8Array) return v;
    if (v instanceof ArrayBuffer) return new Uint8Array(v);
    if (v && v.buffer instanceof ArrayBuffer) return new Uint8Array(v.buffer, v.byteOffset, v.byteLength);
    if (typeof v === 'string') {
    // hyparquet returns BYTE_ARRAY columns as JS strings — convert char-by-char
    const b = new Uint8Array(v.length);
    for (let i = 0; i < v.length; i++) b[i] = v.charCodeAt(i) & 0xff;
    return b;
    }
    return null;
}

// Extract [minx, miny, maxx, maxy] from a ring (array of sequential x,y doubles)
function _ringBbox(dv, off, n, le) {
    let x0=Infinity, y0=Infinity, x1=-Infinity, y1=-Infinity;
    for (let i = 0; i < n; i++, off += 16) {
    const x = dv.getFloat64(off, le), y = dv.getFloat64(off+8, le);
    if (x < x0) x0=x; if (x > x1) x1=x;
    if (y < y0) y0=y; if (y > y1) y1=y;
    }
    return [x0, y0, x1, y1];
}

// Extract [minx, miny, maxx, maxy] from WKB bytes
export function wkbBbox(bytes) {
    if (!bytes || bytes.length < 5) return null;
    try {
    const le = bytes[0] === 1;
    const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const gt = dv.getUint32(1, le) & 0xffff;
    if (gt === 1) { // POINT
        const x = dv.getFloat64(5, le), y = dv.getFloat64(13, le);
        return isFinite(x) && isFinite(y) ? [x, y, x, y] : null;
    }
    if (gt === 2) { // LINESTRING
        const n = dv.getUint32(5, le);
        return _ringBbox(dv, 9, n, le);
    }
    if (gt === 3) { // POLYGON
        const nr = dv.getUint32(5, le);
        if (!nr) return null;
        const n = dv.getUint32(9, le);
        return _ringBbox(dv, 13, n, le);
    }
    if (gt >= 4 && gt <= 7) { // MULTI* / GEOMETRYCOLLECTION
        const ng = dv.getUint32(5, le);
        let bb = null, off = 9;
        for (let g = 0; g < ng; g++) {
        const sle = bytes[off] === 1; off++;
        const st = dv.getUint32(off, sle) & 0xffff; off += 4;
        let sb = null;
        if (st === 1) {
            const x=dv.getFloat64(off,sle), y=dv.getFloat64(off+8,sle);
            sb = [x, y, x, y]; off += 16;
        } else if (st === 2) {
            const n = dv.getUint32(off, sle); off += 4;
            sb = _ringBbox(dv, off, n, sle); off += n*16;
        } else if (st === 3) {
            const nr2 = dv.getUint32(off, sle); off += 4;
            if (nr2 > 0) {
            const n = dv.getUint32(off, sle); off += 4;
            sb = _ringBbox(dv, off, n, sle); off += n*16;
            for (let r = 1; r < nr2; r++) { const rn = dv.getUint32(off, sle); off += 4+rn*16; }
            }
        }
        if (sb) bb = bb ? [Math.min(bb[0],sb[0]),Math.min(bb[1],sb[1]),Math.max(bb[2],sb[2]),Math.max(bb[3],sb[3])] : sb;
        }
        return bb;
    }
    return null;
    } catch(e) { return null; }
}

// Merge two [minx,miny,maxx,maxy] extents
export function mergeBbox(a, b) {
    if (!a) return b; if (!b) return a;
    return [Math.min(a[0],b[0]), Math.min(a[1],b[1]), Math.max(a[2],b[2]), Math.max(a[3],b[3])];
}

// Wrap raw WKB bytes in a GeoPackage geometry blob (GP header + optional bbox envelope + WKB)
// GP blob format: http://www.geopackage.org/spec/#gpb_format
export function toGpkgBlob(v, srsId) {
    const wkb = _ensureBytes(v);
    if (!wkb || !wkb.length) return null;
    // Already a GP blob (magic bytes 'G','P')?
    if (wkb[0] === 0x47 && wkb[1] === 0x50) return wkb;

    const bbox = wkbBbox(wkb);
    // flags: bit0=little-endian=1, bits1-3=envelope type (1=bbox, 0=none)
    // envelope type 1 = minx,maxx,miny,maxy (4x float64 = 32 bytes)
    const hLen = bbox ? 40 : 8;
    const hdr = new Uint8Array(hLen);
    hdr[0] = 0x47; hdr[1] = 0x50; hdr[2] = 0x00;
    hdr[3] = bbox ? 0x03 : 0x01; // 0x03 = le + envelope type 1; 0x01 = le + no envelope
    const hdv = new DataView(hdr.buffer);
    hdv.setInt32(4, srsId, true); // SRS ID little-endian
    if (bbox) {
    hdv.setFloat64(8,  bbox[0], true); // minx
    hdv.setFloat64(16, bbox[2], true); // maxx
    hdv.setFloat64(24, bbox[1], true); // miny
    hdv.setFloat64(32, bbox[3], true); // maxy
    }
    const out = new Uint8Array(hLen + wkb.length);
    out.set(hdr); out.set(wkb, hLen);
    return out;
}

// ============================================================
// GEOPACKAGE BUILDER
// ============================================================

// Geometry type per feature table (matches working.gpkg gpkg_geometry_columns)
const GEOM_TYPE = {
divides: 'POLYGON',
flowpaths: 'GEOMETRY',
nexus: 'POINT',
hydrolocations: 'POINT',
lakes: 'POINT',
};

// Hardcoded column definitions for tables that may have 0 matching rows,
// taken directly from template.sql to ensure schema consistency.
// fid is excluded here — it is prepended as PRIMARY KEY AUTOINCREMENT below.
const EMPTY_TABLE_COLS = {
'hydrolocations': '"poi_id" INTEGER,"id" TEXT,"nex_id" TEXT,"hf_id" REAL,"hl_link" TEXT,"hl_reference" TEXT,"hl_uri" TEXT,"hl_source" TEXT,"hl_x" REAL,"hl_y" REAL,"vpuid" TEXT,"geom" BLOB',
'pois':           '"poi_id" INTEGER,"id" TEXT,"nex_id" TEXT,"vpuid" TEXT',
'lakes':          '"geom" BLOB,"lake_id" REAL,"LkArea" REAL,"LkMxE" REAL,"WeirC" REAL,"WeirL" REAL,"OrificeC" REAL,"OrificeA" REAL,"OrificeE" REAL,"WeirE" REAL,"ifd" REAL,"Dam_Length" REAL,"domain" TEXT,"poi_id" INTEGER,"hf_id" REAL,"reservoir_index_AnA" REAL,"reservoir_index_Extended_AnA" REAL,"reservoir_index_GDL_AK" REAL,"reservoir_index_Medium_Range" REAL,"reservoir_index_Short_Range" REAL,"res_id" TEXT,"vpuid" TEXT,"lake_x" REAL,"lake_y" REAL',
};

export function useGpkg() {

    async function buildGeoPackage(tableData) {
      const SQL = await initSqlJs({
        locateFile: f => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.11.0/${f}`
      });
      const db = new SQL.Database();

      db.run(`
        CREATE TABLE gpkg_spatial_ref_sys (
          srs_name TEXT NOT NULL, srs_id INTEGER NOT NULL PRIMARY KEY,
          organization TEXT NOT NULL, organization_coordsys_id INTEGER NOT NULL,
          definition TEXT NOT NULL, description TEXT
        );
        INSERT INTO gpkg_spatial_ref_sys VALUES
          ('NAD83 / Conus Albers',5070,'EPSG',5070,'PROJCS["NAD83 / Conus Albers",GEOGCS["NAD83",DATUM["North_American_Datum_1983",SPHEROID["GRS 1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["latitude_of_center",23],PARAMETER["longitude_of_center",-96],PARAMETER["standard_parallel_1",29.5],PARAMETER["standard_parallel_2",45.5],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1]]',NULL),
          ('WGS 84',4326,'EPSG',4326,'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',NULL),
          ('Undefined cartesian',-1,'NONE',-1,'undefined',NULL),
          ('Undefined geographic',0,'NONE',0,'undefined',NULL);
        CREATE TABLE gpkg_contents (
          table_name TEXT NOT NULL PRIMARY KEY, data_type TEXT NOT NULL,
          identifier TEXT, description TEXT DEFAULT '',
          last_change DATETIME DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
          min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE,
          srs_id INTEGER REFERENCES gpkg_spatial_ref_sys(srs_id)
        );
        CREATE TABLE gpkg_geometry_columns (
          table_name TEXT NOT NULL, column_name TEXT NOT NULL,
          geometry_type_name TEXT NOT NULL, srs_id INTEGER NOT NULL,
          z TINYINT NOT NULL, m TINYINT NOT NULL,
          CONSTRAINT pk_gc PRIMARY KEY (table_name, column_name)
        );
        CREATE TABLE gpkg_ogr_contents (table_name TEXT NOT NULL PRIMARY KEY, feature_count INTEGER);
        CREATE TABLE gpkg_extensions (
          table_name TEXT, column_name TEXT, extension_name TEXT NOT NULL,
          definition TEXT NOT NULL, scope TEXT NOT NULL,
          CONSTRAINT ge_tce UNIQUE (table_name, column_name, extension_name)
        );
        CREATE TABLE gpkg_tile_matrix_set (
          table_name TEXT NOT NULL PRIMARY KEY, srs_id INTEGER NOT NULL,
          min_x DOUBLE NOT NULL, min_y DOUBLE NOT NULL,
          max_x DOUBLE NOT NULL, max_y DOUBLE NOT NULL
        );
        CREATE TABLE gpkg_tile_matrix (
          table_name TEXT NOT NULL, zoom_level INTEGER NOT NULL,
          matrix_width INTEGER NOT NULL, matrix_height INTEGER NOT NULL,
          tile_width INTEGER NOT NULL, tile_height INTEGER NOT NULL,
          pixel_x_size DOUBLE NOT NULL, pixel_y_size DOUBLE NOT NULL,
          CONSTRAINT pk_ttm PRIMARY KEY (table_name, zoom_level)
        );
        PRAGMA application_id = 1196444487;
        PRAGMA user_version = 10200;
      `);


      const geomTables = new Set(Object.keys(GEOM_TYPE));

      

      for (const [tableName, entry] of Object.entries(tableData)) {
        // entry is { rows, url } from doTable
        const rows = Array.isArray(entry) ? entry : (entry?.rows ?? []);

        const hasGeom = geomTables.has(tableName);

        let columns, colDefs, geomCol;
        if (rows.length > 0) {
          columns = Object.keys(rows[0]);
          geomCol = (hasGeom && columns.find(c => c === 'geom' || c === 'geometry')) || null;
          colDefs = columns.map(c => {
            if (c === geomCol) return `"${c}" BLOB`;
            const sample = rows[0][c];
            if (typeof sample === 'number') return Number.isInteger(sample) ? `"${c}" INTEGER` : `"${c}" REAL`;
            return `"${c}" TEXT`;
          }).join(', ');
        } else if (EMPTY_TABLE_COLS[tableName]) {
          colDefs = EMPTY_TABLE_COLS[tableName];
          columns = colDefs.split(',').map(d => d.match(/"([^"]+)"/)[1]);
          geomCol = hasGeom ? (columns.find(c => c === 'geom' || c === 'geometry') || null) : null;
        } else {
          continue;
        }

        const hasFid = columns.includes('fid');
        db.run(`CREATE TABLE "${tableName}" (${hasFid ? colDefs : `fid INTEGER PRIMARY KEY AUTOINCREMENT, ${colDefs}`})`);

        let extent = null;
        if (rows.length > 0) {
          const placeholders = columns.map(() => '?').join(',');
          const colStr = columns.map(c => `"${c}"`).join(',');
          const stmt = db.prepare(`INSERT INTO "${tableName}" (${colStr}) VALUES (${placeholders})`);
          for (const row of rows) {
            const vals = columns.map(c => {
              const v = row[c];
              if (v == null) return null;
              if (c === geomCol) {
                const gpb = toGpkgBlob(v, 5070);
                if (gpb) {
                  const envType = (gpb[3] & 0x0E) >> 1;
                  const wkbOff = 8 + [0,32,48,48,64][envType];
                  extent = mergeBbox(extent, wkbBbox(gpb.subarray(wkbOff)));
                }
                return gpb;
              }
              return v;
            });
            try { stmt.run(vals); } catch(e) {}
          }
          stmt.free();
        }

        const dataType = hasGeom ? 'features' : 'attributes';
        if (hasGeom && extent) {
          db.run(
            `INSERT INTO gpkg_contents (table_name,data_type,identifier,description,min_x,min_y,max_x,max_y,srs_id) VALUES (?,?,?,'',?,?,?,?,?)`,
            [tableName, dataType, tableName, extent[0], extent[1], extent[2], extent[3], 5070]
          );
        } else {
          db.run(`INSERT INTO gpkg_contents (table_name,data_type,identifier,srs_id) VALUES (?,?,?,?)`,
            [tableName, dataType, tableName, hasGeom ? 5070 : 0]);
        }
        if (hasGeom) {
          db.run(`INSERT INTO gpkg_geometry_columns VALUES (?,?,?,5070,0,0)`,
            [tableName, geomCol, GEOM_TYPE[tableName] || 'GEOMETRY']);
        }
        db.run(`INSERT INTO gpkg_ogr_contents VALUES (?,?)`, [tableName, rows.length]);
        log(`  gpkg: ${tableName} (${rows.length} rows)`, '');
      }

      const data = db.export();
      db.close();
      return new Blob([data], { type: 'application/geopackage+sqlite3' });
    }
    return { buildGeoPackage };
}