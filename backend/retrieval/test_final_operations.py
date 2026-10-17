"""Independent raw-file oracles and source-grounded final-field operations; no API calls."""
import collections
import datetime as dt
import json
from pathlib import Path
import re
import sqlite3
import statistics
import tempfile
import unittest

from .provider import SQLiteRetrievalProvider
from .contracts import AuthoritySnapshot, RetrievalError
from .final_operations import gas_note, bypass_action, replacement_override, section, instant


class LanguageBoundaryTests(unittest.TestCase):
    def test_positive_and_negative_operator_events(self):
        for text in ("Crew smelled gas.","Rotten-egg smell on arrival.","H2S monitor alarmed."):
            self.assertTrue(gas_note(text))
        for text in ("No gas odor at pad.","Crew did not smell gas.","No H2S monitor alarmed."):
            self.assertFalse(gas_note(text))
        self.assertEqual(bypass_action("Put the bypass in yesterday."),"in")
        self.assertEqual(bypass_action("Took the bypass out."),"out")
        self.assertIsNone(bypass_action("Bypass not installed; will install tomorrow."))
        self.assertIsNone(bypass_action("Bypass not removed yet."))

    def test_direct_update_hearsay_and_conflict_authority(self):
        direct=dict(statement="The recalled pump was swapped yesterday; work order not in system yet. Count it as replaced from now on.",status="attributed",author="USER")
        self.assertTrue(replacement_override(direct))
        self.assertFalse(replacement_override(dict(direct,statement="A colleague told me the pump was swapped. Take it off the recall list.")))
        self.assertFalse(replacement_override(dict(direct,qualifier="hearsay")))
        self.assertFalse(replacement_override(dict(direct,conflicts=["other_claim"])))
        self.assertFalse(replacement_override(dict(direct,statement="The pump was not replaced. Count it as replaced.")))

    def test_passive_direct_unconfirmed_public_fact_is_operational_not_verified(self):
        from backend.memory.store import MemoryStore
        fact=dict(id="claim",scope="shared",kind="observation",subject_ids=["ASSET-A"],
                  statement="The recalled pump was swapped out yesterday, pending formal system documentation, and should be counted as replaced from now on.",
                  source_quote="The recalled pump was swapped out yesterday. The work order isn't in the system yet. Please count it as replaced from now on.",
                  author_user_id="supervisor",valid_from="2027-01-15",valid_to=None,status="unconfirmed",conflict_ids=[],revision=1,data={"qualifier":"attributed"})
        public=MemoryStore.public_fact(None,fact)
        public["firsthand"]=False  # Reproduce the legacy passive-voice projection without requiring that upstream limitation.
        public["attribution_basis"]="attributed"
        self.assertTrue(replacement_override(public))
        hearsay=dict(fact,source_quote="A colleague told me the recalled pump was swapped. Take it off the recall list.")
        public_hearsay=MemoryStore.public_fact(None,hearsay)
        self.assertEqual(public_hearsay["qualifier"],"hearsay")
        self.assertFalse(replacement_override(public_hearsay))  # Even if the summary omitted the hearsay wording.
        self.assertFalse(replacement_override(dict(public,statement="The recalled pump may have been replaced.")))
        self.assertFalse(replacement_override(dict(public,statement="The recalled pump was replaced.")))
        self.assertFalse(replacement_override(dict(public,status="withdrawn")))

    def test_shutdown_paraphrase_is_current_event_but_plans_and_negation_are_not(self):
        from .temporal import AssetTimeline
        for text in ("Found a stuffing box leak, shut the well in.","Repair crew on the pad, shut the well in for them."):
            note=dict(note_id="event",asset_id="ASSET-A",created_at="2027-01-14T15:35:00Z",author_user_id="operator",text=text)
            state=AssetTimeline({"ASSET-A":{}},[note],"ops").status("ASSET-A","2027-01-14T11:45:00Z",True,"2027-01-15")
            self.assertFalse(state["producing"])
            self.assertEqual(state["latest_status_note_id"],"event")
            self.assertEqual(state["status_source"],"operator_note")
        for text in ("Did not shut the well in.","Will shut the well in tomorrow.","We didn't shut the well in.","Workover rig delayed by weather; restart pushed back about a week."):
            note=dict(note_id="not-event",asset_id="ASSET-A",created_at="2027-01-14T15:35:00Z",author_user_id="operator",text=text)
            state=AssetTimeline({"ASSET-A":{}},[note],"ops").status("ASSET-A","2027-01-14T11:45:00Z",True,"2027-01-15")
            self.assertTrue(state["producing"])
            self.assertIsNone(state["latest_status_note_id"])

    def test_section_scope_and_affirmative_lab_sentence(self):
        text="## Spill clean-up and waste\n- Soil samples sent to the lab.\n## Other\nNo results."
        body=section(text,"Spill clean-up and waste")
        pattern=r"(?:^\s*(?:[-*]\s+)?|[.!?]\s+)Soil samples sent to the lab\.(?:\s|$)"
        self.assertTrue(re.search(pattern,body,re.M))
        for text in ('No Soil samples sent to the lab.', 'The report did not contain "Soil samples sent to the lab."', '- Soil samples not sent to the lab.'):
            self.assertFalse(re.search(pattern,text,re.M))


class FullFieldOperationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path("dataset/test-data/dataset")
        if not Path("runtime/retrieval-test.sqlite").is_file():raise unittest.SkipTest("Final dataset index unavailable")
        cls.temp=tempfile.TemporaryDirectory();path=Path(cls.temp.name)/"index.sqlite"
        with sqlite3.connect('file:runtime/retrieval-test.sqlite?mode=ro',uri=True) as source,sqlite3.connect(path) as target:source.backup(target)
        cls.p=SQLiteRetrievalProvider(path);cls.ctx=dict(reference_date="2027-01-15")
        cls.notes=cls.read_all("context");cls.jobs=cls.read_all("maintenance");cls.inspections=cls.read_all("inspections")
        cls.assets={json.loads(p.read_text())["asset_id"]:json.loads(p.read_text()) for p in (cls.root/"assets").glob("*/metadata.json")}
        cls.effective={i["inspection_id"]:dict(i) for i in cls.inspections}
        for n in cls.notes:
            if n["note_type"]=="correction" and re.search(r"not a (?:crude )?spill|no crude",n["text"],re.I):cls.effective[n["inspection_id"]]["spill_detected"]=False
            if n["note_type"]=="data_correction":cls.effective[n["inspection_id"]][n["field"]]=n["corrected_value"]

    @classmethod
    def read_all(cls,name):
        return [json.loads(line) for p in (cls.root/"assets").glob("*/"+name+".jsonl") for line in p.read_text().splitlines() if line.strip()]

    @classmethod
    def tearDownClass(cls):cls.p.close();cls.temp.cleanup()

    def query(self,metric,**kwargs):return self.p.query(dict(metric=metric,limit=100,**kwargs),self.ctx)

    def report(self,job):return (self.root/"assets"/job["asset_id"]/job["report_file"]).read_text() if job.get("report_file") else ""

    def test_gas_every_note_earliest_response_and_revision_deadline(self):
        # Independent source population: none of this dataset's positive notes uses a negated gas phrase.
        notes=[n for n in self.notes if n["note_type"]=="operator_note" and n["created_at"]>="2026-11-01" and re.search(r"smelled gas|rotten.egg smell|gas odor|H2S monitor alarmed",n["text"],re.I)]
        result=self.query("gas_response",start="2026-11-01")
        rows={r["note_id"]:r for r in result["rows"]}
        self.assertEqual(set(rows),{n["note_id"] for n in notes})
        for n in notes:
            options=[(j["started_at"],j["maintenance_id"]) for j in self.jobs if j["asset_id"]==n["asset_id"] and n["created_at"]<j["started_at"]<"2027-01-16"]
            options += [(i["inspected_at"],i["inspection_id"]) for i in self.inspections if i["asset_id"]==n["asset_id"] and i["method"]=="manual" and n["created_at"]<i["inspected_at"]<"2027-01-16"]
            response=min(options,default=None);row=rows[n["note_id"]]
            limit=12 if n["created_at"]>="2027-01-01" else 24
            self.assertEqual(row["deadline_hours"],limit)
            self.assertEqual(row["response_id"],response[1] if response else None)
            if response:self.assertAlmostEqual(row["hours_to_response"],(instant(response[0])-instant(n["created_at"])).total_seconds()/3600)
            self.assertIsNone(row["h2s_ppm"])
        paged=self.query("gas_response",start="2026-11-01",offset=25)
        self.assertEqual(paged["summary"],result["summary"])
        self.assertFalse(paged["coverage"]["aggregation_input_truncated"])

    def test_bypass_pairing_current_and_moc_extension(self):
        result=self.query("bypass_intervals");rows=result["rows"]
        positive=[n for n in self.notes if n["note_type"]=="operator_note" and re.search(r"bypass in place|bypass installed|put the bypass in",n["text"],re.I)]
        self.assertEqual(len(rows),len(positive))
        for row in rows:
            starts=[n for n in positive if n["asset_id"]==row["asset_id"]]
            self.assertIn(row["bypass_in"],{n["created_at"] for n in starts})
            if row["extension_id"]:
                memo=(self.root/"fleet/sops"/(row["extension_id"].lower()+".md")).read_text()
                self.assertIn(row["approval_id"],memo);self.assertIn(row["asset_id"],memo)
                self.assertEqual(row["approval_valid_until"],"2027-02-28")
            if row["assessment"]=="expired":self.assertGreater((row["bypass_out"] or self.ctx["reference_date"])[:10],row["approval_valid_until"])
        self.assertEqual(result["summary"]["current_in_place"],sum(r["bypass_out"] is None for r in rows))

    def test_recall_current_installations_lots_costs_and_claim_counts(self):
        notice=(self.root/"fleet/sops/supplier-recall-notice-2026-12-01.md").read_text()
        lots=set(re.findall(r"^- (LOT-[\w-]+)",notice,re.M));latest={}
        for j in self.jobs:
            if j["equipment_kind"]!="downhole_pump" or not j["completed_at"] or j["completed_at"]>="2027-01-16":continue
            line=re.search(r"^\*\*Parts installed:\*\* (.+)",self.report(j),re.M)
            if not line:continue
            lot=re.search(r"lot (LOT-[\w-]+)",line[1]);serial=re.search(r"serial (SN-[\w-]+)",line[1])
            if not lot or not serial:continue
            old=latest.get(j["asset_id"])
            if not old or j["completed_at"]>old[0]["completed_at"]:latest[j["asset_id"]]=(j,lot[1],serial[1])
        expected={aid:v for aid,v in latest.items() if v[1] in lots and self.assets[aid]["well_type"]!="T500"}
        result=self.query("recall_inventory");actual={r["asset_id"]:r for r in result["rows"]}
        self.assertEqual(set(actual),set(expected))
        for aid,(j,lot,serial) in expected.items():
            self.assertEqual((actual[aid]["installation_job"],actual[aid]["lot"],actual[aid]["serial"]),(j["maintenance_id"],lot,serial))
            self.assertEqual(actual[aid]["installation_cost_usd"],j["cost_usd"]["total"])
        aid=next(iter(actual));claim=dict(id="fact_test",subject_ids=[aid],statement="Pump was swapped yesterday; work order missing. Count it as replaced from now on.",author="test_supervisor",valid_from="2027-01-14",status="unconfirmed",qualifier="attributed",firsthand=False,attribution_basis="attributed")
        claimed=self.p.query(dict(metric="recall_inventory",limit=100),self.ctx,AuthoritySnapshot(knowledge_revision=1,shared_claims=[claim]))
        self.assertEqual(claimed["summary"]["documented_in_ground"],len(expected))
        self.assertEqual(claimed["summary"]["operational_in_ground"],len(expected)-1)
        self.assertEqual(claimed["total_rows"],len(expected)-1)
        self.assertNotIn(aid,{r["asset_id"] for r in claimed["rows"]})
        excluded=claimed["summary"]["excluded_replacement_updates"]
        self.assertEqual(len(excluded),1)
        self.assertEqual(excluded[0]["asset_id"],aid)
        self.assertTrue(excluded[0]["documented_in_ground"])
        self.assertFalse(excluded[0]["work_order_verified"])
        self.assertEqual(excluded[0]["replacement_claims"][0]["status"],"unconfirmed")
        claim["statement"]="Another supervisor told me the pump was swapped. Take it off recall list."
        hearsay=self.p.query(dict(metric="recall_inventory",limit=100),self.ctx,AuthoritySnapshot(shared_claims=[claim]))
        self.assertEqual(hearsay["summary"]["operational_in_ground"],len(expected))
        self.assertIn(aid,{r["asset_id"] for r in hearsay["rows"]})
        self.assertFalse(hearsay["summary"]["excluded_replacement_updates"])

    def test_letter_exact_population_and_cleanup_section_evidence(self):
        letter=(self.root/"fleet/sops/regulator-letter-2026-11-20.md").read_text()
        areas=json.loads((self.root/"fleet/areas.json").read_text())["areas"]
        ids={a["area_id"] for a in areas if a["name"] in letter}
        expected={i["inspection_id"]:i for i in self.effective.values() if self.assets[i["asset_id"]]["area_id"] in ids and i["inspected_at"]>="2026-06-01" and i["spill_detected"] and (i["spill_est_volume_bbl"] is None or i["spill_est_volume_bbl"]>=5)}
        result=self.query("letter_compliance")
        self.assertEqual({r["inspection_id"] for r in result["rows"]},set(expected))
        states=[]
        for row in result["rows"]:
            jobs=[j for j in self.jobs if j.get("triggered_by_inspection_id")==row["inspection_id"]]
            bodies=[section(self.report(j),"Spill clean-up and waste") for j in jobs]
            compliant=any("- Soil samples sent to the lab." in b for b in bodies)
            self.assertEqual(row["assessment"],"compliant" if compliant else "not_compliant")
            states.append(compliant)
        self.assertIn(True,states);self.assertIn(False,states)

    def test_freeze_effective_producing_population_and_manual_window(self):
        result=self.query("freeze_checks",start="2026-12-01",end="2026-12-31")
        expected=[]
        for i in self.effective.values():
            if not "2026-12-01"<=i["inspected_at"]<"2027-01-01" or i["ambient_temp_c"]>-5:continue
            threshold={"T200":15,"T350":20,"T500":25}[self.assets[i["asset_id"]]["well_type"]]
            if i["wellhead_temp_c"]-i["ambient_temp_c"]>=threshold:expected.append(i)
        self.assertEqual({r["inspection_id"] for r in result["rows"]},{i["inspection_id"] for i in expected})
        for row in result["rows"]:
            checks=[j for j in self.jobs if j["asset_id"]==row["asset_id"] and row["inspected_at"]<j["started_at"]<"2027-01-16" and "Heat trace check" in j["issue"]]
            check=min(checks,key=lambda j:j["started_at"],default=None)
            self.assertEqual(row["response_id"],check["maintenance_id"] if check else None)
            self.assertEqual(row["assessment"]=="met",bool(check and instant(check["started_at"])<=instant(row["inspected_at"])+dt.timedelta(days=7)))

    def test_wait_reason_group_population_shares_and_medians(self):
        expected=collections.defaultdict(list)
        for j in self.jobs:
            if not "2026-01-01"<=j["started_at"]<"2027-01-01":continue
            text=self.report(j)
            line=next((x for x in text.splitlines() if "days longer than the repair itself because" in x),None)
            if not line or "expected" in line:continue
            days=float(re.search(r"about ([\d.]+) days",line)[1]);reason=line.split("because ",1)[1]
            category="parts" if "part" in reason else "weather" if "rain" in reason else "contractors" if "contractor" in reason else "crews"
            expected[(self.assets[j["asset_id"]]["area_id"],category)].append(days)
        result=self.query("wait_reasons",start="2026-01-01",end="2026-12-31")
        self.assertEqual({(r["area_id"],r["reason"]) for r in result["rows"]},set(expected))
        for r in result["rows"]:
            vals=expected[(r["area_id"],r["reason"])]
            self.assertEqual(r["job_count"],len(vals));self.assertEqual(r["median_extra_days"],statistics.median(vals))
        for area in {r["area_id"] for r in result["rows"]}:self.assertAlmostEqual(sum(r["share"] for r in result["rows"] if r["area_id"]==area),1)

    def test_temperature_profile_full_population_effective_values_and_type_history(self):
        groups=collections.defaultdict(list)
        for i in self.effective.values():
            if i["inspected_at"]>="2027-01-16":continue
            asset=self.assets[i["asset_id"]];typ=asset["well_type"]
            if asset.get("type_history"):
                matches=[h["well_type"] for h in asset["type_history"] if (not h.get("from") or h["from"]<=i["inspected_at"][:10]) and (not h.get("to") or i["inspected_at"][:10]<=h["to"])]
                typ=matches[0] if len(matches)==1 else None
            groups[(asset["area_id"],typ)].append(i)
        result=self.query("temperature_profile")
        self.assertEqual(sum(r["inspection_count"] for r in result["rows"]),sum(map(len,groups.values())))
        self.assertEqual(len(result["rows"]),len(groups))
        for r in result["rows"]:
            readings=groups[(r["area_id"],r["well_type"])];count=len(readings)
            self.assertEqual(r["inspection_count"],count)
            self.assertAlmostEqual(r["mean_wellhead_c"],sum(i["wellhead_temp_c"] for i in readings)/count)
            self.assertAlmostEqual(r["mean_delta_c"],sum(i["wellhead_temp_c"]-i["ambient_temp_c"] for i in readings)/count)
            self.assertLessEqual(r["months_highest_producing_delta_same_type"],r["comparable_months_with_other_areas_same_type"])

    def test_status_disagreement_matches_latest_actual_operator_event_and_chronology(self):
        from decimal import Decimal
        latest_inspections={}
        for reading in sorted(self.effective.values(),key=lambda i:(i["inspected_at"],i["inspection_id"])):
            if reading["inspected_at"]<"2027-01-16":latest_inspections[reading["asset_id"]]=reading
        latest_notes={}
        for note in sorted(self.notes,key=lambda n:(n["created_at"],n["note_id"])):
            if note["note_type"]!="operator_note" or note["created_at"]>="2027-01-16":continue
            text=note["text"].lower()
            # Actual supplied event wording; a delayed/planned restart is not a restart.
            if re.search(r"\bshut(?:[- ]in| the well in)\b",text):state=False
            elif re.search(r"\brestarted\b|\bput back on production\b|\bbrought\b.{0,50}\bback online\b",text):state=True
            else:continue
            latest_notes[note["asset_id"]]=(note,state)
        expected={};all_status={}
        for aid,reading in latest_inspections.items():
            asset=self.assets[aid];typ=asset["well_type"]
            if asset.get("type_history"):
                matches=[h["well_type"] for h in asset["type_history"] if (not h.get("from") or h["from"]<=reading["inspected_at"][:10]) and (not h.get("to") or reading["inspected_at"][:10]<=h["to"])]
                typ=matches[0] if len(matches)==1 else None
            delta=Decimal(str(reading["wellhead_temp_c"]))-Decimal(str(reading["ambient_temp_c"]))
            inspected=delta>={"T200":15,"T350":20,"T500":25}[typ]
            pair=latest_notes.get(aid);current=inspected;confirmed=True
            if pair and pair[0]["created_at"]>reading["inspected_at"]:current=pair[1];confirmed=not current
            if asset.get("status")=="plugged_and_abandoned" and asset.get("decommissioned_on", "9999")<="2027-01-15":current=False;confirmed=True
            all_status[aid]=(current,confirmed,pair[0]["note_id"] if pair else None)
            if pair and pair[1]!=inspected:expected[aid]=pair[0]["note_id"]
        actual={}
        for offset in range(0,len(self.assets),100):
            result=self.query("status",offset=offset)
            actual.update({r["asset_id"]:r for r in result["rows"]})
        for aid,(current,confirmed,note_id) in all_status.items():
            self.assertEqual(actual[aid]["producing"],current,aid)
            self.assertEqual(actual[aid]["status_confirmed"],confirmed,aid)
            self.assertEqual(actual[aid]["latest_status_note_id"],note_id,aid)
        selected={}
        for offset in range(0,len(expected),100):
            result=self.query("status",filters={"status_note_disagrees":True},offset=offset)
            selected.update({r["asset_id"]:r["latest_status_note_id"] for r in result["rows"]})
        self.assertEqual(selected,expected)

    def test_repair_candidates_quote_real_notes_exclude_later_repairs_and_explain_ranking(self):
        result=self.query("repair_candidates",start="2026-12-15")
        self.assertTrue(result["coverage"]["display_truncated"])
        source_notes={n["note_id"]:n for n in self.notes}
        for row in result["rows"]:
            self.assertIn("heuristic",row["ranking_basis"])
            self.assertNotIn("probability",row)
            for note in row["operator_notes"]:
                original=source_notes[note["note_id"]]
                self.assertEqual(note["quote"],original["text"])
                self.assertGreaterEqual(note["date"],"2026-12-15")
                later=[j for j in self.jobs if j["asset_id"]==row["asset_id"] and j["maintenance_type"]=="corrective" and j["started_at"]>note["date"] and not re.search(r"spill|clean.?up",j["issue"],re.I)]
                self.assertFalse(later)
            if row["thermal_warning"]:
                recent=row["thermal_warning"]["readings"]
                self.assertEqual(len(recent),4)
                self.assertTrue(all(r["well_type"]=="T500" and r["producing"] for r in recent))
                self.assertTrue(all(recent[i]["delta_c"]<recent[i-1]["delta_c"] for i in range(1,4)))
                self.assertGreaterEqual(recent[0]["delta_c"]-recent[-1]["delta_c"],3)

    def test_expected_waits_do_not_enter_observed_share_or_median(self):
        result=self.query("wait_reasons",start="2026-01-01",end="2026-12-31")
        estimated=[j for j in self.jobs if "2026-01-01"<=j["started_at"]<"2027-01-01" and "is expected to stay shut in for about" in self.report(j)]
        self.assertEqual(sum(r["estimated_job_count"] for r in result["rows"]),len(estimated))
        self.assertTrue(estimated)
        self.assertTrue(all(r["estimated_median_extra_days"] is not None for r in result["rows"] if r["estimated_job_count"]))

    def test_lineage_replays_typed_metric_and_rejects_silent_filter_ignoring(self):
        result=self.query("gas_response",start="2026-11-01")
        evidence=self.p.evidence(result["result_set_id"],self.ctx)
        self.assertEqual(evidence["members"]["total_rows"],result["total_rows"])
        self.assertIn("note_id",evidence["members"]["rows"][0])
        with self.assertRaises(RetrievalError):self.query("gas_response",filters=dict(equipment_kind="flowline"))
        with self.assertRaises(RetrievalError):self.query("gas_response",group_by=["area_id"])
        with self.assertRaises(RetrievalError):self.query("reservoir_pressure")


if __name__=="__main__":unittest.main()
