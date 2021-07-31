import data_viz as dv
import definitions

# Generates files for all regions, current date
for region in definitions.regions.keys():
    dv.plot_tables(region=region)
    dv.plot_graphs(region=region)

