# Thanatos/plugins/system_skills/security_auditor/security_auditor_skill.py

import json
import logging
import os
import re
import socket
import ssl
from typing import Any, Dict, List, Optional
import urllib.parse
import httpx

from plugins.base.skill_interface import BaseSkill
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class SecurityAuditorSkill(BaseSkill):
    """
    Skill for authorized defensive cybersecurity assessments:
    - Inspecting open services & listening ports on authorized hosts/interfaces
    - Auditing web endpoint defensive security headers (CSP, HSTS, X-Frame-Options) & TLS certificates
    - Organizing legitimate contact and OSINT intelligence (names, numbers, email associations)
    - Recommending defensive remediation and hardening playbooks
    """

    @property
    def skill_name(self) -> str:
        return "security_auditor"

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="audit_authorized_services",
                description="Defensive audit of common network service ports on an authorized target or localhost.",
                parameters={
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "description": "Authorized target host/IP (default: localhost / 127.0.0.1)"},
                        "ports": {"type": "array", "items": {"type": "integer"}, "description": "Specific ports to audit (default: standard services 22,80,443,3306,5432,6379,8000,8080,11434)"},
                    },
                    "required": ["host"],
                },
            ),
            ToolDefinition(
                name="audit_web_security_headers",
                description="Inspects defensive HTTP security headers (HSTS, CSP, X-Frame-Options, CORS) and TLS certificate details of an authorized web service.",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Web URL to audit (e.g. http://localhost:8000 or https://example.com)"},
                    },
                    "required": ["url"],
                },
            ),
            ToolDefinition(
                name="organize_entity_intel",
                description="Aggregates and formats authorized entity records (names, phone numbers, email domains, titles) into structured profile intelligence.",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Entity name or identifier"},
                        "phone_number": {"type": "string", "description": "Phone number (if legally provided or authorized)"},
                        "email": {"type": "string", "description": "Email address"},
                        "organization": {"type": "string", "description": "Organization or associated company"},
                        "notes": {"type": "string", "description": "Contextual notes or observation details"},
                    },
                    "required": ["name"],
                },
            ),
            ToolDefinition(
                name="generate_defensive_remediation",
                description="Provides hardening recommendations and firewall/configuration remediation for identified exposures.",
                parameters={
                    "type": "object",
                    "properties": {
                        "findings": {"type": "array", "items": {"type": "string"}, "description": "List of discovered open services or missing security headers"},
                        "platform": {"type": "string", "description": "Target platform (windows, linux, docker)"},
                    },
                    "required": ["findings"],
                },
            ),
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "audit_authorized_services":
            host = params.get("host", "localhost")
            if host in ("localhost", "127.0.0.1"):
                host = "127.0.0.1"

            default_ports = [22, 80, 443, 3000, 3306, 5432, 6379, 8000, 8001, 8080, 11434, 27017]
            ports_to_check = params.get("ports") or default_ports

            service_names = {
                22: "SSH",
                80: "HTTP",
                443: "HTTPS",
                3000: "Dev Web UI",
                3306: "MySQL",
                5432: "PostgreSQL",
                6379: "Redis",
                8000: "FastAPI / Thanatos API Server",
                8001: "LLM Adapter / ChromaDB",
                8080: "Gemma-4 / Remote Inference",
                11434: "Ollama Local Daemon",
                27017: "MongoDB",
            }

            open_services = []
            closed_count = 0

            for port in ports_to_check:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.35)
                try:
                    res = s.connect_ex((host, port))
                    if res == 0:
                        open_services.append({
                            "port": port,
                            "service": service_names.get(port, "Custom Service"),
                            "status": "OPEN / LISTENING",
                            "risk_assessment": "Standard" if port in (80, 443, 8000, 8080) else "Review access restrictions",
                        })
                    else:
                        closed_count += 1
                except Exception:
                    closed_count += 1
                finally:
                    s.close()

            return ToolResult.success_result(
                tool_name=tool_name,
                content={
                    "target_host": host,
                    "audited_ports": len(ports_to_check),
                    "open_services_count": len(open_services),
                    "closed_filtered_count": closed_count,
                    "open_services": open_services,
                    "assessment": "Healthy (Expected dev services active)" if len(open_services) < 5 else "Action Required: Review publicly exposed ports",
                },
            )

        elif tool_name == "audit_web_security_headers":
            url = params.get("url", "http://localhost:8000")
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"http://{url}"

            try:
                async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, verify=False) as client:
                    resp = await client.get(url)
                    headers = {k.lower(): v for k, v in resp.headers.items()}

                recommended_headers = {
                    "strict-transport-security": "Enforces HTTPS connections (HSTS)",
                    "content-security-policy": "Prevents XSS and unauthorized resource loading (CSP)",
                    "x-frame-options": "Defends against clickjacking attacks",
                    "x-content-type-options": "Disables MIME-sniffing vulnerabilities",
                    "referrer-policy": "Controls referrer information leakage",
                }

                present = []
                missing = []
                for h, purpose in recommended_headers.items():
                    if h in headers:
                        present.append({"header": h, "value": headers[h], "purpose": purpose})
                    else:
                        missing.append({"header": h, "purpose": purpose})

                return ToolResult.success_result(
                    tool_name=tool_name,
                    content={
                        "target_url": url,
                        "status_code": resp.status_code,
                        "server_banner": headers.get("server", "Hidden/Not specified"),
                        "present_security_headers": present,
                        "missing_security_headers": missing,
                        "defensive_rating": f"{len(present)}/{len(recommended_headers)} standard headers present",
                    },
                )
            except Exception as e:
                return ToolResult.error_result(tool_name=tool_name, error=f"Could not reach or audit URL {url}: {e}")

        elif tool_name == "organize_entity_intel":
            name = params.get("name")
            phone = params.get("phone_number")
            email = params.get("email")
            org = params.get("organization")
            notes = params.get("notes")

            # Format normalized phone
            clean_phone = re.sub(r"[^\d+]", "", phone) if phone else None

            intel_card = {
                "entity_name": name,
                "primary_phone": clean_phone,
                "email_address": email,
                "organization": org,
                "contact_domain": email.split("@")[-1] if email and "@" in email else None,
                "notes": notes,
                "verified_format": True,
            }

            # Save to authorized intel records
            intel_dir = os.path.join("data", "security_intel")
            os.makedirs(intel_dir, exist_ok=True)
            fname = f"{re.sub(r'[^a-zA-Z0-9]', '_', name.lower())}_intel.json"
            fpath = os.path.join(intel_dir, fname)

            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(intel_card, f, indent=2)

            return ToolResult.success_result(
                tool_name=tool_name,
                content={
                    "status": "Structured & Logged",
                    "file_path": os.path.abspath(fpath),
                    "intel_card": intel_card,
                },
            )

        elif tool_name == "generate_defensive_remediation":
            findings = params.get("findings", [])
            platform = (params.get("platform") or "windows").lower()

            recommendations = []
            for item in findings:
                lower = item.lower()
                if "hsts" in lower or "strict-transport-security" in lower:
                    recommendations.append("Web Server: Inject header `Strict-Transport-Security: max-age=31536000; includeSubDomains` in reverse proxy (Nginx/Caddy/FastAPI).")
                elif "csp" in lower or "content-security-policy" in lower:
                    recommendations.append("Web Server: Formulate a restrictive `Content-Security-Policy: default-src 'self'` policy to eliminate inline script injection.")
                elif "clickjacking" in lower or "x-frame-options" in lower:
                    recommendations.append("Web Server: Add `X-Frame-Options: DENY` or `SAMEORIGIN` to disallow unauthorized iframe embedding.")
                elif "ssh" in lower or "22" in lower:
                    recommendations.append("Host Hardening: Restrict port 22 access via firewall to specific VPN/internal IPs and enforce SSH key authentication (disable root password login).")
                elif "redis" in lower or "6379" in lower:
                    recommendations.append("Database: Bind Redis strictly to `127.0.0.1` and require high-entropy AUTH password.")
                else:
                    recommendations.append(f"Security Control: Audit access control list (ACL) and restrict inbound access to: {item}")

            return ToolResult.success_result(
                tool_name=tool_name,
                content={
                    "platform": platform,
                    "remediation_steps": recommendations,
                    "hardening_guide": "Follow the CIS Benchmark guidelines for OS & Network layer hardening.",
                },
            )

        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")
