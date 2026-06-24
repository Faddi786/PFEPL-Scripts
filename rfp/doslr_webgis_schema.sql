-- =============================================================================
--  DoSLR Puducherry WebGIS — Database Schema (PostgreSQL + PostGIS)
--  RFP No: M-13/1237/2025
--  Covers Module 2 (WebGIS Platform) + Module 3 (Mobile / Georeferencing)
--
--  LEGEND in comments:
--    [RFP-EXPLICIT]  = table/columns the RFP names directly (verbatim fields)
--    [SUPPORTING]    = table the architecture needs to make those features work
--
--  CONVENTIONS:
--    * All geometry stored in WGS 84 / EPSG:4326 (RFP Sec 18.2.3 storage rule).
--    * Display reprojection (India Zone II / LCC) is handled at the service
--      layer (GeoServer / pygeoapi), NOT in storage.
--    * Row-level history, rollback and "queryable as of any date" (Sec 18.3.3)
--      are provided by the pgMemento extension layered on top of these tables,
--      so per-table shadow/history tables are intentionally NOT hand-written.
--    * Authentication is owned by Keycloak; iam.app_user only mirrors the
--      Keycloak user id plus the jurisdiction scope the app needs.
--
--  TO RESET (run on a fresh DB, or uncomment to wipe and rebuild):
--    DROP SCHEMA IF EXISTS geo, ror, mut, agri, gref, iam, aud, app CASCADE;
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE SCHEMA IF NOT EXISTS geo;   -- spatial core: admin units, FMB sheets, parcels
CREATE SCHEMA IF NOT EXISTS ror;   -- record-of-rights: owners, tenants, encumbrances
CREATE SCHEMA IF NOT EXISTS mut;   -- mutations, workflow, lineage, ULPIN
CREATE SCHEMA IF NOT EXISTS agri;  -- AgriStack: farmer registry + crop survey
CREATE SCHEMA IF NOT EXISTS gref;  -- georeferencing: control points + jobs
CREATE SCHEMA IF NOT EXISTS iam;   -- users + roles + permission matrix
CREATE SCHEMA IF NOT EXISTS aud;   -- audit / export / query logs + anomalies
CREATE SCHEMA IF NOT EXISTS app;   -- app-level: extracts, bookmarks


-- =============================================================================
--  ENUM TYPES
-- =============================================================================

-- Land classification — RFP Sec 18.3.4 names Nanjai / Punjai / Manavari.
CREATE TYPE ror.land_classification AS ENUM
    ('Nanjai', 'Punjai', 'Manavari', 'Other');

CREATE TYPE geo.parcel_status AS ENUM
    ('active', 'retired', 'provisional');   -- provisional = CollabLand placeholder

-- Mutation events — RFP Sec 18.2.5 / 18.3.4: sub-division, amalgamation, attr-only.
CREATE TYPE mut.mutation_type   AS ENUM ('subdivision', 'amalgamation', 'attribute_change');
-- Approval workflow — RFP Sec 18.3.4 (digital approval before sync-back).
CREATE TYPE mut.mutation_status AS ENUM ('draft', 'submitted', 'approved', 'rejected', 'synced');
CREATE TYPE mut.parcel_role     AS ENUM ('parent', 'child', 'affected');
CREATE TYPE mut.ulpin_status    AS ENUM ('active', 'retired');
CREATE TYPE mut.ulpin_relation  AS ENUM ('split', 'merge');

-- Control-point source — RFP Sec 18.4.2: csv, manual, mobile (Bluetooth/NTRIP/file).
CREATE TYPE gref.point_source AS ENUM
    ('csv_upload', 'manual_entry', 'mobile_dgps', 'mobile_gnss', 'ntrip', 'bluetooth', 'file_import');
CREATE TYPE gref.point_status AS ENUM ('pending', 'accepted', 'rejected', 'flagged');
-- Transform types — RFP Sec 18.2.3 / 18.4.2 / 18.4.3 name all four.
CREATE TYPE gref.transform_type AS ENUM ('affine', 'polynomial', 'spline', 'thin_plate_spline');
CREATE TYPE gref.job_status     AS ENUM ('dry_run', 'committed', 'reverted', 'failed');

-- Role classes — RFP Sec 18.3.7 lists these nine verbatim.
CREATE TYPE iam.user_role AS ENUM
    ('public_citizen', 'authenticated_citizen', 'village_taluk_officer', 'revenue_inspector',
     'surveyor', 'doslr_officer', 'line_department_officer', 'administrator', 'auditor');

-- Anomaly analytics — RFP Sec 18.3.8 dashboard categories + variance/boundary checks.
CREATE TYPE aud.anomaly_type AS ENUM
    ('area_variance', 'boundary_mismatch', 'missing_ror_record', 'missing_geometry',
     'duplicate_geometry', 'ulpin_conflict', 'classification_mismatch', 'ownership_conflict');
CREATE TYPE aud.variance_band  AS ENUM ('green', 'amber', 'red');   -- ≤1% / 1–5% / >5%
CREATE TYPE aud.anomaly_status AS ENUM ('open', 'under_review', 'resolved', 'dismissed');


-- =============================================================================
--  geo — ADMINISTRATIVE HIERARCHY  (RFP Sec 18.3.1: Region/Taluk/Village/Ward)
--  Hierarchy: Region -> Taluk -> Village -> Ward/Block
-- =============================================================================

CREATE TABLE geo.region (                                   -- [RFP-EXPLICIT]
    region_id    serial PRIMARY KEY,
    code         varchar(20)  NOT NULL UNIQUE,
    name         varchar(120) NOT NULL,                     -- Puducherry / Karaikal / Mahe / Yanam
    geom         geometry(MultiPolygon, 4326),
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE geo.taluk (                                     -- [RFP-EXPLICIT]
    taluk_id     serial PRIMARY KEY,
    region_id    integer NOT NULL REFERENCES geo.region(region_id),
    code         varchar(20)  NOT NULL UNIQUE,
    name         varchar(120) NOT NULL,
    geom         geometry(MultiPolygon, 4326),
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE geo.village (                                   -- [RFP-EXPLICIT]
    village_id   serial PRIMARY KEY,
    taluk_id     integer NOT NULL REFERENCES geo.taluk(taluk_id),
    code         varchar(20)  NOT NULL UNIQUE,
    name         varchar(120) NOT NULL,
    geom         geometry(MultiPolygon, 4326),
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE geo.ward_block (                                -- [RFP-EXPLICIT] Ward / block boundaries
    ward_id      serial PRIMARY KEY,
    village_id   integer NOT NULL REFERENCES geo.village(village_id),
    code         varchar(20)  NOT NULL,
    name         varchar(120),
    kind         varchar(20) NOT NULL DEFAULT 'ward',        -- 'ward' | 'block'
    geom         geometry(MultiPolygon, 4326),
    created_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (village_id, code, kind)
);


-- =============================================================================
--  geo — FMB SHEETS  (RFP Sec 18.3.1: FMB layer is a visualisation layer;
--  Sec 18.2.2 lineage: every parcel traces back to source FMB sheet + page)
--  NOTE: FMB *reconstruction* is Module 1; this table only holds the sheet
--  outline + metadata the platform displays and links parcels to.
-- =============================================================================

CREATE TABLE geo.fmb_sheet (                                 -- [SUPPORTING] (display + lineage)
    fmb_sheet_id   serial PRIMARY KEY,
    village_id     integer NOT NULL REFERENCES geo.village(village_id),
    sheet_no       varchar(40)  NOT NULL,
    legibility     varchar(20),                              -- legibility grade (Sec 18.2.1)
    survey_scale   varchar(40),                              -- scale of source survey
    survey_year    integer,
    provenance     text,                                     -- data provenance note
    outline_geom   geometry(MultiPolygon, 4326),             -- toggleable FMB outline (Sec 18.3.1)
    created_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (village_id, sheet_no)
);


-- =============================================================================
--  geo — PARCEL  (the cadastral layer the platform serves)
--  This holds the GEOMETRY/CADASTRAL-SIDE attributes. The RoR-RECORDED values
--  live separately in ror.ror_record so the two can be compared for variance
--  analytics (RFP Sec 18.3.8). This duplication is intentional.
-- =============================================================================

CREATE TABLE geo.parcel (                                    -- [RFP-EXPLICIT] (Survey/Sub-Div/Village)
    parcel_id        bigserial PRIMARY KEY,
    ulpin            char(14) UNIQUE,                         -- 14-digit ULPIN (Sec 18.3.6)
    survey_no        varchar(40)  NOT NULL,                   -- Survey No.        (Sec 18.3.4)
    sub_div_no       varchar(40),                             -- Sub-Div No.       (Sec 18.3.4)
    village_id       integer NOT NULL REFERENCES geo.village(village_id),
    classification   ror.land_classification,                 -- cadastral-side classification
    geom             geometry(Polygon, 4326) NOT NULL,        -- parcel polygon, WGS84
    computed_area_sqm numeric(16,2),                          -- ST_Area-derived extent (for variance)
    -- lineage back to source FMB sheet + page (Sec 18.2.2)
    fmb_sheet_id     integer REFERENCES geo.fmb_sheet(fmb_sheet_id),
    fmb_page         varchar(20),
    -- time-awareness (Sec 18.3.3 "queryable as of any date")
    status           geo.parcel_status NOT NULL DEFAULT 'active',
    valid_from       timestamptz NOT NULL DEFAULT now(),
    valid_to         timestamptz,                             -- NULL = currently valid
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_parcel_geom        ON geo.parcel USING gist (geom);
CREATE INDEX idx_parcel_survey      ON geo.parcel (survey_no, sub_div_no);
CREATE INDEX idx_parcel_village     ON geo.parcel (village_id);
CREATE INDEX idx_parcel_ulpin       ON geo.parcel (ulpin);
CREATE INDEX idx_parcel_status      ON geo.parcel (status);


-- =============================================================================
--  ror — RECORD OF RIGHTS  (RFP Sec 18.3.4 — every field below is named in the RFP)
--  Source systems: Nilamagal (RoR/Patta/Chitta/Adangal) + Collabland.
-- =============================================================================

CREATE TABLE ror.ror_record (                               -- [RFP-EXPLICIT]
    ror_record_id    bigserial PRIMARY KEY,
    parcel_id        bigint NOT NULL REFERENCES geo.parcel(parcel_id),
    -- RoR-recorded identifiers (may differ from cadastral side -> variance)
    survey_no        varchar(40),                             -- Survey No.
    sub_div_no       varchar(40),                             -- Sub-Div No.
    village_id       integer REFERENCES geo.village(village_id),
    classification   ror.land_classification,                 -- Classification (Nanjai/Punjai/Manavari)
    ror_extent_sqm   numeric(16,2),                           -- Extent as recorded in RoR
    kist_amount      numeric(14,2),                           -- Land Revenue / Kist
    patta_no         varchar(60),                             -- Patta reference (Nilamagal)
    source_system    varchar(40) NOT NULL DEFAULT 'nilamagal',-- nilamagal | collabland
    ror_txn_id       varchar(80),                             -- linked RoR transaction id
    last_synced_at   timestamptz,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_ror_parcel ON ror.ror_record (parcel_id);

CREATE TABLE ror.owner (                                     -- [RFP-EXPLICIT] Owner(s) and share
    owner_id         bigserial PRIMARY KEY,
    ror_record_id    bigint NOT NULL REFERENCES ror.ror_record(ror_record_id) ON DELETE CASCADE,
    owner_name       varchar(200) NOT NULL,                   -- PII: never exposed in public tier
    owner_ref_key    varchar(80),                             -- owner reference key (Sec 18.2.1)
    share_fraction   numeric(8,5),                            -- normalised share 0..1
    share_text       varchar(40),                             -- raw RoR share e.g. '1/3'
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_owner_record ON ror.owner (ror_record_id);

CREATE TABLE ror.tenant (                                     -- [RFP-EXPLICIT] Tenant(s) and share
    tenant_id        bigserial PRIMARY KEY,
    ror_record_id    bigint NOT NULL REFERENCES ror.ror_record(ror_record_id) ON DELETE CASCADE,
    tenant_name      varchar(200) NOT NULL,                   -- PII: never exposed in public tier
    share_fraction   numeric(8,5),
    share_text       varchar(40),
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_tenant_record ON ror.tenant (ror_record_id);

CREATE TABLE ror.encumbrance (                               -- [RFP-EXPLICIT] Encumbrances
    encumbrance_id   bigserial PRIMARY KEY,
    ror_record_id    bigint NOT NULL REFERENCES ror.ror_record(ror_record_id) ON DELETE CASCADE,
    enc_type         varchar(80),                             -- mortgage / lien / court attachment ...
    description      text,
    amount           numeric(14,2),
    party            varchar(200),
    registered_date  date,
    released_date    date,
    is_active        boolean NOT NULL DEFAULT true,
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_encumbrance_record ON ror.encumbrance (ror_record_id);


-- =============================================================================
--  mut — MUTATIONS, WORKFLOW & ULPIN LINEAGE
--  RFP Sec 18.2.5 / 18.3.4 (bidirectional mutation, digital approval),
--  Sec 18.3.6 (ULPIN lifecycle), "Mutation history with dates" (Sec 18.3.4).
-- =============================================================================

CREATE TABLE mut.mutation_event (                           -- [RFP-EXPLICIT]
    mutation_id      bigserial PRIMARY KEY,
    mutation_type    mut.mutation_type  NOT NULL,             -- subdivision/amalgamation/attribute_change
    status           mut.mutation_status NOT NULL DEFAULT 'draft',
    ror_txn_id       varchar(80),                             -- linked RoR transaction identifier
    -- audit trail required by Sec 18.2.5: before/after geometry + attributes
    before_geom      geometry(Geometry, 4326),
    after_geom       geometry(Geometry, 4326),
    before_attrs     jsonb,
    after_attrs      jsonb,
    -- approval workflow (Sec 18.3.4: digital approval before sync-back)
    initiated_by     uuid,                                    -- iam.app_user.keycloak_id
    initiated_at     timestamptz NOT NULL DEFAULT now(),
    approved_by      uuid,
    approved_at      timestamptz,
    rejected_reason  text,
    synced_at        timestamptz,                             -- when pushed back to Nilamagal/Collabland
    notes            text
);
CREATE INDEX idx_mutation_status ON mut.mutation_event (status);
CREATE INDEX idx_mutation_txn    ON mut.mutation_event (ror_txn_id);

CREATE TABLE mut.mutation_parcel (                          -- [SUPPORTING] parcel genealogy
    id               bigserial PRIMARY KEY,
    mutation_id      bigint NOT NULL REFERENCES mut.mutation_event(mutation_id) ON DELETE CASCADE,
    parcel_id        bigint NOT NULL REFERENCES geo.parcel(parcel_id),
    role             mut.parcel_role NOT NULL,                -- parent (retired) / child (new) / affected
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_mutparcel_mutation ON mut.mutation_parcel (mutation_id);
CREATE INDEX idx_mutparcel_parcel   ON mut.mutation_parcel (parcel_id);

-- Authoritative ULPIN registry (can outlive a parcel — RFP Sec 18.3.6).
CREATE TABLE mut.ulpin_registry (                           -- [RFP-EXPLICIT]
    ulpin            char(14) PRIMARY KEY,                    -- 14-digit Bhu-Aadhaar
    parcel_id        bigint REFERENCES geo.parcel(parcel_id),
    status           mut.ulpin_status NOT NULL DEFAULT 'active',
    issued_at        timestamptz NOT NULL DEFAULT now(),
    retired_at       timestamptz,
    issued_mutation  bigint REFERENCES mut.mutation_event(mutation_id),
    retired_mutation bigint REFERENCES mut.mutation_event(mutation_id)
);

-- ULPIN lineage: parent->child on split/merge (RFP Sec 18.3.6).
CREATE TABLE mut.ulpin_lineage (                            -- [RFP-EXPLICIT]
    id               bigserial PRIMARY KEY,
    parent_ulpin     char(14) NOT NULL REFERENCES mut.ulpin_registry(ulpin),
    child_ulpin      char(14) NOT NULL REFERENCES mut.ulpin_registry(ulpin),
    relation         mut.ulpin_relation NOT NULL,             -- split / merge
    mutation_id      bigint REFERENCES mut.mutation_event(mutation_id),
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_ulpin_lineage_parent ON mut.ulpin_lineage (parent_ulpin);
CREATE INDEX idx_ulpin_lineage_child  ON mut.ulpin_lineage (child_ulpin);

-- Cross-reference of legacy parcel identifiers (RFP Sec 18.3.6 mapping register).
CREATE TABLE mut.legacy_id_map (                            -- [RFP-EXPLICIT]
    id               bigserial PRIMARY KEY,
    ulpin            char(14) REFERENCES mut.ulpin_registry(ulpin),
    legacy_system    varchar(60) NOT NULL,                    -- collabland / nilamagal / legacy_sheet
    legacy_id        varchar(120) NOT NULL,
    created_at       timestamptz NOT NULL DEFAULT now(),
    UNIQUE (legacy_system, legacy_id)
);


-- =============================================================================
--  agri — AGRISTACK INTEGRATION  (RFP Sec 18.3.5)
--  Farmer Registry (Farmer ID) + Digital Crop Survey (DCS). Consent-based,
--  IDEA framework, DPDP Act — tokenised refs, no raw PII beyond what's needed.
-- =============================================================================

CREATE TABLE agri.farmer_parcel_link (                      -- [RFP-EXPLICIT]
    id               bigserial PRIMARY KEY,
    parcel_id        bigint NOT NULL REFERENCES geo.parcel(parcel_id),
    farmer_id        varchar(80) NOT NULL,                    -- AgriStack Farmer ID (tokenised)
    role             varchar(30) NOT NULL DEFAULT 'cultivator', -- cultivator / tenant / owner
    consent_ref      varchar(120),                            -- consent artifact reference (IDEA)
    valid_from       date,
    valid_to         date,
    linked_at        timestamptz NOT NULL DEFAULT now(),
    UNIQUE (parcel_id, farmer_id, role)
);
CREATE INDEX idx_farmerlink_parcel ON agri.farmer_parcel_link (parcel_id);
CREATE INDEX idx_farmerlink_farmer ON agri.farmer_parcel_link (farmer_id);

CREATE TABLE agri.crop_survey (                             -- [RFP-EXPLICIT] Digital Crop Survey
    id               bigserial PRIMARY KEY,
    parcel_id        bigint NOT NULL REFERENCES geo.parcel(parcel_id),
    season           varchar(40) NOT NULL,                    -- e.g. 'Kharif 2026' / 'Samba 2025-26'
    crop             varchar(120),                            -- crop sown
    sown_date        date,
    dcs_ref          varchar(120),                            -- Digital Crop Survey record ref
    source_system    varchar(40) NOT NULL DEFAULT 'dcs',
    recorded_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (parcel_id, season)
);
CREATE INDEX idx_cropsurvey_parcel ON agri.crop_survey (parcel_id);
CREATE INDEX idx_cropsurvey_season ON agri.crop_survey (season);


-- =============================================================================
--  gref — GEOREFERENCING  (RFP Module 3, Sec 18.4)
--  control_point: the single "GCP library" that web upload, manual entry AND
--  mobile DGPS/GNSS points all stream into (Sec 18.4.2). Columns ID/description/
--  latitude/longitude/easting/northing/datum/accuracy/source/notes are the
--  RFP's verbatim CSV template.
-- =============================================================================

CREATE TABLE gref.control_point (                           -- [RFP-EXPLICIT] (CSV template fields)
    control_point_id bigserial PRIMARY KEY,
    external_id      varchar(80),                             -- "ID" from upload template
    description      text,                                    -- "description"
    latitude         double precision,                        -- "latitude"  (decimal degrees)
    longitude        double precision,                        -- "longitude"
    easting          double precision,                        -- "easting"   (projected)
    northing         double precision,                        -- "northing"
    datum            varchar(40),                             -- "datum"
    accuracy         numeric(8,3),                            -- "accuracy" (metres)
    source           gref.point_source NOT NULL,              -- "source": csv/manual/mobile/ntrip...
    notes            text,                                    -- "notes"
    -- derived geometry for map display / spatial use
    geom             geometry(Point, 4326),
    -- library/workflow fields (Sec 18.4.2: accept/reject/flag per point)
    village_id       integer REFERENCES geo.village(village_id),
    cluster_ref      varchar(80),
    status           gref.point_status NOT NULL DEFAULT 'pending',
    review_remark    text,
    captured_by      uuid,                                    -- field officer / uploader
    captured_at      timestamptz,
    reviewed_by      uuid,
    reviewed_at      timestamptz,
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_ctrlpoint_geom    ON gref.control_point USING gist (geom);
CREATE INDEX idx_ctrlpoint_village ON gref.control_point (village_id);
CREATE INDEX idx_ctrlpoint_status  ON gref.control_point (status);

-- A bulk upload batch (Sec 18.4.2: preview rejected rows, bulk-promote accepted).
CREATE TABLE gref.upload_batch (                            -- [SUPPORTING]
    batch_id         bigserial PRIMARY KEY,
    filename         varchar(255),
    village_id       integer REFERENCES geo.village(village_id),
    rows_total       integer,
    rows_accepted    integer,
    rows_rejected    integer,
    uploaded_by      uuid,
    uploaded_at      timestamptz NOT NULL DEFAULT now()
);

-- Server-side georeferencing run (Sec 18.4.3): transform, RMSE, weights, dry-run,
-- explainability log, before/after geometry, immutable audit linkage.
CREATE TABLE gref.georef_job (                              -- [RFP-EXPLICIT]
    georef_job_id    bigserial PRIMARY KEY,
    scope            varchar(20) NOT NULL,                    -- parcel / cluster / village
    village_id       integer REFERENCES geo.village(village_id),
    transform_type   gref.transform_type NOT NULL,            -- affine/polynomial/spline/tps
    rmse             numeric(10,4),                           -- residual reported by GDAL
    status           gref.job_status NOT NULL DEFAULT 'dry_run',
    -- weight-based merging (Sec 18.4.3 defaults DGPS=1.0 / drone=0.7 / legacy=0.3)
    weight_dgps      numeric(4,2) DEFAULT 1.00,
    weight_drone     numeric(4,2) DEFAULT 0.70,
    weight_legacy    numeric(4,2) DEFAULT 0.30,
    input_point_ids  bigint[],                                -- control points used
    justification    text,                                    -- explainability log (Sec 18.4.3)
    before_geom      geometry(Geometry, 4326),
    after_geom       geometry(Geometry, 4326),
    run_by           uuid,
    run_at           timestamptz NOT NULL DEFAULT now(),
    committed_by     uuid,
    committed_at     timestamptz
);
CREATE INDEX idx_georefjob_village ON gref.georef_job (village_id);
CREATE INDEX idx_georefjob_status  ON gref.georef_job (status);


-- =============================================================================
--  iam — USERS, ROLES & PERMISSION MATRIX
--  RFP Sec 18.3.7. Keycloak is the identity provider; app_user mirrors the
--  Keycloak id + jurisdiction scope. permission_matrix is the RFP-required
--  "Role-Based Permission Matrix" deliverable (CRUD + export per role).
-- =============================================================================

CREATE TABLE iam.app_user (                                 -- [SUPPORTING] (mirrors Keycloak)
    keycloak_id      uuid PRIMARY KEY,                        -- subject id from Keycloak
    username         varchar(120) NOT NULL,
    display_name     varchar(200),
    role             iam.user_role NOT NULL,
    -- jurisdiction scope (an officer only sees their region/taluk/village)
    region_id        integer REFERENCES geo.region(region_id),
    taluk_id         integer REFERENCES geo.taluk(taluk_id),
    village_id       integer REFERENCES geo.village(village_id),
    is_active        boolean NOT NULL DEFAULT true,
    created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE iam.permission_matrix (                        -- [RFP-EXPLICIT] (SRS deliverable)
    id               bigserial PRIMARY KEY,
    role             iam.user_role NOT NULL,
    resource         varchar(80)  NOT NULL,                   -- e.g. parcel / ror_record / mutation / export
    can_create       boolean NOT NULL DEFAULT false,
    can_read         boolean NOT NULL DEFAULT false,
    can_update       boolean NOT NULL DEFAULT false,
    can_delete       boolean NOT NULL DEFAULT false,
    can_export       boolean NOT NULL DEFAULT false,
    UNIQUE (role, resource)
);


-- =============================================================================
--  aud — AUDIT / EXPORT / QUERY LOGS + ANOMALY ANALYTICS
--  Immutable audit log (Sec 18.3.3); export events logged with extent
--  (Sec 18.3.2); owner-name queries logged (Sec 18.3.2);
--  anomaly persistence for the Discrepancy & Anomaly dashboard (Sec 18.3.8).
-- =============================================================================

CREATE TABLE aud.audit_log (                                -- [RFP-EXPLICIT] immutable audit log
    audit_id         bigserial PRIMARY KEY,
    actor            uuid,                                    -- iam.app_user.keycloak_id
    action           varchar(80) NOT NULL,                    -- create/update/delete/georef/approve...
    entity_type      varchar(80) NOT NULL,                    -- parcel / mutation / control_point ...
    entity_id        varchar(80),
    before_geom      geometry(Geometry, 4326),
    after_geom       geometry(Geometry, 4326),
    before_attrs     jsonb,
    after_attrs      jsonb,
    occurred_at      timestamptz NOT NULL DEFAULT now(),
    ip_address       inet
);
CREATE INDEX idx_audit_entity ON aud.audit_log (entity_type, entity_id);
CREATE INDEX idx_audit_actor  ON aud.audit_log (actor);
CREATE INDEX idx_audit_time   ON aud.audit_log (occurred_at);

CREATE TABLE aud.export_log (                               -- [RFP-EXPLICIT] (user, time, extent)
    export_id        bigserial PRIMARY KEY,
    actor            uuid NOT NULL,
    format           varchar(20) NOT NULL,                    -- pdf / csv / shapefile / geojson / geopackage
    extent_geom      geometry(Polygon, 4326),                 -- geographic extent of the export
    record_count     integer,
    occurred_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_export_actor ON aud.export_log (actor);

CREATE TABLE aud.query_log (                                -- [RFP-EXPLICIT] (owner-name searches logged)
    query_id         bigserial PRIMARY KEY,
    actor            uuid,                                    -- NULL allowed for anonymous tiers
    query_type       varchar(40) NOT NULL,                    -- owner_name_search / spatial / attribute
    parameters       jsonb,
    result_count     integer,
    occurred_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_query_actor ON aud.query_log (actor);
CREATE INDEX idx_query_type  ON aud.query_log (query_type);

-- Persisted anomalies feeding the Discrepancy & Anomaly dashboard (Sec 18.3.8).
CREATE TABLE aud.anomaly (                                  -- [RFP-EXPLICIT]
    anomaly_id       bigserial PRIMARY KEY,
    anomaly_type     aud.anomaly_type NOT NULL,
    parcel_id        bigint REFERENCES geo.parcel(parcel_id),
    village_id       integer REFERENCES geo.village(village_id),
    variance_pct     numeric(7,3),                            -- for area_variance
    variance_band    aud.variance_band,                       -- green/amber/red
    detail           jsonb,                                   -- type-specific payload
    highlight_geom   geometry(Geometry, 4326),                -- segment/parcel to highlight on map
    status           aud.anomaly_status NOT NULL DEFAULT 'open',
    detected_at      timestamptz NOT NULL DEFAULT now(),
    resolved_by      uuid,
    resolved_at      timestamptz
);
CREATE INDEX idx_anomaly_geom    ON aud.anomaly USING gist (highlight_geom);
CREATE INDEX idx_anomaly_type    ON aud.anomaly (anomaly_type);
CREATE INDEX idx_anomaly_village ON aud.anomaly (village_id);
CREATE INDEX idx_anomaly_band    ON aud.anomaly (variance_band);


-- =============================================================================
--  app — CERTIFIED EXTRACTS & MAP BOOKMARKS
--  Certified extract (Sec 18.3.4: digitally-signed, via DigiLocker);
--  map bookmark (Sec 18.3.2: "zoom to bookmark").
-- =============================================================================

CREATE TABLE app.certified_extract (                        -- [RFP-EXPLICIT] certified extracts
    extract_id       bigserial PRIMARY KEY,
    parcel_id        bigint NOT NULL REFERENCES geo.parcel(parcel_id),
    ulpin            char(14),
    generated_by     uuid NOT NULL,
    generated_at     timestamptz NOT NULL DEFAULT now(),
    format           varchar(20) NOT NULL DEFAULT 'pdf',
    signature_ref    varchar(200),                            -- digital signature reference
    digilocker_uri   varchar(300),                            -- DigiLocker issuance URI
    status           varchar(30) NOT NULL DEFAULT 'issued'    -- issued / revoked
);
CREATE INDEX idx_extract_parcel ON app.certified_extract (parcel_id);

CREATE TABLE app.map_bookmark (                             -- [SUPPORTING] (zoom-to-bookmark)
    bookmark_id      bigserial PRIMARY KEY,
    owner            uuid NOT NULL,                           -- iam.app_user.keycloak_id
    name             varchar(120) NOT NULL,
    extent_geom      geometry(Polygon, 4326) NOT NULL,
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_bookmark_owner ON app.map_bookmark (owner);


-- =============================================================================
--  FK back-references to iam.app_user
--  (added here because iam.app_user is created after the tables that reference
--   actors by uuid; keeping those as plain uuid columns avoids a circular
--   create-order problem. Uncomment to enforce referential integrity once
--   Keycloak-synced users are guaranteed to exist before any actor is written.)
-- =============================================================================
-- ALTER TABLE mut.mutation_event   ADD CONSTRAINT fk_mut_initiator FOREIGN KEY (initiated_by) REFERENCES iam.app_user(keycloak_id);
-- ALTER TABLE aud.audit_log        ADD CONSTRAINT fk_audit_actor   FOREIGN KEY (actor)        REFERENCES iam.app_user(keycloak_id);
-- ALTER TABLE gref.georef_job      ADD CONSTRAINT fk_georef_runby  FOREIGN KEY (run_by)       REFERENCES iam.app_user(keycloak_id);
-- ... (apply the same pattern to other actor columns as needed)

-- =============================================================================
--  END OF SCHEMA
-- =============================================================================
