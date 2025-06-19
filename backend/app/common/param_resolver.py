from logging import getLogger
from typing import Any

logger = getLogger(__name__)


def resolve_param(
    config_param: Any, dict_param: Any, default: Any, param_name: str
) -> Any:
    """
    Resolve a parameter from a config, dictionary or a default value.

    Args:
        config_param (Any): Config parameter.
        dict_param (Any): Dictionary parameter.
        default (Any): Default value.
        param_name (str): Name of the parameter.

    Returns:
        Any: The resolved parameter.
    """

    if config_param is not None and dict_param is not None:
        logger.warning(
            f'Both config["{param_name}"] and dict_param["{param_name}"] are set. \
            Using config["{param_name}"].'
        )
        return config_param

    return config_param or dict_param or default
