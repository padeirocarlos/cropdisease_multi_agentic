import re
import os
import ast
import base64
import json
import urllib
import urllib.parse
from typing import Any
from datetime import datetime

# --- Third-party ---
import duckdb
import pandas as pd
from IPython.display import display, HTML

# list of preferred domains for Tavily results
TOP_AGRO_DOMAINS = {
    # USDA Agricultural Research Service:
   " ars.usda.gov",
    # USA National Plant Diagnostic Network:
    "npdn.org",
    # Agriculture and Agri-Food Canada:
    "agriculture.canada.ca",
    # Australian Centre for International Agricultural Research (ACIAR):
    "aciar.gov.au",
    # FAO (Food and Agriculture Organization of the United Nations):
    "fao.org/plant-production-protection",
    # Cornell University - College of Agriculture and Life Sciences:
    "cals.cornell.edu",
    # University of California - Statewide Integrated Pest Management Program (UC IPM):
    "ipm.ucanr.edu",
    # University of Florida - IFAS Extension:
    "sfyl.ifas.ufl.edu",
    # Iowa State University - Extension and Outreach:
    "extension.iastate.edu",
    # Purdue University - Extension:
    "extension.purdue.edu",
    # International Maize and Wheat Improvement Center (CIMMYT):
    "cimmyt.org",
    # International Rice Research Institute (IRRI):
    "irri.org",
    # International Institute of Tropical Agriculture (IITA):
    "iita.org",
    # EPPO (European Plant Protection)
    "eppo.int",
}

TOP_DOMAINS = {
    # General reference / institutions / publishers
    "wikipedia.org", "nature.com", "science.org", "sciencemag.org", "cell.com",
    "mit.edu", "stanford.edu", "harvard.edu", "nasa.gov", "noaa.gov", "europa.eu",

    # CS/AI venues & indexes
    "arxiv.org", "acm.org", "ieee.org", "neurips.cc", "icml.cc", "openreview.net",

    # Other reputable outlets
    "elifesciences.org", "pnas.org", "jmlr.org", "springer.com", "sciencedirect.com",

    # Extra domains (case-specific additions)
    "pbs.org", "nova.edu", "nvcc.edu", "cccco.edu",

    # Well known programming sites
    "codecademy.com", "datacamp.com"
}

_URL_RE = re.compile(r"https?://[^\s\)\]\}<>\"']+", re.IGNORECASE)

def _extract_hostname(url: str) -> str:
    try:
        host = urllib.parse.urlparse(url).hostname or ""
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""

def extract_urls(text: str) -> list[dict[str, Any]]:
    """
    Best-effort URL extractor from arbitrary text.
    Returns list of {title, url, source} dicts (title/source may be None).
    """
    if not isinstance(text, str):
        text = str(text)
    urls = _URL_RE.findall(text)
    items = []
    for u in urls:
        host = _extract_hostname(u)
        items.append({"title": None, "url": u, "source": host or None})
    return items

def json_block_cleaner(raw: str) -> str:
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return raw.strip()


def evaluate_anytext_against_domains(TOP_DOMAINS: set[str], payload: Any, min_ratio: float = 0.4):
    """
    Accepts:
      - raw list[dict] (Tavily-like), or
      - raw string (free text with links), or
      - dict with 'results' list
    Returns (ok, report_dict), same shape as before.
    """
    # Normalize into items: list[dict(title,url,source)]
    items = []
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
        items = payload["results"]
    elif isinstance(payload, str):
        # try JSON first
        s = payload.strip()
        if s.startswith("```"):
            s = re.sub(r"^```(?:json|text|markdown)?\s*", "", s)
            s = re.sub(r"\s*```$", "", s)
        try:
            maybe = json.loads(s)
            if isinstance(maybe, list):
                items = maybe
            else:
                items = extract_urls(payload)
        except Exception:
            items = extract_urls(payload)
    else:
        items = extract_urls(str(payload))

    total = len(items)
    if total == 0:
        return False, {"total": 0, "approved": 0, "ratio": 0.0, "details": [], "note": "No items/links parsed"}

    details = []
    approved = 0
    for it in items:
        url = (it or {}).get("url")
        host = _extract_hostname(url or "")
        ok = any(host.endswith(dom) for dom in TOP_DOMAINS) if host else False
        if ok:
            approved += 1
        details.append({
            "title": (it or {}).get("title"),
            "url": url,
            "host": host,
            "approved": ok,
        })

    ratio = approved / max(total, 1)
    ok = ratio >= min_ratio
    return ok, {"total": total, "approved": approved, "ratio": ratio, "details": details, "min_ratio": min_ratio}

def evaluate_references(history: list[tuple[str, str, str]], TOP_DOMAINS: set[str], min_ratio: float = 0.4) -> str:
    """
    Pure evaluator. Finds the most recent research_agent output (any text or JSON),
    extracts links, compares domains to TOP_DOMAINS, and returns a Markdown PASS/FAIL.
    """
    # 1) Prefer latest research_agent output
    payload = None
    for step, agent, output in reversed(history):
        if agent == "research_agent":
            payload = output
            break
    # 2) Fallback: any output with links or array-looking text
    if payload is None:
        for _, _, output in reversed(history):
            if isinstance(output, str) and (("http://" in output) or ("https://" in output) or ("[" in output and "]" in output)):
                payload = output
                break

    if payload is None:
        ok, report = False, {"total": 0, "approved": 0, "ratio": 0.0, "details": [], "min_ratio": min_ratio}
    else:
        ok, report = evaluate_anytext_against_domains(TOP_DOMAINS, payload, min_ratio=min_ratio)

    status = "✅ PASS" if ok else "⚠️ FAIL"
    header = f"### Evaluation — Tavily Top Domains ({status})"
    summary = (f"- Total: {report['total']}\n"
               f"- Approved: {report['approved']}\n"
               f"- Ratio: {report['ratio']:.0%} (min {int(min_ratio*100)}%)\n")

    rows = (report.get("details") or [])[:10]
    lines = ["| Host | Approved | Title |", "|---|:---:|---|"]
    for r in rows:
        lines.append(f"| {r.get('host') or '-'} | {'✔' if r.get('approved') else '—'} | {r.get('title') or r.get('url') or '-'} |")

    note = "*Note: Evaluation compares extracted link domains to a fixed allow-list (`TOP_DOMAINS`) and does not re-query tools.*"
    return "\n".join([header, summary, *lines, note])


def evaluate_reliable_results(TOP_AGRO_DOMAINS, raw: str, min_ratio=0.4):
    """
    Evaluate whether plain-text research results mostly come from preferred domains.

    Args:
        TOP_AGRO_DOMAINS (set[str]): Set of preferred domains (e.g., 'arxiv.org', 'nature.com').
        raw (str): Plain text or Markdown containing URLs.
        min_ratio (float): Minimum preferred ratio required to pass (e.g., 0.4 = 40%).

    Returns:
        tuple[bool, str]: (flag, markdown_report)
            flag -> True if PASS, False if FAIL
            markdown_report -> Markdown-formatted summary of the evaluation
    """

    # Extract URLs from the text
    url_pattern = re.compile(r'https?://[^\s\]\)>\}]+', flags=re.IGNORECASE)
    urls = url_pattern.findall(raw)

    if not urls:
        return False, """### Evaluation — Tavily Preferred Domains
            No URLs detected in the provided text. 
            Please include links in your research results.
            """

    # Count preferred vs total
    total = len(urls)
    preferred_count = 0
    details = []

    for url in urls:
        domain = url.split("/")[2]
        preferred = any(td in domain for td in TOP_AGRO_DOMAINS)
        if preferred:
            preferred_count += 1
        details.append(f"- {url} → {'✅ PREFERRED' if preferred else '❌ NOT PREFERRED'}")

    ratio = preferred_count / total if total > 0 else 0.0
    flag = ratio >= min_ratio

    # Markdown report
    report = f"""
        ### Evaluation — Tavily Preferred Domains
        - Total results: {total}
        - Preferred results: {preferred_count}
        - Ratio: {ratio:.2%}
        - Threshold: {min_ratio:.0%}
        - Status: {"✅ PASS" if flag else "❌ FAIL"}

        **Details:**
        {chr(10).join(details)}
        """
    return flag, report

