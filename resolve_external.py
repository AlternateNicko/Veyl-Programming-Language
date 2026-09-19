"""
resolve_external.py

Bridges the `external` configuration surface (see `external._config` in
veylbinder.py) into a live VEY interpreter instance.

A VEY object created with `isexternal=True` (or any external instance whose
config gets rebound later through `external.set_config` / `bind_function` /
etc.) calls into this module to actually apply that configuration:

    - attribute overrides -> changes the VEY instance's own attributes
      (`filename` -> vey.file_name, `fileextension` -> vey.file_extension,
      `path` -> vey.path)
    - state merges -> folds preset `variables` / `functions` / `classes` /
      `objects` / `libraries` straight into the matching VEY dictionaries
    - injections -> python functions/classes/objects/libraries bound through
      `external.bind_function` / `bind_classes` / `bind_object` /
      `bind_library` are wired in as the VEY instance's *own* built-ins:
      their names are added to `vey.bif` (the built-in name table the parser
      already consults) and the actual python callables are kept in
      `vey.external_call`, so calling them from Veyl source resolves exactly
      like a native built-in call.
"""

_SYSTEM_ATTR_MAP = {
    "filename": "file_name",
    "fileextension": "file_extension",
    "path": "path",
}


class resolve:
    def __init__(self, vey, config=None):
        self.vey = vey
        # fall back to whatever config the vey instance was last resolved
        # with, so re-resolving after a later bind doesn't need the caller
        # to keep passing the whole config back in
        self.config = config if config is not None else getattr(vey, "external_config", None)

    def start(self):
        vey = self.vey
        config = self.config
        vey.external_config = config

        if not config:
            return vey

        self._apply_attributes(config)
        self._merge_state(config)
        self._apply_injections(config.get("injections", {}) or {})
        return vey

    def _apply_attributes(self, config):
        vey = self.vey
        for cfg_key, attr in _SYSTEM_ATTR_MAP.items():
            if config.get(cfg_key) is not None:
                setattr(vey, attr, config[cfg_key])

    def _merge_state(self, config):
        vey = self.vey

        if config.get("variables"):
            vey.variables.update(config["variables"])
            for name, value in config["variables"].items():
                vey.constants.setdefault(name, [False, value])
            if hasattr(vey, "process_vars"):
                try:
                    vey.process_vars()
                except Exception:
                    pass

        if config.get("functions"):
            vey.functions.update(config["functions"])

        if config.get("classes"):
            vey.classes.update(config["classes"])

        if config.get("objects"):
            vey.objects.update(config["objects"])

        if config.get("libraries"):
            for name, lib in config["libraries"].items():
                vey.nplibs[name] = lib
                if name not in vey.libraries:
                    vey.libraries.append(name)
                vey.nplibs_acc[name] = False

    def _apply_injections(self, injections):
        vey = self.vey

        # python functions become the VEY instance's own built-ins: their
        # name is recognized by the same `self.bif` table native built-ins
        # (num, length, sum, ...) use, and the real call is dispatched to
        # the python callable stored in `vey.external_call`.
        for name, func in injections.get("functions", {}).items():
            if not callable(func):
                raise TypeError(f"injected function `{name}` must be callable")
            vey.external_call[name] = func
            vey.external.setdefault("functions", {})[name] = func
            if name not in vey.bif:
                vey.bif.append(name)

        # python classes are inherited the same way: calling the class name
        # like a built-in constructs it directly through `external_call`.
        for name, cls_obj in injections.get("classes", {}).items():
            vey.external.setdefault("classes", {})[name] = cls_obj
            vey.external_call[name] = cls_obj
            if name not in vey.bif:
                vey.bif.append(name)

        # a bound python object is exposed directly as a Veyl variable, so
        # existing attribute access / assignment on it just works.
        for name, obj in injections.get("object", {}).items():
            vey.external.setdefault("objects", {})[name] = obj
            vey.variables[name] = obj
            vey.constants.setdefault(name, [False, obj])

        # injected libraries behave exactly like the built-in libraries list
        # (math, time, ...): available to `import`, resolved through nplibs.
        for name, lib in injections.get("libraries", {}).items():
            vey.nplibs[name] = lib
            if name not in vey.libraries:
                vey.libraries.append(name)
            vey.nplibs_acc[name] = False
            vey.external.setdefault("libraries", {})[name] = lib

        return vey
