# CommonChart
A QGiS plugin enabling very basic chart visualization for vector layers. Chart are opened on seaprate scaleble user panels so that grouping and stacking of various cahrts into a full updated dashboard is easy.

## Easy to start:
- Press the CommonChart icon to open a new CommonChart pannel
- Keep opening as many CommonChart pannels a you like. Pannels can be sorted as a side dock side by side or stocked together with other pannels as tabs
- 
### Choose data
- Use the Layers menu to pick which layer data you want visuallize
- Choose the field you want aggregation to be grouped by
- Choose what data to sum up

### Change visualisation
- For now display is limited only to bars or pie charts.
- Display legend bellow chart figure. Chart's objects have basic tool tip showing category's label on hovering above it.
- For now, bars chart will show summed up numbers for each category while pie charts display precentage of total categories.
- Advanced styling is accessible when exporting as SVG with the use of CSS ids and classes. Use ids "Chart" or "Legend" for those objects. "Polygons","Labels","InnerLabels" classes are availbale for styling every chart part and "LegendItems" and "LegendLabels" classes for legend elements.
- Hopefully migration to Qt6 on QGiS new coming V4.0 will open up new options for interactive interface with charts figures


## Show your chart
<b> Show chart by collapsing the settings box</b>
(Clicking the arrow by the top left corner)
<b> Export chart as SVG </b>



## Limitations and under the hood explained:
- Charts calculations are qgis's virtual layer based which makes them quite fast. Virtual layers are constructed with SQL queries. For that reason only data that is part of the source layer can be calculated, meaning Qgs Expressions or virtual fields are not supported.
- Coloring of the charts can be done by one of two options:
  -  Based on layer's styling if it's categoriesed.
     Using layer's categories symobls for painting the chart will only work for fill symbols (patterns, dot and gradients fill included).
  -  Random assignment of colors derived from project's colors settings. Using project colors limits the number of shown categories to the number of given colors. all other categories will be summed together        to a new 'All others' category.
- Exporting charts as SVG files will save the svg code to file. Layer's category styling settings are saved as patterns linked for each category representation on charts. 
