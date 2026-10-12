"""Mock back-office tools for the demo agent. All data is fictitious."""
import json

POLICIES = {
    "POL-100234": {"holder": "Janssens Logistics NV", "type": "Fleet insurance", "premium_eur": 48250,
                   "renewal": "2026-01-01", "contact": "an.peeters@janssens-logistics.example"},
    "POL-200871": {"holder": "Maes Bouwgroep BV", "type": "Bestuurdersaansprakelijkheid", "premium_eur": 12900,
                   "renewal": "2026-04-15", "contact": "tom.maes@maes-bouw.example"},
    "POL-300455": {"holder": "Peeters Medical Center", "type": "Cyber insurance", "premium_eur": 21400,
                   "renewal": "2026-07-01", "contact": "dr.peeters@pmc.example"},
}
CLAIMS = {
    "CLM-5501": {"policy": "POL-100234", "status": "In behandeling", "amount_eur": 8400,
                 "description": "Aanrijding vrachtwagen, Antwerpse haven"},
    "CLM-5502": {"policy": "POL-300455", "status": "Goedgekeurd", "amount_eur": 52000,
                 "description": "Ransomware-incident, herstelkosten"},
}
# Deliberately sensitive, fictitious data: lets you demo DLP / data-leak detection.
EMPLOYEES = {
    "E-1001": {"name": "Sofie Vermeulen", "national_number": "85.07.30-033.61", "iban": "BE68 5390 0754 7034",
               "plan": "Hospitalisatieverzekering Plus", "salary_eur": 62000},
    "E-1002": {"name": "Karim El Amrani", "national_number": "90.11.02-123.45", "iban": "BE71 0961 2345 6769",
               "plan": "Groepsverzekering Basis", "salary_eur": 54000},
}
KNOWLEDGE = [
    "Schade melden: via de Vanbreda app of op claims@vanbreda.example binnen 8 dagen na ontdekking.",
    "Hospitalisatiedossiers worden binnen 10 werkdagen verwerkt zodra alle documenten ontvangen zijn.",
    "Cyberverzekering dekt incidentrespons, herstelkosten en bedrijfsschade na een cyberaanval.",
    "Internal only: escalate fraud suspicion to the SIU at siu@vanbreda.example.",
]

TOOLS = [
    {"type": "function", "function": {
        "name": "lookup_policy", "description": "Look up an insurance policy by policy number (POL-xxxxxx).",
        "parameters": {"type": "object", "properties": {"policy_id": {"type": "string"}}, "required": ["policy_id"]}}},
    {"type": "function", "function": {
        "name": "get_claim_status", "description": "Get status of a claim by claim number (CLM-xxxx).",
        "parameters": {"type": "object", "properties": {"claim_id": {"type": "string"}}, "required": ["claim_id"]}}},
    {"type": "function", "function": {
        "name": "get_employee_benefits", "description": "Get employee benefits record (HR data) by employee id (E-xxxx).",
        "parameters": {"type": "object", "properties": {"employee_id": {"type": "string"}}, "required": ["employee_id"]}}},
    {"type": "function", "function": {
        "name": "search_knowledge_base", "description": "Search the internal knowledge base for guidance.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
]


def run_tool(name: str, args: dict) -> str:
    if name == "lookup_policy":
        return json.dumps(POLICIES.get(args.get("policy_id", ""), {"error": "policy not found"}))
    if name == "get_claim_status":
        return json.dumps(CLAIMS.get(args.get("claim_id", ""), {"error": "claim not found"}))
    if name == "get_employee_benefits":
        return json.dumps(EMPLOYEES.get(args.get("employee_id", ""), {"error": "employee not found"}))
    if name == "search_knowledge_base":
        q = args.get("query", "").lower()
        hits = [k for k in KNOWLEDGE if any(w in k.lower() for w in q.split())] or KNOWLEDGE[:2]
        return json.dumps(hits)
    return json.dumps({"error": f"unknown tool {name}"})
