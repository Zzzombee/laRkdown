"""Check the separation between the user package and repository resources."""
from __future__ import annotations

import unittest

from tools import build_release


class PackageBoundaryTests(unittest.TestCase):
    def test_package_selects_runtime_files_only(self):
        required = {name: b'fixture' for name in build_release.PACKAGE_EXACT}
        candidates = {
            **required,
            '.agents/instructions/project-layout.md': b'runtime instruction',
            '.agents/skills/upgrade-larkdown/SKILL.md': b'runtime skill',
            '.agents/config/project-layout.json': b'runtime schema',
            '.agents/config/feishu.example.json': b'public example',
            '.agents/config/feishu.json': b'private configuration',
            '.agents/config/publisher-notes.md': b'publisher notes',
            '.github/workflows/release-contract.yml': b'publisher workflow',
            '.gitignore': b'git configuration',
            'tools/build_release.py': b'build script',
            'tools/RELEASING.md': b'publisher specification',
            'tests/test_release.py': b'test code',
            '.planning/plan.md': b'private plan',
        }
        selected = build_release.package_files(candidates)
        self.assertEqual(set(selected), set(required) | {
            '.agents/instructions/project-layout.md',
            '.agents/skills/upgrade-larkdown/SKILL.md',
            '.agents/config/project-layout.json',
            '.agents/config/feishu.example.json',
        })

    def test_package_requires_user_entrypoints(self):
        with self.assertRaisesRegex(ValueError, 'missing required files'):
            build_release.package_files({'README.md': b'fixture'})


if __name__ == '__main__':
    unittest.main()
