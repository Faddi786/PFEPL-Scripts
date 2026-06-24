/**
 * DoSLR WebGIS - application UI wiring.
 */
(function () {
  "use strict";

  var state = {
    role: "officer",
    selectedParcel: null,
    auditLog: [],
  };

  var EYE_ICON =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>';

  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function pushAudit(action, detail) {
    state.auditLog.push({ time: new Date().toISOString(), action: action, detail: detail || "" });
    if (state.auditLog.length > 500) state.auditLog.shift();
  }

  function showToast(msg) {
    var t = qs("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(function () { t.classList.remove("show"); }, 2200);
  }

  function setHud(text) {
    qs("#measure-hud").textContent = text;
  }

  function openModal(title, html, actions) {
    qs("#panel-title").textContent = title;
    qs("#panel-body").innerHTML = html;
    var foot = qs("#panel-foot");
    foot.innerHTML = "";
    (actions || []).forEach(function (a) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn" + (a.primary ? " btn-primary" : "");
      btn.textContent = a.label;
      btn.addEventListener("click", function () { a.onClick && a.onClick(); });
      foot.appendChild(btn);
    });
    if (!actions || !actions.length) {
      var closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.className = "btn";
      closeBtn.textContent = "Close";
      closeBtn.addEventListener("click", function () { closeModal("panel-modal"); });
      foot.appendChild(closeBtn);
    }
    qs("#panel-modal").classList.add("open");
  }

  function closeModal(id) {
    qs("#" + id).classList.remove("open");
  }

  function findLayerCfg(id) {
    for (var i = 0; i < MOCK_DATA.layerGroups.length; i++) {
      for (var j = 0; j < MOCK_DATA.layerGroups[i].layers.length; j++) {
        if (MOCK_DATA.layerGroups[i].layers[j].id === id) return MOCK_DATA.layerGroups[i].layers[j];
      }
    }
    return null;
  }

  function renderLayerPanel() {
    var host = qs("#layer-panel-body");
    host.innerHTML = MOCK_DATA.layerGroups.map(function (group) {
      var rows = group.layers.map(function (layer) {
        var isBase = layer.type === "basemap";
        var isVisible = isBase ? MapEngine.getActiveBasemap() === layer.id : MapEngine.getLayerVisible(layer.id);
        return '<div class="layer-row" data-layer="' + layer.id + '" data-basemap="' + (isBase ? "1" : "0") + '">' +
          '<button class="eye-btn' + (isVisible ? "" : " off") + '" type="button" aria-label="Toggle layer visibility" title="' + (isVisible ? "Hide layer" : "Show layer") + '">' + EYE_ICON + '</button>' +
          '<div class="layer-name">' + layer.label + '</div>' +
          '</div>';
      }).join("");
      return '<div class="layer-group"><div class="group-head"><span>' + group.label + '</span><span>v</span></div><div class="group-layers">' + rows + "</div></div>";
    }).join("");

    qsa(".group-head", host).forEach(function (head) {
      head.addEventListener("click", function () {
        qs(".group-layers", head.parentElement).classList.toggle("collapsed");
      });
    });

    qsa(".eye-btn", host).forEach(function (btn) {
      btn.addEventListener("click", function (evt) {
        evt.stopPropagation();
        var row = btn.closest(".layer-row");
        if (!row) return;
        var layerId = row.getAttribute("data-layer");
        var isBase = row.getAttribute("data-basemap") === "1";
        if (isBase) {
          MapEngine.setBasemap(layerId);
          pushAudit("basemap", layerId);
        } else {
          var next = !MapEngine.getLayerVisible(layerId);
          MapEngine.setLayerVisible(layerId, next);
          var cfg = findLayerCfg(layerId);
          if (cfg) cfg.visible = next;
          pushAudit("layer-toggle", layerId + ":" + next);
        }
        renderLayerPanel();
      });
    });
  }

  function attrRows(parcel) {
    if (!parcel) return '<div style="color:#666">No parcel selected</div>';
    var pairs = [
      ["Survey", parcel.surveyNo],
      ["ULPIN", parcel.ulpin],
      ["Village", parcel.village],
      ["Taluk", parcel.taluk],
      ["Area", Number(parcel.areaSqM || 0).toLocaleString() + " m2"],
      ["Owner", state.role === "public" || state.role === "citizen" || state.role === "auditor" ? parcel.ownerMasked : parcel.owner],
      ["Status", parcel.status],
    ];
    return '<table class="ctx-table">' + pairs.map(function (r) { return "<tr><td>" + r[0] + "</td><td>" + (r[1] || "-") + "</td></tr>"; }).join("") + "</table>";
  }

  function hideContextMenu() {
    var menu = qs("#ctx-menu");
    menu.hidden = true;
    menu.innerHTML = "";
  }

  function showContextMenu(evtInfo) {
    hideContextMenu();
    if (!evtInfo || !evtInfo.parcel) return;

    var parcel = evtInfo.parcel;
    var menu = qs("#ctx-menu");
    menu.style.left = evtInfo.clientX + "px";
    menu.style.top = evtInfo.clientY + "px";
    menu.innerHTML =
      '<div class="ctx-head">Parcel ' + (parcel.surveyNo || parcel.id) + '</div>' +
      '<div class="ctx-body">' + attrRows(parcel) +
      '<div class="ctx-actions">' +
      '<button data-ctx="zoom">Zoom</button>' +
      '<button data-ctx="vertex">Edit vertices</button>' +
      '<button data-ctx="buffer">Buffer</button>' +
      '<button data-ctx="query">Spatial query</button>' +
      '</div></div>';
    menu.hidden = false;

    qsa("[data-ctx]", menu).forEach(function (btn) {
      btn.addEventListener("click", function () {
        var action = btn.getAttribute("data-ctx");
        if (action === "zoom") MapEngine.selectParcelById(parcel.id);
        if (action === "vertex") MapEngine.startVertexEdit();
        if (action === "buffer") MapEngine.startBuffer();
        if (action === "query") MapEngine.startSpatialQuery();
        pushAudit("ctx-action", action + " on " + parcel.id);
        hideContextMenu();
      });
    });
  }

  function computeAnomalies() {
    var map = MapEngine.getMap();
    var source = map.getLayers().getArray().find(function (ly) { return ly.get("layerId") === "parcels"; }).getSource();
    return source.getFeatures().map(function (f) {
      var id = f.get("id");
      var attr = MOCK_DATA.getParcelById(id);
      if (!attr) return null;
      var geomArea = f.getGeometry().getArea();
      var variance = Math.abs(((geomArea - attr.areaSqM) / (attr.areaSqM || 1)) * 100);
      return {
        id: id,
        survey: attr.surveyNo,
        areaRecord: attr.areaSqM,
        areaMap: Math.round(geomArea),
        variance: variance,
        band: variance > 5 ? "red" : (variance > 2 ? "amber" : "green"),
      };
    }).filter(Boolean);
  }

  function exportText(filename, text, type) {
    var blob = new Blob([text], { type: type || "text/plain" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    setTimeout(function () { URL.revokeObjectURL(url); }, 2500);
  }

  function runParcelSearch(ownerSearch) {
    var query = window.prompt(ownerSearch ? "Enter owner / parcel query" : "Enter survey no / ULPIN / village", ownerSearch ? "owner:" : "142");
    if (query == null) return;
    var result = MOCK_DATA.searchParcels(query, state.role);
    if (result.blocked) {
      showToast(result.reason);
      return;
    }
    if (!result.results.length) {
      showToast("No parcel matched");
      return;
    }
    MapEngine.selectParcelById(result.results[0].id);
    showToast("Found " + result.results[0].surveyNo);
    pushAudit("search", query);
  }

  function openRegionSwitcher() {
    var regions = MapEngine.getRegionCatalog ? MapEngine.getRegionCatalog() : [];
    if (!regions.length) {
      showToast("No region catalog configured");
      return;
    }
    var current = MapEngine.getCurrentRegion ? MapEngine.getCurrentRegion() : null;
    var selectHtml =
      '<label for="region-select">Region</label>' +
      '<select id="region-select" class="input" style="width:100%;margin-top:8px;">' +
      regions.map(function (r) {
        var selected = current && current.key === r.key ? " selected" : "";
        return '<option value="' + r.key + '"' + selected + ">" + r.label + "</option>";
      }).join("") +
      "</select>" +
      "<p style='margin-top:10px;color:#666'>Loads region-specific parcels, admin boundaries, FMB and labels.</p>";

    openModal("Switch Region", selectHtml, [
      {
        label: "Apply",
        primary: true,
        onClick: function () {
          var sel = qs("#region-select");
          var key = sel ? sel.value : "";
          var result = MapEngine.switchRegion ? MapEngine.switchRegion(key) : { ok: false, reason: "Map engine mismatch" };
          if (!result.ok) {
            showToast(result.reason || "Region switch failed");
            return;
          }
          renderLayerPanel();
          if (MOCK_DATA.parcels && MOCK_DATA.parcels.length) {
            MapEngine.selectParcelById(MOCK_DATA.parcels[0].id);
          }
          showToast("Region loaded: " + (result.region ? result.region.label : key));
          pushAudit("region-switch", key);
          closeModal("panel-modal");
        },
      },
      { label: "Close", onClick: function () { closeModal("panel-modal"); } },
    ]);
  }

  function bindMenus() {
    qsa(".menu-item").forEach(function (item) {
      var btn = qs(".menu-btn", item);
      var drop = qs(".menu-drop", item);
      if (!btn || !drop) return;

      btn.addEventListener("click", function (evt) {
        evt.preventDefault();
        evt.stopPropagation();
        var isOpen = item.classList.contains("open");
        qsa(".menu-item").forEach(function (m) { m.classList.remove("open"); });
        if (!isOpen) item.classList.add("open");
      });

      drop.addEventListener("click", function (evt) {
        evt.stopPropagation();
      });
    });

    document.addEventListener("click", function () {
      qsa(".menu-item").forEach(function (m) { m.classList.remove("open"); });
      hideContextMenu();
    });

    qsa("[data-action]").forEach(function (btn) {
      btn.addEventListener("click", function (evt) {
        evt.preventDefault();
        evt.stopPropagation();
        var action = btn.getAttribute("data-action");
        qsa(".menu-item").forEach(function (m) { m.classList.remove("open"); });
        handleAction(action);
      });
    });
  }

  function handleAction(action) {
    var selected = MapEngine.getSelectedParcels();

    var map = {
      "viz-layers": function () {
        openModal("Layer Catalogue", "<p>All configured layers are available and visible by default. Use right panel toggles to adjust visibility.</p>", [{ label: "Close", onClick: function () { closeModal("panel-modal"); } }]);
      },
      "viz-symbology": function () {
        var now = !MapEngine.getLayerVisible("admin-labels");
        MapEngine.setLayerVisible("admin-labels", now);
        var cfg = findLayerCfg("admin-labels");
        if (cfg) cfg.visible = now;
        renderLayerPanel();
        showToast("Boundary labels " + (now ? "enabled" : "disabled"));
      },
      "view-region": function () { openRegionSwitcher(); },
      "search-parcel": function () { runParcelSearch(false); },
      "search-owner": function () { runParcelSearch(true); },
      "nav-bookmark": function () {
        if (selected.length) {
          MapEngine.selectParcelById(selected[0].id);
          showToast("Zoomed to selection");
        } else {
          showToast("Select a parcel first");
        }
      },
      "nav-home": function () { MapEngine.zoomHome(); showToast("Home extent loaded"); },
      "measure-distance": function () { MapEngine.startMeasureDistance(); },
      "measure-area": function () { MapEngine.startMeasureArea(); },
      "measure-bearing": function () { MapEngine.startMeasureBearing(); },
      "measure-buffer": function () { MapEngine.startBuffer(); },
      "spatial-query": function () { MapEngine.startSpatialQuery(); },
      "print-map": function () { window.print(); },
      "export-data": function () {
        var geo = MapEngine.exportSelectionGeoJSON();
        if (!geo) {
          showToast("Select parcel(s) to export");
          return;
        }
        exportText("selected-parcels.geojson", JSON.stringify(geo, null, 2), "application/geo+json");
        showToast("GeoJSON exported");
      },
      "edit-vertex": function () { MapEngine.startVertexEdit(); },
      "edit-subdivide": function () { MapEngine.startSplit(); },
      "edit-amalgamate": function () {
        var result = MapEngine.amalgamateSelected();
        if (!result.ok) {
          showToast(result.reason);
          MapEngine.startAmalgamate();
          return;
        }
        showToast("Amalgamation completed — " + result.merged.surveyNo);
      },
      "edit-rubber": function () { MapEngine.startRubberSheet(); },
      "edit-version": function () {
        openModal("Version Snapshot", "<p>Selected parcels: <strong>" + selected.length + "</strong></p><p>Active mode: <strong>" + qs("#measure-hud").textContent + "</strong></p>", [
          { label: "Close", onClick: function () { closeModal("panel-modal"); } },
        ]);
      },
      "edit-audit": function () {
        exportText("webgis-audit-log.json", JSON.stringify(state.auditLog, null, 2), "application/json");
        showToast("Audit log exported");
      },
      "mut-online": function () {
        openModal("Online Mutation Workflow",
          "<p>Run geometry mutation operations on selected parcels.</p>" +
          "<ul><li>Auto subdivide splits first selected parcel into two children.</li><li>Amalgamate merges selected parcels.</li></ul>",
          [
            {
              label: "Auto Subdivide", primary: true, onClick: function () {
                var res = MapEngine.autoSubdivideSelectedParcel();
                showToast(res.ok ? "Subdivision created" : res.reason);
                closeModal("panel-modal");
              }
            },
            {
              label: "Amalgamate", onClick: function () {
                var res = MapEngine.amalgamateSelected();
                showToast(res.ok ? "Amalgamation created" : res.reason);
                closeModal("panel-modal");
              }
            },
            { label: "Close", onClick: function () { closeModal("panel-modal"); } },
          ]
        );
      },
      "mut-nilamagal": function () {
        openModal("Nilamagal Sync", "<p>Sync payload prepared for selected parcels: <strong>" + selected.length + "</strong>.</p><p>Use Export GeoJSON from Tools for transfer payload.</p>", [{ label: "Close", onClick: function () { closeModal("panel-modal"); } }]);
      },
      "mut-collabland": function () {
        var next = !MapEngine.getLayerVisible("collabland");
        MapEngine.setLayerVisible("collabland", next);
        var cfg = findLayerCfg("collabland");
        if (cfg) cfg.visible = next;
        renderLayerPanel();
        showToast("CollabLand reference " + (next ? "shown" : "hidden"));
      },
      "mut-extract": function () {
        openModal("Certified Extract", "<p>Generate printable map extract for current selection.</p><p>Selected parcels: <strong>" + selected.length + "</strong></p>", [
          { label: "Print", primary: true, onClick: function () { window.print(); closeModal("panel-modal"); } },
          { label: "Close", onClick: function () { closeModal("panel-modal"); } },
        ]);
      },
      "agri-registry": function () {
        openModal("AgriStack Farmer Registry", "<p>Registry linkage state is available for parcel-owner mapping.</p>", [{ label: "Close", onClick: function () { closeModal("panel-modal"); } }]);
      },
      "agri-dcs": function () {
        openModal("DCS Plot Crosswalk", "<table class='table-mini'><tr><th>Survey</th><th>DCS Plot</th></tr><tr><td>142/3A</td><td>DCS-KUR-9912</td></tr><tr><td>087/12</td><td>DCS-MUT-4410</td></tr></table>", [{ label: "Close", onClick: function () { closeModal("panel-modal"); } }]);
      },
      "ulpin-lifecycle": function () {
        openModal("ULPIN Lifecycle", "<table class='table-mini'><tr><th>Date</th><th>Event</th><th>ULPIN</th></tr>" + MOCK_DATA.ulpinEvents.map(function (e) { return "<tr><td>" + e.date + "</td><td>" + e.event + "</td><td>" + e.ulpin + "</td></tr>"; }).join("") + "</table>", [{ label: "Close", onClick: function () { closeModal("panel-modal"); } }]);
      },
      "rbac-matrix": function () {
        openModal("RBAC Matrix", "<table class='table-mini'><tr><th>Role</th><th>Search</th><th>Owner</th><th>Edit</th></tr>" + MOCK_DATA.rbacRoles.map(function (r) { return "<tr><td>" + r.label + "</td><td>" + r.search + "</td><td>" + r.owner + "</td><td>" + r.edit + "</td></tr>"; }).join("") + "</table>", [{ label: "Close", onClick: function () { closeModal("panel-modal"); } }]);
      },
      "anomaly-dashboard": function () {
        var rows = computeAnomalies();
        openModal("Anomaly Analytics", "<table class='table-mini'><tr><th>Survey</th><th>Record Area</th><th>Map Area</th><th>Variance %</th><th>Band</th></tr>" + rows.map(function (r) { return "<tr><td>" + r.survey + "</td><td>" + r.areaRecord + "</td><td>" + r.areaMap + "</td><td>" + r.variance.toFixed(2) + "</td><td>" + r.band + "</td></tr>"; }).join("") + "</table>", [{ label: "Close", onClick: function () { closeModal("panel-modal"); } }]);
      },
      "georef-workbench": function () {
        MapEngine.startGeoref();
        openModal("Georef Workbench", "<p>DGPS points are now editable on the map. Drag points to refine georeference controls.</p>", [{ label: "Close", onClick: function () { closeModal("panel-modal"); } }]);
      },
      "clear-mode": function () { MapEngine.clearMode(); },
    };

    if (map[action]) {
      map[action]();
      pushAudit("action", action);
    }
  }

  function bindEvents() {
    qsa("[data-close]").forEach(function (btn) {
      btn.addEventListener("click", function () { closeModal(btn.getAttribute("data-close")); });
    });

    document.addEventListener("keydown", function (evt) {
      if (evt.key === "Escape") {
        hideContextMenu();
        MapEngine.clearMode();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    try {
      MapEngine.init("map");
      MapEngine.setBasemap("basemap-carto");
      MapEngine.onParcelSelect(function (parcel) {
        state.selectedParcel = parcel;
      });
      MapEngine.onContextMenu(function (evtInfo) {
        state.selectedParcel = evtInfo.parcel || null;
        showContextMenu(evtInfo);
      });
      MapEngine.onModeChange(function (info) {
        if (info && info.mode) setHud("Mode: " + info.mode);
      });
      MapEngine.onMeasureUpdate(function (text) {
        if (text) setHud(text);
      });

      bindMenus();
      bindEvents();
      renderLayerPanel();
      if (MOCK_DATA.parcels && MOCK_DATA.parcels.length) {
        MapEngine.selectParcelById(MOCK_DATA.parcels[0].id);
      }
      showToast("WebGIS ready");
    } catch (err) {
      console.error(err);
      showToast("Error: " + err.message);
    }
  });
})();
