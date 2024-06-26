# How to Use the Epa Multi Calls Tool

The **Epa Multi Calls** tool is designed to enhance the calibration and analysis of EPANET models by allowing users to efficiently generate multiple EPANET files from a Giswater database. With this tool, engineers and researchers can define a series of modifications to be applied recursively to the EPANET model, enabling them to analyze the system's hydraulic behavior under various scenarios and make data-driven decisions to optimize network performance. This documentation provides a step-by-step guide on using the Epa Multi Calls tool effectively.

## Opening the Dialog

To open the Epa Multi Calls dialog, follow these steps:

1. Launch QGIS.
2. Open a Giswater project.
2. Click on the GwEpaTools icon in the QGIS toolbar to access the GwEpaTools plugin.
3. Select "Analytics" from the plugin menu.
4. Choose "Epa Multi Calls" from the Analytics submenu.

## Using the Epa Multi Calls Tool

The Epa Multi Calls dialog requires the following fields to be filled before running the tool:

- **Configuration file**: Provide the path to the .ini file that contains the definitions of modifications to be applied to the EPANET model. This .ini file allows users to specify the desired changes to network elements, such as demands, valve settings, and more.

- **Output folder**: Choose the path to the folder where you want to save the output files generated by the tool. The tool will create multiple EPANET files, each representing a different scenario based on the defined modifications.

- **File name**: Specify a prefix for the output file names. The tool will create files with names starting with this prefix followed by relevant information.

## Example .ini File

Here's an example of the contents of a .ini file used by the Epa Multi Calls tool:

```ini
[options]
# go2epa steps. 0 or 3
steps=0
export_subcatch=False

# WS
# --------------------------------------
[list1]
query1=UPDATE inp_junction SET demand = '$list1object'
list1=0, 0.01, 0.1, 1, 0

[list2]
query1= "UPDATE node SET obse FROM selector_inp_dscenario WHERE cur_user=current_user; INSERT INTO selector_inp_dscenario SELECT unnest('{$list2object}'::integer[]), current_user";
list1="31,32,33", "41,42,43,44", "51,52", "61", "71,72,73"

[list3]
query1=UPDATE v_edit_inp_dscenario_lid_usage SET numelem = $list3object
list1=1,2
```

- The `[options]` section allows users to set various options for the tool, such as steps and export_subcatch.

- The `[listX]` sections (e.g., `[list1]`, `[list2]`, `[list3]`) define modifications to the EPANET model based on user-defined queries and lists.

- Each `[listX]` section contains a `query1` line that defines a SQL query to modify specific elements of the EPANET model. The queries are parameterized using `$listXobject`, where `X` corresponds to the respective list number.

- The `listX` lines under each `[listX]` section provide the values to be used in the corresponding query. Users can define different sets of values for each list to generate multiple scenarios.

## Running the Analysis

After filling in the required fields and providing the necessary input files, follow these steps to run the Epa Multi Calls analysis:

1. Click the "OK" button on the Epa Multi Calls dialog.
2. The tool will start generating multiple EPANET files based on the defined modifications in the .ini file.
3. Once the analysis is complete, the tool will save the generated EPANET files in the specified output folder, each representing a different scenario with varying configurations.