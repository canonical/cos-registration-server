import yaml
from jinja2 import Environment, TemplateSyntaxError
from typing import (
    Any,
    Dict,
)

def is_alert_rule_a_jinja_template(yaml_dict: Dict[str, Any], context=None) -> bool:
    """
    Determines if the given alert rule YAML is a Jinja template.
    Alert rules define go template keys such as {{ $labels.instance }}.
    Those are similar to jinja templates, however the $ character causes a 
    TemplateSyntaxError.
    This function tries to render an alert rule, if the go-template key
    is not correctly escaped, it will detect a TemplateSyntaxError and
    infer that this rule is not a jinja template.
    
    Args:
        yaml_string (str): The YAML content as a string.
        context (dict): A dictionary of variables to render the template.
        
    Returns:
        bool: True if the YAML contains Jinja syntax, False otherwise.
    """
    if context is None:
        context = {"cos": "robot1"}
    
    env = Environment()

    # Dump the yaml since jinja can only render strings
    yaml_string = yaml.dump(yaml_dict)
    try:
        template = env.from_string(yaml_string)
        rendered_output = template.render(context)
    except TemplateSyntaxError:
        return False
    except Exception as e:
        raise RuntimeError(f"Error rendering template: {e}")
    return True
