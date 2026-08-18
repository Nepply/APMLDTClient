try:
    # Safely import icon_paths alongside Component and Type
    from worlds.LauncherComponents import Component, Type, components, launch_subprocess, icon_paths
except ModuleNotFoundError:
    Component = Type = None
    components = []
    icon_paths = None  # Fallback gracefully to None instead of a blank dictionary

from .client import N3DSAdapter, create_n3ds_mldt_client

__all__ = ["N3DSAdapter", "create_n3ds_mldt_client"]


if Component is not None and Type is not None:
    def launch_client(*args):
        from .launcher import launch
        launch_subprocess(launch, name="MLDTClient", args=args)

    # 1. Register the unique icon lookup alias if icon_paths is available
    if icon_paths is not None:
        icon_paths["mldticon"] = f"ap:{__name__}/data/mldticon.png"

    # 2. Append the component using your defined icon alias
    components.append(
        Component(
            "Mario & Luigi Dream Team Client",
            func=launch_client,
            component_type=Type.CLIENT,
            description="Secondary client for Mario & Luigi Dream team.",
            icon="mldticon"
        )
    )