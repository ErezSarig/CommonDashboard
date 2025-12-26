# CommonChart
A QGiS plugin enabling very basic chart visualization for vector layers. Charts are opened on application's dock panels making grouping and stacking of your charts into a full functioning dashboard is easy and fast.
<br>
<div>
<img src="Mapping of development over geology layer, israel 1880-2020.png"></img>
</div>
<br>

## Easy to start:
- Press the CommonChart icon to open a new CommonChart panel
- Keep opening as many CommonChart pannels a you like. Panels can be sorted as a side dock side by side or stacked on top of each other as tabs

### Choose data
- Use the Layers menu to pick which layer you want to sum up and visuallize
- Choose the field you want to grouped your data aggregation with
- Choose what data you want to sum up (Numeric fields only). Amount will sum features of each category and area will sum up the category's aggregated area

### Change visualisation
- For now display is limited only to bars or pie charts.
- Bars chart will display absolute numbers for each category while pie charts show precentage of the category from the total sum.
- Display or hide legend bellow chart figure. Hovering over any chart's object will show the name of the category it represents

- Advanced styling using CSS is accessible when exporting as SVG. Use ids "Chart" or "Legend" for those grouped objects. "Polygons","Labels","InnerLabels" classes are availbale for styling every chart element separatly while "LegendItems" and "LegendLabels" classes exist as well.
- Change the <filter> on the top of code to aplly filter effects on any group of objects
- Hopefully migration to Qt6 on QGiS new coming V4.0 will open up new options for advanced svg drawing. Hopefully this includes inserting CSS and dynamic interaction with elements of the chart in qgis without exporting.



## Show your chart
<b> Show chart by collapsing the settings box</b><br>
(Clicking the arrow by the top left corner) <br>
<br>
<img height= "240" src="SettingBox.png"></img>
<br>
<b> Or export your chart as SVG </b>



## Limitations and under the hood explained:
- Charts calculations are done using qgis's virtual layers. Virtual layers are constructed with SQL which makes them quite fast. On the down side, this makes any Qgs Expressions or virtual field invisible. This happens since the virtual layers query the source of the layer directly. For a technical reason, at the moment, that goes for Temporary layers as well (Memory based). <br>
- Coloring of the charts derives from the layer's category renderer or from project's colors settings. For the moment no other options are available.
  -  Based on layer's styling if it's categoriesed. Category's symbol will only work for fill symbols (patterns, dot and gradients fill included). For now fill is created using tiles of 60x60 pixels.  Depending on the symbolgy's inner patterns this can sometimes cause a visible unwanted grid shaped pattern.
  -  Random assignment of colors derived from project's colors settings. Using project colors limits the number of shown categories to the number of given colors. all other categories will be summed together        to a new 'All others' category. Charts are drawn from largest parts to the smallest ones so that colors aren't always assigned to the same categories.
