from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CoreBoundaryTests(unittest.TestCase):
    def test_core_contains_protocol_interface_without_capability_implementation(self):
        forbidden = (
            ROOT / "04_capabilities",
            ROOT / "06_evaluations" / "dokumentenarbeit-invarianten",
            ROOT / "src" / "impacts_protocol" / "capabilities.py",
            ROOT / "05_examples" / "dokumentenarbeit-golden",
        )

        self.assertEqual([], [str(path.relative_to(ROOT)) for path in forbidden if path.exists()])

    def test_core_routes_and_packaging_do_not_name_capability_implementation(self):
        files = (
            ROOT / "README.md",
            ROOT / "CONTEXT.md",
            ROOT / "pyproject.toml",
        )
        forbidden = ("04_capabilities", "capability_packs", "dokumentenarbeit")

        findings = []
        for path in files:
            text = path.read_text(encoding="utf-8")
            findings.extend(
                f"{path.name}: {term}" for term in forbidden if term in text
            )
        self.assertEqual([], findings)

    def test_core_has_no_capability_registry_dependency(self):
        findings = []
        for path in (ROOT / "src" / "impacts_protocol").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "CapabilityRegistry" in text or "from .capabilities" in text:
                findings.append(path.name)

        self.assertEqual([], findings)

    def test_evaluation_router_names_each_core_evaluation(self):
        router = (ROOT / "06_evaluations" / "CONTEXT.md").read_text(encoding="utf-8")

        self.assertIn("cold-walk/CONTEXT.md", router)
        self.assertIn("complexity-budget/CONTEXT.md", router)


if __name__ == "__main__":
    unittest.main()
