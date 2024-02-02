## WELCOME TO EPA TOOLS PLUGIN (gw_epatools_plugin)

This repo is focused to add capabilities in order to run recursive go2epa processes

## TABLE OF CONTENTS

- [Requirements](#requirements)
- [Install](#install)
  - [How to install WNTR package](#how-to-install-wntr-package)
- [License](#license)
- [Thanks to](#thanks-to)

## REQUIREMENTS

You will need QGIS:(Geoprocessing software)

Since gw_epatools_plugin is a plugin that's build to work with a Giswater project, you will need to have Giswater plugin installed.

For more information about to getting started with Giswater<br> you can visit the README.md file of one the main repositories:

https://github.com/Giswater/docs <br>
https://github.com/Giswater/giswater_qgis_plugin. <br>
https://github.com/Giswater/giswater_dbmodel. <br>

Also, to run this tool you need a python interpreter with the following packages:
- WNTR

## INSTALL
In this point you will learn how to install gw_epatools_plugin.<br>

To install the plugin you will need to download the source code. You can download the .ZIP file directly from this repository. Once you have de .ZIP file you must extract it in the QGIS plugins folder*:

`C:\Users\user\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`<br>

*This is the location of the QGIS plugins folder in Windows. The location may be diffrent in other operating systems.

After that you can open QGIS and a Giswater project and activate the plugin. To activate the plugin you must find _Plugins_ in the QGIS Menu Toolbar and then go to _Manage and Install Plugins_ > _Installed_ and click the checkbox for _gw_epatools_plugine_.

### How to install WNTR package:

1. Open the _OSGeo4W Shell_ application that comes with your QGIS instalation.

2. Check the version of _OSGeo4W Shell_. There is one shell for each version of QGIS installed on computer. For example, if you are installing the `gw_epatools_plugin` on QGIS 3.22, the prompt in _OSGeo4W Shell_ must read something like `C:\Program Files\QGIS 3.22.9>`.

3. Ensure `pip` is installed with the command: `python -m ensurepip`.

4. Execute the command: `pip install wntr`. (You may get a warning about a pip update. It does not interfere with the operation of the WNTR.)

5. Restart QGIS.

## LICENSE
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. See LICENSE file for more information.


## THANKS TO
GITS-BarcelonaTech University<br>
Aigües de Mataró<br>
Aigües de Girona<br>
Aigües de Blanes<br>
Aigües del Prat<br>
Aigües de Vic<br>
Aigües de Castellbisbal<br>
Aigües de Banyoles<br>
Figueres de Serveis, S.A<br>
Prodaisa<br>
Sabemsa<br>
Consorci Aigües de Tarragona<br>

-----------------------------------

