# A Mario & Luigi Dream team Setup Guide
This guide assumes you are using the North American version of the game, other vesions are untested.
## Setup

1. Download and install [mldt.apworld and Pi.illomizer](https://github.com/MnL-Modding/Piillomizer/releases) and [mldtclient.apworld](https://github.com/Nepply/APMLDTClient/releases) to play on azahar or a real 3ds.
2. Generate the yaml in archipelago
3. Change the settings in the yaml to fit how you want to play
4. Generate the seed
5. Go to the output folder in you Archipelago directory, then extract the folder that generated with the seed
6. Click "Open Dump" in the Pi'illomizer, then open your dump of Dream Team
7. Change the settings you want. Note that starting with key items, mini/ball hop settings, and your second progressive hammer are set by the yaml, and thus do nothing in this program
8. Click "Generate AP", then use the .bin in the folder from Step 5
9. You will now have a folder with the game mod named the title id of your region's game. e.g `00040000000D5A00`. (If your folder gets named  `00040000000D5A00-ap0x0` rename it to your regions title id.)

### Setup (Emulator)

10. In Azahar, select `File > Open Azahar Folder`. Create a `load` folder inside this folder, and inside the `load` folder create a `mods` folder. Put the folder from step 8 into the `mods` folder.
11. Also in Azahar, select `Emulation > Configure`. Then, in the general section, on the top, select `Debug`. Finally, at the bottom, ensure that the `Enable RPC Server` option is enabled.


### Setup (3DS)

10. Install Luma3DS, following the guide at https://3ds.hacks.guide/
11. On the Luma3DS configuration screen after power-up (if this screen does not show up, hold SELECT during power-up):
	1. _Make sure_ that `Enable loading external FIRMs and modules` does **NOT** have an x next to it. If so, disable it.
	2. Turn `Enable game patching` on and make sure it **DOES** have an x next to it.
	3. Press Start or choose `Save and exit`.
12. Press L+DPadDown+Select to open the Rosalina menu, and make sure that `Plugin loader` is set to `[Enabled]`.
13. Download [plugin.3gx](https://github.com/LittleCube-hax/albw-ap-plugin/releases/latest) and copy it to `/luma/plugins/00040000000D5A00/` on your SD card. (If you are not on the North American version of the game rename the 00040000000D5A00 folder to the title ID of your region.)
14. Open the folder made in step 9 go to the `00040000000D5A00/ExeFS/` folder and move the `code.bin` file from the `ExeFS` folder into the `00040000000D5A00` folder (Not moving this file up will crash a real 3ds after dream team's file select screen)
15. Move the `00040000000D5A00` folder from step 14 into the `/luma/titles/` folder


## Playing a Game

### Playing a Game (Emulator)

1. Open the game on azahar and launch the Mario & Luigi Dream Team Client from the Archipelago Launcher
2. Enter the server URL into the client and press Connect. Enter your slot name. 
3. Enjoy.

### Playing a Game (3DS)

1. Run Mario & Luigi Dream team. At the end of the red 3DS loading screen, you should see a blue flash. This means the plugin has loaded successfully.
2. Open the Mario & Luigi Dream Team client found in the Archipelago Launcher.
3. Run the command on-screen into your Mario & Luigi Dream Team client.
5. Enter the server URL into the client and press Connect. Enter your slot name.
6. Enjoy
