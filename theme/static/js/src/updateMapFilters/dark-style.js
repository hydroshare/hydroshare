import { S3_MAP } from '../config.js';

export function useDarkStyle() {
  return{
  "version": 8,
  "sources": {
    "protomaps": {
      "type": "vector",
      "url": "pmtiles://https://communityhydrofabric.s3.us-east-1.amazonaws.com/map/basemaps-assets-main/20241118.pmtiles",
      "attribution": "&copy; <a href=\"https://openmaptiles.org/\">OpenMapTiles</a> &copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a>"
    },
    "hydrofabric": {
      "type": "vector",
      "url": `pmtiles://${S3_MAP}/merged.pmtiles`,
      "attribution": "Community Hydrofabric Based on hf2.2 ODbL <a href=\"https://lynker-spatial.s3-us-west-2.amazonaws.com/copyright.html\">lynker-spatial</a>",
      "maxzoom": 10
    },
    "conus_vpu": {
      "type": "vector",
      "url": `pmtiles://${S3_MAP}/only_geometry/reference/vpu.pmtiles`
    }
  },
  "layers": [
    {
      "id": "background",
      "type": "background",
      "paint": {
        "background-color": "#34373d"
      }
    },
    {
      "id": "earth",
      "type": "fill",
      "filter": ["==", ["geometry-type"], "Polygon"],
      "source": "protomaps",
      "source-layer": "earth",
      "paint": {
        "fill-color": "#1f1f1f"
      }
    },
    {
      "id": "landcover",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landcover",
      "paint": {
        "fill-color": [
          "match",
          ["get", "kind"],
          "grassland",
          "rgba(30, 41, 31, 1)",
          "barren",
          "rgba(38, 38, 36, 1)",
          "urban_area",
          "rgba(28, 28, 28, 1)",
          "farmland",
          "rgba(31, 36, 32, 1)",
          "glacier",
          "rgba(43, 43, 43, 1)",
          "scrub",
          "rgba(34, 36, 30, 1)",
          "rgba(28, 41, 37, 1)"
        ],
        "fill-opacity": ["interpolate", ["linear"], ["zoom"], 5, 1, 7, 0]
      }
    },
    {
      "id": "landuse_park",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "filter": [
        "in",
        "kind",
        "national_park",
        "park",
        "cemetery",
        "protected_area",
        "nature_reserve",
        "forest",
        "golf_course",
        "wood",
        "nature_reserve",
        "forest",
        "scrub",
        "grassland",
        "grass",
        "military",
        "naval_base",
        "airfield"
      ],
      "paint": {
        "fill-opacity": ["interpolate", ["linear"], ["zoom"], 6, 0, 11, 1],
        "fill-color": [
          "case",
          [
            "in",
            ["get", "kind"],
            [
              "literal",
              [
                "national_park",
                "park",
                "cemetery",
                "protected_area",
                "nature_reserve",
                "forest",
                "golf_course"
              ]
            ]
          ],
          "#192a24",
          [
            "in",
            ["get", "kind"],
            ["literal", ["wood", "nature_reserve", "forest"]]
          ],
          "#202121",
          ["in", ["get", "kind"], ["literal", ["scrub", "grassland", "grass"]]],
          "#222323",
          ["in", ["get", "kind"], ["literal", ["glacier"]]],
          "#1c1c1c",
          ["in", ["get", "kind"], ["literal", ["sand"]]],
          "#212123",
          [
            "in",
            ["get", "kind"],
            ["literal", ["military", "naval_base", "airfield"]]
          ],
          "#222323",
          "#1f1f1f"
        ]
      }
    },
    {
      "id": "landuse_urban_green",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "filter": ["in", "kind", "allotments", "village_green", "playground"],
      "paint": {
        "fill-color": "#192a24",
        "fill-opacity": 0.7
      }
    },
    {
      "id": "landuse_hospital",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "filter": ["==", "kind", "hospital"],
      "paint": {
        "fill-color": "#252424"
      }
    },
    {
      "id": "landuse_industrial",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "filter": ["==", "kind", "industrial"],
      "paint": {
        "fill-color": "#222222"
      }
    },
    {
      "id": "landuse_school",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "filter": ["in", "kind", "school", "university", "college"],
      "paint": {
        "fill-color": "#262323"
      }
    },
    {
      "id": "landuse_beach",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "filter": ["in", "kind", "beach"],
      "paint": {
        "fill-color": "#28282a"
      }
    },
    {
      "id": "landuse_zoo",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "filter": ["in", "kind", "zoo"],
      "paint": {
        "fill-color": "#222323"
      }
    },
    {
      "id": "landuse_aerodrome",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "filter": ["in", "kind", "aerodrome"],
      "paint": {
        "fill-color": "#1e1e1e"
      }
    },
    {
      "id": "roads_runway",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": ["==", "kind_detail", "runway"],
      "paint": {
        "line-color": "#333333",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          10,
          0,
          12,
          4,
          18,
          30
        ]
      }
    },
    {
      "id": "roads_taxiway",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 13,
      "filter": ["==", "kind_detail", "taxiway"],
      "paint": {
        "line-color": "#333333",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          13.5,
          1,
          15,
          6
        ]
      }
    },
    {
      "id": "landuse_runway",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "filter": ["any", ["in", "kind", "runway", "taxiway"]],
      "paint": {
        "fill-color": "#333333"
      }
    },
    {
      "id": "water",
      "type": "fill",
      "filter": ["==", ["geometry-type"], "Polygon"],
      "source": "protomaps",
      "source-layer": "water",
      "paint": {
        "fill-color": "#31353f"
      }
    },
    {
      "id": "water_stream",
      "type": "line",
      "source": "protomaps",
      "source-layer": "water",
      "minzoom": 14,
      "filter": ["in", "kind", "stream"],
      "paint": {
        "line-color": "#31353f",
        "line-opacity": {
          "stops": [
            [7, 1],
            [8, 0.05]
          ]
        },
        "line-width": 0.5
      }
    },
    {
      "id": "water_river",
      "type": "line",
      "source": "protomaps",
      "source-layer": "water",
      "minzoom": 9,
      "filter": ["in", "kind", "river"],
      "paint": {
        "line-color": "#31353f",
        "line-opacity": {
          "stops": [
            [7, 1],
            [8, 0.05]
          ]
        },
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          9,
          0,
          9.5,
          1,
          18,
          12
        ]
      }
    },
    {
      "id": "landuse_pedestrian",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "filter": ["==", "kind", "pedestrian"],
      "paint": {
        "fill-color": "#1e1e1e"
      }
    },
    {
      "id": "landuse_pier",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "filter": ["==", "kind", "pier"],
      "paint": {
        "fill-color": "#333333"
      }
    },
    {
      "id": "roads_tunnels_other_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": ["all", ["has", "is_tunnel"], ["in", "kind", "other", "path"]],
      "paint": {
        "line-color": "#141414",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          14,
          0,
          20,
          7
        ]
      }
    },
    {
      "id": "roads_tunnels_minor_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": ["all", ["has", "is_tunnel"], ["==", "kind", "minor_road"]],
      "paint": {
        "line-color": "#141414",
        "line-dasharray": [3, 2],
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          11,
          0,
          12.5,
          0.5,
          15,
          2,
          18,
          11
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          12,
          0,
          12.5,
          1
        ]
      }
    },
    {
      "id": "roads_tunnels_link_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": ["all", ["has", "is_tunnel"], ["has", "is_link"]],
      "paint": {
        "line-color": "#141414",
        "line-dasharray": [3, 2],
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          13.5,
          1,
          18,
          11
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          12,
          0,
          12.5,
          1
        ]
      }
    },
    {
      "id": "roads_tunnels_major_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "major_road"]
      ],
      "paint": {
        "line-color": "#141414",
        "line-dasharray": [3, 2],
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          7,
          0,
          7.5,
          0.5,
          18,
          13
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          9,
          0,
          9.5,
          1
        ]
      }
    },
    {
      "id": "roads_tunnels_highway_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "highway"],
        ["!has", "is_link"]
      ],
      "paint": {
        "line-color": "#141414",
        "line-dasharray": [6, 0.5],
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          3,
          0,
          3.5,
          0.5,
          18,
          15
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          7,
          0,
          7.5,
          1,
          20,
          15
        ]
      }
    },
    {
      "id": "roads_tunnels_other",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": ["all", ["has", "is_tunnel"], ["in", "kind", "other", "path"]],
      "paint": {
        "line-color": "#292929",
        "line-dasharray": [4.5, 0.5],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          14,
          0,
          20,
          7
        ]
      }
    },
    {
      "id": "roads_tunnels_minor",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": ["all", ["has", "is_tunnel"], ["==", "kind", "minor_road"]],
      "paint": {
        "line-color": "#292929",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          11,
          0,
          12.5,
          0.5,
          15,
          2,
          18,
          11
        ]
      }
    },
    {
      "id": "roads_tunnels_link",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": ["all", ["has", "is_tunnel"], ["has", "is_link"]],
      "paint": {
        "line-color": "#292929",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          13.5,
          1,
          18,
          11
        ]
      }
    },
    {
      "id": "roads_tunnels_major",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": ["all", ["has", "is_tunnel"], ["==", "kind", "major_road"]],
      "paint": {
        "line-color": "#292929",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          6,
          0,
          12,
          1.6,
          15,
          3,
          18,
          13
        ]
      }
    },
    {
      "id": "roads_tunnels_highway",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": [
        "all",
        ["has", "is_tunnel"],
        ["==", ["get", "kind"], "highway"],
        ["!", ["has", "is_link"]]
      ],
      "paint": {
        "line-color": "#292929",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          3,
          0,
          6,
          1.1,
          12,
          1.6,
          15,
          5,
          18,
          15
        ]
      }
    },
    {
      "id": "buildings",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "buildings",
      "paint": {
        "fill-color": "#111111",
        "fill-opacity": 0.5
      }
    },
    {
      "id": "roads_pier",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": ["==", "kind_detail", "pier"],
      "paint": {
        "line-color": "#333333",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          12,
          0,
          12.5,
          0.5,
          20,
          16
        ]
      }
    },
    {
      "id": "roads_minor_service_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 13,
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "minor_road"],
        ["==", "kind_detail", "service"]
      ],
      "paint": {
        "line-color": "#1f1f1f",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          18,
          8
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          13.5,
          0.8
        ]
      }
    },
    {
      "id": "roads_minor_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "minor_road"],
        ["!=", "kind_detail", "service"]
      ],
      "paint": {
        "line-color": "#1f1f1f",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          11,
          0,
          12.5,
          0.5,
          15,
          2,
          18,
          11
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          12,
          0,
          12.5,
          1
        ]
      }
    },
    {
      "id": "roads_link_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 13,
      "filter": ["has", "is_link"],
      "paint": {
        "line-color": "#1f1f1f",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          13.5,
          1,
          18,
          11
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          13.5,
          1.5
        ]
      }
    },
    {
      "id": "roads_major_casing_late",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 12,
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "major_road"]
      ],
      "paint": {
        "line-color": "#1f1f1f",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          6,
          0,
          12,
          1.6,
          15,
          3,
          18,
          13
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          9,
          0,
          9.5,
          1
        ]
      }
    },
    {
      "id": "roads_highway_casing_late",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 12,
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "highway"],
        ["!has", "is_link"]
      ],
      "paint": {
        "line-color": "#1f1f1f",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          3,
          0,
          3.5,
          0.5,
          18,
          15
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          7,
          0,
          7.5,
          1,
          20,
          15
        ]
      }
    },
    {
      "id": "roads_other",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["in", "kind", "other", "path"],
        ["!=", "kind_detail", "pier"]
      ],
      "paint": {
        "line-color": "#333333",
        "line-dasharray": [3, 1],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          14,
          0,
          20,
          7
        ]
      }
    },
    {
      "id": "roads_link",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": ["has", "is_link"],
      "paint": {
        "line-color": "#3d3d3d",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          13.5,
          1,
          18,
          11
        ]
      }
    },
    {
      "id": "roads_minor_service",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "minor_road"],
        ["==", "kind_detail", "service"]
      ],
      "paint": {
        "line-color": "#333333",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          18,
          8
        ]
      }
    },
    {
      "id": "roads_minor",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "minor_road"],
        ["!=", "kind_detail", "service"]
      ],
      "paint": {
        "line-color": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          11,
          "#3d3d3d",
          16,
          "#333333"
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          11,
          0,
          12.5,
          0.5,
          15,
          2,
          18,
          11
        ]
      }
    },
    {
      "id": "roads_major_casing_early",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "maxzoom": 12,
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "major_road"]
      ],
      "paint": {
        "line-color": "#1f1f1f",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          7,
          0,
          7.5,
          0.5,
          18,
          13
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          9,
          0,
          9.5,
          1
        ]
      }
    },
    {
      "id": "roads_major",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "major_road"]
      ],
      "paint": {
        "line-color": "#3d3d3d",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          6,
          0,
          12,
          1.6,
          15,
          3,
          18,
          13
        ]
      }
    },
    {
      "id": "roads_highway_casing_early",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "maxzoom": 12,
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "highway"],
        ["!has", "is_link"]
      ],
      "paint": {
        "line-color": "#1f1f1f",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          3,
          0,
          3.5,
          0.5,
          18,
          15
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          7,
          0,
          7.5,
          1
        ]
      }
    },
    {
      "id": "roads_highway",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": [
        "all",
        ["!has", "is_tunnel"],
        ["!has", "is_bridge"],
        ["==", "kind", "highway"],
        ["!has", "is_link"]
      ],
      "paint": {
        "line-color": "#474747",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          3,
          0,
          6,
          1.1,
          12,
          1.6,
          15,
          5,
          18,
          15
        ]
      }
    },
    {
      "id": "roads_rail",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": ["==", "kind", "rail"],
      "paint": {
        "line-dasharray": [0.3, 0.75],
        "line-opacity": 0.5,
        "line-color": "#000000",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          3,
          0,
          6,
          0.15,
          18,
          9
        ]
      }
    },
    {
      "id": "boundaries_country",
      "type": "line",
      "source": "protomaps",
      "source-layer": "boundaries",
      "filter": ["<=", "kind_detail", 2],
      "paint": {
        "line-color": "#5b6374",
        "line-width": 1,
        "line-dasharray": [3, 2]
      }
    },
    {
      "id": "boundaries",
      "type": "line",
      "source": "protomaps",
      "source-layer": "boundaries",
      "filter": [">", "kind_detail", 2],
      "paint": {
        "line-color": "#5b6374",
        "line-width": 0.5,
        "line-dasharray": [3, 2]
      }
    },
    {
      "id": "roads_bridges_other_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 12,
      "filter": ["all", ["has", "is_bridge"], ["in", "kind", "other", "path"]],
      "paint": {
        "line-color": "#2b2b2b",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          14,
          0,
          20,
          7
        ]
      }
    },
    {
      "id": "roads_bridges_link_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 12,
      "filter": ["all", ["has", "is_bridge"], ["has", "is_link"]],
      "paint": {
        "line-color": "#1f1f1f",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          13.5,
          1,
          18,
          11
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          12,
          0,
          12.5,
          1.5
        ]
      }
    },
    {
      "id": "roads_bridges_minor_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 12,
      "filter": ["all", ["has", "is_bridge"], ["==", "kind", "minor_road"]],
      "paint": {
        "line-color": "#1f1f1f",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          11,
          0,
          12.5,
          0.5,
          15,
          2,
          18,
          11
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          13.5,
          0.8
        ]
      }
    },
    {
      "id": "roads_bridges_major_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 12,
      "filter": ["all", ["has", "is_bridge"], ["==", "kind", "major_road"]],
      "paint": {
        "line-color": "#1f1f1f",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          7,
          0,
          7.5,
          0.5,
          18,
          10
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          9,
          0,
          9.5,
          1.5
        ]
      }
    },
    {
      "id": "roads_bridges_other",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 12,
      "filter": ["all", ["has", "is_bridge"], ["in", "kind", "other", "path"]],
      "paint": {
        "line-color": "#333333",
        "line-dasharray": [2, 1],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          14,
          0,
          20,
          7
        ]
      }
    },
    {
      "id": "roads_bridges_minor",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 12,
      "filter": ["all", ["has", "is_bridge"], ["==", "kind", "minor_road"]],
      "paint": {
        "line-color": "#333333",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          11,
          0,
          12.5,
          0.5,
          15,
          2,
          18,
          11
        ]
      }
    },
    {
      "id": "roads_bridges_link",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 12,
      "filter": ["all", ["has", "is_bridge"], ["has", "is_link"]],
      "paint": {
        "line-color": "#333333",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          13,
          0,
          13.5,
          1,
          18,
          11
        ]
      }
    },
    {
      "id": "roads_bridges_major",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 12,
      "filter": ["all", ["has", "is_bridge"], ["==", "kind", "major_road"]],
      "paint": {
        "line-color": "#3d3d3d",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          6,
          0,
          12,
          1.6,
          15,
          3,
          18,
          13
        ]
      }
    },
    {
      "id": "roads_bridges_highway_casing",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 12,
      "filter": [
        "all",
        ["has", "is_bridge"],
        ["==", "kind", "highway"],
        ["!has", "is_link"]
      ],
      "paint": {
        "line-color": "#1f1f1f",
        "line-gap-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          3,
          0,
          3.5,
          0.5,
          18,
          15
        ],
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          7,
          0,
          7.5,
          1,
          20,
          15
        ]
      }
    },
    {
      "id": "roads_bridges_highway",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "filter": [
        "all",
        ["has", "is_bridge"],
        ["==", "kind", "highway"],
        ["!has", "is_link"]
      ],
      "paint": {
        "line-color": "#474747",
        "line-width": [
          "interpolate",
          ["exponential", 1.6],
          ["zoom"],
          3,
          0,
          6,
          1.1,
          12,
          1.6,
          15,
          5,
          18,
          15
        ]
      }
    },
    {
      "id": "vpu",
      "type": "line",
      "source": "conus_vpu",
      "source-layer": "vpu",
      "layout": {},
      "paint": {
        "line-width": 2,
        "line-color": ["rgba", 0, 153, 136, 1]
      }
    },
    {
      "id": "ak_flowpaths",
      "type": "line",
      "source": "hydrofabric",
      "source-layer": "ak_flowpaths",
      "layout": {},
      "paint": {
        "line-color": ["rgba", 0, 119, 187, 1],
        "line-width": {
          "stops": [
            [7, 1],
            [10, 2]
          ]
        },
        "line-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      }
    },
    {
      "id": "ak_catchments",
      "type": "fill",
      "source": "hydrofabric",
      "source-layer": "ak_divides",
      "layout": {},
      "paint": {
        "fill-color": ["rgba", 0, 0, 0, 0],
        "fill-outline-color": ["rgba", 0, 0, 0, 0.5],
        "fill-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      }
    },
    {
      "id": "gl_flowpaths",
      "type": "line",
      "source": "hydrofabric",
      "source-layer": "gl_flowpaths",
      "layout": {},
      "paint": {
        "line-color": ["rgba", 0, 119, 187, 1],
        "line-width": {
          "stops": [
            [7, 1],
            [10, 2]
          ]
        },
        "line-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      }
    },
    {
      "id": "gl_catchments",
      "type": "fill",
      "source": "hydrofabric",
      "source-layer": "gl_divides",
      "layout": {},
      "paint": {
        "fill-color": ["rgba", 0, 0, 0, 0],
        "fill-outline-color": ["rgba", 0, 0, 0, 0.5],
        "fill-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      }
    },
    {
      "id": "hi_flowpaths",
      "type": "line",
      "source": "hydrofabric",
      "source-layer": "hi_flowpaths",
      "layout": {},
      "paint": {
        "line-color": ["rgba", 0, 119, 187, 1],
        "line-width": {
          "stops": [
            [7, 1],
            [10, 2]
          ]
        },
        "line-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      }
    },
    {
      "id": "hi_catchments",
      "type": "fill",
      "source": "hydrofabric",
      "source-layer": "hi_divides",
      "layout": {},
      "paint": {
        "fill-color": ["rgba", 0, 0, 0, 0],
        "fill-outline-color": ["rgba", 0, 0, 0, 0.5],
        "fill-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      }
    },
    {
      "id": "prvi_flowpaths",
      "type": "line",
      "source": "hydrofabric",
      "source-layer": "prvi_flowpaths",
      "layout": {},
      "paint": {
        "line-color": ["rgba", 0, 119, 187, 1],
        "line-width": {
          "stops": [
            [7, 1],
            [10, 2]
          ]
        },
        "line-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      }
    },
    {
      "id": "prvi_catchments",
      "type": "fill",
      "source": "hydrofabric",
      "source-layer": "prvi_divides",
      "layout": {},
      "paint": {
        "fill-color": ["rgba", 0, 0, 0, 0],
        "fill-outline-color": ["rgba", 0, 0, 0, 0.5],
        "fill-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      }
    },
    {
      "id": "flowpaths",
      "type": "line",
      "source": "hydrofabric",
      "source-layer": "conus_flowpaths",
      "layout": {},
      "paint": {
        "line-color": ["rgba", 0, 119, 187, 1],
        "line-width": {
          "stops": [
            [7, 1],
            [10, 2]
          ]
        },
        "line-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      }
    },
    {
      "id": "catchments",
      "type": "fill",
      "source": "hydrofabric",
      "source-layer": "conus_divides",
      "layout": {},
      "paint": {
        "fill-color": ["rgba", 0, 0, 0, 0],
        "fill-outline-color": ["rgba", 200, 200, 200, 0.5],
        "fill-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      }
    },
    {
      "id": "selected-flowpaths",
      "type": "line",
      "source": "hydrofabric",
      "source-layer": "conus_flowpaths",
      "layout": {},
      "paint": {
        "line-color": ["rgba", 0, 119, 187, 1],
        "line-width": {
          "stops": [
            [7, 1],
            [10, 2]
          ]
        },
        "line-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      },
      "filter": ["any", ["in", "id", ""]]
    },
    {
      "id": "selected-catchments",
      "type": "fill",
      "source": "hydrofabric",
      "source-layer": "conus_divides",
      "layout": {},
      "paint": {
        "fill-color": ["rgba", 238, 51, 119, 0.316],
        "fill-outline-color": ["rgba", 238, 51, 119, 0.7],
        "fill-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      },
      "filter": ["any", ["in", "divide_id", ""]]
    },
    {
      "id": "upstream-catchments",
      "type": "fill",
      "source": "hydrofabric",
      "source-layer": "conus_divides",
      "layout": {},
      "paint": {
        "fill-color": ["rgba", 238, 119, 51, 0.278],
        "fill-outline-color": ["rgba", 238, 119, 51, 0.7],
        "fill-opacity": {
          "stops": [
            [7, 0],
            [11, 1]
          ]
        }
      },
      "filter": ["any", ["in", "divide_id", ""]]
    },
    {
      "id": "conus_gages",
      "type": "circle",
      "source": "hydrofabric",
      "source-layer": "conus_gages",
      "layout": {},
      "filter": ["any", ["==", "hl_reference", ""]],
      "paint": {
        "circle-radius": {
          "stops": [
            [3, 2],
            [11, 5]
          ]
        },
        "circle-color": ["rgba", 200, 200, 200, 1],
        "circle-opacity": {
          "stops": [
            [3, 0],
            [9, 1]
          ]
        }
      }
    },
    {
      "id": "water_waterway_label",
      "type": "symbol",
      "source": "protomaps",
      "source-layer": "water",
      "minzoom": 13,
      "filter": ["in", "kind", "river", "stream"],
      "layout": {
        "symbol-placement": "line",
        "text-font": ["Noto Sans Italic"],
        "text-field": [
          "case",
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["!", ["any", ["has", "name2"], ["has", "pgf:name2"]]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["has", "script"],
            [
              "case",
              [
                "any",
                ["is-supported-script", ["get", "name"]],
                ["has", "pgf:name"]
              ],
              [
                "format",
                ["coalesce", ["get", "name:en"], ["get", "name:en"]],
                {},
                "\n",
                {},
                [
                  "case",
                  [
                    "all",
                    ["!", ["has", "name:en"]],
                    ["has", "name:en"],
                    ["!", ["has", "script"]]
                  ],
                  "",
                  ["coalesce", ["get", "pgf:name"], ["get", "name"]]
                ],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["get", "name:en"]
            ],
            [
              "format",
              [
                "coalesce",
                ["get", "name:en"],
                ["get", "pgf:name"],
                ["get", "name"]
              ],
              {}
            ]
          ],
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["any", ["has", "name2"], ["has", "pgf:name2"]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["has", "script2"],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"], ["has", "script3"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script3"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["!", ["has", "script"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["!", ["has", "script2"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name3"],
                  ["get", "name3"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ]
        ],
        "text-size": 12,
        "text-letter-spacing": 0.2
      },
      "paint": {
        "text-color": "#717784"
      }
    },
    {
      "id": "roads_labels_minor",
      "type": "symbol",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 15,
      "filter": ["in", "kind", "minor_road", "other", "path"],
      "layout": {
        "symbol-sort-key": ["get", "min_zoom"],
        "symbol-placement": "line",
        "text-font": ["Noto Sans Regular"],
        "text-field": [
          "case",
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["!", ["any", ["has", "name2"], ["has", "pgf:name2"]]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["has", "script"],
            [
              "case",
              [
                "any",
                ["is-supported-script", ["get", "name"]],
                ["has", "pgf:name"]
              ],
              [
                "format",
                ["coalesce", ["get", "name:en"], ["get", "name:en"]],
                {},
                "\n",
                {},
                [
                  "case",
                  [
                    "all",
                    ["!", ["has", "name:en"]],
                    ["has", "name:en"],
                    ["!", ["has", "script"]]
                  ],
                  "",
                  ["coalesce", ["get", "pgf:name"], ["get", "name"]]
                ],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["get", "name:en"]
            ],
            [
              "format",
              [
                "coalesce",
                ["get", "name:en"],
                ["get", "pgf:name"],
                ["get", "name"]
              ],
              {}
            ]
          ],
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["any", ["has", "name2"], ["has", "pgf:name2"]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["has", "script2"],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"], ["has", "script3"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script3"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["!", ["has", "script"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["!", ["has", "script2"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name3"],
                  ["get", "name3"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ]
        ],
        "text-size": 12
      },
      "paint": {
        "text-color": "#525252",
        "text-halo-color": "#1f1f1f",
        "text-halo-width": 1,
        "text-halo-blur": 1
      }
    },
    {
      "id": "water_label_ocean",
      "type": "symbol",
      "source": "protomaps",
      "source-layer": "water",
      "filter": [
        "in",
        "kind",
        "sea",
        "ocean",
        "lake",
        "water",
        "bay",
        "strait",
        "fjord"
      ],
      "layout": {
        "text-font": ["Noto Sans Italic"],
        "text-field": [
          "case",
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["!", ["any", ["has", "name2"], ["has", "pgf:name2"]]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["has", "script"],
            [
              "case",
              [
                "any",
                ["is-supported-script", ["get", "name"]],
                ["has", "pgf:name"]
              ],
              [
                "format",
                ["coalesce", ["get", "name:en"], ["get", "name:en"]],
                {},
                "\n",
                {},
                [
                  "case",
                  [
                    "all",
                    ["!", ["has", "name:en"]],
                    ["has", "name:en"],
                    ["!", ["has", "script"]]
                  ],
                  "",
                  ["coalesce", ["get", "pgf:name"], ["get", "name"]]
                ],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["get", "name:en"]
            ],
            [
              "format",
              [
                "coalesce",
                ["get", "name:en"],
                ["get", "pgf:name"],
                ["get", "name"]
              ],
              {}
            ]
          ],
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["any", ["has", "name2"], ["has", "pgf:name2"]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["has", "script2"],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"], ["has", "script3"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script3"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["!", ["has", "script"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["!", ["has", "script2"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name3"],
                  ["get", "name3"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ]
        ],
        "text-size": ["interpolate", ["linear"], ["zoom"], 3, 10, 10, 12],
        "text-letter-spacing": 0.1,
        "text-max-width": 9,
        "text-transform": "uppercase"
      },
      "paint": {
        "text-color": "#717784"
      }
    },
    {
      "id": "water_label_lakes",
      "type": "symbol",
      "source": "protomaps",
      "source-layer": "water",
      "filter": ["in", "kind", "lake", "water"],
      "layout": {
        "text-font": ["Noto Sans Italic"],
        "text-field": [
          "case",
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["!", ["any", ["has", "name2"], ["has", "pgf:name2"]]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["has", "script"],
            [
              "case",
              [
                "any",
                ["is-supported-script", ["get", "name"]],
                ["has", "pgf:name"]
              ],
              [
                "format",
                ["coalesce", ["get", "name:en"], ["get", "name:en"]],
                {},
                "\n",
                {},
                [
                  "case",
                  [
                    "all",
                    ["!", ["has", "name:en"]],
                    ["has", "name:en"],
                    ["!", ["has", "script"]]
                  ],
                  "",
                  ["coalesce", ["get", "pgf:name"], ["get", "name"]]
                ],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["get", "name:en"]
            ],
            [
              "format",
              [
                "coalesce",
                ["get", "name:en"],
                ["get", "pgf:name"],
                ["get", "name"]
              ],
              {}
            ]
          ],
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["any", ["has", "name2"], ["has", "pgf:name2"]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["has", "script2"],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"], ["has", "script3"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script3"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["!", ["has", "script"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["!", ["has", "script2"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name3"],
                  ["get", "name3"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ]
        ],
        "text-size": ["interpolate", ["linear"], ["zoom"], 3, 0, 6, 12, 10, 12],
        "text-letter-spacing": 0.1,
        "text-max-width": 9
      },
      "paint": {
        "text-color": "#717784"
      }
    },
    {
      "id": "roads_labels_major",
      "type": "symbol",
      "source": "protomaps",
      "source-layer": "roads",
      "minzoom": 11,
      "filter": ["in", "kind", "highway", "major_road"],
      "layout": {
        "symbol-sort-key": ["get", "min_zoom"],
        "symbol-placement": "line",
        "text-font": ["Noto Sans Regular"],
        "text-field": [
          "case",
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["!", ["any", ["has", "name2"], ["has", "pgf:name2"]]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["has", "script"],
            [
              "case",
              [
                "any",
                ["is-supported-script", ["get", "name"]],
                ["has", "pgf:name"]
              ],
              [
                "format",
                ["coalesce", ["get", "name:en"], ["get", "name:en"]],
                {},
                "\n",
                {},
                [
                  "case",
                  [
                    "all",
                    ["!", ["has", "name:en"]],
                    ["has", "name:en"],
                    ["!", ["has", "script"]]
                  ],
                  "",
                  ["coalesce", ["get", "pgf:name"], ["get", "name"]]
                ],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["get", "name:en"]
            ],
            [
              "format",
              [
                "coalesce",
                ["get", "name:en"],
                ["get", "pgf:name"],
                ["get", "name"]
              ],
              {}
            ]
          ],
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["any", ["has", "name2"], ["has", "pgf:name2"]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["has", "script2"],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"], ["has", "script3"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script3"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["!", ["has", "script"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["!", ["has", "script2"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name3"],
                  ["get", "name3"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ]
        ],
        "text-size": 12
      },
      "paint": {
        "text-color": "#666666",
        "text-halo-color": "#1f1f1f",
        "text-halo-width": 1,
        "text-halo-blur": 1
      }
    },
    {
      "id": "pois",
      "type": "symbol",
      "source": "protomaps",
      "source-layer": "pois",
      "filter": [
        "all",
        [
          "in",
          ["get", "kind"],
          [
            "literal",
            [
              "beach",
              "forest",
              "marina",
              "park",
              "peak",
              "zoo",
              "garden",
              "bench",
              "aerodrome",
              "station",
              "bus_stop",
              "ferry_terminal",
              "stadium",
              "university",
              "library",
              "school",
              "animal",
              "toilets",
              "drinking_water"
            ]
          ]
        ],
        [">=", ["zoom"], ["+", ["get", "min_zoom"], 0]]
      ],
      "layout": {
        "icon-image": [
          "match",
          ["get", "kind"],
          "station",
          "train_station",
          ["get", "kind"]
        ],
        "text-font": ["Noto Sans Regular"],
        "text-justify": "auto",
        "text-field": [
          "case",
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["!", ["any", ["has", "name2"], ["has", "pgf:name2"]]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["has", "script"],
            [
              "case",
              [
                "any",
                ["is-supported-script", ["get", "name"]],
                ["has", "pgf:name"]
              ],
              [
                "format",
                ["coalesce", ["get", "name:en"], ["get", "name:en"]],
                {},
                "\n",
                {},
                [
                  "case",
                  [
                    "all",
                    ["!", ["has", "name:en"]],
                    ["has", "name:en"],
                    ["!", ["has", "script"]]
                  ],
                  "",
                  ["coalesce", ["get", "pgf:name"], ["get", "name"]]
                ],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["get", "name:en"]
            ],
            [
              "format",
              [
                "coalesce",
                ["get", "name:en"],
                ["get", "pgf:name"],
                ["get", "name"]
              ],
              {}
            ]
          ],
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["any", ["has", "name2"], ["has", "pgf:name2"]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["has", "script2"],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"], ["has", "script3"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script3"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["!", ["has", "script"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["!", ["has", "script2"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name3"],
                  ["get", "name3"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ]
        ],
        "text-size": ["interpolate", ["linear"], ["zoom"], 17, 10, 19, 16],
        "text-max-width": 8,
        "text-offset": [1.1, 0],
        "text-variable-anchor": ["left", "right"]
      },
      "paint": {
        "text-color": [
          "case",
          [
            "in",
            ["get", "kind"],
            [
              "literal",
              [
                "beach",
                "forest",
                "marina",
                "park",
                "peak",
                "zoo",
                "garden",
                "bench"
              ]
            ]
          ],
          "#30C573",
          [
            "in",
            ["get", "kind"],
            ["literal", ["aerodrome", "station", "bus_stop", "ferry_terminal"]]
          ],
          "#2B5CEA",
          [
            "in",
            ["get", "kind"],
            [
              "literal",
              [
                "stadium",
                "university",
                "library",
                "school",
                "animal",
                "toilets",
                "drinking_water"
              ]
            ]
          ],
          "#93939F",
          "#1f1f1f"
        ]
      }
    },
    {
      "id": "places_subplace",
      "type": "symbol",
      "source": "protomaps",
      "source-layer": "places",
      "filter": ["==", "kind", "neighbourhood"],
      "layout": {
        "symbol-sort-key": ["get", "min_zoom"],
        "text-field": [
          "case",
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["!", ["any", ["has", "name2"], ["has", "pgf:name2"]]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["has", "script"],
            [
              "case",
              [
                "any",
                ["is-supported-script", ["get", "name"]],
                ["has", "pgf:name"]
              ],
              [
                "format",
                ["coalesce", ["get", "name:en"], ["get", "name:en"]],
                {},
                "\n",
                {},
                [
                  "case",
                  [
                    "all",
                    ["!", ["has", "name:en"]],
                    ["has", "name:en"],
                    ["!", ["has", "script"]]
                  ],
                  "",
                  ["coalesce", ["get", "pgf:name"], ["get", "name"]]
                ],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["get", "name:en"]
            ],
            [
              "format",
              [
                "coalesce",
                ["get", "name:en"],
                ["get", "pgf:name"],
                ["get", "name"]
              ],
              {}
            ]
          ],
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["any", ["has", "name2"], ["has", "pgf:name2"]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["has", "script2"],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"], ["has", "script3"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script3"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["!", ["has", "script"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["!", ["has", "script2"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name3"],
                  ["get", "name3"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ]
        ],
        "text-font": ["Noto Sans Regular"],
        "text-max-width": 7,
        "text-letter-spacing": 0.1,
        "text-padding": [
          "interpolate",
          ["linear"],
          ["zoom"],
          5,
          2,
          8,
          4,
          12,
          18,
          15,
          20
        ],
        "text-size": [
          "interpolate",
          ["exponential", 1.2],
          ["zoom"],
          11,
          8,
          14,
          14,
          18,
          24
        ],
        "text-transform": "uppercase"
      },
      "paint": {
        "text-color": "#525252",
        "text-halo-color": "#1f1f1f",
        "text-halo-width": 1,
        "text-halo-blur": 1
      }
    },
    {
      "id": "places_locality",
      "type": "symbol",
      "source": "protomaps",
      "source-layer": "places",
      "filter": ["==", "kind", "locality"],
      "layout": {
        "icon-image": ["step", ["zoom"], "townspot", 8, ""],
        "icon-size": 0.7,
        "text-field": [
          "case",
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["!", ["any", ["has", "name2"], ["has", "pgf:name2"]]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["has", "script"],
            [
              "case",
              [
                "any",
                ["is-supported-script", ["get", "name"]],
                ["has", "pgf:name"]
              ],
              [
                "format",
                ["coalesce", ["get", "name:en"], ["get", "name:en"]],
                {},
                "\n",
                {},
                [
                  "case",
                  [
                    "all",
                    ["!", ["has", "name:en"]],
                    ["has", "name:en"],
                    ["!", ["has", "script"]]
                  ],
                  "",
                  ["coalesce", ["get", "pgf:name"], ["get", "name"]]
                ],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["get", "name:en"]
            ],
            [
              "format",
              [
                "coalesce",
                ["get", "name:en"],
                ["get", "pgf:name"],
                ["get", "name"]
              ],
              {}
            ]
          ],
          [
            "all",
            ["any", ["has", "name"], ["has", "pgf:name"]],
            ["any", ["has", "name2"], ["has", "pgf:name2"]],
            ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["has", "script2"],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ],
          [
            "case",
            ["all", ["has", "script"], ["has", "script2"], ["has", "script3"]],
            [
              "format",
              ["get", "name:en"],
              {},
              "\n",
              {},
              ["coalesce", ["get", "pgf:name"], ["get", "name"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script2"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              },
              "\n",
              {},
              ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
              {
                "text-font": [
                  "case",
                  ["==", ["get", "script3"], "Devanagari"],
                  ["literal", ["Noto Sans Devanagari Regular v1"]],
                  ["literal", ["Noto Sans Regular"]]
                ]
              }
            ],
            [
              "case",
              ["!", ["has", "script"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              ["!", ["has", "script2"]],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name2"],
                  ["get", "name2"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name3"],
                  ["get", "name3"]
                ],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ]
            ]
          ]
        ],
        "text-font": [
          "case",
          ["<=", ["get", "min_zoom"], 5],
          ["literal", ["Noto Sans Medium"]],
          ["literal", ["Noto Sans Regular"]]
        ],
        "text-padding": [
          "interpolate",
          ["linear"],
          ["zoom"],
          5,
          3,
          8,
          7,
          12,
          11
        ],
        "text-size": [
          "interpolate",
          ["linear"],
          ["zoom"],
          2,
          [
            "case",
            ["<", ["get", "population_rank"], 13],
            8,
            [">=", ["get", "population_rank"], 13],
            13,
            0
          ],
          4,
          [
            "case",
            ["<", ["get", "population_rank"], 13],
            10,
            [">=", ["get", "population_rank"], 13],
            15,
            0
          ],
          6,
          [
            "case",
            ["<", ["get", "population_rank"], 12],
            11,
            [">=", ["get", "population_rank"], 12],
            17,
            0
          ],
          8,
          [
            "case",
            ["<", ["get", "population_rank"], 11],
            11,
            [">=", ["get", "population_rank"], 11],
            18,
            0
          ],
          10,
          [
            "case",
            ["<", ["get", "population_rank"], 9],
            12,
            [">=", ["get", "population_rank"], 9],
            20,
            0
          ],
          15,
          [
            "case",
            ["<", ["get", "population_rank"], 8],
            12,
            [">=", ["get", "population_rank"], 8],
            22,
            0
          ]
        ],
        "icon-padding": [
          "interpolate",
          ["linear"],
          ["zoom"],
          0,
          0,
          8,
          4,
          10,
          8,
          12,
          6,
          22,
          2
        ],
        "text-justify": "auto",
        "text-anchor": ["step", ["zoom"], "left", 8, "center"],
        "text-radial-offset": 0.4
      },
      "paint": {
        "text-color": "#7a7a7a",
        "text-halo-color": "#212121",
        "text-halo-width": 1,
        "text-halo-blur": 1
      }
    },
    {
      "id": "places_region",
      "type": "symbol",
      "source": "protomaps",
      "source-layer": "places",
      "filter": ["==", "kind", "region"],
      "layout": {
        "symbol-sort-key": ["get", "min_zoom"],
        "text-field": [
          "step",
          ["zoom"],
          ["get", "name:short"],
          6,
          [
            "case",
            [
              "all",
              ["any", ["has", "name"], ["has", "pgf:name"]],
              ["!", ["any", ["has", "name2"], ["has", "pgf:name2"]]],
              ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
            ],
            [
              "case",
              ["has", "script"],
              [
                "case",
                [
                  "any",
                  ["is-supported-script", ["get", "name"]],
                  ["has", "pgf:name"]
                ],
                [
                  "format",
                  ["coalesce", ["get", "name:en"], ["get", "name:en"]],
                  {},
                  "\n",
                  {},
                  [
                    "case",
                    [
                      "all",
                      ["!", ["has", "name:en"]],
                      ["has", "name:en"],
                      ["!", ["has", "script"]]
                    ],
                    "",
                    ["coalesce", ["get", "pgf:name"], ["get", "name"]]
                  ],
                  {
                    "text-font": [
                      "case",
                      ["==", ["get", "script"], "Devanagari"],
                      ["literal", ["Noto Sans Devanagari Regular v1"]],
                      ["literal", ["Noto Sans Regular"]]
                    ]
                  }
                ],
                ["get", "name:en"]
              ],
              [
                "format",
                [
                  "coalesce",
                  ["get", "name:en"],
                  ["get", "pgf:name"],
                  ["get", "name"]
                ],
                {}
              ]
            ],
            [
              "all",
              ["any", ["has", "name"], ["has", "pgf:name"]],
              ["any", ["has", "name2"], ["has", "pgf:name2"]],
              ["!", ["any", ["has", "name3"], ["has", "pgf:name3"]]]
            ],
            [
              "case",
              ["all", ["has", "script"], ["has", "script2"]],
              [
                "format",
                ["get", "name:en"],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "case",
                ["has", "script2"],
                [
                  "format",
                  [
                    "coalesce",
                    ["get", "name:en"],
                    ["get", "pgf:name"],
                    ["get", "name"]
                  ],
                  {},
                  "\n",
                  {},
                  ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                  {
                    "text-font": [
                      "case",
                      ["==", ["get", "script2"], "Devanagari"],
                      ["literal", ["Noto Sans Devanagari Regular v1"]],
                      ["literal", ["Noto Sans Regular"]]
                    ]
                  }
                ],
                [
                  "format",
                  [
                    "coalesce",
                    ["get", "name:en"],
                    ["get", "pgf:name2"],
                    ["get", "name2"]
                  ],
                  {},
                  "\n",
                  {},
                  ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                  {
                    "text-font": [
                      "case",
                      ["==", ["get", "script"], "Devanagari"],
                      ["literal", ["Noto Sans Devanagari Regular v1"]],
                      ["literal", ["Noto Sans Regular"]]
                    ]
                  }
                ]
              ]
            ],
            [
              "case",
              [
                "all",
                ["has", "script"],
                ["has", "script2"],
                ["has", "script3"]
              ],
              [
                "format",
                ["get", "name:en"],
                {},
                "\n",
                {},
                ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script2"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                },
                "\n",
                {},
                ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                {
                  "text-font": [
                    "case",
                    ["==", ["get", "script3"], "Devanagari"],
                    ["literal", ["Noto Sans Devanagari Regular v1"]],
                    ["literal", ["Noto Sans Regular"]]
                  ]
                }
              ],
              [
                "case",
                ["!", ["has", "script"]],
                [
                  "format",
                  [
                    "coalesce",
                    ["get", "name:en"],
                    ["get", "pgf:name"],
                    ["get", "name"]
                  ],
                  {},
                  "\n",
                  {},
                  ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                  {
                    "text-font": [
                      "case",
                      ["==", ["get", "script2"], "Devanagari"],
                      ["literal", ["Noto Sans Devanagari Regular v1"]],
                      ["literal", ["Noto Sans Regular"]]
                    ]
                  },
                  "\n",
                  {},
                  ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                  {
                    "text-font": [
                      "case",
                      ["==", ["get", "script3"], "Devanagari"],
                      ["literal", ["Noto Sans Devanagari Regular v1"]],
                      ["literal", ["Noto Sans Regular"]]
                    ]
                  }
                ],
                ["!", ["has", "script2"]],
                [
                  "format",
                  [
                    "coalesce",
                    ["get", "name:en"],
                    ["get", "pgf:name2"],
                    ["get", "name2"]
                  ],
                  {},
                  "\n",
                  {},
                  ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                  {
                    "text-font": [
                      "case",
                      ["==", ["get", "script"], "Devanagari"],
                      ["literal", ["Noto Sans Devanagari Regular v1"]],
                      ["literal", ["Noto Sans Regular"]]
                    ]
                  },
                  "\n",
                  {},
                  ["coalesce", ["get", "pgf:name3"], ["get", "name3"]],
                  {
                    "text-font": [
                      "case",
                      ["==", ["get", "script3"], "Devanagari"],
                      ["literal", ["Noto Sans Devanagari Regular v1"]],
                      ["literal", ["Noto Sans Regular"]]
                    ]
                  }
                ],
                [
                  "format",
                  [
                    "coalesce",
                    ["get", "name:en"],
                    ["get", "pgf:name3"],
                    ["get", "name3"]
                  ],
                  {},
                  "\n",
                  {},
                  ["coalesce", ["get", "pgf:name"], ["get", "name"]],
                  {
                    "text-font": [
                      "case",
                      ["==", ["get", "script"], "Devanagari"],
                      ["literal", ["Noto Sans Devanagari Regular v1"]],
                      ["literal", ["Noto Sans Regular"]]
                    ]
                  },
                  "\n",
                  {},
                  ["coalesce", ["get", "pgf:name2"], ["get", "name2"]],
                  {
                    "text-font": [
                      "case",
                      ["==", ["get", "script2"], "Devanagari"],
                      ["literal", ["Noto Sans Devanagari Regular v1"]],
                      ["literal", ["Noto Sans Regular"]]
                    ]
                  }
                ]
              ]
            ]
          ]
        ],
        "text-font": ["Noto Sans Regular"],
        "text-size": ["interpolate", ["linear"], ["zoom"], 3, 11, 7, 16],
        "text-radial-offset": 0.2,
        "text-anchor": "center",
        "text-transform": "uppercase"
      },
      "paint": {
        "text-color": "#3d3d3d",
        "text-halo-color": "#1f1f1f",
        "text-halo-width": 1,
        "text-halo-blur": 1
      }
    },
    {
      "id": "places_country",
      "type": "symbol",
      "source": "protomaps",
      "source-layer": "places",
      "filter": ["==", "kind", "country"],
      "layout": {
        "symbol-sort-key": ["get", "min_zoom"],
        "text-field": [
          "format",
          ["coalesce", ["get", "name:en"], ["get", "name:en"]],
          {}
        ],
        "text-font": ["Noto Sans Medium"],
        "text-size": [
          "interpolate",
          ["linear"],
          ["zoom"],
          2,
          [
            "case",
            ["<", ["get", "population_rank"], 10],
            8,
            [">=", ["get", "population_rank"], 10],
            12,
            0
          ],
          6,
          [
            "case",
            ["<", ["get", "population_rank"], 8],
            10,
            [">=", ["get", "population_rank"], 8],
            18,
            0
          ],
          8,
          [
            "case",
            ["<", ["get", "population_rank"], 7],
            11,
            [">=", ["get", "population_rank"], 7],
            20,
            0
          ]
        ],
        "icon-padding": [
          "interpolate",
          ["linear"],
          ["zoom"],
          0,
          2,
          14,
          2,
          16,
          20,
          17,
          2,
          22,
          2
        ],
        "text-transform": "uppercase"
      },
      "paint": {
        "text-color": "#5c5c5c"
      }
    }
  ],
  "sprite": "https://protomaps.github.io/basemaps-assets/sprites/v4/dark",
  "glyphs": "https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf"
}}