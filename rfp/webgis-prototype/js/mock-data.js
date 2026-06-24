/**
 * DoSLR WebGIS - realistic synthetic cadastral data generator.
 * Fallback dataset when open, editable parcel vectors are unavailable.
 */
(function (global) {
  "use strict";

  function createRng(seedText) {
    var seed = 0;
    for (var i = 0; i < seedText.length; i++) {
      seed = (seed * 31 + seedText.charCodeAt(i)) >>> 0;
    }
    if (seed === 0) seed = 123456789;
    return function () {
      seed = (1664525 * seed + 1013904223) >>> 0;
      return seed / 4294967296;
    };
  }

  function metersToLatDeg(meters) {
    return meters / 111320;
  }

  function metersToLonDeg(meters, latitude) {
    var scale = Math.cos((latitude * Math.PI) / 180);
    var safeScale = Math.max(0.2, Math.abs(scale));
    return meters / (111320 * safeScale);
  }

  function makeRectPolygon(center, halfWidthM, halfHeightM) {
    var lon = center[0];
    var lat = center[1];
    var dx = metersToLonDeg(halfWidthM, lat);
    var dy = metersToLatDeg(halfHeightM);
    return [
      [lon - dx, lat - dy],
      [lon + dx, lat - dy],
      [lon + dx, lat + dy],
      [lon - dx, lat + dy],
      [lon - dx, lat - dy],
    ];
  }

  function toFeature(coords, props) {
    return {
      type: "Feature",
      properties: props || {},
      geometry: { type: "Polygon", coordinates: [coords] },
    };
  }

  function toLine(coords, props) {
    return {
      type: "Feature",
      properties: props || {},
      geometry: { type: "LineString", coordinates: coords },
    };
  }

  function toPoint(coord, props) {
    return {
      type: "Feature",
      properties: props || {},
      geometry: { type: "Point", coordinates: coord },
    };
  }

  function bboxFromParcels(parcelFeatures) {
    var minX = Infinity;
    var minY = Infinity;
    var maxX = -Infinity;
    var maxY = -Infinity;
    parcelFeatures.forEach(function (f) {
      var ring = f.geometry.coordinates[0];
      ring.forEach(function (c) {
        if (c[0] < minX) minX = c[0];
        if (c[1] < minY) minY = c[1];
        if (c[0] > maxX) maxX = c[0];
        if (c[1] > maxY) maxY = c[1];
      });
    });
    return [minX, minY, maxX, maxY];
  }

  function bboxPolygon(minX, minY, maxX, maxY) {
    return [
      [minX, minY],
      [maxX, minY],
      [maxX, maxY],
      [minX, maxY],
      [minX, minY],
    ];
  }

  function pickByIndex(list, index) {
    if (!list.length) return "";
    return list[index % list.length];
  }


  function partitionWeights(total, parts, rng, minFrac) {
    if (parts <= 0) return [0, total];
    var weights = [];
    var sum = 0;
    for (var i = 0; i < parts; i++) {
      var w = minFrac + rng() * (1 - minFrac);
      weights.push(w);
      sum += w;
    }
    var positions = [0];
    var acc = 0;
    for (var j = 0; j < parts; j++) {
      acc += (weights[j] / sum) * total;
      positions.push(acc);
    }
    positions[positions.length - 1] = total;
    return positions;
  }

  function jitteredPartitions(baseOffsets, rng, jitterMax, minGap) {
    var out = baseOffsets.slice();
    for (var i = 1; i < out.length - 1; i++) {
      out[i] += (rng() - 0.5) * jitterMax;
    }
    for (var k = 1; k < out.length; k++) {
      if (out[k] <= out[k - 1] + minGap) out[k] = out[k - 1] + minGap;
    }
    out[0] = baseOffsets[0];
    out[out.length - 1] = baseOffsets[baseOffsets.length - 1];
    return out;
  }

  function localRingToGeo(ringLocal, cfg) {
    return ringLocal.map(function (p) {
      return [
        cfg.center[0] + metersToLonDeg(p[0], cfg.center[1]),
        cfg.center[1] + metersToLatDeg(p[1]),
      ];
    });
  }

  function quadAreaSqM(sw, se, ne, nw) {
    var ring = [sw, se, ne, nw, sw];
    var area = 0;
    for (var i = 0; i < 4; i++) {
      area += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1];
    }
    return Math.abs(area) / 2;
  }

  function makeSurveyNo(blockNo, parcelInBlock, rng) {
    var main = blockNo * 23 + parcelInBlock;
    if (rng() > 0.68) {
      return String(main) + "/" + String(1 + (parcelInBlock % 5));
    }
    if (rng() > 0.9) {
      return String(main) + "/" + String(1 + (parcelInBlock % 3)) + String.fromCharCode(65 + (parcelInBlock % 3));
    }
    return String(main);
  }

  function generateCadastralParcels(cfg, rng, owners) {
    var layout = cfg.layout || {
      widthM: 3600,
      heightM: 3000,
      blocksX: 3,
      blocksY: 2,
      roadM: 14,
    };
    var totalW = layout.widthM;
    var totalH = layout.heightM;
    var road = layout.roadM;
    var blocksX = layout.blocksX;
    var blocksY = layout.blocksY;
    var blockCellW = (totalW - road * (blocksX - 1)) / blocksX;
    var blockCellH = (totalH - road * (blocksY - 1)) / blocksY;
    var originWest = -totalW / 2;
    var originSouth = -totalH / 2;

    var parcelFeatures = [];
    var parcelAttrs = {};
    var parcelIndex = 1;

    for (var by = 0; by < blocksY; by++) {
      for (var bx = 0; bx < blocksX; bx++) {
        var blockWest = originWest + bx * (blockCellW + road);
        var blockSouth = originSouth + by * (blockCellH + road);
        var blockNo = by * blocksX + bx + 1;
        var rows = 4 + Math.floor(rng() * 8);
        var yOffsets = partitionWeights(blockCellH, rows, rng, 0.03);
        var yLines = yOffsets.map(function (v) { return blockSouth + v; });
        var parcelInBlock = 0;

        for (var row = 0; row < rows; row++) {
          var colsThisRow = 5 + Math.floor(rng() * 9);
          var xBottom = jitteredPartitions(
            partitionWeights(blockCellW, colsThisRow, rng, 0.025).map(function (v) { return blockWest + v; }),
            rng,
            blockCellW * 0.022,
            2.5
          );
          var xTop = jitteredPartitions(
            partitionWeights(blockCellW, colsThisRow, rng, 0.025).map(function (v) { return blockWest + v; }),
            rng,
            blockCellW * 0.028,
            2.5
          );
          var y0 = yLines[row];
          var y1 = yLines[row + 1];

          for (var col = 0; col < colsThisRow; col++) {
            if (rng() < 0.02) continue;

            var sw = [xBottom[col], y0];
            var se = [xBottom[col + 1], y0];
            var ne = [xTop[col + 1], y1];
            var nw = [xTop[col], y1];
            var areaSqM = Math.round(quadAreaSqM(sw, se, ne, nw));
            if (areaSqM < 20) continue;

            parcelInBlock++;
            var ring = localRingToGeo([sw, se, ne, nw, sw], cfg);
            var surveyNo = makeSurveyNo(blockNo, parcelInBlock, rng);
            var subDiv = surveyNo.indexOf("/") > -1 ? surveyNo.split("/")[1] : String((col % 4) + 1);
            var id = cfg.code + "-P-" + String(parcelIndex).padStart(3, "0");
            var ulpin = cfg.ulpinPrefix + String(parcelIndex).padStart(10, "0");
            var village = pickByIndex(cfg.villages, parcelIndex - 1);
            var taluk = pickByIndex(cfg.taluks, parcelIndex - 1);
            var ward = "Ward " + String(((parcelIndex - 1) % 12) + 1);
            var owner = pickByIndex(owners, parcelIndex - 1);
            var ownerMasked = owner.charAt(0) + "********";
            var statusRoll = rng();
            var status = statusRoll < 0.82 ? "active" : (statusRoll < 0.92 ? "mutation_pending" : "disputed");
            var variancePct = Number((rng() * 4.8).toFixed(2));
            var varianceBand = variancePct > 3.6 ? "red" : (variancePct > 2.2 ? "amber" : "green");

            var props = {
              id: id,
              surveyNo: surveyNo,
              subDiv: subDiv,
              ulpin: ulpin,
              village: village,
              taluk: taluk,
              ward: ward,
              region: cfg.label,
              areaSqM: areaSqM,
              owner: owner,
              ownerMasked: ownerMasked,
              status: status,
              classification: rng() > 0.58 ? "Punjai" : "Nanjai",
              landUse: rng() > 0.52 ? "Residential" : "Agriculture",
              encumbrance: rng() > 0.86 ? "Bank lien (sample)" : "None",
              fmbSheet: cfg.code + "-FMB-" + String(blockNo).padStart(2, "0"),
              blockNo: blockNo,
              varianceBand: varianceBand,
              variancePct: variancePct,
            };

            parcelFeatures.push(toFeature(ring, props));
            parcelAttrs[id] = props;
            parcelIndex++;
          }
        }
      }
    }

    return { parcelFeatures: parcelFeatures, parcelAttrs: parcelAttrs };
  }

  function buildRegionDataset(cfg) {
    var rng = createRng(cfg.key + "-cadastral");
    var owners = [
      "S. Ravi",
      "M. Lakshmi",
      "P. Kannan",
      "R. Salma",
      "A. Joseph",
      "K. Nirmala",
      "T. Rahim",
      "V. Anandhi",
      "D. Prakash",
      "G. Mariam",
      "N. Suresh",
      "F. Ashok",
    ];

    var parcelFeatures = [];
    var parcelAttrs = {};
    if (typeof CADASTRAL_OSM !== "undefined" && CADASTRAL_OSM[cfg.key] && CADASTRAL_OSM[cfg.key].features && CADASTRAL_OSM[cfg.key].features.length) {
      parcelFeatures = CADASTRAL_OSM[cfg.key].features.slice();
      parcelAttrs = Object.assign({}, CADASTRAL_OSM[cfg.key].attrs || {});
    } else {
      var generated = generateCadastralParcels(cfg, rng, owners);
      parcelFeatures = generated.parcelFeatures;
      parcelAttrs = generated.parcelAttrs;
    }

    var bounds = bboxFromParcels(parcelFeatures);
    var minX = bounds[0];
    var minY = bounds[1];
    var maxX = bounds[2];
    var maxY = bounds[3];
    var midX = (minX + maxX) / 2;
    var midY = (minY + maxY) / 2;
    var width = maxX - minX;
    var height = maxY - minY;

    var regionFeature = toFeature(
      bboxPolygon(minX - width * 0.04, minY - height * 0.04, maxX + width * 0.04, maxY + height * 0.04),
      { name: cfg.label + " Region", level: "region" }
    );

    var talukFeatures = cfg.taluks.map(function (name, idx) {
      var tMinX = idx % 2 === 0 ? minX : midX;
      var tMaxX = idx % 2 === 0 ? midX : maxX;
      return toFeature(
        bboxPolygon(tMinX, minY, tMaxX, maxY),
        { name: name, level: "taluk" }
      );
    });

    var villageFeatures = cfg.villages.map(function (name, idx) {
      var vBand = idx / cfg.villages.length;
      var vMinY = minY + height * vBand;
      var vMaxY = minY + height * ((idx + 1) / cfg.villages.length);
      return toFeature(
        bboxPolygon(minX, vMinY, maxX, vMaxY),
        { name: name, level: "village" }
      );
    });

    var wardFeatures = [
      toFeature(bboxPolygon(minX, minY, midX, midY), { name: "Ward 1", level: "ward" }),
      toFeature(bboxPolygon(midX, minY, maxX, midY), { name: "Ward 2", level: "ward" }),
      toFeature(bboxPolygon(minX, midY, midX, maxY), { name: "Ward 3", level: "ward" }),
      toFeature(bboxPolygon(midX, midY, maxX, maxY), { name: "Ward 4", level: "ward" }),
    ];

    var fmbFeatures = [];
    for (var fm = 0; fm < 4; fm++) {
      var sx = minX + (width * fm) / 4;
      var ex = minX + (width * (fm + 1)) / 4;
      fmbFeatures.push(
        toFeature(
          bboxPolygon(sx, minY, ex, maxY),
          { sheet: cfg.code + "-FMB-" + String(fm + 1).padStart(2, "0"), village: pickByIndex(cfg.villages, fm) }
        )
      );
    }

    var varianceFeatures = parcelFeatures.slice(0, 80).map(function (f) {
      return {
        type: "Feature",
        properties: {
          band: f.properties.varianceBand,
          pct: f.properties.variancePct,
          parcelId: f.properties.id,
        },
        geometry: JSON.parse(JSON.stringify(f.geometry)),
      };
    });

    var dgpsFeatures = [];
    for (var g = 0; g < 6; g++) {
      var gx = minX + (width * (g + 1)) / 7;
      var gy = minY + (height * (((g % 3) + 1) / 4));
      dgpsFeatures.push(
        toPoint([gx, gy], {
          id: cfg.code + "-GCP-" + String(g + 1).padStart(2, "0"),
          source: g % 2 === 0 ? "DGPS" : "GNSS RTK",
          rmse: Number((0.05 + g * 0.03).toFixed(2)),
        })
      );
    }

    var collabLine = toLine(
      [
        [minX, minY],
        [midX, midY],
        [maxX, maxY],
      ],
      { ref: "CollabLand " + cfg.label + " sample baseline" }
    );

    var orthoFeature = toFeature(
      bboxPolygon(minX - width * 0.02, minY - height * 0.02, maxX + width * 0.02, maxY + height * 0.02),
      { name: cfg.label + " Ortho Reference 2026" }
    );

    return {
      center: cfg.center,
      zoom: cfg.zoom,
      parcelAttrs: parcelAttrs,
      parcels: Object.keys(parcelAttrs).map(function (k) { return parcelAttrs[k]; }),
      geojson: {
        region: { type: "FeatureCollection", features: [regionFeature] },
        taluk: { type: "FeatureCollection", features: talukFeatures },
        village: { type: "FeatureCollection", features: villageFeatures },
        ward: { type: "FeatureCollection", features: wardFeatures },
        fmb: { type: "FeatureCollection", features: fmbFeatures },
        parcels: { type: "FeatureCollection", features: parcelFeatures },
        variance: { type: "FeatureCollection", features: varianceFeatures },
        dgps: { type: "FeatureCollection", features: dgpsFeatures },
        collabland: { type: "FeatureCollection", features: [collabLine] },
        ortho: { type: "FeatureCollection", features: [orthoFeature] },
      },
    };
  }

  var REGION_CONFIGS = [
    {
      key: "puducherry",
      code: "PY",
      label: "Puducherry",
      center: [79.8083, 11.9375],
      zoom: 15,
      ulpinPrefix: "3411",
      taluks: ["Oulgaret", "Villianur"],
      villages: ["Kurumbapet", "Muthialpet", "Ariyankuppam", "Lawspet", "Reddiarpalayam"],
      layout: { widthM: 4200, heightM: 3600, blocksX: 3, blocksY: 2, roadM: 16 },
    },
    {
      key: "karaikal",
      code: "KR",
      label: "Karaikal",
      center: [79.8372, 10.9254],
      zoom: 15,
      ulpinPrefix: "3412",
      taluks: ["Karaikal", "Thirunallar"],
      villages: ["Nedungadu", "Kottucherry", "Tirumalairayanpattinam", "Neravy", "Varichikudy"],
      layout: { widthM: 4000, heightM: 3800, blocksX: 3, blocksY: 2, roadM: 14 },
    },
    {
      key: "mahe",
      code: "MH",
      label: "Mahe",
      center: [75.5503, 11.7012],
      zoom: 16,
      ulpinPrefix: "3413",
      taluks: ["Mahe", "Palloor"],
      villages: ["Mahe Town", "Chalakkara", "Palloor", "Pandakkal"],
      layout: { widthM: 2600, heightM: 2300, blocksX: 2, blocksY: 2, roadM: 12 },
    },
    {
      key: "yanam",
      code: "YN",
      label: "Yanam",
      center: [82.2155, 16.7351],
      zoom: 16,
      ulpinPrefix: "3414",
      taluks: ["Yanam", "Kanakalapeta"],
      villages: ["Mettakur", "Kanakalapeta", "Adavipolam", "Jambavanpet"],
      layout: { widthM: 3000, heightM: 2600, blocksX: 2, blocksY: 3, roadM: 12 },
    },
  ];

  var DATASETS = {};
  REGION_CONFIGS.forEach(function (cfg) {
    DATASETS[cfg.key] = buildRegionDataset(cfg);
  });

  function makeDynamicMetadata(regionLabel, parcels) {
    var first = parcels[0] || null;
    var second = parcels[1] || first;
    var third = parcels[2] || second;
    var nowUlpin = first ? first.ulpin : "00000000000000";
    return {
      mutations: [
        {
          id: "MUT-" + regionLabel.slice(0, 2).toUpperCase() + "-2026-0041",
          type: "subdivision",
          status: "submitted",
          village: first ? first.village : "-",
          parentSurvey: first ? first.surveyNo : "-",
          origin: "Online portal",
          submittedBy: "clerk." + regionLabel.toLowerCase().slice(0, 2) + "-01",
        },
      ],
      anomalies: [
        {
          id: "AN-" + regionLabel.slice(0, 2).toUpperCase() + "-018",
          parcel: second ? second.surveyNo : "-",
          village: second ? second.village : "-",
          type: "area_variance",
          band: second ? second.varianceBand : "green",
          variancePct: second ? second.variancePct : 0,
          status: "open",
        },
      ],
      georefJob: {
        id: "GRF-" + regionLabel.slice(0, 2).toUpperCase() + "-2026-0008",
        village: third ? third.village : "-",
        fmbSheet: third ? third.fmbSheet : "-",
        transform: "thin_plate_spline",
        rmse: 0.23,
        gcpCount: 6,
      },
      ulpinEvents: [
        { date: "2025-09-21", event: "issued", ulpin: nowUlpin, note: "Initial assignment" },
        { date: "2026-01-11", event: "verified", ulpin: nowUlpin, note: "Field verification complete" },
      ],
    };
  }

  var layerGroups = [
    {
      id: "basemap",
      label: "Basemap",
      layers: [
        { id: "basemap-osm", label: "OpenStreetMap", type: "basemap", default: true },
        { id: "basemap-imagery", label: "Esri World Imagery", type: "basemap" },
        { id: "basemap-carto", label: "Carto Positron", type: "basemap" },
      ],
    },
    {
      id: "imagery",
      label: "Imagery",
      layers: [{ id: "ortho", label: "Ortho Reference", opacity: 0.55, visible: true }],
    },
    {
      id: "cadastral",
      label: "Cadastral",
      layers: [
        { id: "parcels", label: "Parcel Boundaries", opacity: 0.9, visible: true },
        { id: "fmb", label: "FMB Sheet Outlines", opacity: 0.75, visible: true },
      ],
    },
    {
      id: "admin",
      label: "Administrative",
      layers: [
        { id: "region", label: "Region", opacity: 0.35, visible: true },
        { id: "taluk", label: "Taluk", opacity: 0.4, visible: true },
        { id: "village", label: "Village", opacity: 0.5, visible: true },
        { id: "ward", label: "Ward", opacity: 0.55, visible: true },
        { id: "admin-labels", label: "Boundary Labels", opacity: 1, visible: true },
      ],
    },
    {
      id: "field",
      label: "Field & Analytics",
      layers: [
        { id: "variance", label: "Variance Bands", opacity: 0.45, visible: true },
        { id: "dgps", label: "DGPS / GNSS Points", opacity: 1, visible: true },
        { id: "collabland", label: "CollabLand Reference", opacity: 0.8, visible: true },
      ],
    },
  ];

  var currentRegionKey = "puducherry";

  var MOCK_DATA = {
    center: DATASETS[currentRegionKey].center,
    zoom: DATASETS[currentRegionKey].zoom,
    geojson: DATASETS[currentRegionKey].geojson,
    parcelAttrs: DATASETS[currentRegionKey].parcelAttrs,
    parcels: DATASETS[currentRegionKey].parcels,
    layerGroups: layerGroups,
    rbacRoles: [
      { id: "public", label: "Public Citizen", search: "Survey/ULPIN", owner: "Redacted", edit: "No" },
      { id: "citizen", label: "Registered Citizen", search: "Survey/ULPIN", owner: "Self only", edit: "No" },
      { id: "field", label: "Field Officer", search: "Full", owner: "Full", edit: "Verify" },
      { id: "clerk", label: "Revenue Clerk", search: "Full", owner: "Full", edit: "Draft mutation" },
      { id: "officer", label: "DoSLR Officer", search: "Full + owner", owner: "Full", edit: "Approve" },
      { id: "surveyor", label: "Surveyor", search: "Full", owner: "Full", edit: "Geometry" },
      { id: "agri", label: "AgriStack Liaison", search: "DCS scope", owner: "Tokenized", edit: "No" },
      { id: "auditor", label: "Auditor", search: "Read-only", owner: "Masked", edit: "No" },
      { id: "admin", label: "Administrator", search: "Full", owner: "Full", edit: "All" },
    ],
    controlPoints: DATASETS[currentRegionKey].geojson.dgps.features.map(function (f) {
      return {
        id: f.properties.id,
        source: f.properties.source,
        status: "accepted",
        rmse: f.properties.rmse,
        lat: f.geometry.coordinates[1],
        lng: f.geometry.coordinates[0],
      };
    }),
    setRegion: function (regionKey) {
      if (!DATASETS[regionKey]) return false;
      currentRegionKey = regionKey;
      var dataset = DATASETS[regionKey];
      this.center = dataset.center;
      this.zoom = dataset.zoom;
      this.geojson = dataset.geojson;
      this.parcelAttrs = dataset.parcelAttrs;
      this.parcels = dataset.parcels;
      this.controlPoints = dataset.geojson.dgps.features.map(function (f) {
        return {
          id: f.properties.id,
          source: f.properties.source,
          status: "accepted",
          rmse: f.properties.rmse,
          lat: f.geometry.coordinates[1],
          lng: f.geometry.coordinates[0],
        };
      });
      var dynamic = makeDynamicMetadata(this.getCurrentRegion().label, this.parcels);
      this.mutations = dynamic.mutations;
      this.anomalies = dynamic.anomalies;
      this.georefJob = dynamic.georefJob;
      this.ulpinEvents = dynamic.ulpinEvents;
      return true;
    },
    getCurrentRegionKey: function () {
      return currentRegionKey;
    },
    getCurrentRegion: function () {
      return REGION_CONFIGS.find(function (r) { return r.key === currentRegionKey; }) || REGION_CONFIGS[0];
    },
    getRegions: function () {
      return REGION_CONFIGS.map(function (r) {
        return {
          key: r.key,
          code: r.code,
          label: r.label,
          center: r.center,
          zoom: r.zoom,
        };
      });
    },
    getParcelById: function (id) {
      return this.parcelAttrs[id] || null;
    },
    searchParcels: function (query, role) {
      var q = String(query || "").trim().toLowerCase();
      var list = this.parcels.slice();
      if (!q) return { results: list };
      var canOwner = ["officer", "admin", "surveyor", "clerk"].indexOf(role) >= 0;
      if (!canOwner && q.indexOf("owner:") === 0) {
        return { blocked: true, reason: "Owner-name search requires officer tier (RFP 18.3.2)." };
      }
      return {
        results: list.filter(function (p) {
          return p.surveyNo.toLowerCase().indexOf(q) >= 0 ||
            p.ulpin.toLowerCase().indexOf(q) >= 0 ||
            p.village.toLowerCase().indexOf(q) >= 0 ||
            p.taluk.toLowerCase().indexOf(q) >= 0 ||
            (canOwner && p.owner.toLowerCase().indexOf(q) >= 0);
        }),
      };
    },
  };

  MOCK_DATA.setRegion(currentRegionKey);
  global.MOCK_DATA = MOCK_DATA;
})(window);
