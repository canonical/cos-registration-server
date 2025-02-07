"""Application utils functions."""

from typing import Any, Dict, Optional

import yaml
from applications.models import AlertRuleFile
from devices.models import Device
from django.core.serializers.pyyaml import DjangoSafeDumper
from jinja2 import Environment, StrictUndefined, UndefinedError

TEMPLATE_FILTER_START_STRING = "%%"
TEMPLATE_FILTER_END_STRING = "%%"


def is_alert_rule_a_jinja_template(
    yaml_dict: Dict[str, Any], context: Optional[Any] = None
) -> bool:
    """Determine if the given alert rule YAML is a Jinja template.

    Alert rules define go template keys such as {{ $labels.instance }}.
    Jinja fails to render $ because it is a special character.
    The pattern we are using to render jinja is %%key_to_render%% to
    follow the juju observability team pattern.
    In this way, we also avoid rendering the alert rules go template.
    This function renders an alert rule with a dummy context,
    then compares the rendered rule with the original yaml string,
    if they are different it infers that the provided yaml is a template.

    Args:
        yaml_string (str): The YAML content as a string.
        context (dict): A dictionary of variables to render the template.

    Returns:
        bool: True if the YAML contains Jinja syntax, False otherwise.
    """
    if context is None:
        context = {"juju_device_uuid": "dummy"}

    env = Environment(
        variable_start_string=TEMPLATE_FILTER_START_STRING,
        variable_end_string=TEMPLATE_FILTER_END_STRING,
        undefined=StrictUndefined,
    )

    # Dump the yaml since jinja can only render strings
    yaml_string = yaml.dump(
        yaml_dict, Dumper=DjangoSafeDumper, default_flow_style=False
    )
    try:
        template = env.from_string(yaml_string)
        rendered = template.render(context)
        return rendered.strip() != yaml_string.strip()
    except UndefinedError as e:
        raise RuntimeError(f"Invalid jinja file template: {e}")
    except Exception as e:
        raise RuntimeError(f"Error rendering template: {e}")


def render_alert_rule_template_for_device(
    rule: AlertRuleFile, device: Device
) -> str:
    """Render template alert rules helper function.

    rule: a rule dictionary stored in the db.
    device: a device instance in the db.
    """
    env = Environment(
        variable_start_string=TEMPLATE_FILTER_START_STRING,
        variable_end_string=TEMPLATE_FILTER_END_STRING,
    )
    rule_string = yaml.dump(
        rule.rules, Dumper=DjangoSafeDumper, default_flow_style=False
    )
    template = env.from_string(rule_string)
    context = {"juju_device_uuid": f"{device.uid}"}
    return template.render(context)
