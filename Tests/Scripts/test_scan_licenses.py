import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "template" / "Scripts" / "scan_licenses.py"
spec = importlib.util.spec_from_file_location("scan_licenses", SCRIPT)
scan_licenses = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan_licenses)


class ScanLicensesTests(unittest.TestCase):
    def make_tree(self) -> Path:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        return root

    def write_resolved(self, root: Path, payload: dict) -> Path:
        workspace = root / "App.xcworkspace"
        resolved = workspace / "xcshareddata" / "swiftpm" / "Package.resolved"
        resolved.parent.mkdir(parents=True)
        resolved.write_text(json.dumps(payload), encoding="utf-8")
        return workspace

    def test_display_names_maps_distinct_identity_and_repo_name(self) -> None:
        root = self.make_tree()
        workspace = self.write_resolved(
            root,
            {
                "version": 2,
                "pins": [
                    {
                        "identity": "custom-identity",
                        "location": "https://github.com/org/RepoAlias.git",
                    }
                ],
            },
        )

        names = scan_licenses.display_names(workspace)

        self.assertEqual(names["custom-identity"], "RepoAlias")
        self.assertEqual(names["repoalias"], "RepoAlias")

    def test_display_names_supports_v1_package_resolved(self) -> None:
        root = self.make_tree()
        workspace = self.write_resolved(
            root,
            {
                "version": 1,
                "object": {
                    "pins": [
                        {
                            "package": "LegacyPkg",
                            "repositoryURL": "https://github.com/org/LegacyRepo.git",
                        }
                    ]
                },
            },
        )

        names = scan_licenses.display_names(workspace)

        self.assertEqual(names["legacypkg"], "LegacyRepo")
        self.assertEqual(names["legacyrepo"], "LegacyRepo")

    def test_display_names_supports_registry_pin_and_manual_license(self) -> None:
        root = self.make_tree()
        workspace = self.write_resolved(
            root,
            {
                "version": 3,
                "pins": [
                    {
                        "identity": "example.lib",
                        "kind": "registry",
                        "location": "",
                        "state": {"version": "1.0.0"},
                    }
                ],
            },
        )
        names = scan_licenses.display_names(workspace)
        self.assertEqual(names, {"example.lib": "example.lib"})

        manual = root / "Licenses"
        manual_license = manual / "example.lib" / "LICENSE"
        manual_license.parent.mkdir(parents=True)
        manual_license.write_text("MIT Registry", encoding="utf-8")

        licenses = scan_licenses.collect_licenses(root / "checkouts", root / "Vendor", manual, names)
        self.assertEqual(licenses, {"example.lib": manual_license})

    def test_display_names_rejects_unsupported_package_resolved(self) -> None:
        for payload in (
            {"version": 99, "unexpected": []},
            {"version": 99, "pins": [{"id": "Live", "url": "https://example.invalid/LiveRepo.git"}]},
            {"version": 3, "pins": [{"kind": "registry", "location": ""}]},
        ):
            with self.subTest(payload=payload):
                root = self.make_tree()
                workspace = self.write_resolved(root, payload)

                with self.assertRaises(SystemExit) as raised:
                    scan_licenses.display_names(workspace)

                self.assertIn("unsupported", str(raised.exception.code))

    def test_collect_licenses_matches_repo_alias_skips_stale_and_prefers_manual_override(self) -> None:
        root = self.make_tree()
        workspace = self.write_resolved(
            root,
            {
                "version": 2,
                "pins": [
                    {
                        "identity": "custom-identity",
                        "location": "https://github.com/org/RepoAlias.git",
                    },
                    {
                        "identity": "grdb.swift",
                        "location": "https://github.com/groue/GRDB.swift.git",
                    },
                ],
            },
        )
        names = scan_licenses.display_names(workspace)

        checkouts = root / "checkouts"
        vendor = root / "Vendor"
        manual = root / "Licenses"
        for path, text in (
            (checkouts / "RepoAlias" / "LICENSE", "alias checkout MIT"),
            (checkouts / "GRDB.swift" / "LICENSE", "checkout MIT"),
            (checkouts / "RemovedPkg" / "LICENSE", "stale MIT"),
            (vendor / "LocalDep" / "COPYING", "vendor BSD"),
            (manual / "grdb.swift" / "LICENSE", "manual MIT"),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        licenses = scan_licenses.collect_licenses(checkouts, vendor, manual, names)

        self.assertEqual(set(licenses), {"RepoAlias", "GRDB.swift", "LocalDep"})
        self.assertEqual(licenses["RepoAlias"].read_text(encoding="utf-8"), "alias checkout MIT")
        self.assertEqual(licenses["GRDB.swift"].read_text(encoding="utf-8"), "manual MIT")

    def test_render_licenses_rejects_uppercase_gpl(self) -> None:
        root = self.make_tree()
        gpl = root / "LICENSE"
        gpl.write_text("GNU GENERAL PUBLIC LICENSE\nVersion 3", encoding="utf-8")

        with self.assertRaises(SystemExit) as raised:
            scan_licenses.render_licenses({"SomePkg": gpl})

        self.assertIn("incompatible license in SomePkg", str(raised.exception.code))

    def test_render_licenses_sorts_case_insensitively_and_preserves_utf8(self) -> None:
        root = self.make_tree()
        first = root / "a.txt"
        second = root / "b.txt"
        first.write_text("MIT © François", encoding="utf-8")
        second.write_text("Apache 2.0", encoding="utf-8")

        rendered = scan_licenses.render_licenses({"zeta": second, "Alpha": first})

        self.assertEqual(
            rendered,
            "# Open Source License\n\n## Alpha\n\nMIT © François\n\n## zeta\n\nApache 2.0\n",
        )


if __name__ == "__main__":
    unittest.main()
