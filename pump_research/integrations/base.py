"""
Switchable Hugging Face integrations.

Each integration wraps one model, dataset or app from the Hugging Face Hub and
can be turned on or off independently (integrations.json, the CLI, the API or
the settings page). Heavy libraries are imported only when an integration runs,
and everything downloaded is cached by huggingface_hub.
"""

import importlib
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

CONFIG_ENV = "PUMP_INTEGRATIONS_FILE"
DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                              "integrations.json")


class IntegrationUnavailable(Exception):
    """Raised when an integration can't run (switched off, missing package, download failed)"""


@dataclass
class Integration:
    key: str
    title: str
    hf_id: str
    hf_kind: str                  # model | dataset | space
    category: str                 # pattern_detector | price_source | social_source | signal | validation
    description: str
    requires: List[str] = field(default_factory=list)   # importable module names
    pip: List[str] = field(default_factory=list)        # packages to install for it

    @property
    def url(self):
        prefix = {"model": "", "dataset": "datasets/", "space": "spaces/"}[self.hf_kind]
        return f"https://huggingface.co/{prefix}{self.hf_id}"

    def missing_packages(self) -> List[str]:
        missing = []
        for mod in self.requires:
            try:
                importlib.import_module(mod)
            except Exception:
                missing.append(mod)
        return missing

    def status(self, config: Dict[str, bool]) -> Dict:
        missing = self.missing_packages()
        return {"key": self.key, "title": self.title, "hf_id": self.hf_id, "url": self.url, "kind": self.hf_kind,
                "category": self.category, "description": self.description, "enabled": bool(config.get(self.key)),
                "ready": not missing, "missing_packages": missing, "install": " ".join(self.pip)}

    def run(self, prices: Optional[pd.DataFrame] = None, **kwargs) -> Dict:
        raise NotImplementedError


# --- Config ---------------------------------------------------------------------------------

def config_path() -> str:
    return os.environ.get(CONFIG_ENV, DEFAULT_CONFIG)


def load_config() -> Dict[str, bool]:
    try:
        with open(config_path()) as f:
            data = json.load(f)
        return {k: bool(v) for k, v in data.get("enabled", data).items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(config: Dict[str, bool]):
    with open(config_path(), "w") as f:
        json.dump({"enabled": dict(sorted(config.items()))}, f, indent=2)
        f.write("\n")


def hf_download(repo_id: str, filename: str, repo_type: str = "model") -> str:
    """Download (or reuse the cached copy of) one file from the Hub"""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise IntegrationUnavailable("huggingface_hub is not installed (pip install huggingface_hub)")
    try:
        return hf_hub_download(repo_id=repo_id, filename=filename, repo_type=repo_type)
    except Exception as e:
        raise IntegrationUnavailable(f"could not download {repo_id}/{filename}: {type(e).__name__}: {str(e)[:160]}")
