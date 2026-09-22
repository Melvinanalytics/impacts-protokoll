"""Bind pytest to local sources.

test_cli.py keeps its bootstrap for direct and unittest execution. test_b_repairs.py,
test_b_knowledge_walk.py and test_b_contract_partitions.py keep theirs so
IMPACTS_AUDIT_ROOT can redirect imports to a second checkout.
"""

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
