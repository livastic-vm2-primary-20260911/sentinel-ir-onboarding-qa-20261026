# Reproducible onboarding observations

## Confirmed behavior

The setup flow preserves an unrelated synthetic MCP server and an unrelated top-level preference. It writes a backup containing the original bytes when it changes an existing configuration. A second identical setup does not create another backup or alter the file. A dry run and noninteractive invocation without consent leave configuration untouched. Malformed JSON is refused without modification.

The real `doctor` process completed its package-owned MCP handshake and listed `analyze_code`, `analyze_directory`, and `analyze_file`. Its directory call reported exactly one checked synthetic file. A missing Cursor configuration caused overall `ok:false`, even though the package could still be started for its independent handshake. This distinction is useful when interpreting automated onboarding logs.

## Documentation integration suggestions

1. State that noninteractive setup without `--yes` returns exit status 1 and makes no change. Automation should choose an explicit dry-run or consented setup mode rather than interpret this as an installer crash.
2. Keep the distinction between package-owned `doctor` diagnostics and the real desktop client's configured launcher prominent.
3. Use an exact package version for reproducibility in a release-specific troubleshooting example; keep the moving `@0.2` example only where following the release line is intended.

These are clarity/integration suggestions, not security findings. The current observed cases passed after correcting two initial expectations in the independent harness.

## Scope of a possible paid engagement

A separately accepted fixed-scope engagement could integrate this synthetic-only suite into an agreed upstream branch, add an agreed CI job, and produce a concise troubleshooting guide, with one review revision. Repository permission, a specific brief, and a supported payout route must be agreed first. No project endorsement, employment, commercial warranty, or paid acceptance is implied by this sample.
