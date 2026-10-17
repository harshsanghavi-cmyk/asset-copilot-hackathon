"""Source-derived final-field operations behind the existing typed query boundary.

No runtime model, raw filesystem access, index mutation, or scenario-specific asset lists.
"""
import collections
import datetime as dt
import json
import re
import statistics
import time
import uuid
from fractions import Fraction

from ..ingestion.loader import uid
from .contracts import RetrievalError

DESCRIPTIONS = {
    "temperature_profile": "Full-population area/type thermal comparison: corrected mean wellhead, ambient, delta, producing-only delta, observed wells/readings and monthly within-type hottest counts. Separates weather/type/operating-state confounds; no reservoir pressure or oil volume inference. Fixed area+well_type rows, all months evaluated before pagination.",
    "gas_response": "Every operator gas/rotten-egg/H2S alarm report and earliest later same-well maintenance start or manual inspection, with OPS-1 versioned 24/12-hour deadline; drones excluded. Full enumeration before paging.",
    "bypass_intervals": "All operator-note bypass in/out intervals, current-in-place flag, MOC approval and extension expiry, and past/current unauthorized or expired intervals. only_breaches filters violations; default includes current allowed and historical intervals.",
    "recall_inventory": "Current recalled rod-pump serial/lot inventory from Parts installed report lines, chronological later replacements, installation costs and current production. Attributed shared replacement claims remain separate from documented inventory. Operational rows exclude honored direct replacement updates; physical inventory and excluded update provenance remain in summary. Hearsay never excludes a pump.",
    "letter_compliance": "Every effective reportable spill covered by the supplied regulator letter's named areas/date; linked cleanup report must contain affirmative exact lab-samples sentence in Spill clean-up and waste section. No SR/RC closure substitution.",
    "freeze_checks": "OPS-5 cold producing inspections and subsequent Heat trace check starts within supplied deadline; excludes down wells, uses corrected readings and event-time type.",
    "repair_candidates": "Operator equipment symptom notes in the requested period without a later corrective non-cleanup repair. Transparent heuristic ranking, last repair and thermal warnings; no calibrated 90-day probability.",
    "wait_reasons": "Report-attributed extra shut-in days beyond repair from job narrative, grouped by area/reason with count, share and median days. Uses maintenance start-date window; expected future waits are separate from observed medians/shares.",
}


def instant(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=dt.timezone.utc)


def section(text, name):
    match = re.search(r"^##\s+" + re.escape(name) + r"\s*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return match[1] if match else ""


def date_text(text):
    return dt.datetime.strptime(text, "%d %b %Y").date().isoformat()


def gas_note(text):
    # A denied smell is not a positive observation. No concentration is inferred.
    return bool(re.search(r"smelled gas|gas (?:odor|odour|smell)|rotten[- ]egg|H2S monitor alarmed", text, re.I)) and not bool(re.search(r"\b(?:no|not|never)\b.{0,20}(?:gas|rotten|H2S)|(?:did not|didn't) smell", text, re.I))


def bypass_action(text):
    if not re.search(r"\bbypass\b", text, re.I) or re.search(r"\b(?:no|not|never)\s+(?:temporary\s+)?bypass|not (?:installed|removed)|will (?:install|remove)", text, re.I):
        return None
    if re.search(r"bypass (?:removed|pulled)|took the bypass out", text, re.I):
        return "out"
    if re.search(r"bypass (?:in place|installed)|bypass in\b|put the bypass in", text, re.I):
        return "in"
    return None


def replacement_override(claim):
    """Apply an attributed operational update without claiming a verified work order.

    Passive voice is still a direct report: lack of an ``I/we`` verb does not
    imply hearsay. ``unconfirmed`` describes evidence, not permission to honor
    the author's explicit count-as-replaced instruction.
    """
    text = claim.get("source_quote") or claim.get("statement", "")
    if (claim.get("scope", "shared") != "shared"
            or claim.get("qualifier") in ("hearsay", "inferred")
            or claim.get("attribution_basis") == "hearsay"
            or claim.get("conflicts")
            or claim.get("status") in ("conflict_pending", "candidate", "retracted", "withdrawn", "rejected", "superseded")):
        return False
    if re.search(r"told me|heard (?:that|from)|apparently|reportedly|might|may have|not (?:been )?(?:swapped|replaced|pulled)|(?:wasn't|hasn't been) (?:swapped|replaced|pulled)", text, re.I):
        return False
    replacement = bool(re.search(r"\b(?:swapped|replaced|pulled)\b", text, re.I))
    instruction = bool(re.search(r"count.{0,35}replaced|take.{0,35}off.{0,25}recall|remove.{0,35}recall|from now on", text, re.I))
    direct_observation = claim.get("firsthand") is True or claim.get("attribution_basis") == "direct"
    return replacement and (instruction or direct_observation)


class Operations:
    def __init__(self, p, filters, reference):
        self.p, self.reference = p, reference
        self.end = (dt.date.fromisoformat(reference) + dt.timedelta(days=1)).isoformat()
        self.assets = {r["asset_id"]: dict(r) for r in p._run("SELECT a.*,b.name area_name FROM assets a JOIN areas b USING(area_id)")}
        self.equipment=collections.defaultdict(set)
        for equipment in p._run("SELECT asset_id,kind FROM equipment"):self.equipment[equipment["asset_id"]].add(equipment["kind"])
        self.selected = {}
        for aid, asset in self.assets.items():
            if filters.get("asset_id") and aid != filters["asset_id"]: continue
            if filters.get("asset_ids") is not None and aid not in filters["asset_ids"]: continue
            if filters.get("area_id") and asset["area_id"] != filters["area_id"]: continue
            if filters.get("team_id") and p._timeline.at(aid, "team_id", reference) != filters["team_id"]: continue
            if filters.get("well_type") and p._timeline.at(aid, "well_type", reference) != filters["well_type"]: continue
            self.selected[aid] = asset
        self.docs = {r["id"]: r for r in p._run("SELECT id,path,kind,preview,byte_count FROM sources WHERE kind IN ('sop','manual','report')")}
        self.jobs = [dict(r, original=json.loads(r["raw_json"])) for r in p._run("SELECT m.*,r.raw_json FROM maintenance m JOIN records r ON r.id=m.maintenance_id WHERE m.started_at<? ORDER BY m.started_at,m.maintenance_id", (self.end,)) if r["asset_id"] in self.selected]
        self.notes = [r for r in p._run("SELECT * FROM context_notes WHERE note_type='operator_note' AND created_at<? ORDER BY created_at,note_id", (self.end,)) if r["asset_id"] in self.selected]
        self.rules = []
        self.missing_evidence = set()
        self.warnings = ["Missing records do not independently prove real-world inaction; calendar reference date supplies no time of day."]

    def doc(self, pattern):
        matches = [d for d in self.docs.values() if d["kind"] != "report" and re.search(pattern, d["preview"], re.I | re.M)]
        if len(matches) != 1:
            raise RetrievalError("unsupported_operation", "Required source rule is absent or ambiguous: " + pattern)
        self.rules.append(matches[0]["id"])
        return matches[0]

    def report(self, job):
        source = self.docs.get(job["report_source_id"])
        if not source or len(source["preview"].encode()) < source["byte_count"]:
            if job.get("report_path"): self.missing_evidence.add(job["maintenance_id"])
            return None
        return source

    def row(self, asset, refs=(), **fields):
        a = self.assets[asset]
        return dict(asset_id=asset, area_id=a["area_id"], area_name=a["area_name"], evidence_refs=list(dict.fromkeys([uid("ev_", asset), *refs])), **fields)

    def correction_refs(self, record_id):
        refs=[]
        for (rid,field), correction in self.p._active_corrections.items():
            if rid==record_id:
                refs.extend([correction[k] for k in ("source_id",) if correction.get(k)])
                if correction.get("id"): refs.append(uid("ev_",correction["id"]) if correction["id"].startswith("CTX-") else correction["id"])
        return refs

    def in_window(self, timestamp, start, end):
        return (not start or timestamp >= start[:10]) and timestamp < min(self.end, (dt.date.fromisoformat(end[:10]) + dt.timedelta(days=1)).isoformat() if end else self.end)

    def temperature_profile(self,start,end):
        self.rules.extend(r["source_id"] for r in self.p._rules.values())
        sql="SELECT inspection_id,asset_id,inspected_at,effective_value(inspection_id,'ambient_temp_c',ambient_milli) ambient,effective_value(inspection_id,'wellhead_temp_c',wellhead_milli) wellhead FROM inspections WHERE inspected_at>=? AND inspected_at<? ORDER BY inspected_at,inspection_id"
        bound=min(self.end,(dt.date.fromisoformat(end[:10])+dt.timedelta(days=1)).isoformat() if end else self.end)
        groups={};monthly=collections.defaultdict(lambda:[0,0]);unknown=0
        for i in self.p._run(sql,(start or "0001-01-01",bound),deadline=8):
            aid=i["asset_id"]
            if aid not in self.selected:continue
            typ=self.p._timeline.at(aid,"well_type",i["inspected_at"])
            key=(self.assets[aid]["area_id"],typ)
            g=groups.setdefault(key,dict(count=0,valid=0,wells=set(),ambient=0,wellhead=0,delta=0,producing=0,producing_delta=0,months=set(),refs=[]))
            g["count"]+=1;g["wells"].add(aid);g["months"].add(i["inspected_at"][:7])
            if None in (i["ambient"],i["wellhead"]):unknown+=1;continue
            delta=i["wellhead"]-i["ambient"];threshold=self.p._threshold(typ)
            g["valid"]+=1;g["ambient"]+=i["ambient"];g["wellhead"]+=i["wellhead"];g["delta"]+=delta
            if threshold is not None and delta>=threshold:
                g["producing"]+=1;g["producing_delta"]+=delta
                m=monthly[(i["inspected_at"][:7],typ,key[0])];m[0]+=delta;m[1]+=1
            if len(g["refs"])<2:g["refs"].append(uid("ev_",i["inspection_id"]))
        wins=collections.Counter();comparisons=collections.Counter()
        domains=collections.defaultdict(dict)
        for (month,typ,area),(total,count) in monthly.items():domains[(month,typ)][area]=(total,count)
        for (month,typ),areas in domains.items():
            if len(areas)<2:continue
            # Integer cross multiplication prevents float rounding from creating/removing ties.
            winner=max(areas,key=lambda a:Fraction(*areas[a]));top=areas[winner]
            for area,(total,count) in areas.items():
                comparisons[(area,typ)]+=1
                if total*top[1]==top[0]*count:wins[(area,typ)]+=1
        rows=[]
        for (area,typ),g in sorted(groups.items(),key=lambda item:(item[0][0],str(item[0][1]))):
            count=g["valid"];name=next(a["area_name"] for a in self.assets.values() if a["area_id"]==area)
            rows.append(dict(area_id=area,area_name=name,well_type=typ,inspection_count=g["count"],valid_temperature_count=count,well_count=len(g["wells"]),mean_wellhead_c=g["wellhead"]/count/1000 if count else None,mean_ambient_c=g["ambient"]/count/1000 if count else None,mean_delta_c=g["delta"]/count/1000 if count else None,producing_inspection_count=g["producing"],mean_producing_delta_c=g["producing_delta"]/g["producing"]/1000 if g["producing"] else None,months_measured=len(g["months"]),comparable_months_with_other_areas_same_type=comparisons[(area,typ)],months_highest_producing_delta_same_type=wins[(area,typ)],unknown_count=g["count"]-count,assessment="measured",evidence_refs=g["refs"]+[r["source_id"] for r in self.p._rules.values()]))
        self.warnings += ["Means are inspection-weighted observed temperatures, not flow volumes or reservoir pressure. Compare same type and producing state; absolute wellhead heat also reflects ambient weather. Monthly hottest counts allow ties and use only months with another area of that type; unmatched type/area coverage is not field-wide consistency."]
        return rows

    def gas_response(self, start, end):
        rule = self.doc(r"^## OPS-1 Gas odor response")
        body = section(rule["preview"], "OPS-1 Gas odor response")
        versions = re.findall(r"\*\*(\d+) hours\*\* for reports noted (before|from) (\d+ \w+ \d{4})", body)
        if len(versions) != 2: raise RetrievalError("unsupported_operation", "OPS-1 deadline table not recognized")
        responses = collections.defaultdict(list)
        for job in self.jobs: responses[job["asset_id"]].append((job["started_at"], job["maintenance_id"], "maintenance"))
        for r in self.p._run("SELECT inspection_id,asset_id,inspected_at FROM inspections WHERE method='manual' AND inspected_at<? ORDER BY inspected_at,inspection_id", (self.end,)):
            if r["asset_id"] in self.selected: responses[r["asset_id"]].append((r["inspected_at"], r["inspection_id"], "manual_inspection"))
        for values in responses.values(): values.sort()
        rows = []
        for n in self.notes:
            if not self.in_window(n["created_at"], start, end) or not gas_note(n["text"]): continue
            hours = next(int(h) for h, op, day in versions if (n["created_at"][:10] < date_text(day)) == (op == "before"))
            response = next((r for r in responses[n["asset_id"]] if r[0] > n["created_at"]), None)
            elapsed = (instant(response[0]) - instant(n["created_at"])).total_seconds()/3600 if response else None
            due = instant(n["created_at"]) + dt.timedelta(hours=hours)
            assessment = "met" if elapsed is not None and elapsed <= hours else "missed" if response or due.date().isoformat() < self.reference else "pending_not_due"
            rows.append(self.row(n["asset_id"], [uid("ev_", n["note_id"]), rule["id"], *([uid("ev_", response[1])] if response else [])], note_id=n["note_id"], reported_at=n["created_at"], note=n["text"], response_id=response[1] if response else None, response_at=response[0] if response else None, response_kind=response[2] if response else None, hours_to_response=elapsed, deadline_hours=hours, due_at=due.isoformat(), assessment=assessment, h2s_ppm=None))
        return rows

    def bypass_intervals(self, start, end):
        self.doc(r"^## OPS-2 Temporary bypass")
        approvals, extensions = [], []
        for d in self.docs.values():
            text = d["preview"]
            if d["kind"] != "sop" or not re.search(r"^# Management of Change", text): continue
            identifier = re.search(r"^#.*?(MOC-\d{4}-\d+)", text)
            expires = re.search(r"expires on (\d+ \w+ \d{4})", text, re.I)
            issued = re.search(r"\*\*Date:\*\* (\d+ \w+ \d{4})", text)
            if not identifier or not expires or not issued: continue
            if date_text(issued[1]) > self.reference: continue
            self.rules.append(d["id"])
            extends = re.search(r"This memo extends (MOC-\d{4}-\d+)", text, re.I)
            if extends:
                extensions.append((extends[1], date_text(issued[1]), date_text(expires[1]), identifier[1], d["id"]))
            else:
                effective = re.search(r"(?:effective (?:from |on )?|takes effect (?:on )?)(\d+ \w+ \d{4})", text, re.I)
                approvals.append(dict(id=identifier[1], wells=set(re.findall(r"WELL-\d+", text)), effective=date_text(effective[1]) if effective else date_text(issued[1]), expires=date_text(expires[1]), refs=[d["id"]], extension=None))
        for memo, issued, expiry, ext, ref in sorted(extensions, key=lambda v:v[1]):
            for a in approvals:
                if a["id"] == memo:
                    a.update(expires=expiry, extension=ext); a["refs"].append(ref)
        open_intervals, intervals = {}, []
        for n in self.notes:
            action, aid = bypass_action(n["text"]), n["asset_id"]
            if action == "in" and aid not in open_intervals: open_intervals[aid] = n
            elif action == "out" and aid in open_intervals: intervals.append((open_intervals.pop(aid), n))
        intervals += [(n, None) for n in open_intervals.values()]
        rows = []
        for begin, finish in intervals:
            if not self.in_window(begin["created_at"], start, end): continue
            aid = begin["asset_id"]
            authorized = [a for a in approvals if aid in a["wells"] and a["effective"] <= begin["created_at"][:10]]
            a = max(authorized, key=lambda v:v["expires"]) if authorized else None
            expired = bool(a and (finish["created_at"] if finish else self.reference)[:10] > a["expires"])
            state = "not_approved" if a is None else "expired" if expired else "allowed"
            rows.append(self.row(aid, [uid("ev_",begin["note_id"]), *([uid("ev_",finish["note_id"])] if finish else []), *(a["refs"] if a else [])], bypass_in=begin["created_at"], bypass_out=finish["created_at"] if finish else None, current_in_place=finish is None, approval_id=a["id"] if a else None, extension_id=a["extension"] if a else None, approval_valid_until=a["expires"] if a else None, assessment=state, violation=state != "allowed"))
        rows.sort(key=lambda r:(not r["current_in_place"],not r["violation"],r["asset_id"],r["bypass_in"]))
        return rows

    def current_status(self, aid):
        values = self.p._run("SELECT * FROM inspections WHERE asset_id=? AND inspected_at<? ORDER BY inspected_at DESC,inspection_id DESC LIMIT 1", (aid,self.end))
        if not values: return {"producing": None, "status_now": "unknown"}
        r = values[0]
        well = self.p._effective(r["inspection_id"], "wellhead_temp_c", r["wellhead_milli"])
        ambient = self.p._effective(r["inspection_id"], "ambient_temp_c", r["ambient_milli"])
        threshold = self.p._threshold(self.p._timeline.at(aid,"well_type",r["inspected_at"]))
        producing = None if None in (well,ambient,threshold) else well-ambient >= threshold
        status = self.p._timeline.status(aid,r["inspected_at"],producing,self.reference)
        status["inspection_id"] = r["inspection_id"]
        return status

    def recall_inventory(self, start, end):
        notice = self.doc(r"^# Supplier Recall Notice")
        recalled = set(re.findall(r"^-\s+(LOT-[\w-]+)", section(notice["preview"],"What is recalled"), re.M))
        product = re.search(r"^([A-Za-z][\w .&-]*?) (RP-\d+) downhole",section(notice["preview"],"What is recalled"),re.M)
        if not product:raise RetrievalError("unsupported_operation","Recall product not recognized")
        if not recalled: raise RetrievalError("unsupported_operation","Recall lot list not recognized")
        by_asset = collections.defaultdict(list)
        for job in self.jobs:
            if job["equipment_kind"] != "downhole_pump": continue
            report = self.report(job)
            line = re.search(r"^\*\*Parts installed:\*\* (.+)$", report["preview"], re.M) if report else None
            if not line: continue
            serial, lot = re.search(r"\bserial\s+(SN-[\w-]+)",line[1],re.I), re.search(r"\blot\s+(LOT-[\w-]+)",line[1],re.I)
            if serial and lot: by_asset[job["asset_id"]].append((job,report,serial[1],lot[1],line[1]))
        rows=[]
        for aid, installs in by_asset.items():
            job,report,serial,lot,parts = max(installs,key=lambda v:(v[0]["completed_at"] or v[0]["started_at"],v[0]["maintenance_id"]))
            # A future/in-progress replacement does not prove the installed pump was pulled.
            eligible = [i for i in installs if i[0]["completed_at"] and i[0]["completed_at"] < self.end]
            if not eligible: continue
            job,report,serial,lot,parts = max(eligible,key=lambda v:(v[0]["completed_at"],v[0]["maintenance_id"]))
            if lot not in recalled: continue
            if not re.search(re.escape(product[1])+r"\s+"+re.escape(product[2])+r"\b",parts,re.I):continue
            if "esp_pump" in self.equipment[aid] and "downhole_pump" not in self.equipment[aid]:continue
            subsequent = [j for j in self.jobs if j["asset_id"]==aid and j["equipment_kind"]=="downhole_pump" and j["started_at"]>job["started_at"] and j["maintenance_type"]=="corrective"]
            uncertain = [j for j in subsequent if j["completed_at"] and j["completed_at"]<self.end and not re.search(r"^\*\*Parts installed:\*\*", (self.report(j) or {}).get("preview",""),re.M) and re.search(r"replac|pump pulled|pulled.*pump",j["original"].get("action_taken", ""),re.I)]
            claims = [c for c in self.p._authority.shared_claims if aid in c.get("subject_ids",[]) and c.get("scope","shared")=="shared" and c.get("status") not in ("retracted","rejected","superseded") and (not c.get("valid_from") or c["valid_from"][:10]<=self.reference) and (not c.get("valid_to") or c["valid_to"][:10]>=self.reference) and re.search(r"replac|swapp|pull",c.get("statement",""),re.I)]
            claims=[c for c in claims if not c.get("valid_from") or c["valid_from"][:10]>=job["completed_at"][:10]]
            claim_rows=[{k:c.get(k) for k in ("id","author","statement","valid_from","valid_to","status","conflicts","qualifier","firsthand","attribution_basis")} for c in claims]
            override=any(replacement_override(c) for c in claims)
            state = "reported_replaced_unverified" if override else "replacement_claim_unconfirmed" if claims else "unknown_later_replacement" if uncertain else "recorded_in_ground"
            status=self.current_status(aid)
            last_repair=max([j for j in self.jobs if j["asset_id"]==aid and j["maintenance_type"]=="corrective" and not re.search(r"spill|clean.?up",j["original"].get("issue",""),re.I)],key=lambda j:j["started_at"],default=None)
            cost=job["original"].get("cost_usd",{}).get("total")
            rows.append(self.row(aid,[uid("ev_",job["maintenance_id"]),report["id"],notice["id"],*([uid("ev_",status["inspection_id"])] if status.get("inspection_id") else []),*[uid("ev_",j["maintenance_id"]) for j in uncertain],*([uid("ev_",status["latest_status_note_id"])] if status.get("latest_status_note_id") else []),*([uid("ev_",last_repair["maintenance_id"])] if last_repair else [])], serial=serial,lot=lot,parts_installed=parts,installation_job=job["maintenance_id"],installed_at=job["completed_at"],installation_cost_usd=cost,assessment=state,documented_in_ground=not bool(uncertain),included_in_operational_recall_list=not override and not bool(uncertain),work_order_verified=False if claims else None,replacement_claims=claim_rows,producing=status["producing"],status_now=status["status_now"],status_confirmed=status.get("status_confirmed"),last_repair_id=last_repair["maintenance_id"] if last_repair else None,last_repair_at=last_repair["started_at"] if last_repair else None,last_repair_equipment=last_repair["equipment_kind"] if last_repair else None))
        self.warnings += ["Physical inventory and operational count are separate: explicit direct attributed replacement instruction changes operational count with unverified-work-order flag; hearsay does not. No claim becomes inspected physical evidence.","Installation cost is recorded total job cost, not pump-only price or paid expenditure."]
        return rows

    def letter_compliance(self, start, end):
        letter=self.doc(r"^# Letter from the State Oil")
        text=letter["preview"]
        covered={a["area_id"] for a in self.assets.values() if a["area_name"] in text}
        since=re.search(r"since (\d+ \w+ \d{4})",text)
        due=re.search(r"submitted by (\d+ \w+ \d{4})",text)
        sop=self.doc(r"^# Spill Response SOP")
        threshold=re.search(r"Reportable\s*\|\s*(\d+(?:\.\d+)?) bbl",sop["preview"])
        sentence=re.search(r'contains the sentence "([^"]+)"',text)
        if not covered or not since or not due or not threshold or not sentence: raise RetrievalError("unsupported_operation","Letter scope or compliance rule not recognized")
        start=date_text(since[1])
        end=self.reference
        self.scope_start,self.scope_end=start,end
        self.warnings.append("Letter assessment uses its stated incident window through the reference date; publication date is not the spill window.")
        sql,params,_,_,_=self.p._compile("inspections","spills",{},[],start,end,self.end,self.reference)
        incidents=self.p._run(sql,params,deadline=5)
        rows=[]
        for i in incidents:
            aid=i["asset_id"]
            if aid not in self.selected or self.assets[aid]["area_id"] not in covered: continue
            volume=i["spill_est_volume_bbl"]
            if volume is not None and volume<float(threshold[1]): continue
            jobs=[j for j in self.jobs if j["inspection_id"]==i["inspection_id"]]
            evidence=[]; compliant=False
            for j in jobs:
                report=self.report(j)
                if not report: continue
                body=section(report["preview"],"Spill clean-up and waste")
                # Require the affirmative sentence itself, not quoted or negated prose.
                positive=bool(re.search(r"(?:^\s*(?:[-*]\s+)?|[.!?]\s+)"+re.escape(sentence[1])+r"(?:\s|$)",body,re.M))
                compliant |= positive
                evidence.append(dict(maintenance_id=j["maintenance_id"],report_source_id=report["id"],lab_sentence_present=positive))
            assessment="unknown_volume" if volume is None else "compliant" if compliant else "not_compliant"
            rows.append(self.row(aid,[*i.get("evidence_refs",[]),uid("ev_",i["inspection_id"]),*self.correction_refs(i["inspection_id"]),letter["id"],sop["id"],*[e["report_source_id"] for e in evidence],*[uid("ev_",j["maintenance_id"]) for j in jobs]],inspection_id=i["inspection_id"],inspected_at=i["inspected_at"],spill_volume_bbl=volume,cleanup_jobs=[j["maintenance_id"] for j in jobs],cleanup_job_ids=", ".join(j["maintenance_id"] for j in jobs) or None,compliant=None if volume is None else compliant,report_checks=evidence,due_date=date_text(due[1]),assessment=assessment,reason="Affirmative required lab sentence in specified report section" if compliant else "No linked cleanup report with the affirmative required lab sentence in specified section; on-site readings do not count"))
        self.warnings += ["Compliant means the letter's explicit internal report-evidence criterion is met; report wording alone does not independently verify actual laboratory submission time."]
        return rows

    def freeze_checks(self,start,end):
        rule=self.doc(r"^## OPS-5 Freeze protection")
        body=section(rule["preview"],"OPS-5 Freeze protection (1 Dec – 28 Feb)")
        cold=re.search(r"[−-](\d+) °C",body); days=re.search(r"\*\*(\d+) days\*\*",body)
        if not cold or not days: raise RetrievalError("unsupported_operation","Freeze rule not recognized")
        sql,params,_,_,_=self.p._compile("inspections","temperature_series",{},[],start,end,self.end,self.reference)
        rows=[]
        for i in self.p._run(sql,params,deadline=8):
            if i["asset_id"] not in self.selected or int(i["inspected_at"][5:7]) not in (12,1,2) or not i["producing"] or i["ambient_temp_c"] is None or i["ambient_temp_c"]>-int(cold[1]): continue
            due=instant(i["inspected_at"])+dt.timedelta(days=int(days[1]))
            checks=[j for j in self.jobs if j["asset_id"]==i["asset_id"] and j["started_at"]>i["inspected_at"] and re.search(r"Heat trace check",j["original"].get("issue",""),re.I)]
            check=min(checks,key=lambda j:j["started_at"],default=None)
            met=bool(check and instant(check["started_at"])<=due)
            rows.append(self.row(i["asset_id"],[uid("ev_",i["inspection_id"]),*self.correction_refs(i["inspection_id"]),rule["id"],*([uid("ev_",check["maintenance_id"])] if check else [])],inspection_id=i["inspection_id"],inspected_at=i["inspected_at"],ambient_temp_c=i["ambient_temp_c"],producing=True,response_id=check["maintenance_id"] if check else None,response_at=check["started_at"] if check else None,due_at=due.isoformat(),assessment="met" if met else "missed" if due.date().isoformat()<self.reference or check else "pending_not_due"))
        return rows

    def repair_candidates(self,start,end):
        start=start or (dt.date.fromisoformat(self.reference)-dt.timedelta(days=31)).isoformat()
        symptoms=r"rattl|squeal|fluid pound|tagging bottom|vibrat|knock|grind|chatter|surging|erratic|overheat|unusual noise|burning|hot smell"
        grouped=collections.defaultdict(list)
        for n in self.notes:
            if self.in_window(n["created_at"],start,end) and re.search(symptoms,n["text"],re.I) and not re.search(r"no (?:unusual |abnormal )?(?:noise|vibration)|running smooth|normal\b",n["text"],re.I): grouped[n["asset_id"]].append(n)
        rows=[]
        manuals=[d for d in self.docs.values() if d["kind"]=="manual" and "## 5. Early warning signs" in d["preview"]]
        for aid,notes in grouped.items():
            repairs=[j for j in self.jobs if j["asset_id"]==aid and j["maintenance_type"]=="corrective" and not re.search(r"spill|clean.?up",j["original"].get("issue",""),re.I)]
            outstanding=[n for n in notes if not any(j["started_at"]>n["created_at"] for j in repairs)]
            if not outstanding:continue
            last=max(repairs,key=lambda j:j["started_at"],default=None)
            status=self.current_status(aid)
            recent=self.p._run("SELECT inspection_id,inspected_at,ambient_milli,wellhead_milli FROM inspections WHERE asset_id=? AND inspected_at<? ORDER BY inspected_at DESC,inspection_id DESC",(aid,self.end))
            readings=[]
            for reading in reversed(recent):
                iid=reading["inspection_id"];typ=self.p._timeline.at(aid,"well_type",reading["inspected_at"])
                ambient=self.p._effective(iid,"ambient_temp_c",reading["ambient_milli"])
                wellhead=self.p._effective(iid,"wellhead_temp_c",reading["wellhead_milli"])
                threshold=self.p._threshold(typ)
                readings.append(dict(inspection_id=iid,inspected_at=reading["inspected_at"],well_type=typ,delta_c=None if None in (ambient,wellhead) else (wellhead-ambient)/1000,delta_milli=None if None in (ambient,wellhead) else wellhead-ambient,producing=None if None in (ambient,wellhead,threshold) else wellhead-ambient>=threshold))
            thermal_warning=None;manual_refs=[]
            for manual in manuals:
                text=manual["preview"]
                type_match=re.search(r'well_type = "([^"\n]+)"',text)
                if not type_match or self.p._timeline.at(aid,"well_type",self.reference)!=type_match[1]:continue
                fall=re.search(r"(\d+) °C or more in total",text)
                deadline=re.search(r"check within \*\*(\d+) days\*\*",text)
                if not fall or not deadline:continue
                for index in range(3,len(readings)):
                    window=readings[index-3:index+1]
                    if window[-1]["inspected_at"]<start:continue
                    if not all(r["well_type"]==type_match[1] and r["producing"] for r in window):continue
                    if not all(window[i]["delta_c"]<window[i-1]["delta_c"] for i in range(1,4)) or window[0]["delta_milli"]-window[-1]["delta_milli"]<int(fall[1])*1000:continue
                    detected=window[-1]["inspected_at"]
                    if any(j["started_at"]>detected and j["asset_id"]==aid and re.search(r"(?:drive.*insulation|insulation.*drive)",j["original"].get("issue",""),re.I) for j in self.jobs):continue
                    thermal_warning=dict(total_delta_drop_c=(window[0]["delta_milli"]-window[-1]["delta_milli"])/1000,detected_at=detected,check_due_at=(instant(detected)+dt.timedelta(days=int(deadline[1]))).isoformat(),readings=window,rule="Supplied ESP manual: three consecutive decreases, four producing readings, minimum total drop; no subsequent recorded drive/insulation check")
                    manual_refs.append(manual["id"]);self.rules.append(manual["id"])
            score=len(outstanding)+(2 if status["producing"] is False else 0)+(3 if thermal_warning else 0)
            rows.append(self.row(aid,[*[uid("ev_",n["note_id"]) for n in outstanding],*([uid("ev_",last["maintenance_id"])] if last else []),*[uid("ev_",r["inspection_id"]) for r in (readings[-4:]+(thermal_warning["readings"] if thermal_warning else []))],*[e for r in (readings[-4:]+(thermal_warning["readings"] if thermal_warning else [])) for e in self.correction_refs(r["inspection_id"])],*manual_refs],latest_note_at=outstanding[-1]["created_at"],latest_note_quote=outstanding[-1]["text"],other_warning_signs="ESP declining-delta warning" if thermal_warning else "Currently not producing" if status["producing"] is False else "No additional deterministic warning established",recent_readings=readings[-4:],thermal_warning=thermal_warning,operator_notes=[dict(note_id=n["note_id"],date=n["created_at"],quote=n["text"]) for n in outstanding],warning_note_count=len(outstanding),last_repair_id=last["maintenance_id"] if last else None,last_repair_at=last["started_at"] if last else None,producing=status["producing"],assessment="candidate",priority_score=score,ranking_basis="Unrepaired symptom-note count +2 if currently not producing +3 for an unreconciled supplied ESP four-reading declining-delta warning in the note window; heuristic, not a calibrated 90-day forecast"))
        rows.sort(key=lambda r:(-r["priority_score"],r["asset_id"]))
        for rank,r in enumerate(rows,1):r["rank"]=rank
        self.warnings += ["Candidate ranking is an explicit heuristic, not a predicted probability. Absence of a later recorded corrective repair does not prove no field action occurred; targeted manual warning checks are not exhaustively implemented."]
        return rows

    def wait_reasons(self,start,end):
        groups=collections.defaultdict(list);estimates=collections.defaultdict(list);refs=collections.defaultdict(list)
        conflicts=collections.defaultdict(list);missing_reports=0;unquantified=0
        categories=(("parts",r"part|supplier|back.order|vendor"),("weather",r"rain|weather|road impass"),("contractors",r"contractor"),("crews",r"crew"))
        for j in self.jobs:
            if not self.in_window(j["started_at"],start,end):continue
            report=self.report(j)
            if not report:
                if j["report_path"]:missing_reports+=1
                continue
            match=re.search(r"(?:stayed shut in|is expected to stay shut in) for about (\d+(?:\.\d+)?) days longer than the repair itself because (.+?)(?:\.|\n|$)",report["preview"],re.I)
            if not match:
                if re.search(r"wait|longer than the repair",report["preview"],re.I):unquantified+=1
                continue
            reason=match[2]
            kind=next((name for name,pattern in categories if re.search(pattern,reason,re.I)),"other")
            key=(self.assets[j["asset_id"]]["area_id"],kind)
            (estimates if "expected" in match[0].lower() else groups)[key].append(float(match[1]))
            refs[key] += [uid("ev_",j["maintenance_id"]),report["id"]]
            # Same well + explicitly bounded repair/wait episode; expose differing attribution,
            # never rewrite the report's reason or add a second job to the denominator.
            begin=instant(j["started_at"])-dt.timedelta(days=float(match[1]))
            finish=min(instant(j["completed_at"] or self.end+"T00:00:00Z"),instant(self.end+"T00:00:00Z"))
            for n in self.notes:
                if n["asset_id"]!=j["asset_id"] or not begin<=instant(n["created_at"])<=finish or not re.search(r"wait|back.order",n["text"],re.I):continue
                note_kind=next((name for name,pattern in categories if re.search(pattern,n["text"],re.I)),None)
                if note_kind and note_kind!=kind:
                    conflicts[key].append(dict(maintenance_id=j["maintenance_id"],note_id=n["note_id"],note_reason=note_kind,report_reason=kind,quote=n["text"]))
                    refs[key].append(uid("ev_",n["note_id"]))
        totals=collections.Counter()
        for (area,reason),values in groups.items():totals[area]+=len(values)
        rows=[]
        for area,reason in sorted(set(groups)|set(estimates)):
            values=groups[(area,reason)];expected=estimates[(area,reason)]
            name=next(a["area_name"] for a in self.assets.values() if a["area_id"]==area)
            rows.append(dict(area_id=area,area_name=name,reason=reason,job_count=len(values),area_jobs_with_wait_evidence=totals[area],share=len(values)/totals[area] if totals[area] else None,median_extra_days=statistics.median(values) if values else None,extra_days_total=sum(values),estimated_job_count=len(expected),estimated_median_extra_days=statistics.median(expected) if expected else None,conflicting_note_count=len(conflicts[(area,reason)]),conflicting_notes=conflicts[(area,reason)],assessment="report_attributed",evidence_refs=list(dict.fromkeys(refs[(area,reason)]))))
        self.warnings += ["Shares and median extra days use observed report-attributed waits only; future expected waits are separate estimates. Denominator is jobs with explicit extra-wait-duration narrative, not all jobs. Differing nearby note attributions remain visible; downtime_hours is never subtracted to invent waiting time.",f"Source coverage: {missing_reports} declared reports unavailable/truncated; {unquantified} reports mention waiting without a recognized numeric extra-wait sentence."]
        return rows


def assess(provider,plan,context,filters,start,end,reference,asof_end):
    metric=plan["metric"]
    if plan.get("group_by") and (metric not in ("wait_reasons","temperature_profile") or set(plan["group_by"] if isinstance(plan["group_by"],list) else [plan["group_by"]]) not in ({"area_id"},{"area_id","well_type"}) or metric=="wait_reasons" and "well_type" in plan["group_by"]):raise RetrievalError("unsupported_operation","Typed row metric; only wait_reasons/temperature_profile support their fixed grouping")
    unsupported=set(filters)-{"asset_id","asset_ids","area_id","team_id","well_type"}
    if unsupported:raise RetrievalError("unsupported_operation","Unsupported filters for this metric: "+", ".join(sorted(unsupported)))
    for key,value in filters.items():
        if key=="asset_ids":
            if not isinstance(value,list) or len(value)>6000 or any(not isinstance(v,str) or len(v)>128 for v in value):raise RetrievalError("invalid_plan","asset_ids must be a bounded list of IDs")
        elif not isinstance(value,str) or len(value)>128:raise RetrievalError("invalid_plan","Filter values must be literal IDs")
    began=time.perf_counter();ops=Operations(provider,filters,reference)
    all_rows=getattr(ops,metric)(start,end)
    rows=all_rows
    if metric=="recall_inventory":
        # Keep documented membership/provenance in summary; the operational table
        # must not list a pump whose explicit direct replacement update we honored.
        rows=[r for r in rows if r["assessment"]!="reported_replaced_unverified"]
    if plan.get("only_breaches"):
        rows=[r for r in rows if r["assessment"] in ("missed","not_approved","expired","not_compliant","unknown_volume","unknown_later_replacement")]
    counts=dict(collections.Counter(r["assessment"] for r in all_rows))
    limit,offset=int(plan.get("limit",50)),int(plan.get("offset",0))
    page=[dict(r) for r in rows[offset:offset+limit]]
    rid="result_"+uuid.uuid4().hex
    for i,row in enumerate(page):row.update(row_id=uid("row_",rid+str(i+offset)));row["evidence_refs"].append(rid)
    unknown=sum(v for k,v in counts.items() if k.startswith("unknown"))+len(ops.missing_evidence)+sum(r.get("unknown_count",0) for r in all_rows)
    import_issues=provider._run("SELECT count(*) n FROM issues")[0]["n"]
    if ops.missing_evidence:ops.warnings.append(f"{len(ops.missing_evidence)} declared reports unavailable/truncated; derived inventory/report totals are lower-bound known evidence, not an exhaustive absence claim")
    coverage=dict(unit=metric,matching=len(all_rows),evaluated=len(all_rows),unknown=unknown,import_issues=import_issues,status="partial" if unknown or import_issues else "complete",displayed_rows=len(page),output_rows=len(rows),display_truncated=offset+len(page)<len(rows),aggregation_input_truncated=False)
    summary=dict(total_matching=len(all_rows),assessment_counts=counts,area_counts=dict(collections.Counter(r.get("area_name") for r in all_rows if r.get("area_name"))))
    if metric=="temperature_profile":summary.update(source_observation_count=sum(r["inspection_count"] for r in all_rows),profile_groups=len(all_rows))
    if metric=="wait_reasons":summary.update(observed_jobs=sum(r["job_count"] for r in all_rows),estimated_jobs=sum(r["estimated_job_count"] for r in all_rows),conflicting_note_attributions=sum(r["conflicting_note_count"] for r in all_rows))
    if metric=="bypass_intervals":summary.update(current_in_place=sum(r["current_in_place"] for r in all_rows),violations=sum(r["violation"] for r in all_rows))
    if metric=="recall_inventory":summary.update(documented_in_ground=sum(r["documented_in_ground"] for r in all_rows),unconfirmed_replacement_claims=sum(bool(r["replacement_claims"]) for r in all_rows),operational_in_ground=sum(r["included_in_operational_recall_list"] for r in all_rows),operational_area_counts=dict(collections.Counter(r["area_name"] for r in all_rows if r["included_in_operational_recall_list"])))
    if metric=="recall_inventory":summary["excluded_replacement_updates"]=[{k:r[k] for k in ("asset_id","area_name","assessment","serial","lot","installation_job","documented_in_ground","work_order_verified","replacement_claims")} for r in all_rows if r["assessment"]=="reported_replaced_unverified"]
    trace=provider._save_trace(dict(operation=metric,plan=plan,coverage=coverage,summary=summary,tables=["records","assets","inspections","maintenance","context_notes","sources"],safe_sql="Fixed parameterized full-population reads; source-derived typed Python interval/response/report joins",selected_evidence=list(dict.fromkeys(e for r in page for e in r["evidence_refs"]))[:40],elapsed_ms=round((time.perf_counter()-began)*1000,3),knowledge_revision=provider._authority.knowledge_revision))
    result=dict(schema_version="1.0",provider_id=provider.provider_id,result_set_id=rid,dataset_namespace=provider.namespace,dataset_revision=provider._manifest["dataset_revision"],knowledge_revision=provider._authority.knowledge_revision,reference_date=reference,bounds=dict(start=getattr(ops,"scope_start",start),end=getattr(ops,"scope_end",end),closure="both"),time_basis="Observation/event timestamps; repairs by started_at; installed pump identity by completed replacement",rows=page,columns=provider._result_columns(page,[("hours_to_response","hour"),("deadline_hours","hour"),("installation_cost_usd","USD"),("spill_volume_bbl","bbl"),("median_extra_days","day"),("share","fraction")]),coverage=coverage,summary=summary,assessment_counts=counts,total_rows=len(rows),limit=limit,offset=offset,rule_refs=list(dict.fromkeys(ops.rules)),lineage_manifest_ref=rid,trace_id=trace,warnings=ops.warnings)
    provider._persist_manifest(rid,plan,context,provider._authority,result)
    provider._results[rid]=dict(plan=dict(plan),context=dict(context),authority=provider._authority,result=result)
    while len(provider._results)>32:provider._results.popitem(last=False)
    return result
