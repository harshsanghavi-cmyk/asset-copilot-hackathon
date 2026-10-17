"""Source-backed asset history and OPS-3 note precedence; no model work."""
import datetime as dt
import re


class AssetTimeline:
    def __init__(self, metadata, notes, operations_source=None, operations_effective=None):
        self.metadata = metadata
        self.operations_source = operations_source
        self.operations_effective = operations_effective
        self.notes = {}
        for note in notes:
            text = note.get("text", "")
            state = None
            shutdown = r"\bshut(?:[- ]in|\s+(?:the\s+)?well\s+in)\b"
            negated_shutdown = r"\b(?:not|never|didn't|hasn't|will|plan(?:ned)?)\b[^.!?;\n]{0,30}" + shutdown
            if re.search(shutdown, text, re.I) and not re.search(negated_shutdown, text, re.I):
                state = False
            elif re.search(r"\brestarted\b|\bput back on production\b|\bbrought\b.{0,50}\bback online\b|\breturned to production\b", text, re.I) and not re.search(r"\bnot\b.{0,15}\brestarted\b", text, re.I):
                state = True
            if state is not None:
                self.notes.setdefault(note["asset_id"], []).append(dict(note, interpreted_producing=state))
        for rows in self.notes.values():
            rows.sort(key=lambda n: (n["created_at"], n["note_id"]), reverse=True)

    def at(self, asset_id, field, when):
        metadata = self.metadata.get(asset_id, {})
        history = metadata.get("type_history" if field == "well_type" else "team_history")
        if not history:
            return metadata.get(field)
        day = str(when)[:10]
        matches = [row.get(field) for row in history if (not row.get("from") or row["from"][:10] <= day)
                   and (not row.get("to") or day <= row["to"][:10])]
        return matches[0] if len(matches) == 1 else None

    def status(self, asset_id, inspected_at, inspection_producing, reference):
        inspection_producing = None if inspection_producing is None else bool(inspection_producing)
        metadata = self.metadata.get(asset_id, {})
        day = str(reference)[:10]
        until = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
        note = next((n for n in self.notes.get(asset_id, []) if n["created_at"] < until), None)
        status = {"producing": inspection_producing, "status_confirmed": inspection_producing is not None,
                  "status_source": "inspection", "latest_status_note_id": note["note_id"] if note else None,
                  "latest_status_note_at": note["created_at"] if note else None,
                  "latest_status_note_text": note["text"] if note else None,
                  "latest_status_note_author_user_id": note["author_user_id"] if note else None,
                  "status_note_disagrees": bool(note and inspection_producing is not None
                                                and note["interpreted_producing"] != bool(inspection_producing))}
        closed = metadata.get("decommissioned_on")
        if metadata.get("status") == "plugged_and_abandoned" and closed and closed[:10] <= day:
            status.update(producing=False, status_confirmed=True, status_source="decommissioned_metadata")
        elif (self.operations_source and (not self.operations_effective or day >= self.operations_effective)
              and note and (not inspected_at or note["created_at"] > inspected_at)):
            status.update(producing=note["interpreted_producing"], status_confirmed=not note["interpreted_producing"],
                          status_source="operator_note", status_rule_source=self.operations_source)
        state = status["producing"]
        status["status_now"] = ("Unknown" if state is None else "Producing oil" if state else "Not producing oil")
        if state and not status["status_confirmed"]:
            status["status_now"] += " (unconfirmed)"
        return status
