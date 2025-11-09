import importlib
import pkgutil

import modules

for _, module_name, _ in pkgutil.iter_modules(modules.__path__):
    try:
        importlib.import_module(f"modules.{module_name}.model")
    except ModuleNotFoundError:
        pass