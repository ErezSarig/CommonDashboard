# CommonChart
A QGiS plugin enabling very basic chart visualization for vector layers. Chart are opened on seaprate scaleble user panels so that grouping and stacking of various cahrts into a full updated dashboard is easy.

## Easy to use:
### Choose data
- Press the CommonChart icon to open a new CommonChart pannel
- Use the Layers menu to pick which layer data you want visuallize
- Choose the field you want aggregation to be grouped by
- Choose what data to sum up

### Change visualisation
- For now display is limited only to bars or pie charts.
- Display legend bellow chart figure. Chart's objects have basic tool tip showing category's label on hovering above it.
- For now, bars chart will show summed up numbers for each category while pie charts display precentage of total categories.

### Show chart by collapsing the settings box
(Clicking the arrow by the top left corner)
### Export chart as SVG 

## Under the hood and limitations explained:
- Charts calculations are qgis's virtual layer based which makes them quite fast. Virtual layers are constructed with SQL queries. For that reason only data that is part of the source layer can be calculated, meaning Qgs Expressions or virtual fields are not supported.
- Coloring of the charts can be done by one of two options:
  -  Based on layer's styling if it's categoriesed.
     Using layer's categories symobls for painting the chart will only work for fill symbols (patterns, dot and gradients fill included).
  -  Random assignment of colors derived from project's colors settings. Using project colors limits the number of shown categories to the number of given colors. all other categories will be summed together        to a new 'All others' category.
- Exporting charts as SVG files will save the svg code to file. Layer's category styling settings are saved as patterns linked for each category representation on charts.
- Advanced styling is accessible with CSS ids and classes using "Chart" and "Legend" group ids and "Polygons","Labels","InnerLabels" classes for chart objects or "LegendItems" and "LegendLabels" classes for legend parts.
 
