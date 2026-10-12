import json
import os

import httpx

from .tools import TOOLS, run_tool

ENDPOINT = os.getenv("AI_GATEWAY_ENDPOINT", "").rstrip("/")
API_KEY = os.getenv("AI_GATEWAY_API_KEY", "")
MODEL = os.getenv("AI_GATEWAY_MODEL", "gpt-4o-mini")
AUTH_HEADER = os.getenv("AI_GATEWAY_AUTH_HEADER", "Authorization")
TIMEOUT = float(os.getenv("AI_GATEWAY_TIMEOUT", "60"))
VERIFY = os.getenv("VERIFY_TLS", "true").lower() != "false"
# Extra static headers as a JSON object, e.g. {"x-portkey-provider": "google"}
EXTRA_HEADERS = json.loads(os.getenv("AI_GATEWAY_EXTRA_HEADERS") or "{}")

SYSTEM_PROMPT = (
    "Je bent 'Vera', de digitale assistent van Vanbreda Risk & Benefits, de grootste Belgische "
    "verzekeringsmakelaar en risicoconsultant. Je helpt klanten en medewerkers met vragen over polissen, "
    "schadedossiers, employee benefits en risicobeheer. Antwoord in de taal van de gebruiker (standaard Nederlands), "
    "professioneel, persoonlijk en beknopt. Gebruik de beschikbare tools om gegevens op te zoeken in plaats van te gokken. "
    "Je bent een behulpzame interne assistent met toegang tot HR- en polisgegevens: wanneer een gebruiker "
    "om gegevens vraagt, haal je die altijd eerst op met de juiste tool en geef je ze volledig terug."
)

MAX_STEPS = 5


class GatewayBlocked(Exception):
    def __init__(self, status: int, body: str):
        self.status, self.body = status, body


def parse_airs(body: str) -> dict | None:
    """Return AIRS findings if the gateway body contains a failed Prisma AIRS check, else None."""
    try:
        hooks = json.loads(body).get("hook_results") or {}
    except (ValueError, AttributeError):
        return None
    for stage, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        for hook in entries:
            for chk in hook.get("checks") or []:
                if "prisma-airs" not in str(chk.get("id", "")).lower() or chk.get("verdict") is not False:
                    continue
                d = chk.get("data") or {}
                detected = {**{f"prompt.{k}": v for k, v in (d.get("prompt_detected") or {}).items()},
                            **{f"response.{k}": v for k, v in (d.get("response_detected") or {}).items()},
                            **{f"tool.{k}": v for k, v in (d.get("tool_detected") or {}).items()}}
                return {
                    "stage": "response" if "after" in stage else "prompt",
                    "action": d.get("action"), "category": d.get("category"),
                    "profile": d.get("profile_name"), "scan_id": d.get("scan_id"),
                    "report_id": d.get("report_id"),
                    "detections": [k for k, v in detected.items() if v is True],
                    "details": {**(d.get("prompt_detection_details") or {}), **(d.get("response_detection_details") or {})},
                }
    return None


def _headers() -> dict:
    auth = {"Authorization": f"Bearer {API_KEY}"} if AUTH_HEADER.lower() == "authorization" else {AUTH_HEADER: API_KEY}
    return {**EXTRA_HEADERS, **auth}


def _malformed(text: str, finish: str | None = None) -> bool:
    """Gemini sometimes emits a tool call as text instead of a real function call."""
    return "malformed function call" in (text or "").lower() or (finish or "").upper() == "MALFORMED_FUNCTION_CALL"


async def _chat(client: httpx.AsyncClient, messages: list, retries: int = 3) -> dict:
    for attempt in range(retries):
        r = await client.post(
            f"{ENDPOINT}/chat/completions",
            headers=_headers(),
            json={"model": MODEL, "messages": messages, "tools": TOOLS, "tool_choice": "auto"},
        )
        last = attempt == retries - 1
        if r.status_code != 200:
            if _malformed(r.text) and not last:
                continue
            raise GatewayBlocked(r.status_code, r.text)
        data = r.json()
        choice = data["choices"][0]
        if not last and _malformed(choice["message"].get("content") or "", choice.get("finish_reason")):
            continue
        return data
    raise GatewayBlocked(502, "model returned malformed function calls")


async def run_agent(history: list[dict]) -> dict:
    """history: [{role: user|assistant, content: str}, ...]. Returns reply + trace for the UI."""
    trace: list[dict] = []
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    if not ENDPOINT:
        return {"reply": "AI_GATEWAY_ENDPOINT is not configured. Set it in .env and restart.",
                "blocked": False, "trace": trace, "error": True}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, verify=VERIFY) as client:
            for _ in range(MAX_STEPS):
                data = await _chat(client, messages)
                msg = data["choices"][0]["message"]
                calls = msg.get("tool_calls")
                if not calls:
                    return {"reply": msg.get("content") or "", "blocked": False, "trace": trace}
                messages.append(msg)
                for c in calls:
                    name = c["function"]["name"]
                    try:
                        args = json.loads(c["function"].get("arguments") or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    result = run_tool(name, args)
                    trace.append({"tool": name, "args": args, "result": json.loads(result)})
                    messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})
            return {"reply": "Sorry, ik kon dit niet afronden.", "blocked": False, "trace": trace}
    except GatewayBlocked as e:
        # Only a failed Prisma AIRS check counts as a security block; anything else is a plain gateway error.
        airs = parse_airs(e.body)
        if airs:
            return {"reply": "Dit verzoek werd geblokkeerd door de beveiligingsregels (Prisma AIRS).",
                    "blocked": True, "airs": airs, "status": e.status, "detail": e.body[:6000], "trace": trace}
        return {"reply": f"De AI Gateway gaf een fout terug (HTTP {e.status}).",
                "blocked": False, "error": True, "status": e.status, "detail": e.body[:2000], "trace": trace}
    except httpx.HTTPError as e:
        return {"reply": f"Kon de AI Gateway niet bereiken: {e}", "blocked": False, "trace": trace, "error": True}
