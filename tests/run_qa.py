#!/usr/bin/env python3
"""Independent, synthetic-only CLI and MCP onboarding checks.

No wallet, account credential, real desktop client or customer source is used.
The tested Node processes receive a clean environment and scoped filesystem
permissions. This is not an operating-system or network-isolation guarantee.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'runtime'
EVIDENCE = ROOT / 'evidence'
BIN = ROOT / 'node_modules/sentinel-ir-mcp/bin/sentinel-ir-mcp.js'
COMMANDS: list[dict] = []

def clean(text: str) -> str:
    return text.replace(str(ROOT), '<WORKROOT>')

class OnboardingQA(unittest.TestCase):
    def setUp(self) -> None:
        RUNTIME.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='case-', dir=RUNTIME)
        self.root = Path(self.tmp.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        (self.project / 'sample.js').write_text('export function add(a, b) { return a + b; }\n')
        self.home = self.root / 'home'
        self.home.mkdir()
        self.config = self.project / '.cursor/mcp.json'

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def cli(self, *args: str, child: bool = False) -> subprocess.CompletedProcess:
        env = {
            'HOME': str(self.home), 'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8',
            'NODE_OPTIONS': f'--permission --allow-fs-read={ROOT} --allow-fs-write={RUNTIME}',
        }
        # Only the reviewed doctor entrypoint needs to spawn its own Node server.
        # The child inherits scoped NODE_OPTIONS, but not --allow-child-process.
        cmd = [shutil.which('node') or '/usr/bin/node']
        if child:
            cmd.append('--allow-child-process')
        cmd += [str(BIN), *args]
        result = subprocess.run(cmd, cwd=self.project, env=env, input='',
                                capture_output=True, text=True, timeout=15)
        COMMANDS.append({'test': self.id().split('.')[-1],
                         'argv': [clean(x) for x in cmd],
                         'returncode': result.returncode,
                         'stdout': clean(result.stdout), 'stderr': clean(result.stderr)})
        return result

    def setup_cursor(self) -> subprocess.CompletedProcess:
        result = self.cli('setup', '--client', 'cursor', '--yes')
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_01_pinned_cli_version(self):
        r = self.cli('--version')
        self.assertEqual((r.returncode, r.stdout.strip()), (0, '0.2.2'))

    def test_02_help_names_onboarding_commands(self):
        r = self.cli('--help')
        self.assertEqual(r.returncode, 0, r.stderr)
        for value in ('setup', 'doctor', 'guide'):
            self.assertIn(value, r.stdout)

    def test_03_guide_orders_directory_then_file_and_caveats(self):
        r = self.cli('guide')
        self.assertEqual(r.returncode, 0, r.stderr)
        for value in ('analyze_directory', 'analyze_file', 'incomplete', 'not a security scanner'):
            self.assertIn(value, r.stdout)
        self.assertLess(r.stdout.index('analyze_directory'), r.stdout.index('analyze_file'))

    def test_04_cursor_dry_run_does_not_write(self):
        r = self.cli('setup', '--client', 'cursor', '--dry-run')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.config.exists())

    def test_05_noninteractive_setup_requires_consent(self):
        r = self.cli('setup', '--client', 'cursor')
        # setup.js intentionally returns 1 when noninteractive consent is absent.
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertFalse(self.config.exists())
        self.assertIn('Nothing was written', r.stdout)

    def test_06_cursor_setup_uses_portable_project_folder(self):
        self.setup_cursor()
        data = json.loads(self.config.read_text())
        entry = data['mcpServers']['sentinel-ir']
        self.assertEqual(entry['command'], 'npx')
        self.assertIn('${workspaceFolder}', entry['args'])

    def test_07_existing_servers_and_preferences_preserved(self):
        self.config.parent.mkdir()
        old = {'mcpServers': {'fixture-only': {'command': 'echo', 'args': ['synthetic']}},
               'fixturePreference': {'theme': 'plain'}}
        self.config.write_text(json.dumps(old))
        self.setup_cursor()
        data = json.loads(self.config.read_text())
        self.assertEqual(data['mcpServers']['fixture-only'], old['mcpServers']['fixture-only'])
        self.assertEqual(data['fixturePreference'], old['fixturePreference'])

    def test_08_existing_config_backup_matches_original_bytes(self):
        self.config.parent.mkdir()
        original = b'{"mcpServers":{},"fixture":true}\n'
        self.config.write_bytes(original)
        self.setup_cursor()
        backups = list(self.config.parent.glob('mcp.json.bak-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)

    def test_09_second_setup_is_idempotent(self):
        self.setup_cursor()
        before = self.config.read_bytes()
        self.setup_cursor()
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual(list(self.config.parent.glob('*.bak-*')), [])

    def test_10_invalid_json_remains_unchanged(self):
        self.config.parent.mkdir()
        original = b'{ "mcpServers": '
        self.config.write_bytes(original)
        r = self.cli('setup', '--client', 'cursor', '--yes')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.config.read_bytes(), original)

    def test_11_windsurf_setup_uses_isolated_home(self):
        r = self.cli('setup', '--client', 'windsurf', '--yes')
        self.assertEqual(r.returncode, 0, r.stderr)
        config = self.home / '.codeium/windsurf/mcp_config.json'
        self.assertIn('sentinel-ir', json.loads(config.read_text())['mcpServers'])

    def test_12_vscode_outputs_install_command_without_client_execution(self):
        r = self.cli('setup', '--client', 'vscode', '--yes')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('code --add-mcp', r.stdout)
        self.assertFalse(self.config.exists())

    def test_13_claude_code_outputs_install_command_without_client_execution(self):
        r = self.cli('setup', '--client', 'claude-code', '--yes')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('claude mcp add', r.stdout)
        self.assertFalse(self.config.exists())

    def test_14_doctor_performs_real_stdio_handshake_tools_and_file_call(self):
        self.setup_cursor()
        r = self.cli('doctor', '--client', 'cursor', '--json', child=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        report = json.loads(r.stdout)
        self.assertTrue(report['ok'])
        checks = {x['id']: x for x in report['checks']}
        for value in ('mcp.handshake', 'mcp.tools', 'mcp.call'):
            self.assertEqual(checks[value]['status'], 'ok')
        self.assertIn('1 file(s)', checks['mcp.call']['message'])

    def test_15_doctor_missing_configuration_is_not_overall_success(self):
        r = self.cli('doctor', '--client', 'cursor', '--json', child=True)
        self.assertNotEqual(r.returncode, 0)
        report = json.loads(r.stdout)
        self.assertFalse(report['ok'])
        self.assertTrue(any(x['id'] == 'cursor.config' and x['status'] == 'fail'
                            for x in report['checks']))

    def test_16_project_path_with_spaces_is_supported(self):
        spaced = self.root / 'synthetic project with spaces'
        spaced.mkdir()
        (spaced / 'sample.ts').write_text('export const answer: number = 42;\n')
        r = self.cli('setup', '--client', 'cursor', '--project', str(spaced), '--yes')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads((spaced / '.cursor/mcp.json').read_text())
        self.assertIn('${workspaceFolder}', data['mcpServers']['sentinel-ir']['args'])

if __name__ == '__main__':
    EVIDENCE.mkdir(exist_ok=True)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(OnboardingQA))
    transcript = clean(stream.getvalue())
    (EVIDENCE / 'test-transcript.txt').write_text(transcript)
    report = {
        'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'package': 'sentinel-ir-mcp', 'version': '0.2.2',
        'node_version': subprocess.check_output(['node', '--version'], text=True).strip(),
        'platform': 'Linux', 'ai_assisted': True, 'synthetic_data_only': True,
        'tests_run': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'successful': result.wasSuccessful(),
        'limitations': [
            'No actual Cursor, Windsurf, VS Code or Claude desktop session was launched.',
            'doctor tests the package-owned stdio server, not the saved client launch command.',
            'No macOS/Windows runtime, wallet, payment or production source was tested.',
            'Node filesystem permissions and clean environment are not OS/network isolation.',
            'Functional QA only; not a security audit or vulnerability report.'
        ],
        'lockfile_sha256': hashlib.sha256((ROOT / 'package-lock.json').read_bytes()).hexdigest(),
        'commands': COMMANDS,
    }
    (EVIDENCE / 'qa-results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(transcript)
    print(json.dumps({k: report[k] for k in ['tests_run', 'failures', 'errors', 'successful']}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
