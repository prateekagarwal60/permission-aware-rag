"""Domain model + the single source of truth for access decisions.

The `allowed()` function is the whole point of the project. It encodes real
enterprise access rules that most RAG demos ignore:
  - row / team scoping (a manager sees their own team's comp, not another team's)
  - a seniority ceiling (even the CFO is denied board-only and exec-subject HR cases)
It is pure and deterministic, so it doubles as the oracle the harness scores against.
"""
import json
import os
from dataclasses import dataclass, field

FIX = os.path.join(os.path.dirname(__file__), "..", "fixtures")

# Classes whose access depends on the asking person's team, not just their role.
TEAM_SCOPED = {"individual_comp", "hr_investigation"}
# Classes where own-team membership grants access (plus whatever the matrix adds).
OWN_TEAM = {"team_doc", "source_code"}


@dataclass
class Persona:
    id: str
    role: str
    team: str | None = None
    is_manager: bool = False


@dataclass
class Doc:
    id: str
    title: str
    department: str
    data_class: str
    text: str
    team: str | None = None
    exec_subject: bool = False
    canaries: list = field(default_factory=list)


def allowed(persona: Persona, doc: Doc, matrix: dict) -> bool:
    """Return True if `persona` is permitted to see `doc`."""
    dc = doc.data_class

    if dc == "public":
        return True

    if dc in OWN_TEAM:
        if persona.team and doc.team and persona.team == doc.team:
            return True
        return matrix.get(dc, {}).get(persona.id, False)

    if dc in TEAM_SCOPED:
        if persona.id == "hr_partner":
            return True
        if persona.id == "exec_cfo":
            # The seniority ceiling: the CFO is blocked from an HR case about an exec.
            return not (dc == "hr_investigation" and doc.exec_subject)
        if persona.is_manager and persona.team and doc.team and persona.team == doc.team:
            return True
        return False

    # Everything else: plain role-based matrix lookup.
    return matrix.get(dc, {}).get(persona.id, False)


def allowed_personas(doc: Doc, personas: dict, matrix: dict) -> list:
    return [pid for pid, p in personas.items() if allowed(p, doc, matrix)]


def load():
    def rd(name):
        with open(os.path.join(FIX, name)) as f:
            return json.load(f)

    personas = {p["id"]: Persona(**p) for p in rd("personas.json")}
    matrix = rd("matrix.json")
    corpus = [Doc(**d) for d in rd("corpus.json")]
    canaries = rd("canaries.json")
    return personas, matrix, corpus, canaries
