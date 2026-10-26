# Sentinel-IR MCP onboarding QA — independent sample

An original, AI-assisted functional QA sample for `sentinel-ir-mcp@0.2.2`, prepared by the existing VM2 operator. This repository is a capability sample, **not a commissioned delivery, a security audit, an accepted bounty, or evidence of payment**. It uses only synthetic code and temporary client configuration files.

## Reproduce

Requirements: Linux, Node.js 22, Python 3.11 or newer, npm.

```sh
npm ci --ignore-scripts --no-audit --no-fund
python3 tests/run_qa.py
```

No wallet, API credential, LLM subscription, desktop client, or mainnet action is needed. The runner creates and removes its own fixtures beneath `runtime/`. It clears the tested processes' environment and applies Node filesystem permissions scoped to this repository. The reviewed `doctor` command is allowed to start its own Node stdio server. These precautions are **not** an operating-system sandbox or a network-isolation guarantee.

## Observed result

On 26 October 2026, Linux / Node.js v22.23.2: **16 tests passed, 0 failures, 0 errors**. See `evidence/test-transcript.txt` and `evidence/qa-results.json` for commands, output, timestamps, dependency-lock hash, and limitations.

Coverage:

- Exact CLI version, help, and directory-first guide workflow.
- Cursor dry-run and noninteractive confirmation behavior.
- Portable project configuration; preservation of existing servers and preferences; byte-exact backup; idempotent second setup.
- Unchanged malformed JSON rather than silent overwrite.
- Windsurf configuration under a synthetic HOME.
- VS Code and Claude Code installation commands **printed, not executed**.
- Real stdio MCP handshake, the three expected tools, and analysis of one synthetic file.
- Missing-config diagnostic failure, plus project paths containing spaces.

## Interpretation

`doctor` starts its own copy of the package. A successful handshake is not proof that Cursor, Windsurf, VS Code or Claude Desktop launches the saved configuration successfully. No desktop application, macOS/Windows installation, private source, production service, or payment path was exercised.

The initial harness expected the guide to enumerate `analyze_code` and expected no-consent setup to exit zero. Reviewing the published implementation showed these were incorrect harness assumptions: the guide intentionally describes the directory/file workflow, and noninteractive setup without `--yes` returns 1 without writing. Both initial results are retained under `evidence/initial-*`; they are **not reported as product defects**. Tool enumeration is independently checked by the actual MCP handshake test.

## Source and integrity

Upstream package: https://www.npmjs.com/package/sentinel-ir-mcp/v/0.2.2

Upstream source: https://gitlab.com/jakubrojicek11/sentinel-ir-mcp/-/tree/v0.2.2

Published tarball SHA-256 verified during acquisition:
`2847b7c82c32b1ccb80d3c70fe5901cbde6b60f75c54997ea202b4881777f348`

The registry's SHA-512 integrity value was also checked before extracting the package. Direct dependency versions are pinned and transitive resolutions are captured in `package-lock.json`.

Original harness/report: MIT. Upstream dependency code and generated CLI text retain their respective licenses, including Apache-2.0 for Sentinel-IR MCP. Upstream source is not copied into this repository.
