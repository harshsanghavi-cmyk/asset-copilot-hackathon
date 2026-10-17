"""Pure history/OPS-3 semantics; no runtime/model calls."""
import unittest
from .temporal import AssetTimeline


class AssetTimelineTests(unittest.TestCase):
    def note(self, identity, at, text):
        return {"note_id": identity, "asset_id": "W", "created_at": at,
                "author_user_id": "operator", "text": text}

    def test_type_and_team_intervals_use_event_date(self):
        timeline = AssetTimeline({"W": {"well_type": "NEW", "team_id": "NEW-TEAM",
            "type_history": [{"well_type": "OLD", "from": "2020-01-01", "to": "2026-11-19"},
                             {"well_type": "NEW", "from": "2026-11-20", "to": None}],
            "team_history": [{"team_id": "OLD-TEAM", "from": "2020-01-01", "to": "2026-11-30"},
                             {"team_id": "NEW-TEAM", "from": "2026-12-01", "to": None}]}}, [])
        self.assertEqual(timeline.at("W", "well_type", "2026-11-19T23:59:00Z"), "OLD")
        self.assertEqual(timeline.at("W", "well_type", "2026-11-20"), "NEW")
        self.assertEqual(timeline.at("W", "team_id", "2026-11-30"), "OLD-TEAM")
        self.assertEqual(timeline.at("W", "team_id", "2026-12-01"), "NEW-TEAM")

    def test_newer_shutin_overrides_inspection_only_with_applicable_ops(self):
        notes = [self.note("stop", "2027-01-15T10:00:00Z", "Shut in W at the wellhead.")]
        timeline = AssetTimeline({"W": {}}, notes, "operations-source", "2026-10-01")
        state = timeline.status("W", "2027-01-14T10:00:00Z", True, "2027-01-15")
        self.assertFalse(state["producing"])
        self.assertTrue(state["status_confirmed"])
        self.assertTrue(state["status_note_disagrees"])
        original = AssetTimeline({"W": {}}, notes)
        self.assertTrue(original.status("W", "2027-01-14T10:00:00Z", True, "2027-01-15")["producing"])

    def test_restart_is_unconfirmed_until_later_inspection(self):
        notes = [self.note("restart", "2027-01-15T10:00:00Z", "Brought W back online after repair."),
                 self.note("gas", "2027-01-15T12:00:00Z", "Gas odor at W."),
                 self.note("future", "2027-01-16T10:00:00Z", "Shut in W.")]
        timeline = AssetTimeline({"W": {}}, notes, "operations-source")
        state = timeline.status("W", "2027-01-14T10:00:00Z", False, "2027-01-15")
        self.assertTrue(state["producing"])
        self.assertFalse(state["status_confirmed"])
        self.assertEqual(state["latest_status_note_id"], "restart")
        confirmed = timeline.status("W", "2027-01-15T13:00:00Z", True, "2027-01-15")
        self.assertTrue(confirmed["status_confirmed"])
        self.assertEqual(confirmed["status_source"], "inspection")

    def test_plugged_well_is_not_producing_after_closure(self):
        metadata = {"W": {"status": "plugged_and_abandoned", "decommissioned_on": "2026-12-10"}}
        timeline = AssetTimeline(metadata, [])
        self.assertTrue(timeline.status("W", "2026-12-01", True, "2026-12-09")["producing"])
        state = timeline.status("W", "2026-12-01", True, "2026-12-10")
        self.assertFalse(state["producing"])
        self.assertEqual(state["status_source"], "decommissioned_metadata")


if __name__ == "__main__":
    unittest.main()
