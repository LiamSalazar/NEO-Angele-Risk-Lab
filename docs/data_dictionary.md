# Data Dictionary

This initial dictionary documents the main silver and gold datasets produced by the Spark ETL pipeline. Types are expected logical types after Spark normalization.

## silver_sbdb_objects

| Column name | Layer | Description | Type expected | Source | Notes |
|---|---|---|---|---|---|
| object_id | silver | Ingestion object identifier or best available object ID | string | Bronze metadata, SBDB Object | Used for lineage |
| source | silver | Bronze source name | string | Bronze metadata | Usually `sbdb_object` |
| ingested_at_utc | silver | UTC ingestion timestamp | string | Bronze metadata | ISO-like string |
| spkid | silver | JPL SPK object identifier | string | SBDB Object | Preferred stable key |
| full_name | silver | Full object name | string | SBDB Object | Human-readable |
| pdes | silver | Primary designation | string | SBDB Object | Used as `des` in gold |
| name | silver | Short object name when available | string | SBDB Object | Optional |
| prefix | silver | Object prefix | string | SBDB Object | Optional |
| orbit_id | silver | Orbit solution identifier | string | SBDB Object | Object or orbit section |
| neo | silver | Near-Earth object flag | boolean | SBDB Object | Converted from API flags |
| pha | silver | Potentially hazardous asteroid flag | boolean | SBDB Object | Converted from API flags |
| kind | silver | Small-body kind | string | SBDB Object | API-defined |
| orbit_class_code | silver | Orbit class code | string | SBDB Object | Example: `AMO` |
| orbit_class_name | silver | Orbit class name | string | SBDB Object | Optional |
| condition_code | silver | Orbit uncertainty condition code | string | SBDB orbit | Used as uncertainty proxy |
| orbit_solution_date | silver | Orbit solution date | string | SBDB orbit | Optional |
| first_obs | silver | First observation date | string | SBDB orbit | Optional |
| last_obs | silver | Last observation date | string | SBDB orbit | Optional |
| arc_length | silver | Observation arc length | double | SBDB orbit | Usually days |
| n_obs_used | silver | Number of observations used | integer | SBDB orbit | Optional |
| rms | silver | Orbit-fit residual RMS | double | SBDB orbit | Optional |
| h | silver | Absolute magnitude | double | SBDB physical parameters | Extracted from `phys_par` |
| diameter | silver | Estimated diameter | double | SBDB physical parameters | Kilometers when provided |
| albedo | silver | Geometric albedo | double | SBDB physical parameters | Optional |
| moid | silver | Minimum orbit intersection distance | double | SBDB orbit | AU |
| moid_ld | silver | MOID in lunar distances | double | SBDB orbit or derived | Derived from AU when absent |
| e, a, q, i, om, w, ma, n, tp, per, ad | silver | Orbital elements | double | SBDB orbit elements | Extracted by element name |
| raw_json | silver | Raw source payload JSON | string | Bronze data | Traceability |

## silver_close_approaches

| Column name | Layer | Description | Type expected | Source | Notes |
|---|---|---|---|---|---|
| source | silver | Bronze source name | string | Bronze metadata | Usually `cad` |
| ingested_at_utc | silver | UTC ingestion timestamp | string | Bronze metadata | Lineage |
| des | silver | Object designation | string | CAD | Join key for gold |
| orbit_id | silver | Orbit solution identifier | string | CAD | Optional |
| jd | silver | Julian date of approach | double | CAD | Optional |
| cd | silver | Calendar date string | string | CAD | Original API value |
| close_approach_datetime | silver | Approach datetime string | string | CAD | Derived from `cd` |
| dist | silver | Nominal close approach distance | double | CAD | AU |
| dist_min | silver | Minimum close approach distance | double | CAD | AU |
| dist_max | silver | Maximum close approach distance | double | CAD | AU |
| v_rel | silver | Relative velocity | double | CAD | km/s |
| v_inf | silver | Hyperbolic excess velocity | double | CAD | km/s |
| t_sigma_f | silver | Time uncertainty string | string | CAD | Optional |
| body | silver | Approach body | string | CAD or query params | Often Earth |
| h | silver | Absolute magnitude | double | CAD | Optional |
| diameter | silver | Estimated diameter | double | CAD | Optional |
| diameter_sigma | silver | Diameter uncertainty | double | CAD | Optional |
| fullname | silver | Full object name | string | CAD | Optional |
| raw_json | silver | Raw normalized row JSON | string | CAD row | Traceability |

## silver_sentry_objects

| Column name | Layer | Description | Type expected | Source | Notes |
|---|---|---|---|---|---|
| source | silver | Bronze source name | string | Bronze metadata | Usually `sentry` |
| ingested_at_utc | silver | UTC ingestion timestamp | string | Bronze metadata | Lineage |
| des | silver | Object designation | string | Sentry | Join key |
| fullname | silver | Full object name | string | Sentry | Optional |
| spk | silver | SPK identifier | string | Sentry | Join key |
| h | silver | Absolute magnitude | double | Sentry | Optional |
| diameter | silver | Estimated diameter | double | Sentry | Optional |
| ip | silver | Cumulative impact probability | double | Sentry | Optional |
| ps_cum | silver | Cumulative Palermo scale | double | Sentry | Optional |
| ps_max | silver | Maximum Palermo scale | double | Sentry | Optional |
| ts_max | silver | Maximum Torino scale | double | Sentry | Optional |
| last_obs | silver | Last observation date | string | Sentry | Optional |
| n_imp | silver | Number of impact solutions | integer | Sentry | Optional |
| last_obs_jd | silver | Last observation Julian date | double | Sentry | Optional |
| raw_json | silver | Raw Sentry record JSON | string | Sentry | Traceability |

## silver_sentry_virtual_impactors

| Column name | Layer | Description | Type expected | Source | Notes |
|---|---|---|---|---|---|
| source | silver | Bronze source name | string | Bronze metadata | Usually `sentry` |
| ingested_at_utc | silver | UTC ingestion timestamp | string | Bronze metadata | Lineage |
| des | silver | Object designation | string | Sentry VI | Optional |
| fullname | silver | Full object name | string | Sentry VI | Optional |
| spk | silver | SPK identifier | string | Sentry VI | Optional |
| ip | silver | Virtual impactor probability | double | Sentry VI | Optional |
| date | silver | Impact date string | string | Sentry VI | Optional |
| dist | silver | Distance field when provided | double | Sentry VI | Optional |
| width | silver | Impact corridor or solution width | double | Sentry VI | Optional |
| sigma_imp | silver | Impact sigma value | double | Sentry VI | Also reads `sigma_vi` |
| ps | silver | Palermo scale | double | Sentry VI | Optional |
| ts | silver | Torino scale | double | Sentry VI | Optional |
| energy | silver | Impact energy | double | Sentry VI | Optional |
| vinf | silver | Incoming velocity | double | Sentry VI | Optional |
| raw_json | silver | Raw Sentry VI record JSON | string | Sentry VI | Traceability |

## silver_ingestion_events

| Column name | Layer | Description | Type expected | Source | Notes |
|---|---|---|---|---|---|
| source | silver | Bronze source name | string | Bronze metadata | All sources |
| ingested_at_utc | silver | UTC ingestion timestamp | string | Bronze metadata | Lineage |
| ingest_date | silver | Date partition from path | string | Bronze path | `YYYY-MM-DD` |
| object_id | silver | Ingested object ID when available | string | Bronze metadata | Optional |
| query_params_json | silver | Query parameters as JSON | string | Bronze metadata | Monitoring |
| api_signature_version | silver | API signature version | string | Bronze metadata | Optional |
| bronze_file_path | silver | Source bronze file path | string | Spark input path | Lineage |

## gold_neo_risk_features

| Column name | Layer | Description | Type expected | Source | Notes |
|---|---|---|---|---|---|
| object_key | gold | Stable object key | string | Silver SBDB, Sentry, CAD | Prefers SPK, then designation, then name |
| spkid, des, full_name, name | gold | Object identifiers and labels | string | Silver tables | Used for joining and reporting |
| orbit_class_code, orbit_class_name | gold | Orbit class fields | string | silver_sbdb_objects | Optional |
| neo, pha, sentry_flag | gold | Classification and Sentry presence flags | boolean | silver_sbdb_objects, silver_sentry_objects | `sentry_flag` is derived |
| h, diameter, albedo | gold | Physical fields | double | Silver SBDB or Sentry | Optional |
| e, a, q, i, om, w, ma, n, per, ad, moid, moid_ld | gold | Orbital fields | double | silver_sbdb_objects | Optional |
| condition_code, arc_length, n_obs_used, rms | gold | Orbit quality fields | string or numeric | silver_sbdb_objects | Used by quality proxies |
| min_close_approach_dist | gold | Minimum nominal CAD distance | double | silver_close_approaches | AU |
| min_close_approach_dist_min | gold | Minimum lower-bound CAD distance | double | silver_close_approaches | AU |
| max_close_approach_v_rel | gold | Maximum relative velocity | double | silver_close_approaches | km/s |
| next_close_approach_datetime | gold | Earliest available approach datetime string | string | silver_close_approaches | Approximate string ordering |
| close_approach_count | gold | Number of close approach records | long | silver_close_approaches | Per designation |
| sentry_ip, sentry_ps_cum, sentry_ps_max, sentry_ts_max, sentry_n_imp | gold | Sentry risk fields | double or integer | silver_sentry_objects | Optional |
| log_diameter | gold | Natural log of one plus diameter | double | Derived | Null if diameter missing |
| inverse_moid | gold | Bounded inverse MOID proxy | double | Derived | Safe for zero and nulls |
| inverse_min_distance | gold | Bounded inverse CAD distance proxy | double | Derived | Safe for zero and nulls |
| relative_velocity_score | gold | Simple velocity proxy in range 0 to 1 | double | Derived | Not calibrated risk |
| observation_quality_score | gold | Observation volume and RMS quality proxy | double | Derived | Range 0 to 1 |
| uncertainty_proxy_score | gold | Condition-code uncertainty proxy | double | Derived | Range 0 to 1 |
| size_proxy_score | gold | Diameter or magnitude size proxy | double | Derived | Range 0 to 1 |
| proximity_proxy_score | gold | Best available proximity proxy | double | Derived | Range 0 to 1 |
| sentry_presence_score | gold | Numeric Sentry presence feature | double | Derived | 1 when Sentry exists |
| feature_completeness_ratio | gold | Ratio of key non-null features | double | Derived | Range 0 to 1 |
| built_at_utc | gold | Build timestamp | string | ETL runtime | UTC |
| source_availability_json | gold | Availability of source silver tables | string | ETL runtime | JSON |
