"""Meaningful provider/ingestion boundary and full-sample regressions (no model calls)."""
import json
from collections import Counter
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest

from backend.ingestion import build_index
from backend.retrieval import create_provider, AuthoritySnapshot, RetrievalError


class ProviderContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "data"
        (self.root / "fleet/well-types").mkdir(parents=True)
        (self.root / "fleet/areas.json").write_text(json.dumps({"areas": [{"area_id": "AREA", "name": "Test area", "team_id": "TEAM"}], "teams": [{"team_id": "TEAM", "name": "Team", "lead_user_id": "USER"}]}))
        (self.root / "fleet/users.json").write_text(json.dumps({"users": [{"user_id": "USER", "name": "Operator", "role": "field_operator", "team_id": "TEAM"}]}))
        (self.root / "fleet/well-types/TYPE.md").write_text("# Type manual\n## Production temperature rule\nProducing when at least **15 °C above ambient**.\n## Maintenance escalation\nThree or more corrective events require analysis.\n")
        for asset, typ, temp in [("ASSET-A", "TYPE", 24.0), ("ASSET-B", "UNSUPPORTED", 24.0)]:
            folder = self.root / "assets" / asset
            folder.mkdir(parents=True)
            (folder / "metadata.json").write_text(json.dumps({"asset_id": asset, "name": asset, "well_type": typ, "area_id": "AREA", "team_id": "TEAM", "location": {"lat": 1, "lon": 2}, "recorded_status": "active", "equipment": []}))
            (folder / "inspections.jsonl").write_text(json.dumps({"inspection_id": "INS-" + asset, "asset_id": asset, "inspected_at": "2026-10-15T12:00:00Z", "inspector_user_id": "USER", "method": "manual", "ambient_temp_c": 19.9, "wellhead_temp_c": temp, "spill_detected": True, "spill_area_pct": 1.0, "spill_est_volume_bbl": 4.5, "notes": "Pump not moving"}) + "\n")
            for name in ("maintenance.jsonl", "context.jsonl", "regulatory-events.jsonl"):
                (folder / name).write_text("")
        self.path = Path(self.temp.name) / "index.sqlite"
        self.provider = create_provider([self.root], self.path, rebuild=True)
        self.context = {"dataset_namespace": self.provider.namespace, "reference_date": "2026-10-16", "user_id": "USER"}

    def tearDown(self):
        self.provider.close()
        self.temp.cleanup()

    def test_unknown_outside_presentation_page_remains_partial(self):
        result = self.provider.query({"collection": "assets", "metric": "status", "limit": 1}, self.context)
        self.assertEqual(len(result["rows"]), 1)
        self.assertEqual(result["coverage"]["unknown"], 1)
        self.assertEqual(result["coverage"]["status"], "partial")
        self.assertFalse(result["coverage"]["aggregation_input_truncated"])

    def test_canonical_correction_changes_effective_not_original(self):
        authority = AuthoritySnapshot(knowledge_revision=1, corrections=[{"inspection_id": "INS-ASSET-A", "field": "wellhead_temp_c", "value": 41.0, "status": "accepted", "author_user_id": "USER", "reason": "remeasured"}])
        plan = {"metric": "status", "filters": {"asset_id": "ASSET-A"}}
        original = self.provider.query(plan, self.context)
        corrected = self.provider.query(plan, self.context, authority)
        self.assertFalse(original["rows"][0]["producing"])
        self.assertTrue(corrected["rows"][0]["producing"])
        row = self.provider.records("inspections", asset_id="ASSET-A", authority=authority)["items"][0]
        self.assertEqual(row["original"]["wellhead_temp_c"], 24)
        self.assertEqual(row["effective"]["wellhead_temp_c"], 41)
        self.assertEqual(corrected["knowledge_revision"], 1)

    def test_ordinary_claim_does_not_change_measurement(self):
        claims = AuthoritySnapshot(knowledge_revision=1, shared_claims=[{"statement": "ASSET-A is producing", "subject_ids": ["ASSET-A"]}])
        row = self.provider.query({"metric": "status", "filters": {"asset_id": "ASSET-A"}}, self.context, claims)["rows"][0]
        self.assertFalse(row["producing"])

    def test_limits_scope_and_raw_sql_are_rejected(self):
        for plan in [{"sql": "SELECT * FROM users"}, {"metric": "records", "limit": 101}, {"filters": {"user_id": "someone"}}]:
            with self.assertRaises(RetrievalError):
                self.provider.query(plan, self.context)
        with self.assertRaises(RetrievalError):
            self.provider.query({}, dict(self.context, dataset_namespace="other"))
        with self.assertRaises(RetrievalError):
            self.provider.sources(limit=1000)
        with self.assertRaises(RetrievalError):
            self.provider.evidence("../../.env", self.context)

    def test_collection_count_semantics_do_not_substitute_inspection_rows(self):
        for collection, expected in (("assets", 2), ("users", 1), ("inspections", 2), ("maintenance", 0)):
            result = self.provider.query({"collection": collection, "metric": "count"}, self.context)
            self.assertEqual(result["rows"][0]["count"], expected, collection)
        with self.assertRaises(RetrievalError):
            self.provider.query({"collection": "users", "metric": "downtime_days"}, self.context)

    def test_indexed_citation_lookup_and_durable_lineage(self):
        result = self.provider.query({"metric": "spill_count", "group_by": ["area_id"]}, self.context)
        handle = result["rows"][0]["evidence_refs"][0]
        self.assertTrue(handle.startswith("result_"))
        info = self.provider.evidence(handle, self.context)
        self.assertEqual(info["source_kind"], "aggregate_lineage")
        member = info["members"]["rows"][0]
        source_handle = next(x for x in member["evidence_refs"] if x.startswith("ev_"))
        began = time.perf_counter()
        for _ in range(30):
            self.assertEqual(self.provider.evidence(source_handle, self.context)["record_id"], member["inspection_id"])
        self.assertLess(time.perf_counter() - began, 1)
        self.provider.close()
        self.provider = create_provider([self.root], self.path)
        self.assertEqual(self.provider.evidence(handle, self.context)["source_kind"], "aggregate_lineage")

    def test_same_source_import_is_idempotent(self):
        new_path = Path(self.temp.name) / "duplicate.sqlite"
        other = create_provider([self.root, self.root], new_path, rebuild=True)
        self.assertEqual(other.overview()["counts"]["inspections"], 2)
        self.assertEqual(other.overview()["counts"]["issues"], 0)
        other.close()

    def test_observations_exclude_future_rows_and_unobserved_month_bins(self):
        self.provider.close()
        source = self.root / "assets/ASSET-A/inspections.jsonl"
        future = json.loads(source.read_text())
        future.update(inspection_id="INS-ASSET-A-FUTURE", inspected_at="2026-11-05T12:00:00Z")
        source.write_text(source.read_text() + json.dumps(future) + "\n")
        self.provider = create_provider([self.root], self.path, rebuild=True)
        plan = {"metric": "spill_count", "group_by": ["area_id", "month"],
                "start": "2026-10-01", "end": "2026-12-31"}
        now = self.provider.query(plan, self.context)
        self.assertEqual([(r["month"], r["spill_count"]) for r in now["rows"]], [("2026-10", 2)])
        self.assertEqual(now["bounds"]["end"], "2026-10-16")
        self.assertEqual(now["requested_bounds"]["end"], "2026-12-31")
        self.assertTrue(any("future periods" in w for w in now["warnings"]))
        later = self.provider.query(plan, dict(self.context, reference_date="2026-11-30"))
        self.assertEqual([(r["month"], r["spill_count"]) for r in later["rows"]],
                         [("2026-10", 2), ("2026-11", 1)])
        with self.assertRaisesRegex(RetrievalError, "after the reference date"):
            self.provider.query({"metric": "temperature_series", "start": "2026-11-01"}, self.context)

    def test_cross_asset_correction_is_quarantined(self):
        self.provider.close()
        note = {"note_id": "NOTE-A", "asset_id": "ASSET-A", "author_user_id": "USER", "created_at": "2026-10-16T12:00:00Z", "note_type": "correction", "inspection_id": "INS-ASSET-B", "text": "Not a crude spill.", "valid_from": "2026-10-15", "valid_to": None}
        (self.root / "assets/ASSET-A/context.jsonl").write_text(json.dumps(note) + "\n")
        self.provider = create_provider([self.root], self.path, rebuild=True)
        self.assertEqual(self.provider.overview()["counts"]["baseline_corrections"], 0)
        self.assertTrue(any(r["kind"] == "correction_target" for r in self.provider.issues()["items"]))
        spills = self.provider.query({"metric": "spill_count", "filters": {"asset_id": "ASSET-B"}}, self.context)
        self.assertEqual(spills["rows"][0]["spill_count"], 1)

    def test_missing_required_spill_volume_is_unknown_not_complete(self):
        self.provider.close()
        source = self.root / "assets/ASSET-A/inspections.jsonl"
        row = json.loads(source.read_text()); row["spill_est_volume_bbl"] = None
        source.write_text(json.dumps(row) + "\n")
        self.provider = create_provider([self.root], self.path, rebuild=True)
        result = self.provider.query({"metric": "spill_volume_bbl", "filters": {"asset_id": "ASSET-A"}}, self.context)
        self.assertIsNone(result["rows"][0]["spill_volume_bbl"])
        self.assertEqual(result["coverage"]["unknown"], 1)
        self.assertEqual(result["coverage"]["status"], "partial")


class FullSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source_path = Path("runtime/retrieval.sqlite")
        if not source_path.exists():
            source_path = Path(__file__).parent / ".cache/dataset.sqlite"
        if not source_path.exists():
            raise unittest.SkipTest("Build sample index before running full-data checks")
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temp.name) / "sample.sqlite"
        # Queries persist result manifests; never write them beside the shared
        # serving index merely by running a regression test.
        with sqlite3.connect(source_path.resolve().as_uri() + "?mode=ro", uri=True) as source, sqlite3.connect(cls.path) as target:
            source.backup(target)
        cls.provider = create_provider([Path("dataset/sample-data")], cls.path)
        cls.context = {"dataset_namespace": cls.provider.namespace, "reference_date": "2026-10-16"}

    @classmethod
    def tearDownClass(cls):
        cls.provider.close()
        cls.temp.cleanup()

    def test_original_source_cardinalities_and_links(self):
        counts = self.provider.overview()["counts"]
        for collection, expected in {"assets": 200, "inspections": 39567, "maintenance": 5665, "regulatory_events": 90, "context_notes": 141, "baseline_corrections": 56, "sources": 2516, "issues": 0}.items():
            self.assertEqual(counts[collection], expected, collection)

    def test_exact_downtime_and_spill_corrections(self):
        downtime = self.provider.query({"metric": "downtime_days", "filters": {"asset_id": "WELL-0001"}, "start": "2025-01-01", "end": "2025-12-31"}, self.context)
        self.assertEqual(downtime["rows"][0]["downtime_days"], 21)
        spills = self.provider.query({"metric": "spill_count", "filters": {"asset_id": "WELL-0001"}}, self.context)
        self.assertEqual(spills["rows"][0]["spill_count"], 6)
        volume = self.provider.query({"metric": "spill_volume_bbl", "filters": {"asset_id": "WELL-0001"}}, self.context)
        self.assertEqual(volume["rows"][0]["spill_volume_bbl"], 15.1)

    def test_complete_containment_and_unknowns(self):
        result = self.provider.query({"metric": "containment", "filters": {"area_id": "SW-24"}, "start": "2026-07-18", "end": "2026-10-16"}, self.context)
        late = {r["asset_id"]: r["containment_hours"] for r in result["rows"] if r["containment_hours"] and r["containment_hours"] > 4}
        self.assertEqual(late, {"WELL-0082": 7.1, "WELL-0100": 8.1})
        self.assertEqual(result["coverage"]["matching"], 10)
        self.assertEqual(result["coverage"]["unknown"], 0)

    def test_scoped_rca_override_and_temperature_correction(self):
        authority = AuthoritySnapshot(knowledge_revision=2, corrections=[{"inspection_id": "INS-0164-0205", "field": "wellhead_temp_c", "value": 41.0}], rule_overrides=[{"well_type": "T350", "equipment_kind": "pump_jack", "threshold": 2, "rule_id": "memory:rule", "status": "accepted"}])
        result = self.provider.query({"metric": "rca", "collection": "maintenance", "filters": {"area_id": "NE-07", "equipment_kind": "pump_jack"}}, self.context, authority)
        required = {r["asset_id"] for r in result["rows"] if r["rca_required"]}
        self.assertEqual(required, {"WELL-0108", "WELL-0120", "WELL-0121", "WELL-0138"})
        status = self.provider.query({"metric": "status", "filters": {"asset_id": "WELL-0164"}}, self.context, authority)
        self.assertEqual(status["rows"][0]["delta_c"], 21.1)
        self.assertTrue(status["rows"][0]["producing"])
        result = self.provider.query({"metric": "rca", "collection": "maintenance", "group_by": ["asset_id"], "filters": {"area_id": "NE-07", "equipment_kind": "pump_jack"}}, self.context, authority)
        self.assertEqual({r["asset_id"] for r in result["rows"] if r["rca_required"]}, required)

    def test_lexical_search_preserves_spans_and_caps(self):
        search = self.provider.search("spill response containment", self.context, kind="sop", budget=2000)
        self.assertLessEqual(len(search["items"]), 8)
        self.assertEqual(search["coverage"]["exhaustive_factual_scope"], False)
        for item in search["items"]:
            source = Path("dataset/sample-data") / item["path"]
            with source.open("rb") as f:
                f.seek(item["byte_start"]); text = f.read(item["byte_end"] - item["byte_start"]).decode()
            self.assertEqual(text, item["text"])

    def test_requested_temperature_and_map_columns_are_bindable(self):
        series = self.provider.query({"metric": "temperature_series", "filters": {"asset_id": "WELL-0001"}, "start": "2026-07-23", "end": "2026-10-16"}, self.context)
        columns = {c["key"] for c in series["columns"]}
        self.assertTrue({"inspected_at", "wellhead_temp_c", "ambient_temp_c", "producing"} <= columns)
        self.assertEqual(len(series["rows"]), 13)
        pins = self.provider.query({"metric": "spills", "filters": {"area_id": "NE-08"}, "start": "2026-07-18", "end": "2026-10-16"}, self.context)
        self.assertTrue({"asset_id", "lat", "lon", "spill_est_volume_bbl"} <= {c["key"] for c in pins["columns"]})
        self.assertEqual({r["asset_id"] for r in pins["rows"]}, {"WELL-0151", "WELL-0165", "WELL-0175", "WELL-0186"})

    def test_rankings_heatmap_and_costs_use_complete_population(self):
        ranked = self.provider.query({"metric": "downtime_days", "filters": {"area_id": "NE-07"}, "start": "2026-06-16", "end": "2026-10-16", "limit": 3}, self.context)
        self.assertEqual({r["asset_id"]: r["downtime_days"] for r in ranked["rows"]}, {"WELL-0121": 49, "WELL-0138": 42, "WELL-0107": 42})
        self.assertFalse(ranked["coverage"]["aggregation_input_truncated"])
        costs = self.provider.query({"collection": "maintenance", "metric": "maintenance_cost_usd", "filters": {"asset_ids": ["WELL-0121", "WELL-0138", "WELL-0107"]}, "start": "2026-01-01", "end": "2026-10-16"}, self.context)
        self.assertEqual({r["asset_id"]: r["maintenance_cost_usd"] for r in costs["rows"]}, {"WELL-0121": 25794, "WELL-0138": 46942, "WELL-0107": 5176})
        areas = self.provider.query({"metric": "spill_count", "group_by": ["area_id"], "start": "2026-01-01", "end": "2026-10-16"}, self.context)
        self.assertEqual({r["area_id"]: r["spill_count"] for r in areas["rows"]}, {"SW-23": 35, "SW-24": 43, "NE-07": 37, "NE-08": 26})

    def test_zero_bins_breach_filter_and_user_report_query(self):
        bins = self.provider.query({"metric": "spill_count", "group_by": ["area_id", "month"], "start": "2026-01-01", "end": "2026-10-16"}, self.context)
        self.assertEqual(bins["total_rows"], 40)
        self.assertEqual({r["month"] for r in bins["rows"] if r["area_id"] == "NE-08" and r["spill_count"] == 0}, {"2026-08", "2026-10"})
        breaches = self.provider.query({"metric": "containment", "filters": {"area_id": "SW-24"}, "start": "2026-07-18", "only_breaches": True}, self.context)
        self.assertEqual({r["asset_id"] for r in breaches["rows"]}, {"WELL-0082", "WELL-0100"})
        self.assertEqual(breaches["coverage"]["matching"], 10)
        search = self.provider.search("find assets whose maintaince report has found crude oil on the pad", self.context, kind="report")
        trace = self.provider.trace(search["trace_id"])
        self.assertEqual(trace["operation"], "lexical_search")
        self.assertIn("chunk_fts", trace["safe_sql"])
        self.assertNotIn("production_threshold", trace["safe_sql"])
        self.assertTrue(search["items"])
        self.assertTrue(all(r["asset_id"] and "/maintenance-reports/" in r["path"] and r["excerpt"] for r in search["items"]))
        self.assertFalse(search["coverage"]["exhaustive_factual_scope"])

    def test_calendar_year_observations_stop_at_reference_date(self):
        result = self.provider.query({"metric": "spill_count", "group_by": ["area_id", "month"],
                                      "start": "2026-01-01", "end": "2026-12-31"}, self.context)
        self.assertEqual(result["total_rows"], 40)
        self.assertEqual(max(row["month"] for row in result["rows"]), "2026-10")
        self.assertEqual(sum(row["spill_count"] for row in result["rows"]), 141)
        self.assertEqual(result["coverage"]["matching"], 141)

    def test_dense_heatmap_cells_match_independent_raw_record_oracle(self):
        root = Path("dataset/sample-data/assets")
        excluded = {note["inspection_id"] for path in root.glob("*/context.jsonl")
                    for line in path.read_text().splitlines() if line.strip()
                    if (note := json.loads(line))["note_type"] == "correction"}
        counts = Counter()
        area_ids = set()
        for path in root.glob("*/metadata.json"):
            metadata = json.loads(path.read_text())
            area_ids.add(metadata["area_id"])
            for line in path.with_name("inspections.jsonl").read_text().splitlines():
                row = json.loads(line)
                if ("2026-01-01" <= row["inspected_at"][:10] <= self.context["reference_date"]
                        and row["spill_detected"] and row["inspection_id"] not in excluded):
                    counts[(metadata["area_id"], row["inspected_at"][:7])] += 1
        months = ["2026-%02d" % month for month in range(1, 11)]
        expected = {(area, month): counts[(area, month)] for area in area_ids for month in months}
        result = self.provider.query({"metric": "spill_count", "group_by": ["area_id", "month"],
                                      "start": "2026-01-01", "end": "2026-12-31"}, self.context)
        self.assertEqual({(r["area_id"], r["month"]): r["spill_count"] for r in result["rows"]}, expected)

    def test_series_bounds_and_original_note_conflicts_remain_explicit(self):
        plan = {"metric": "temperature_series", "filters": {"asset_id": "WELL-0001"},
                "start": "2026-07-23", "end": "2026-10-16"}
        correct = self.provider.query(plan, self.context)
        self.assertEqual(len(correct["rows"]), 13)
        self.assertEqual(min(row["inspected_at"][:10] for row in correct["rows"]), "2026-07-23")
        self.assertEqual({row["inspected_at"][:10] for row in correct["rows"] if not row["producing"]},
                         {"2026-10-08", "2026-10-15"})
        later_start = self.provider.query(dict(plan, start="2026-07-24"), self.context)
        self.assertEqual(len(later_start["rows"]), 12)  # Do not silently pad an incorrect plan.
        notes = self.provider.query({"collection": "context_notes", "metric": "records",
                                     "filters": {"asset_id": "WELL-0101"}}, self.context)
        claims = {row["note_id"]: row for row in notes["rows"]}
        self.assertNotEqual(claims["CTX-0101-002"]["note_type"], "correction")
        self.assertNotEqual(claims["CTX-0101-003"]["note_type"], "correction")
        spill = self.provider.query({"metric": "spills", "filters": {"inspection_id": "INS-0101-0197"}}, self.context)
        self.assertTrue(spill["rows"][0]["spill_detected"])
        self.assertEqual(spill["rows"][0]["spill_est_volume_bbl"], 1.0)

    def test_repair_claims_are_available_as_typed_record_fields(self):
        result = self.provider.query({"collection": "maintenance", "metric": "records",
                                      "filters": {"asset_id": "WELL-0170"}, "end": "2026-12-31", "limit": 1}, self.context)
        row = result["rows"][0]
        self.assertEqual(row["maintenance_id"], "MNT-0170-031")
        self.assertEqual(row["issue"], "Walking beam bearing wear")
        self.assertTrue(row["action_taken"])
        self.assertEqual(row["completion_state"], "planned/in_progress")
        self.assertEqual(row["report_file"], "maintenance-reports/MNT-0170-031.md")
        self.assertEqual(row["triggered_by_inspection_id"], "INS-0170-0202")
        self.assertEqual(result["bounds"]["end"], "2026-12-31")
        self.assertNotIn("requested_bounds", result)  # Planning is not observed-fact clipping.
        self.assertTrue({"issue", "action_taken"} <= {column["key"] for column in result["columns"]})

    def test_status_context_and_cross_user_effective_snapshot_invariants(self):
        latest = self.provider.query({"metric": "status", "filters": {"asset_id": "WELL-0001"}}, self.context)["rows"][0]
        self.assertEqual((latest["inspection_id"], latest["delta_c"], latest["producing"], latest["inspector_name"]),
                         ("INS-0001-0203", 3.2, False, "Ryan Brooks"))
        notes = self.provider.query({"collection": "context_notes", "metric": "records",
                                     "filters": {"asset_id": "WELL-0001"}}, self.context)
        planned = next(row for row in notes["rows"] if row["note_id"] == "CTX-0001-003")
        self.assertEqual(planned["author_user_id"], "U-102")
        self.assertEqual(planned["valid_from"], "2026-10-07")
        self.assertIn("planned rod string replacement", planned["text"])
        down = self.provider.query({"metric": "status", "filters": {"area_id": "NE-08", "producing": False}}, self.context)
        self.assertEqual({row["asset_id"] for row in down["rows"]},
                         {"WELL-0164", "WELL-0170", "WELL-0172", "WELL-0175"})
        repair = self.provider.query({"collection": "maintenance", "metric": "records",
                                      "filters": {"asset_id": "WELL-0172"}, "limit": 1}, self.context)["rows"][0]
        self.assertEqual(repair["issue"], "Flowline corrosion pinhole leak")
        authority = AuthoritySnapshot(knowledge_revision=2, corrections=[
            {"inspection_id": "INS-0164-0205", "field": "wellhead_temp_c", "value": 41.0,
             "author_user_id": "U-201", "status": "accepted"}])
        for user in ("U-202", "U-401"):
            corrected = self.provider.query({"metric": "status", "filters": {"asset_id": "WELL-0164"}},
                                             dict(self.context, user_id=user), authority)
            self.assertTrue(corrected["rows"][0]["producing"])
            self.assertEqual(corrected["rows"][0]["wellhead_temp_c"], 41)
            self.assertEqual(corrected["knowledge_revision"], 2)
        original = self.provider.query({"metric": "status", "filters": {"asset_id": "WELL-0164"}}, self.context)
        self.assertEqual(original["rows"][0]["wellhead_temp_c"], 24)
        claims = AuthoritySnapshot(knowledge_revision=3, shared_claims=[
            {"subject_ids": ["WELL-0175"], "statement": "Running fine", "author_user_id": "U-204"}])
        disputed = self.provider.query({"metric": "status", "filters": {"asset_id": "WELL-0175"}}, self.context, claims)
        self.assertFalse(disputed["rows"][0]["producing"])
        self.assertEqual(disputed["rows"][0]["delta_c"], 0.4)

    def test_compliance_deadlines_and_corrected_classification(self):
        result = self.provider.query({"metric": "compliance", "filters": {"asset_id": "WELL-0001"}, "start": "2025-10-16", "only_breaches": True}, self.context)
        rows = {r["protocol_id"]: r for r in result["rows"]}
        self.assertEqual(set(rows), {"SR-01", "SR-02", "SR-03", "RC-04"})
        self.assertEqual(rows["SR-01"]["observed_hours"], 41)
        self.assertEqual(rows["SR-02"]["observed_hours"], 7)
        self.assertEqual(rows["SR-03"]["due_date"], "2026-08-10")
        self.assertEqual(rows["RC-04"]["due_date"], "2026-07-30")
        self.assertEqual(rows["RC-04"]["fine_usd"], 5000)
        authority = AuthoritySnapshot(knowledge_revision=1, corrections=[{"inspection_id": "INS-0151-0201", "field": "spill_est_volume_bbl", "value": 5.4}])
        corrected = self.provider.query({"metric": "compliance", "filters": {"asset_id": "WELL-0151"}, "start": "2026-07-18"}, self.context, authority)
        rows = {r["protocol_id"]: r for r in corrected["rows"]}
        self.assertEqual(rows["SR-01"]["spill_class"], "reportable")
        self.assertEqual(rows["SR-01"]["assessment"], "possible_breach_missing_record")
        self.assertEqual(rows["SR-01"]["due_at"], "2026-09-25T15:30:00+00:00")
        self.assertEqual(rows["SR-03"]["due_date"], "2026-11-23")
        self.assertEqual(rows["SR-03"]["assessment"], "pending_not_due")

    def test_actual_walkthrough_values_are_source_backed(self):
        result = self.provider.walkthrough("WELL-0001", self.context)
        self.assertEqual(result["linked_report"]["declared_report_file"], "maintenance-reports/MNT-0001-june-2026-flowline-spill.md")
        self.assertEqual(result["extracted_assertion"]["value"], "7")
        self.assertIn("contained about 7 hours", result["extracted_assertion"]["excerpt"])
        self.assertTrue(result["extracted_assertion"]["excerpt_verified_in_preview"])
        self.assertIsNotNone(result["fts_index_row"]["rowid"])
        self.assertEqual(result["methods"]["Gemma_query_expansion"], "not_run")


if __name__ == "__main__":
    unittest.main()
