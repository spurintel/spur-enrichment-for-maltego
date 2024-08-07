import sys
import transforms

from maltego_trx.registry import register_transform_function, register_transform_classes
from maltego_trx.server import application
from maltego_trx.handler import handle_run

# register_transform_function(transform_func)
from extensions import registry

register_transform_classes(transforms)

registry.write_transforms_config()
registry.write_settings_config()

registry.write_local_mtz(
    mtz_path="./local.mtz", 
    working_dir=".", 
    command="/usr/local/bin/python3", 
    params="project.py", 
    debug=True
)

handle_run(__name__, sys.argv, application)