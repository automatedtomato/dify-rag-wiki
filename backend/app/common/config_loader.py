from pathlib import Path
import yaml
from typing import Optional, Dict, Any

from .param_resolver import resolve_param

def load_config(layer: Optional[str] = None) -> Dict[str, Any]:
    config_path = _get_config_path()
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    if layer is not None:
        config = config[layer]
        
    return config

def _get_config_path() -> str:
    current = Path(__file__)
    root = current.parents[2]
    config_path = root / "config/config.yaml"
    
    return config_path.resolve()