try:
    from worlds.LauncherComponents import Component, Type, components, launch_subprocess, icon_paths
except ModuleNotFoundError:
    Component = Type = None
    components = []
    icon_paths = None  

if Component is not None and Type is not None:
    def launch_client(*args):
        from .launcher import launch
        launch_subprocess(launch, name="MLDTClient", args=args)


    if icon_paths is not None:
        icon_paths["mldticon"] = f"ap:{__name__}/data/mldticon.png"


    components.append(
        Component(
            "Mario & Luigi Dream Team Client",
            func=launch_client,
            component_type=Type.CLIENT,
            description="Secondary client for Mario & Luigi Dream team.",
            icon="mldticon"
        )
    )