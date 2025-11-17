import qgis
from qgis.utils import iface
from qgis.core import QgsProject,QgsVectorLayer,QgsProjectColorScheme
from qgis.gui import  QgsHtmlWidgetWrapper
import qgis.PyQt as PyQt
from qgis.PyQt.QtCore import Qt,QUrl,QByteArray,QSize
from qgis.PyQt.QtSvg import QSvgWidget
from qgis.PyQt.QtWidgets import QAction,QApplication,QDialog, QVBoxLayout,QLabel,QPushButton,QGroupBox,QComboBox,QSizePolicy,QCheckBox,QStackedLayout,QFileDialog
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.gui import QgsCollapsibleGroupBoxBasic

from tempfile import NamedTemporaryFile
import math

import xml.etree.ElementTree as ET
##Temp use of beautifulsoap
import sys
import os
sys.path.append(os.path.dirname(__file__)+'/beautifulsoup4-4.14.0')
from bs4 import BeautifulSoup,element

def CommonVLayer(Layer, Sql, Name="CommonVLayer"):
    """Query any QGIS layer as a virtual layer named 'Data'."""
    # Construct virtual layer source string
    Provider = Layer.providerType()
    Src = QUrl.toPercentEncoding(Layer.source()).data().decode()

    # The alias "Data" is what you use in the SQL query
    Source = f"?layer={Provider}:{Src}:Data&query={Sql}"
    
    CommonVL = QgsVectorLayer(Source, Name, "virtual")

    if not CommonVL.isValid():
        raise Exception(f"Virtual layer query failed:\n{CommonVL.lastError()} \n Query sent: {Source}")
    
    return CommonVL

def CommonColors(i=None):
    '''Retriving project colors'''
    
    Colors = QgsProjectColorScheme().fetchColors()
    if i == None:
        return len(Colors)
    C = Colors[i % len(Colors)][0]
    return C.name()
        
def CommonCatSymbol(C,ID=None,Color=False):
    '''Retriving an svg pattern represtenting category's symbol (fill based symbols only)'''
    Size= 60
    if C.symbol().type() == qgis.core.Qgis.SymbolType.Fill and Color == False:  
        with NamedTemporaryFile() as F:
            C.symbol().exportImage(F.name,'svg',QSize(Size,Size))

            #Soup =ET.parse(F.read())
            
            ## --- Trying to replace with xml ---
            Soup = BeautifulSoup(F.read(), 'html.parser') ##Getting the SVG code
            
            ##Cleaning all irelevant tags and comments
            Soup.title.decompose()
            Soup.desc.decompose()
            
            for Line in Soup.contents:
                if type(Line) == element.ProcessingInstruction or Line == '\n':
                    Soup.contents.remove(Line)
            try:
                Soup.defs.unwrap()
            except:
                pass
            ## Looking for the symbol's border element to remove it's stroke and send it back to be used by polygons
            Border=''
            for P in Soup.find_all("path", {"d": f"M0,0 L{Size},0 L{Size},{Size} L0,{Size} L0,0"}): 
                G = P.find_parent("g")
                if G:
                    if 'stroke-width' in G.attrs.keys():
                        Border += 'stroke-width="' + G["stroke-width"] +'" ' 
                        G["stroke-width"] = "0"  # set stroke width to 0

                    if 'stroke' in G.attrs.keys():
                        Border += 'stroke="' + G["stroke"] + '" '
                    #print('Border: ',Border) ##^


            Pattern_tag = Soup.new_tag('pattern' ,id=str(ID),x="0",y="0",width=Size,height=Size,patternUnits="userSpaceOnUse")
            Soup.svg.wrap(Pattern_tag)
            Soup.svg.unwrap()
            return [Soup.prettify(), Border]
            
def CommonPlot(Data,Type='Pie',Dimensions=None,ShowLegend=False,SvgPatterns=[],CSS=''):
    '''
    </h2> C_Plot(Data,Type='Pie',Dimensions=100,SvgPatterns=[],CSS='')</h2>
    <h3> Ploting data to pie or bars charts. Returning svg code to embed where needed
    <br><b>Data</b : JSON object using {"Size": int, "Color":str,"Label":str} like features. use "Color":'Auto' to use project's color scheme
    <br><b>Type</b> : 'Pie'/'Bars' for matching displays
    <br><b>Dimensions</b> : Radius size for pie charts and bar width for bar charts
    <br><b>SvgPatterns</b> : A list of pattern to use for the svg defs section. Enables referncing instead of colors using 'url(#PatternName)'
    <br><b>CSS</b> : Adding any style sheet defintions.
    <br><sub>** Svg's id named #PiePath<Num> are reserved
    '''
    ##+ Add sum label option ('Abs'/'Per'/None) for showing each categorie's size in numbers
    try: ##Going through data to get general properties and check the features are constructed the right way
        Total = 0
        Top = Data[0]['Size']
        Bottom = 0
        for D in Data:
                
            if Top < D['Size']:
                Top = D['Size']
            elif Bottom > D['Size']:
                Bottom = D['Size']
            Total += max(0,D['Size'])
    
    except Exception as Err:
        raise ValueError(f"Expecting attribute named 'Size' with numeric values for all features.Got this error: ",Err)
        
    ColorIndex = 0
    SvgParts= [f'<Style>{CSS}</Style>','<defs>','\n'.join(SvgPatterns),'</defs>']
    if Type.casefold() == 'pie':
        if Dimensions == None:
            Dimensions = 150
        LineH =20 ##+Get font-size from CSS 
        VBox = [0,0,2*(Dimensions+LineH+2),2*(Dimensions+LineH)]
        SvgParts.append(f'<g id="Chart" class="PieChart" filter="url(#Filter)" transform="translate({Dimensions+LineH},{Dimensions+LineH})">') ## Moving the pie to the middle of the viewBox after using the 0,0 as reference
        #SvgParts.append(f'<circle r="{Dimensions}" filter="url(#Shade)" fill="transparent"/>')
        Start = 0 #Starting angle
        
    elif Type.casefold() == 'bars':
        if Dimensions == None:
            Dimensions = 80
        X = 0
        Start= Top*300/(Top-Bottom)
        VBox = [0,0,(Dimensions+2)*len(Data),300+20]
        SvgParts.append(f'<g id="Chart" class="BarsChart" filter="url(#Filter)" transform="translate(0 20)">')
        
    if ShowLegend: ##Adding space at the end of the image
        VBox[3] += len(Data)* 25
    
    ##Adding svg tag after calculating view box
    SvgParts.insert(0,f'''<svg ViewBox="{' '.join(list(map(str,VBox)))}" width="100%" {'hight="100%"' if not ShowLegend else ''} xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1">''')
    #print('Data length: ',len(Data)) ##^
    for i,D in enumerate(Data):
        if 'Color' in D.keys() and type(D['Color']) == str and 'Label' in D.keys() and type(D['Label']) == str:
            if 'url' in D['Color'].casefold() and len(SvgPatterns) == 0: ## for wrong input cases
                D['Color'] = 'Auto'
                
            if D['Color'].casefold() == 'auto' :
                        D['Color'] = f'fill="{CommonColors(ColorIndex)}"'
                        ColorIndex +=1
                
            if Type.casefold() == 'Pie'.casefold():
                if D['Size'] < 0:
                    raise ValueError(f"Pie charts aren't suppose to deal with negative values like the one given on feature number {i}")
                elif D['Size'] > 0:
                    
                    Normal = D['Size'] / Total #Normalized value
                    InnerLabel = '{:.1%}'.format(Normal)
                    
                    End = Start + 360 * Normal
                    x1 = Dimensions*math.cos(math.radians(1-Start))
                    y1 = Dimensions*math.sin(math.radians(1-Start))
                    x2 = Dimensions*math.cos(math.radians(1-End))
                    y2 = Dimensions*math.sin(math.radians(1-End))
                    LabelX = Dimensions*0.7*math.cos(math.radians(1-Start-180*Normal))
                    LabelY = Dimensions*0.7*math.sin(math.radians(1-Start-180*Normal))
                    Large_arc = 1 if End - Start > 180 else 0
                    Path_d = f"M0,0 L{round(x1,1)},{round(y1,1)} A{Dimensions},{Dimensions} 0 {Large_arc},0 {round(x2,1)},{round(y2,1)} Z"
                    LineW = min(round(D['Size']/Total* Dimensions*6.28),len(D['Label'])*20*4) #Estimating for lengthAdjustment
                    SvgParts.append(f'''<path id ="PiePath{i}" class="Polygons" d="{Path_d}" {D['Color']} ><title>{D['Label']}</title></path>''')

                    if not ShowLegend:
                        SvgParts.append(f'''<text class="Labels" dy="0.9em"><textPath href="#PiePath{i}" lengthAdjust="spacingAndGlyphs" startOffset="{Dimensions}" textLength="{LineW}">{D['Label']}</textPath></text>''')
                    SvgParts.append(f'''<text class="InnerLabels" fill="white" text-anchor="middle" font-size="0.7em" x="{round(LabelX)}" y="{round(LabelY)}" lengthAdjust="spacingAndGlyphs" textLength="{50*min(0.05,Normal)}em"> {InnerLabel}</text>''')
                    Start = End
                    
            elif Type.casefold() == 'Bars'.casefold():
                
                InnerLabel = '{:,}'.format(round(D['Size'],1))
                Direction = -1 if D['Size'] <0 else 1 
                Normal = round(D['Size']*300/(Top -Bottom),1) #Normalizing values
                LineH =22*Direction ##+Get font-size from CSS 
                        
                SvgParts.append(f'''<rect class="Polygons" x="{X}" y="{Start-max(Normal,0)}" width="{Dimensions}" height="{abs(Normal)}" {D['Color']}><title>{D['Label']}</title></rect>''')
                if not ShowLegend:
                    SvgParts.append(f'''<text class="Labels" font-size="20" x="{X}" y="{Start-max(abs(Normal),0)}" textLength="{Dimensions}" lengthAdjust="spacingAndGlyphs"> {D['Label'] }</text>''')
                SvgParts.append(f'''<text class="InnerLabels" text-anchor="middle" fill="white" font-size="0.7em" x="{X+(0.5*Dimensions)}" y="{Start-(0.5*Normal)}"> {InnerLabel}</text>''')
                X += Dimensions + 2
            else:
                raise ValueError("Expecting 'Bars' or 'Pie' on Type variable (2nd)")
    
        else:
            raise ValueError("Data must be a json constructed from 'Size','Color' and 'Label' keys as strings even if empty")
            
    SvgParts.append('</g>')

    ##Adding legend
    if ShowLegend:
        SvgParts.append(f'<g transform="translate(0 {VBox[3] - (len(Data)* 25) +5})" id="Legend">')
        for i,D in enumerate(Data):
            SvgParts.append(f'''<rect class="LegendItems" x="0" transform="translate(0 {i*25})" height="1em" width="1.5em" {D['Color']}/>''')
            SvgParts.append(f'''<text class="LegendLabels" x="2em" y="10" transform="translate(0 {i*25})"> {D['Label']}</text>''')
            
        SvgParts.append('</g>')
        ## Resetting viewbox
        
    SvgParts.append('</svg>')

    return '\n'.join(SvgParts)

class CommonChart(QDialog):
    def __init__(self):
        super(CommonChart,self).__init__()
        #self.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.L = iface.activeLayer()
        #self.setWindowOpacity(0.8)
        self.Lay = QVBoxLayout(self)
        self.UI = dict()
        
        self.UI['Settings'] = QgsCollapsibleGroupBoxBasic()
        self.UI['Settings'].setTitle('Choose a layer:')
        ##+ Find the way to make svg resize to max and settings lines to always be minimum
    
        self.SettingsL = QVBoxLayout(self.UI['Settings'])
        self.UI['LayersLabel']=QLabel('Choose a layer to group:')
        self.UI['Layers'] = QComboBox()
        
        self.UI['GroupByLabel']=QLabel('Group features by :')
        self.UI['GroupBy'] = QComboBox()
        
        self.UI['SumTypeLabel']=QLabel('Sum features by :')
        self.UI['SumType'] = QComboBox()
        
        self.UI['ChartTypeLabel'] = QLabel('Chart type:')
        self.UI['ChartType'] = QComboBox()
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        self.UI['ShowLegend'] = QCheckBox('Add legend')
        self.UI['ShowLegend'].setChecked(True)
        self.UI['ExportSVG'] = QPushButton('Export as Svg')
        
        self.UI['Visual'] = QGroupBox()
        self.VisualL = QVBoxLayout(self.UI['Visual'])
        
        #self.UI['Image'] = QSvgWidget()d
        self.UI['Image'] = QWebView()
        #self.UI['Image'].setZoomFactor(1)
        
        Layout = self.Lay
        for O in list(self.UI.values()):
            if type(O) == PyQt.QtWidgets.QGroupBox or type(O) == qgis._gui.QgsCollapsibleGroupBoxBasic:
                self.Lay.addWidget(O)
                Layout = O.layout()
            else:
                Layout.addWidget(O)
                
        for L in QgsProject.instance().mapLayers().values():
            if type(L) ==  qgis.core.QgsVectorLayer and L.source()[0:6] != 'memory': ##Listing only vector layer and no temp layer
                self.UI['Layers'].insertItem(0,L.name())
                
        self.UI['Layers'].setCurrentText(self.L.name())
        
        self.UI['SumType'].insertItem(0,'Amount')
        
        self.UI['ChartType'].insertItems(0,['Pie','Bars'])
        
        self.UI['ExportSVG'].clicked.connect(self.Export)
        self.UI['GroupBy'].currentIndexChanged.connect(self.GroupSet) 
        self.UI['Layers'].currentIndexChanged.connect(self.LayerSet)
        self.UI['SumType'].currentIndexChanged.connect(self.CleanData)
        self.UI['Settings'].collapsedStateChanged.connect(self.ShowSVG)
        
        '''Calculations only triggered when settings group is collapsed or export is clicked'''

    def LayerSet(self):
            
        self.L = QgsProject.instance().mapLayersByName(self.UI['Layers'].currentText())[0]
        if self.L != None:
            self.L.afterCommitChanges.connect(self.LayerSet) ## Refreshing data when layer is cahnged
            self.FieldsList = [] #Resetting

            self.parentWidget().setWindowTitle('{} - CommonChart'.format(self.UI['Layers'].currentText()))
            self.UI['Settings'].setTitle(self.UI['Layers'].currentText())

            self.UI['GroupBy'].clear()
            self.UI['SumType'].clear()
            try:
                self.UI['SumType'].currentIndexChanged.disconnect()
                self.UI['GroupBy'].currentIndexChanged.disconnect()
            except:
                pass

            ## Filling summing options. using layer's numeric fields or dimensions according to geometry type
            NumFields = [F.name() for F in self.L.fields() if F.isNumeric()] #To allow summing of other fields
            self.UI['SumType'].insertItems(self.UI['SumType'].count(),NumFields)
            self.UI['SumType'].insertSeparator(0)
            
            if self.L.geometryType() == qgis.core.Qgis.GeometryType.Line:
                self.UI['SumType'].insertItem(0,'Length')
            elif self.L.geometryType() == qgis.core.Qgis.GeometryType.Polygon:
                self.UI['SumType'].insertItem(0,'Area')
            
            self.UI['SumType'].insertItem(0,'Amount')
            self.UI['SumType'].setCurrentIndex(0)
            self.UI['SumType'].currentIndexChanged.connect(self.CleanData)
            
            ## Filling grouping options. using layer's fields or styling categories
            
            self.FieldsList = [F.name() for F in self.L.fields()]
            self.UI['GroupBy'].insertItems(0,self.FieldsList)
            if type(self.L.renderer()) == qgis._core.QgsCategorizedSymbolRenderer:
                self.UI['GroupBy'].insertSeparator(0)
                self.UI['GroupBy'].insertItem(0,'Layer categories')
                self.UI['GroupBy'].setCurrentIndex(0)
                if self.L.renderer().classAttribute().strip('"') not in [F.name() for F in self.L.fields()]: #Varifying 
                    self.UI['GroupBy'].model().item(0).setEnabled(False)
            self.UI['GroupBy'].currentIndexChanged.connect(self.GroupSet)
            self.GroupSet()

    def GroupSet(self):
        if self.UI['GroupBy'].currentText() == 'Layer categories':
            self.GB = self.L.renderer().classAttribute().strip('"') #In case an expression was used to refernce a legit field name
        elif len(self.UI['GroupBy'].currentText()) > 0:
            self.GB = self.UI['GroupBy'].currentText()
        else:
            self.GB = None
            
        self.CleanData()
        
    def CleanData(self):
        '''When changes made requiring new calculations data is deleted'''
        self.Data = []
        
    def GetData(self):
        '''Getting data from layer and creating a Data dictionary for CommonPlot - 
        Data dict is constructed from Size, Color and Label attributes. Size is always numeric and for pie charts it can't be negative 
        For simplicity the xml feature fill attribute. For layers categories symbologies url(#{CategoryIndex}) will later be used to find layer category and Auto will cause CommonPlot to figure a color of it's own
        Labels are text always and can be empty or duplicates
        '''
        

        R = self.L.renderer()
        ## Categories made by field with no Qgs expressions
        if self.GB != None:
            if self.UI['SumType'].currentText() == 'Amount':
                Sql = f"SELECT {self.GB},COUNT(*) as Sum FROM Data"
            elif self.UI['SumType'].currentText() == 'Length':
                Sql = f"SELECT {self.GB},sum(st_length(geometry)) as Sum FROM Data"
            elif self.UI['SumType'].currentText() == 'Area':
                Sql = f"SELECT {self.GB},sum(st_area(geometry)) as Sum FROM Data"
            else:
                Sql = f"SELECT {self.GB},sum({self.UI['SumType'].currentText()}) as Sum FROM Data"
            
            Sql += f' GROUP BY {self.GB} ORDER BY SUM DESC;'
            #print(Sql) ##^
            VL = CommonVLayer(self.L,Sql)
            #self.ShowLayer = VL ##^
            #QgsProject.instance().addMapLayer(VL) ##^
    
            ## Constructing the Data dict to use with CommonPlot
            ## Creating 'All others' in data
            self.Data =[]
            if self.UI['GroupBy'].currentText() == 'Layer categories' and None in list(map(lambda x: x.value(),R.categories())): # For already defined all others category
                Line = {'Size':0
                    ,'Label':R.categories()[list(map(lambda x: x.value(),R.categories())).index(None)].label()  
                    ,'Color':f'url(#{str(R.categoryIndexForValue(None))})'
                    }
                print('Category index for none: ',str(R.categoryIndexForValue(None)))
            else: # Creating an all other category
                Line = {'Size':0,'Label':'All others','Color':'fill="#00000066"'}
            self.Data.append(Line)
            
            ## Constructing the Data to fit CommonPlot structure
            for F in VL.getFeatures():
                Att = F.attribute(self.GB) #Category value
                
                if self.UI['GroupBy'].currentText() == 'Layer categories':
                    CatIndex = R.categoryIndexForValue(Att)
                else:
                    CatIndex = None 
                
                Line = dict()
                Size = 0 if F.attribute('Sum') == None else F.attribute('Sum')
                if CatIndex == None and len(self.Data) < CommonColors(): ## Adding new category from data
                    Line['Size'] = round(Size,1)
                    Line['Label'] = str(Att)
                    Line['Color'] = 'Auto'
                    self.Data.append(Line)
                    
                elif CatIndex != None and CatIndex > -1: ## Matching with a layer's category 
                    #print(CatIndex) ##^
                    Line['Size'] = round(Size,1)
                    Line['Label'] = R.categories()[CatIndex].label()
                    Line['Color'] = f'url(#{CatIndex})'
                    self.Data.append(Line)
                else: ## if categories are taken from layer and no matching category found
                    self.Data[0]['Size'] += Size
                    
            if self.Data[0]['Size'] == 0:
                self.Data.pop(0) #Only if All Others line was created artifically

    def MakePlot(self):
        ## Calculating only if recalculating is needed
        if len(self.Data) == 0 :
            self.GetData()

        R = self.L.renderer()
        CSS = '* { font-family: ' +QgsProject.instance().styleSettings().defaultTextFormat().font().family()+ '};'
        Patterns = dict()
        Filter ='''<filter id="Shade" x="-30%" y="-30%" width="200%" height="200%">
              <feGaussianBlur in="SourceAlpha" stdDeviation="9" result="blur"/>
              <feOffset dx="0" dy="0" result="offsetBlur"/>
              <feComposite in="offsetBlur" in2="SourceAlpha" operator="arithmetic" k2="-1" k3="1" result="inner"/>
              <feColorMatrix type="matrix" values="
                0 0 0 0 0
                0 0 0 0 0
                0 0 0 0 0
                0 0 0 0.9 0" result="shadowColor"/>
              <feComposite in="shadowColor" in2="SourceGraphic" operator="over"/>
            </filter>'''
        Filter = '<filter id="Filter"><feDropShadow height="115%" width="115%" stdDeviation="1" flood-opacity="0.6"/></filter>' ##Filter for svg's group Chart elements    
        Patterns = [Filter]
        
        ## Creating SVG patterns and border style for categories. Category index is key, pattern and border styles are in a tuple
        if len(self.Data) > 0 :
            if self.UI['GroupBy'].currentText() == 'Layer categories':
                for D in self.Data:
                    if 'url(' in D['Color'].casefold():
                        UrlIndex = int(D['Color'][D['Color'].find('(#')+2 : D['Color'].find(')')]) ## Finding the cat index in the url(#) 
                        #print('Found index in url: ',UrlIndex) ##^
                        C= R.categories()[UrlIndex]
                        P = CommonCatSymbol(C,UrlIndex)
                        ## Getting full border style or any additions for layer's categories
                        D['Color'] = f'fill="url(#{UrlIndex})" {P[1]}'

                        Patterns.append(P[0]) ## Adding pattern to dictionarry for 

        return CommonPlot(self.Data,self.UI['ChartType'].currentText(),ShowLegend=self.UI['ShowLegend'].isChecked(),SvgPatterns=Patterns,CSS=CSS)

    def Export(self):
        self.SVG = self.MakePlot()

        Path =  QFileDialog().getSaveFileName(None,"Save SVG:",'',"SVG (*.svg)")[0]
        if Path:
            with open(Path,'w') as F:
                F.write(self.SVG)
        
                
    def ShowSVG(self): ## A separate svg creation with no patterns until Qt6 will be in
        if self.UI['Settings'].isCollapsed():

            self.SVG = self.MakePlot()

            self.UI['Image'].setHtml(f'<html><body width="100%"><div style="flex:1; display:flex; align-items:stretch;"> {self.SVG} </div></body></html>')

            ## Set dock title with fields alias
            DisplayList = {'Layer categories': 'Layer categories','Amount' :'Amount', 'Length': 'Length', 'Area': 'Area'}
            for F in self.L.fields():
                DisplayList[F.name()] = F.displayName()
                
            self.UI['Settings'].setTitle(' '.join([self.UI['Layers'].currentText(), DisplayList[self.UI['SumType'].currentText()] ,'of',DisplayList[self.UI['GroupBy'].currentText()]]))
            self.UI['Image'].show()
        
        else:
            self.UI['Image'].hide()
            self.UI['Settings'].setTitle(self.UI['Layers'].currentText())
    
