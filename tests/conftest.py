"""Bind pytest to local sources.

test_cli.py keeps its bootstrap for direct and unittest execution. test_b_repairs.py,
test_b_knowledge_walk.py and test_b_contract_partitions.py keep theirs so
IMPACTS_AUDIT_ROOT can redirect imports to a second checkout.
"""

import os
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

git_config_count = int(os.environ.get("GIT_CONFIG_COUNT", "0"))
os.environ[f"GIT_CONFIG_KEY_{git_config_count}"] = "maintenance.auto"
os.environ[f"GIT_CONFIG_VALUE_{git_config_count}"] = "false"
os.environ["GIT_CONFIG_COUNT"] = str(git_config_count + 1)
