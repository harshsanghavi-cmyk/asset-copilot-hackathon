"""Replacement-dataset ingestion/temporal checks; copied index and no LLM calls."""
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest

from backend.ingestion.loader import uid
from .provider import create_provider


class FinalDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path("dataset/test-data/dataset")
        source = Path("runtime/retrieval-test.sqlite")
        if not cls.root.is_dir() or not source.is_file():
            raise unittest.SkipTest("Build the separate replacement-dataset index first")
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temp.name) / "test.sqlite"
        with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as old, sqlite3.connect(cls.path) as new:
            old.backup(new)
        cls.provider = create_provider([cls.root], cls.path)
        cls.context = {"dataset_namespace": cls.provider.namespace, "reference_date": "2027-01-15"}
        cls.metadata = [json.loads(p.read_text()) for p in (cls.root / "assets").glob("*/metadata.json")]

    @classmethod
    def tearDownClass(cls):
        cls.provider.close()
        cls.temp.cleanup()

    def rows(self, name):
        for path in (self.root / "assets").glob("*/" + name + ".jsonl"):
            for line in path.read_text().splitlines():
                if line.strip():
                    yield json.loads(line)

    def test_replacement_inventory_rules_and_no_import_issues(self):
        counts = self.provider.overview()["counts"]
        self.assertEqual(counts["assets"], len(self.metadata))
        self.assertEqual(counts["assets"], 600)
        self.assertEqual(counts["inspections"], 125198)
        self.assertEqual(counts["maintenance"], 17415)
        self.assertEqual(counts["baseline_corrections"], 197)
        self.assertEqual(counts["issues"], 0)
        self.assertEqual({k: r["value_milli"] / 1000 for k, r in self.provider._rules.items()},
                         {"T200": 15, "T350": 20, "T500": 25})
        self.assertEqual(self.provider._rca_threshold("T500", "esp_pump", "2027-01-15")[0], 2)
        self.assertEqual(self.provider._rca_threshold("T500", "flowline", "2027-01-15")[0], 3)

    def test_all_typed_source_corrections_apply_and_keep_original(self):
        notes = [n for n in self.rows("context") if n["note_type"] == "data_correction"]
        self.assertEqual(len(notes), 3)
        for note in notes:
            result = self.provider.query({"collection": "inspections", "metric": "records",
                "filters": {"inspection_id": note["inspection_id"]}}, self.context)
            self.assertEqual(result["rows"][0][note["field"]], note["corrected_value"])
            original = self.provider.evidence(uid("ev_", note["inspection_id"]), self.context)
            self.assertEqual(original["original"][note["field"]], note["original_value"])
            self.assertIn(uid("ev_", note["note_id"]), result["rows"][0]["evidence_refs"])

    def test_type_history_drives_each_reading_not_current_type(self):
        result = self.provider.query({"metric": "temperature_series", "filters": {"asset_id": "WELL-0010"},
            "start": "2026-11-19", "end": "2026-11-26"}, self.context)
        values = {row["inspected_at"][:10]: (row["well_type"], row["threshold_c"]) for row in result["rows"]}
        self.assertEqual(values["2026-11-19"], ("T200", 15))
        self.assertEqual(values["2026-11-26"], ("T350", 20))
        for asset in self.metadata:
            for interval in asset.get("team_history", []):
                self.assertEqual(self.provider._timeline.at(asset["asset_id"], "team_id", interval["from"]), interval["team_id"])
        team = self.provider.query({"collection": "assets", "metric": "count", "filters": {"team_id": "TEAM-NW"}}, self.context)
        self.assertEqual(team["rows"][0]["count"], sum(m["team_id"] == "TEAM-NW" for m in self.metadata))

    def test_plugged_and_newer_restart_notes_have_explicit_status_sources(self):
        closed = [m for m in self.metadata if m.get("status") == "plugged_and_abandoned"]
        self.assertEqual(len(closed), 3)
        for metadata in closed:
            row = self.provider.query({"metric": "status", "filters": {"asset_id": metadata["asset_id"]}}, self.context)["rows"][0]
            self.assertFalse(row["producing"])
            self.assertEqual(row["status_source"], "decommissioned_metadata")
            self.assertIn(uid("ev_", metadata["asset_id"]), row["evidence_refs"])
            source = self.provider.evidence(uid("ev_", metadata["asset_id"]), self.context)
            self.assertEqual(source["original"]["status"], "plugged_and_abandoned")
        row = self.provider.query({"metric": "status", "filters": {"asset_id": "WELL-0026"}}, self.context)["rows"][0]
        self.assertTrue(row["producing"])
        self.assertFalse(row["status_confirmed"])
        self.assertEqual(row["status_source"], "operator_note")
        self.assertIn("unconfirmed", row["status_now"])
        disagreements = self.provider.query({"metric": "status", "filters": {"status_note_disagrees": True},
            "limit": 100}, self.context)
        self.assertTrue(disagreements["rows"])
        self.assertTrue(all(row["status_note_disagrees"] for row in disagreements["rows"]))

    def test_late_entries_sort_by_observation_date_and_cost_revisions_are_typed(self):
        late = [r for r in self.rows("inspections") if r.get("recorded_at")]
        self.assertEqual(len(late), 3)
        for record in late:
            path = self.root / "assets" / record["asset_id"] / "inspections.jsonl"
            original = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            expected = max(original, key=lambda r: (r["inspected_at"], r["inspection_id"]))
            current = self.provider.query({"metric": "status", "filters": {"asset_id": record["asset_id"]}}, self.context)["rows"][0]
            self.assertEqual(current["inspection_id"], expected["inspection_id"])
        jobs = [r for r in self.rows("maintenance") if r.get("cost_revision") or r.get("recorded_at")]
        for job in jobs:
            result = self.provider.query({"collection": "maintenance", "metric": "records",
                "filters": {"asset_id": job["asset_id"]}, "limit": 100}, self.context)
            row = next(r for r in result["rows"] if r["maintenance_id"] == job["maintenance_id"])
            self.assertEqual(row["cost_usd"], job["cost_usd"]["total"])
            self.assertEqual(row["recorded_at"], job.get("recorded_at"))
            if job.get("cost_revision"):
                self.assertEqual(row["original_cost_total_usd"], job["cost_revision"]["original_total"])
                self.assertEqual(row["cost_revision_reason"], job["cost_revision"]["reason"])


if __name__ == "__main__":
    unittest.main()
