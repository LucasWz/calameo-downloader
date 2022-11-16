import logging
import shutil
from typing import Any, Dict, Union
from pathlib import Path


import yaml
from yaml.loader import SafeLoader

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_yaml_config(path: Union[str, Path]) -> Dict[str, Any]:

    with open(path, mode="r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=SafeLoader)

    return data


def clean_title(s: str) -> str:
    keepcharacters = ("-", "_")
    return "".join(c for c in s if c.isalnum() or c in keepcharacters).rstrip()


def remove_tree(path: Union[str, Path]) -> None:
    shutil.rmtree(path, ignore_errors=True)
