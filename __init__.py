from worlds.LauncherComponents import Component, Type, components, launch_subprocess, icon_paths

if Component is not None and Type is not None:
    def launch_client(*args):
        from .launcher import launch
        launch_subprocess(launch, name="MLDTClient", args=args)


    if icon_paths is not None:
        icon_paths["mldticon2"] = f"ap:{__name__}/data/mldticon2.png"


    components.append(
        Component(
            "Mario & Luigi Dream Team Client. Nightly Version",
            func=launch_client,
            component_type=Type.CLIENT,
            description="Secondary client for Mario & Luigi Dream team.",
            icon="mldticon2"
        )
    )