# Security Policy — PlanMyTrip AI

PlanMyTrip AI is an enterprise-grade multi-agent travel orchestration engine. We take the security, privacy, and integrity of our application, infrastructure, and user data seriously. This document outlines our security policies, built-in architectural safeguards, and the process for responsibly reporting vulnerabilities.

---

## 1. Supported Versions

Security updates, dependency patches, and vulnerability fixes are actively maintained for the following branches:

| Version / Branch | Supported | Security Maintenance |
| :--- | :--- | :--- |
| `main` (Latest) | :white_check_mark: Yes | Active vulnerability triage, patch releases, and dependency updates |
| `< 1.0.0` (Legacy tags) | :x: No | Please upgrade to the latest `main` commit |

---

## 2. Security Architecture & Built-in Defenses

PlanMyTrip AI implements defense-in-depth principles across all application layers:

### A. Multi-Layer Input Guardrails & Adversarial Defenses
- **Prompt Injection & System Jailbreak Defense**: All incoming user queries pass through an automated [Input Guardrail](backend/app/guardrails/input_guard.py) before reaching the LangGraph multi-agent orchestrator.
- **Out-of-Domain & Harmful Intent Rejection**: Explicit classification filters reject malicious code generation, port scanning scripts, destructive chemical synthesis, and non-travel queries with a deterministic 96.0%+ accuracy.
- **Sanitized Parsing**: User parameters (dates, destinations, passenger counts) are validated and parsed through strictly-typed Pydantic schemas, eliminating format-string injection and buffer manipulation risks.

### B. Authentication & State Isolation
- **Cryptographic Tokens**: User sessions use JSON Web Tokens (JWT) signed with cryptographically secure secrets (`JWT_SECRET`) using `HS256`.
- **Password Security**: Credentials are protected using one-way salted `bcrypt` hashing before database persistence.
- **Relational LangGraph Checkpoint Ownership**: Multi-agent conversational threads backed by PostgreSQL (`AsyncPostgresSaver`) enforce strict cryptographic binding between `user_id` and `thread_id`. Users cannot inspect, read, or resume state machines belonging to other accounts.

### C. Secret Discipline & Environment Isolation
- **Zero Hardcoded Secrets**: Sensitive API credentials (`OPENAI_API_KEY`, `SERPAPI_API_KEY`, `FLIGHTAPI_KEY`, `TAVILY_API_KEY`, `JWT_SECRET`, database passwords) are loaded exclusively via environment variables using Pydantic Settings.
- **Git Hygiene**: Environment files (`.env`, `.env.*`) are strictly excluded from version control via `.gitignore`.
- **Credential Scoping**: External travel API tokens are isolated within individual Model Context Protocol (MCP) server microservices rather than distributed broadly across agent runtimes.

### D. Model Context Protocol (MCP) Tool Sandboxing
- **Network Decoupling**: Tool execution runs across independent internal microservices on loopback interfaces (`127.0.0.1:8001-8003`).
- **Resilience Controls**: Outbound HTTP tool invocations are wrapped in automated circuit breakers and retry limiters (`backend/app/resilience/`), preventing cascading failure or denial-of-service from upstream provider outages.

### E. Financial Arithmetic & Zero PII Guarantee
- **No Financial PII Storage**: PlanMyTrip AI generates travel itineraries and price estimations. The platform **never** collects, processes, or stores payment card numbers, CVVs, UPI PINs, or banking credentials.
- **Deterministic Math**: Monetary totals are calculated using Python `decimal.Decimal` with ISO-4217 currency tracking, completely preventing floating-point rounding errors and reconciliation drift.

---

## 3. Reporting a Vulnerability

If you discover a potential security vulnerability within PlanMyTrip AI, please report it responsibly. **Do not create public GitHub issues or discussions for undisclosed security flaws.**

### How to Report

1. **Email Disclosure**: Send details to the maintainer:
   - **Maintainer**: Jaywardhan Yadav
   - **Email**: [jaywardhan0310@gmail.com](mailto:jaywardhan0310@gmail.com)
   - **Subject Line**: `[SECURITY VULNERABILITY] PlanMyTrip-AI - <Brief Description>`
2. **GitHub Security Advisory**: Alternatively, submit a private advisory through the repository's **Security > Advisories** tab on GitHub.

### What to Include in Your Report

To help us investigate and resolve the issue quickly, please include:
- A clear description of the vulnerability and its potential impact.
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- Affected endpoints, files, or agent components.
- Any proposed mitigations or remediation steps if available.

---

## 4. Vulnerability Response Timeline

We commit to the following response standards:

| Milestone | Target SLA | Description |
| :--- | :--- | :--- |
| **Initial Acknowledgment** | Within 24–48 hours | Confirmation that the report has been received and initial assessment has started |
| **Triage & Reproduction** | Within 3–5 business days | Verification of the issue and determination of severity score (CVSS) |
| **Patch Development** | Within 7–14 business days | Implementation of targeted fix and automated regression testing |
| **Public Disclosure** | Coordinated Release | Public patch release and advisory attribution to the reporter |

---

## 5. Responsible Disclosure Guidelines

When conducting security research on this project:
- **Do not** attempt to disrupt or degrade availability (DoS / DDoS).
- **Do not** access, modify, or destroy another user's data.
- **Do not** publicly disclose the issue until an official patch has been deployed.
- Maintain communication throughout the triage and remediation process.

---

*Thank you for helping keep PlanMyTrip AI and the open-source community safe and secure.*
