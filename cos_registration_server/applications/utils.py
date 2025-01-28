"""Application utils functions."""

from typing import Any, Dict

import yaml
from jinja2 import Environment, StrictUndefined, UndefinedError


def is_alert_rule_a_jinja_template(
    yaml_dict: Dict[str, Any], context=None
) -> bool:
    """Determine if the given alert rule YAML is a Jinja template.

    Alert rules define go template keys such as {{ $labels.instance }}.
    Jinja fails to render $ because it is a special character.
    The pattern we are using to render jinja is %%key_to_render%% to
    follow the juju observability team pattern.
    In this way we also avoid rendering the alert rules go template.
    This function tries to render an alert rule without any context,
    if the rule returns an UndefinedError it infers that it is trying to
    render a jinja template.

    Args:
        yaml_string (str): The YAML content as a string.
        context (dict): A dictionary of variables to render the template.

    Returns:
        bool: True if the YAML contains Jinja syntax, False otherwise.
    """
    if context is None:
        context = {}

    env = Environment(
        variable_start_string="%%",
        variable_end_string="%%",
        undefined=StrictUndefined,
    )

    # Dump the yaml since jinja can only render strings
    yaml_string = yaml.dump(yaml_dict)
    try:
        template = env.from_string(yaml_string)
        template.render(context)
    except UndefinedError:
        return True
    except Exception as e:
        raise RuntimeError(f"Error rendering template: {e}")
    return False
