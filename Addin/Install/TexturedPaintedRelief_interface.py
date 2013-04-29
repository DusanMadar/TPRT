#-------------------------------------------------------------------------------
# Name:         TexturedPaintedRelief_interface.py
# Purpose:      GUI for TexturedPaintedRelief tool.
#
# Author:       dm
# Version:      1.0
#
# Created:      26/10/2012
# Updated:      26/01/2013 - added get_values()
#               28/01/2013 - added final_data_check()
#               03/02/2013 - added add_message()
#               03/02/2013 - updated on_close()
#               04/03/2013 - added reset_inputs()
#               05/04/2013 - added edit_combobox_choice()
#
# Copyright:    (c) dm 2012
# Licence:      public :)
#-------------------------------------------------------------------------------
# standard modules
import os
import sys
import datetime
# wxPython
import wx
import wx.grid
import wx.lib.scrolledpanel as scrolled
from wx.lib.masked import NumCtrl
from wx.lib.intctrl import IntCtrl
from wx.lib.pubsub import Publisher as pub
# TexturedPaintedRelief_validator & TexturedPaintedRelief_logic
import TexturedPaintedRelief_validator as validator
import TexturedPaintedRelief_logic as processor
#-------------------------------------------------------------------------------
class TprtFrame(wx.Frame):
    """
    Description:
    Creates GUI for TexturedPaintedRelief tool.
    """
    def __init__(self):
        """
        Initialize the Frame and add wx widgets.
        """
        wx.Frame.__init__(self, None, wx.ID_ANY, style=wx.CLOSE_BOX|wx.CAPTION|
                          wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.CLIP_CHILDREN,
                          title="Textured Painted Relief Tool")
        self.SetIcon(wx.Icon(os.path.join(os.path.dirname(__file__),"_tpr.ico"),
                     wx.BITMAP_TYPE_ICO))
        # panel attributes
        self.SetSize((700, 545))
        self.panel = wx.Panel(self)
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.font = wx.Font(10, wx.SYS_SYSTEM_FONT, wx.NORMAL,
                            wx.NORMAL, False, "Arial")
        self.fontBold = wx.Font(10, wx.SYS_SYSTEM_FONT, wx.NORMAL,
                                wx.BOLD, False, "Arial")
        # helper attributes
        self.textureChoice = []
        self.landuseChoice = []
        self.configContent = []
        self.tableRowsCount = 3
        self.processor = None
        # validator object
        self.validator = validator.Validator()
        # configuration---------------------------------------------------------
        self.add_basic_widget("Configuration", "Config", self.on_change_config)
        # terrain---------------------------------------------------------------
        self.add_basic_widget("Terrain", "Terrain")
        # textures--------------------------------------------------------------
        # label
        textureLabel = wx.StaticText(self.panel, label="Textures")
        textureLabel.SetFont(self.fontBold)
        self.panelSizer.Add(textureLabel, flag=wx.LEFT|wx.TOP, border=10)
        # table - labels
        textureTable = wx.grid.Grid(self.panel)
        textureTable.CreateGrid(0, 4)
        textureTable.SetColLabelSize(30)
        # table - hacking not showing row labels, setting row height
        textureTable.SetRowLabelSize(1)
        for row in range(textureTable.GetNumberRows()):
            textureTable.SetRowLabelValue(row, "")
            textureTable.SetRowSize(row, 20)
        # table - setting labels
        textureTable.SetColLabelValue(0, "Layer")
        textureTable.SetColSize(0, 217)
        textureTable.SetColLabelValue(1, "Texture")
        textureTable.SetColSize(1, 100)
        textureTable.SetColLabelValue(2, "LandUse")
        textureTable.SetColSize(2, 100)
        textureTable.SetColLabelValue(3, "Color")
        textureTable.SetColSize(3, 50)
        self.panelSizer.Add(textureTable, flag=wx.LEFT|wx.TOP, border=10)
        # table - rows - set panel
        self.panelRows = scrolled.ScrolledPanel(self.panel, size=(468,63))
        self.panelRowspanelSizer = wx.BoxSizer(wx.VERTICAL)
        self.panelRows.SetSizer(self.panelRowspanelSizer)
        self.panelSizer.Add(self.panelRows, flag=wx.LEFT, border=10)
        # table - rows - add 3 rows
        for x in range(3):
            self.add_table_row()
        # add row button
        paddingTop = wx.StaticLine(self.panel, size=(0,10))
        self.panelSizer.Add(paddingTop)
        addRowBtn = wx.Button(self.panel, label="Add row", size=(100,20))
        addRowBtn.SetToolTip(wx.ToolTip("Click to add another row to the "
                                             "Textures table"))
        addRowBtn.Bind(wx.EVT_BUTTON, self.on_add_table_row)
        self.panelSizer.Add(addRowBtn, flag=wx.LEFT, border=380)
        self.panel.SetSizer(self.panelSizer)
        # hillshading-----------------------------------------------------------
        # label
        label = wx.StaticText(self.panel, label="Hillshading options")
        label.SetFont(self.fontBold)
        self.panelSizer.Add(label, flag=wx.LEFT|wx.BOTTOM|wx.TOP, border=10)
        # options
        # otions - labels
        labelsSizer = wx.BoxSizer(wx.HORIZONTAL)
        azimuth = wx.StaticText(self.panel, label="Azimuth")
        altitude = wx.StaticText(self.panel, label="Altitude")
        zFactor = wx.StaticText(self.panel, label="Z factor")
        shadows = wx.StaticText(self.panel, label="Shadows")
        cellSize = wx.StaticText(self.panel, label="Cell Size")
        color = wx.StaticText(self.panel, label="Color")
        # otions - labels - panelSizers
        labelsSizer.Add(azimuth, flag=wx.LEFT, border=12)
        for label in [altitude, zFactor, shadows]:
            labelsSizer.Add(label, flag=wx.LEFT, border=45)
        labelsSizer.Add(cellSize, flag=wx.LEFT, border=38)
        labelsSizer.Add(color, flag=wx.LEFT, border=42)
        self.panelSizer.Add(labelsSizer)
        # options
        optionsSizer = wx.BoxSizer(wx.HORIZONTAL)
        azimuthCtrl = wx.lib.intctrl.IntCtrl(self.panel, name="Azimuth",
                                             size=(50,20))
        azimuthCtrl.SetValue(315)
        azimuthCtrl.Bind(wx.EVT_TEXT, self.on_change_hillshading)
        #
        altitudeCtrl = wx.lib.intctrl.IntCtrl(self.panel, name="Altitude",
                                              size=(50,20))
        altitudeCtrl.SetValue(45)
        altitudeCtrl.Bind(wx.EVT_TEXT, self.on_change_hillshading)
        #
        zFactorCtrl = wx.lib.masked.NumCtrl(self.panel, name="Zfactor",
                                            size=(50,20), autoSize=False,
                                            integerWidth=1, fractionWidth=2)
        zFactorCtrl.SetFont(wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL, False))
        zFactorCtrl.SetValue(1.0)
        #
        shadowsChoices = ["Yes", "No"]
        shadowsCbx = wx.ComboBox(self.panel,-1,shadowsChoices[1], (0,0),
                                 (50,20), shadowsChoices, style=wx.CB_DROPDOWN,
                                 name="Shadows")
        #
        cellSizeCtrl = wx.lib.intctrl.IntCtrl(self.panel, size=(50,20),
                                          name="Cellsize")
        cellSizeCtrl.SetValue(10)
        cellSizeCtrl.Bind(wx.EVT_TEXT, self.on_change_hillshading)
        #
        colorCtrl = wx.StaticBitmap(self.panel, size=(50, 21),
                                name="HillshadeColor", style=wx.SIMPLE_BORDER)
        colorCtrl.SetBackgroundColour(wx.Color(250,250,250))
        colorCtrl.Bind(wx.EVT_LEFT_DOWN, self.on_change_color)
        # options - bind show_help()
        for option in [azimuthCtrl, altitudeCtrl, zFactorCtrl,
                       shadowsCbx, cellSizeCtrl]:
            option.Bind(wx.EVT_SET_FOCUS, lambda evt, arg=option.Name:
                        self.show_help(evt, arg))
        # options - set panelSizer
        optionsSizer.Add(azimuthCtrl, flag=wx.LEFT, border=10)
        for option in [altitudeCtrl, zFactorCtrl, shadowsCbx,
                       cellSizeCtrl, colorCtrl]:
            optionsSizer.Add(option, flag=wx.LEFT, border=33)
        self.panelSizer.Add(optionsSizer)
        # output----------------------------------------------------------------
        self.add_basic_widget("Output", "Output", self.final_data_check)
        # help------------------------------------------------------------------
        # vertical separator line
        sep = wx.StaticLine(self.panel, pos=(500,10), style=wx.LI_VERTICAL)
        sep.SetSize((1,440))
        # help - label
        helpLabel = wx.StaticText(self.panel, pos=(520,10), label="")
        helpLabel.SetFont(self.fontBold)
        # help - text
        helpText = wx.StaticText(self.panel, pos=(520,40), label="")
        helpText.SetFont(self.font)
        # help - show default help, bind show help when clicked on panel
        self.show_help()
        self.panel.Bind(wx.EVT_LEFT_DOWN, lambda evt, arg="Default":
                        self.show_help(evt, arg))
        # processing buttons----------------------------------------------------
        processingSizer = wx.BoxSizer(wx.HORIZONTAL)
        okBtn = wx.Button(self.panel, label="Ok", size=(100,30))
        okBtn.Bind(wx.EVT_BUTTON, self.create_TPR)
        okBtn.Disable()
        cancelBtn = wx.Button(self.panel, label="Cancel", size=(100,30))
        cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)
        processingSizer.Add(okBtn, flag=wx.LEFT, border=270)
        processingSizer.Add(cancelBtn, flag=wx.LEFT, border=10)
        self.panelSizer.Add((-1,20))
        self.panelSizer.Add(processingSizer)
        self.panelSizer.Add((-1,10))
        # statusbar-------------------------------------------------------------
        statusbar = wx.TextCtrl(self.panel, wx.ID_ANY, size=(695, 60),
                                  style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.panelSizer.Add(statusbar)
        # init methods----------------------------------------------------------
        self.Bind(wx.EVT_CLOSE, self.on_close)
        pub.subscribe(self.add_message, "CHANGE")
# __init__ end -----------------------------------------------------------------
#-------------------------------------------------------------------------------
    def add_bitmap_button(self, printTo, inputType, panel=None):
        """
        Description:
        Creates a bitmap button.

        Arguments:
        All of on_open_or_save_file() arguments +

        (panel) panel:
            - specifies the panel to which the button will be added
            - default is None

        Returns:
        (BitMapButton) bmpBtn - bitmap button by which data cna be selected

        Used in:
        add_basic_widget(), add_table_row()
        """
        # set button image
        if inputType == "Config":
            btnImg = "_addButton.png"
            buttonHelp = "Click to select a configuration file"
        elif inputType == "Terrain":
            btnImg = "_addButton.png"
            buttonHelp = "Click to select a terrain"
        elif inputType == "Layer_F":
            btnImg = "_addButton.png"
            buttonHelp = "Click to select an ESRI ShapeFile"
        elif inputType == "Layer_D":
            btnImg = "_addButton_D.png"
            buttonHelp = "Click to select an ESRI Grid"
        elif inputType == "Output":
            btnImg = "_saveButton.png"
            buttonHelp = "Click to save the output"
        # set button panel
        if panel:
            panel = panel
        else:
            panel = self.panel
        # create bitmat button
        bmp = wx.Image(os.path.join(os.path.dirname(__file__), btnImg),
                       wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        bmpBtn = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp,
                                 size=(bmp.GetWidth(), bmp.GetHeight()))
        bmpBtn.SetToolTip(wx.ToolTip(buttonHelp))
        # set button event method
        bmpBtn.Bind(wx.EVT_BUTTON, lambda evt, arg=printTo, arg2=inputType:
                    self.on_open_or_save_file(evt, arg, arg2))
        # return button
        return bmpBtn

    def add_basic_widget(self, label, inputType, bindFunction=None):
        """
        Description:
        Creates bacis widget which consists of: label, TextCtrl, bitmap button.

        Arguments:
        (string) label:
            - widget label

        (string) inputType:
            - same as in on_open_or_save_file()
            - string that is used to set appropriate wildcard
            - 'Terrain' or 'Config' or 'Layer'

        (method) bindFunction:
            - optional argument, default is None
            - specifies a method which is activated, when the contnet of
            TextCtrl is changed

        Returns:
        (set of widgets) basic widget
        """
        horizontalpanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        # label
        label = wx.StaticText(self.panel, label=label)
        label.SetFont(self.fontBold)
        self.panelSizer.Add(label, flag=wx.LEFT|wx.BOTTOM|wx.TOP, border=10)
        # textCtrl
        textCtrl = wx.TextCtrl(self.panel, size=(440,20), style=wx.TE_READONLY,
                               name=inputType)
        textCtrl.Bind(wx.EVT_LEFT_DOWN, lambda evt, arg=inputType:
                      self.show_help(evt, arg))
        if bindFunction != None:
            textCtrl.Bind(wx.EVT_TEXT, bindFunction)
        horizontalpanelSizer.Add(textCtrl)
        # button
        addDataBtn = self.add_bitmap_button(textCtrl, inputType)
        horizontalpanelSizer.Add(addDataBtn, flag=wx.LEFT, border=10)
        self.panelSizer.Add(horizontalpanelSizer, flag=wx.LEFT, border=10)

    def add_table_row(self, textureChoice=[], landuseChoice=[]):
        """
        Description:
        Creates textures table row widget which consists of:
        TextCtrl, 2x AddDataButton, Texture ComboBox, LandUse ComboBox, Color
        rectangle.

        Arguments:
        (list) textureChoice:
            - optional argument, default is a empty list
            - specifies Texture ComboBox choices

        (list) landuseChoice:
            - optional argument, default is a empty list
            - specifies LandUse ComboBox choices

        Returns:
        (set of widgets) table row
        """
        horizontalpanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        # layer
        layer = wx.TextCtrl(self.panelRows, size=(178,21), style=wx.TE_READONLY)
        layer.Bind(wx.EVT_LEFT_DOWN, lambda evt, arg="Layer":
                   self.show_help(evt, arg))
        # buttons
        addDataBtnF = self.add_bitmap_button(layer, "Layer_F", self.panelRows)
        addDataBtnD = self.add_bitmap_button(layer, "Layer_D", self.panelRows)
        # texture
        texture = wx.ComboBox(self.panelRows, -1, "Select Texture", (0,0),
                              (100,21), textureChoice, style=wx.CB_DROPDOWN,
                              name="Texture")
        texture.Bind(wx.EVT_SET_FOCUS, lambda evt, arg="Texture":
                     self.show_help(evt, arg))
        # landuse
        landuse = wx.ComboBox(self.panelRows, -1, "Select LandUse", (0,0),
                              (100,21), landuseChoice, style=wx.CB_DROPDOWN,
                              name="Landuse")
        landuse.Bind(wx.EVT_SET_FOCUS, lambda evt, arg="LandUse":
                     self.show_help(evt, arg))
        #color rectangle
        color = wx.StaticBitmap(self.panelRows, size=(50, 21),
                                style=wx.SIMPLE_BORDER)
        color.SetBackgroundColour(wx.Color(250,250,250))
        color.Bind(wx.EVT_LEFT_DOWN, self.on_change_color)
        # add items to panelSizer
        horizontalpanelSizer.AddMany([layer, addDataBtnF, addDataBtnD, texture,
                                 landuse,color])
        self.panelRowspanelSizer.Add(horizontalpanelSizer)
        self.panelRowspanelSizer.Layout()

    def add_message(self, message, strip=False):
        """
        Description:
        Creates formatted statusbar message.

        Arguments:
        (string) message:
            - message to be printed to statusbar

        (boolean) strip:
            - determines if line strip is necessary

        Used in:
        on_open_or_save_file(), on_change_config(), on_change_hillshading(),
        final_data_check()
        """
        timestamp = datetime.datetime.now().strftime("\n%d.%m.%Y %H:%M:%S | ")
        # if message is from processor
        if hasattr(message, "data"):
            message = message.data
        # if need to strip line break = the very first message
        statusbar = self.FindWindowById(-257)
        if statusbar.GetValue() == "":
            timestamp = timestamp.lstrip()
        # update statusbar
        statusbar.AppendText(timestamp + message)

    def on_open_or_save_file(self, event, printTo, inputType):
        """
        Description:
        Create and show the Open or Save File/Directory Dialog.

        Arguments:
        (TextCtrl) printTo:
            - TextCtrl where the selected file will be displayed

        (string) inputType:
            - string that is used to set appropriate wildcard
            - 'Config', 'Terrain', 'Layer_F', Layer_D, 'Output'

        Returns:
        (string) path to selected file

        Used in:
        add_bitmap_button()
        """
        # dialog settings=======================================================
        if  inputType == "Terrain":
            dlg = wx.DirDialog(self, style=wx.DD_DIR_MUST_EXIST,
                               defaultPath=os.getcwd(),
                               message="Select an ESRI Grid or TIN container "
                               "(directory in which are saved raster/vector "
                               "files representing the terrain).")
        elif inputType == "Layer_F":
            dlg = wx.FileDialog(self, message="Select an ESRI ShapeFile ...",
                                style=wx.OPEN|wx.CHANGE_DIR,  defaultDir="",
                                wildcard="ESRI ShapeFile (*.shp)|*.shp")
        elif inputType == "Layer_D":
            dlg = wx.DirDialog(self, style=wx.DD_DIR_MUST_EXIST,
                               defaultPath=os.getcwd(),
                               message="Select an ESRI Grid container "
                               "(directory in which are saved raster files "
                               "representing the layer).")
        elif inputType == "Output":
            dlg = wx.FileDialog(self, message="Save as ...", defaultDir="",
                                defaultFile="tpr.png",style=wx.SAVE,
                                wildcard="PNG (*.png)|*.png|JPEG (*.jpg)|"
                                "*.jpg|TIFF (*.tif)|*.tif")
        else:
            dlg = wx.FileDialog(self,message="Select a configuration file ...",
                                defaultFile="", wildcard="Xml (*.xml)|*.xml",
                                style=wx.OPEN|wx.CHANGE_DIR)
        # results===============================================================
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            # test geodata------------------------------------------------------
            if (inputType == "Terrain" or inputType == "Layer_F" or
                inputType == "Layer_D"):
                self.add_message("Testing data ...")
                geodataTest = self.validator.test_geodata(path)
                if geodataTest[1]:
                    # set referenced TextCtrl value
                    printTo.SetValue(str(path))
                    printTo.SetInsertionPointEnd()
                    # edit combobox choices
                    if (inputType == "Layer_F" or inputType == "Layer_D"):
                        self.edit_combobox_choice(event, path)
                # update statusbar
                self.add_message(geodataTest[0])
            # test write access-------------------------------------------------
            elif inputType == "Output":
                dirPath = os.path.abspath(os.path.join(path, os.path.pardir))
                writeTest = self.validator.test_write_access(dirPath)
                if writeTest[1] == False:
                    # update statusbar
                    self.add_message(writeTest[0])
                else:
                    printTo.SetValue(str(path))
                    printTo.SetInsertionPointEnd()
            # other - configuration file----------------------------------------
            else:
                # set referenced TextCtrl value
                printTo.SetValue(str(path))
                printTo.SetInsertionPointEnd()
        # close dialog==========================================================
        dlg.Destroy()

    def on_change_color(self, event):
        """
        Description:
        Shows Color Dialog to choose a color.

        Arguments:
        (event) event:
            - event, which object was clicked and need to be updated
            - in this case a click on a color rectangle
        """
        # get clicked rectangle by ID, show help
        clicked = self.panel.FindWindowById(event.GetId())
        if clicked.Name == "HillshadeColor":
            self.show_help(event, "HillshadeColor")
        else:
            self.show_help(event, "Color")
        # dialog settings
        dlg = wx.ColourDialog(self)
        dlg.GetColourData().SetChooseFull(True)
        # results
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            color = data.GetColour().Get()
            clicked.SetBackgroundColour(wx.Color(color[0], color[1], color[2]))
        dlg.Destroy()
        # refresh panel to show new selected color
        self.panel.Refresh()

    def on_change_config(self, event):
        """
        Description:
        Updates Texture and LanUse combobox choices, whenever a configuration
        file is referenced.

        Arguments:
        (event) event:
            - event, which output is processed
            - in this case a click on a button is expected
        """
        # reset form
        self.reset_inputs("Config")
        # get configFile
        configFile = str(event.GetString())
        # if the TextCtrl was cleared by this method or is used the first time
        if configFile != "":
            # validate configFile
            validation = self.validator.validate_config(configFile)
            if validation[1] == True:
                # read configFile
                self.configContent = self.validator.read_config(configFile)
                # update choices of already created comboboxes
                for child in self.panelRows.GetChildren():
                    if child.__class__.__name__ == "ComboBox":
                        if child.Name == "Texture":
                            if not child.IsEmpty():
                                child.Clear()
                                child.SetValue("Select Texture")
                            # update textureChoice
                            self.textureChoice = ([t[0] for t in
                                                   self.configContent[0]])
                            child.AppendItems(self.textureChoice)
                        elif child.Name == "Landuse":
                            if not child.IsEmpty():
                                child.Clear()
                                child.SetValue("Select Texture")
                            # update landuseChoice
                            self.landuseChoice = ([t[0] for t in
                                                   self.configContent[1]])
                            child.AppendItems(self.landuseChoice)
                # update statusbar
                self.add_message(validation[0])
                self.add_message("Texture and LandUse choices updated.")
            # if validation fails clear the TextCtrl
            else:
                event.ClientObject.SetValue("")

    def on_change_hillshading(self, event):
        """
        Description:
        Restores default hillshading options values on the panel and updates
        the status bar if an incorrect value was used.

        Arguments:
        (event) event:
            - event, which  hillshading option is processed
            - in this case a default value change is expected
        """
        # get changed option its value
        option = str(event.ClientObject.Name)
        value = int(event.GetString())
        # validate value
        hs_test = self.validator.test_hillshading_options(option, value)
        # update statusbar
        if not hs_test[1]:
            event.ClientObject.SetValue(hs_test[2])
            self.add_message(hs_test[0])

    def on_add_table_row(self, event):
        """
        Description:
        Add another row to Texture table.

        Arguments:
        (event) event:
            - event, which output is processed
            - in this case a click on a button is expected

        Returns:
        (set of widgets) table row
        """
        # update tableRowsCount, disable addRowBtn if there are too many rows
        self.tableRowsCount += 1
        if self.tableRowsCount == 10:
            self.FindWindowById(-235).Disable()
        # add row, set up scrolling, scroll to last, refresh panelRows
        self.add_table_row(self.textureChoice, self.landuseChoice)
        self.panelRows.SetupScrolling(scroll_x=False, scroll_y=True,
                                      scrollToTop=False)
        self.panelRows.Scroll(-1, self.tableRowsCount - 3)
        self.panelRows.Refresh()

    def on_close(self, event):
        """
        Description:
        Close the frame, reset and hide it if runs from ArcMap.

        Arguments:
        (event) event:
            - click on Close or X button
        """
        # if run from ArcMap----------------------------------------------------
        # reset
        self.reset_inputs()
        # kill processor
        if self.processor:
            del self.processor
            self.processor = None
        # hide form
        self.Show(False)
        # if run as a standalone script (outside of ArcMap)---------------------
        if __name__ == "__main__":
            # close form
            self.Destroy()

    def reset_inputs(self, ignore=None):
        """
        Description:
        Reset input values.

        Arguments:
        (string) ignore:
            - determines which TextCtrl will not be reset

        Used in:
        on_close(), on_change_config()
        """
        # reset panel
        for child in self.panel.GetChildren():
            # reset TextCtrls, ignore if necessary
            if child.__class__.__name__ == "TextCtrl":
                if ignore != None:
                    if child.Name == ignore:
                        pass
                    else:
                        child.SetValue("")
                else:
                    child.SetValue("")
            # reset hillshading options
            elif hasattr(child, "Name"):
                if child.Name == "Azimuth":
                    child.SetValue(315)
                elif child.Name == "Altitude":
                    child.SetValue(45)
                elif child.Name == "Zfactor":
                    child.SetValue(1.0)
                elif child.Name == "Shadows":
                    child.SetValue("No")
                elif child.Name == "Cellsize":
                    child.SetValue(10)
                elif child.Name == "HillshadeColor":
                    child.SetBackgroundColour(wx.Color(255, 255, 255))
        # reset rowPanel
        for child in self.panelRows.GetChildren():
            # reset TextCtrl
            if child.__class__.__name__ == "TextCtrl":
                child.SetValue("")
            # reset ComboBoxes
            elif child.__class__.__name__ == "ComboBox":
                    if child.Name == "Texture":
                        if not child.IsEmpty():
                            child.Clear()
                            child.SetValue("Select Texture")
                    elif child.Name == "Landuse":
                        if not child.IsEmpty():
                            child.Clear()
                            child.SetValue("Select LandUse")
            # reset Color
            elif child.__class__.__name__ == "StaticBitmap":
                child.SetBackgroundColour(wx.Color(255, 255, 255))

    def edit_combobox_choice(self, event, sourcefile):
        """
        Description:
        Edit combobox choices based on input layer type (polyline ShapeFile).

        Arguments:
        (event) event:
            - layer change

        Arguments:
        (string) sourcefile:
            - referenced layer

        Used in:
        on_open_or_save_file()
        """
        # combobox to update
        combobox = self.FindWindowById(event.EventObject.Id - 2)
        comboboxItems = combobox.GetItems()
        linesTextures = []
        # get line textures names to linesTextures list
        for texture in self.configContent[0]:
            if texture[1] == "lines":
                linesTextures.append(texture[0])
        # reset combobox items
        combobox.Clear()
        combobox.SetValue("Select Texture")
        # set new combobox  options - if Polyline Shapefile and other
        if self.validator.test_line_shapefile(sourcefile):
            combobox.AppendItems([i for i in linesTextures])
        else:
            combobox.AppendItems([i for i in comboboxItems
                                  if i not in linesTextures])

    def show_help(self, event=None, inputType="Default"):
        """
        Description:
        Show help text on the right side of the frame.

        Arguments:
        (event) event:
            - event, which widget is processed, default is None
            - in this case a mouse click is expected
            - default is None

        (string) inputType:
            - string that is used to show appropriate help label and text,
            default is 'Default'
            - 'Default', 'Config', 'Terrain', 'Layer', 'Texture', 'LandUse',
            'Azimuth', 'Altitude', 'Zfactor', 'Shadows','Cellsize',
            'HillshadeColor', 'Output'

        Used in:
        add_basic_widget(), add_table_row(), on_change_color()
        """
        # get objects
        helpLabel = self.FindWindowById(-253)
        helpText = self.FindWindowById(-254)
        # change values
        if inputType == "Default":
            helpLabel.SetLabel("TPR Tool")
            helpText.SetLabel("This tool creates a textured \n"
                                   "painted relief based on a XML \n"
                                   "configuration file and user \n"
                                   "inputs. \n\n"
                                   "Note 1:\n"
                                   "Texture and LandUse \n"
                                   "combobox choices will be \n"
                                   "available after setting a \n"
                                   "valid configuration file. \n\n"
                                   "Note 2: \n"
                                   "To show specific help \n"
                                   "just click the field you \n"
                                   "want to know more about.")
        elif inputType == "Config":
            helpLabel.SetLabel("Configuration")
            helpText.SetLabel("Please selecet a valid XML \n"
                                   "configuration file. \n\n"
                                   "This file must contain \n"
                                   "settings for all supported \n"
                                   "Textures and also LandUse \n"
                                   "setting. \n\n"
                                   "Combobox choices will be \n"
                                   "updated after successful \n"
                                   "validation against a XML \n"
                                   "schema.")
        elif inputType == "Terrain":
            helpLabel.SetLabel("Terrain")
            helpText.SetLabel("Please selecet a terrain \n"
                                   "raster. \n\n"
                                   "Terrain is essential for TPR \n"
                                   "creation - TPR is created \n"
                                   "only inside Terrain extent. \n\n"
                                   "Note: \n"
                                   "Only ESRI Grid is supported.")
        elif inputType == "Layer":
            helpLabel.SetLabel("Layer")
            helpText.SetLabel("Please selecet a layer. \n\n"
                                   "Layer represent a surface or \n"
                                   "a LandUse area, e.g. river, \n"
                                   "lake, forest, road, etc. on \n"
                                   "which a texture will be \n"
                                   "applied. \n\n"
                                   "Note: \n"
                                   "ESRI Grid and ShapeFile \n"
                                   "are supported file formats.")
        elif inputType == "Texture":
            helpLabel.SetLabel("Texture")
            helpText.SetLabel("Please specify a Texture \n"
                                   "which will be applied to \n"
                                   "the selected layer.\n\n"
                                   "Be sure to select a Texture \n"
                                   "type, otherwise no texture \n"
                                   "will be generated.")
        elif inputType == "LandUse":
            helpLabel.SetLabel("LandUse")
            helpText.SetLabel("Please specify what kind \n"
                                   "of LandUse type the \n"
                                   "selected layer represents.\n\n"
                                   "Be sure to select a LandUse \n"
                                   "type, otherwise no texture \n"
                                   "will be generated.")
        elif inputType == "Color":
            helpLabel.SetLabel("Color")
            helpText.SetLabel("Please specify the \n"
                                   "Texture color.")
        elif inputType == "Azimuth":
            helpLabel.SetLabel("Azimuth")
            helpText.SetLabel("Azimuth angle of the light \n"
                                   "source. \n\n"
                                   "The azimuth is expressed in \n"
                                   "positive degrees from 0 to \n"
                                   "360, measured clockwise \n"
                                   "from north.\n\n"
                                   "The default is 315 degrees. \n\n"
                                   "Help source:\n"
                                   "ArcGIS Resource Center")
        elif inputType == "Altitude":
            helpLabel.SetLabel("Altitude")
            helpText.SetLabel("Altitude angle of the light \n"
                                   "source above the horizon. \n\n"
                                   "The altitude is expressed in \n"
                                   "positive degrees, with 0 \n"
                                   "degrees at the horizon and \n"
                                   "90 degrees directly overhead.\n\n"
                                   "The default is 45 degrees. \n\n"
                                   "Help source:\n"
                                   "ArcGIS Resource Center")
        elif inputType == "Zfactor":
            helpLabel.SetLabel("Z factor")
            helpText.SetLabel("Number of ground x,y units \n"
                                   "in one surface z unit. \n\n"
                                   "The z-factor adjusts the \n"
                                   "units of measure for the \n"
                                   "z units when they are \n"
                                   "different  from the x,y \n"
                                   "units of the input surface. \n\n"
                                   "The z-values of the input \n"
                                   "surface are multiplied by \n"
                                   "the z-factor when calculating \n"
                                   "the final output surface. \n\n"
                                   "If the x,y units and z units \n"
                                   "are in the same units of  \n"
                                   "measure, the z-factor is 1. \n"
                                   "This is the default. \n\n"
                                   "Help source:\n"
                                   "ArcGIS Resource Center")
        elif inputType == "Shadows":
            helpLabel.SetLabel("Model Shadows")
            helpText.SetLabel("Type of shaded relief to \n"
                                   "be generated. \n\n"
                                   "Yes - The output raster \n"
                                   "considers both local \n"
                                   "illumination angles and \n"
                                   "shadows.\n\n"
                                   "No - The output raster only \n"
                                   "considers local illumination \n"
                                   "angles; the effects of \n"
                                   "shadows are not considered.\n\n"
                                   "The default is No. \n\n"
                                   "Help source:\n"
                                   "ArcGIS Resource Center")
        elif inputType == "Cellsize":
            helpLabel.SetLabel("Cell Size")
            helpText.SetLabel("This value will be used \n"
                                   "only if no specified texture \n"
                                   "sets own cell size.\n"
                                   "Just 'noise' and 'null' \n"
                                   "texture types do not set an \n"
                                   "own cell size. \n\n"
                                   "For example if only one layer\n"
                                   "is referenced using 'null' \n"
                                   "texture type then this value \n"
                                   "will be used as a processing \n"
                                   "cell size. \n\n"
                                   "In most cases it will be \n"
                                   "ignored.")
        elif inputType == "HillshadeColor":
            helpLabel.SetLabel("Hillshade Color")
            helpText.SetLabel("Please specify the \n"
                                   "Hillshade color.\n\n"
                                   "Specified color will be used\n"
                                   "in all areas where no\n"
                                   "textures will be generated.")
        elif inputType == "Output":
            helpLabel.SetLabel("Output")
            helpText.SetLabel("Please selecet output \n"
                                   "location, name and \n"
                                   "file format. \n\n"
                                   "Note 1:\n"
                                   "*.JPEG, *.PNG, *.TIF are \n"
                                   "suported file formats. \n\n"
                                   "Note 2:\n"
                                   "Select a directory with \n"
                                   "write access. \n\n")
        # skip event if it is referenced to get default cursor behaviour
        if event:
            event.Skip()

    def get_values(self):
        """
        Description:
        Gets user data from the dialog window.

        Returns:
        (list of lists) tested, converted and extended data

        Used in:
        create_tpr()
        """
        data = [[]]
        textures = []
        # get data==============================================================
        for widget in self.panelRows.GetChildren():
            if hasattr(widget, "GetValue"):
                textures.append(widget.GetValue())
            elif widget.__class__.__name__ == "StaticBitmap":
                color = widget.GetBackgroundColour().Get()
                textures.append({"r":color[0], "g":color[1], "b":color[2]})
        # get Terrain + Hillshading data and output
        for widget in self.panel.GetChildren():
            otherAttr = ["Terrain", "Azimuth", "Altitude", "Zfactor",
                          "Shadows", "Cellsize", "Output"]
            if widget.Name in otherAttr:
                data[0].append(widget.GetValue())
            # get hillshade color - will be moved to textures list later
            elif widget.__class__.__name__ == "StaticBitmap":
                color = widget.GetBackgroundColour().Get()
                data[0].append({"r":color[0], "g":color[1], "b":color[2]})
        # group textures data by rows
        rows = []
        for i in range(0, len(textures),4):
            rows.append([textures[i],textures[i+1],textures[i+2],textures[i+3]])
        data.append(rows)
        # replace textures and landuses names with specific paramaters
        # readed from configuration file========================================
        params = self.configContent
        for d in data[1]:
            # get color dictionary to appropriate index
            d.insert(1, d[-1])
            del d[-1]
            # all parameters are specified
            if d[0]!="" and d[2]!="Select Texture" and d[3]!="Select LandUse":
                # textures
                for p in params[0]:
                    # match
                    if d[2] == p[0]:
                        # replace
                        del d[2]
                        for index, value in enumerate(p[1:]):
                            if index != 0:
                                value = int(value)      # texture params
                            else:
                                value = value.title()   # texture name
                            d.insert(index + 2, value)
                # landuses
                for p in params[1]:
                    # match
                     if d[-1] == p[0]:
                        # replace
                        del d[-1]
                        d.insert(1, int(p[1]))
        # delete lists (rows) if not fully specified============================
        data[1][:] = [d for d in data[1] if d[0] != ""]
        data[1][:] = [d for d in data[1] if d[-2] != u"Select Texture"]
        data[1][:] = [d for d in data[1] if d[-1] != u"Select LandUse"]
        # move hillshading color to textures list
        data[1].append([data[0][0], 0, data[0][-2], "Texture"])
        del data[0][-2]
        # return tested, converted and extended data============================
        #
        # 1. list = Terrain data + output
        # 2. list = Textures data
        #   - last list contains hillshading color data
        #   - are used to change the color of the hillshade where no textures
        #     will be generated
        #
        # Exampple:
        # [['C:\\terrain', 315, 45, 1.0, 'No', 10, 'C:\\tpr.png'],
        #  [['C:\\forest', 600, {'r': 0, 'b': 64, 'g': 128},
        #    'Cones', 2, 13, 20, 40],
        #   ['C:\\river', 800, {'r': 0, 'b': 255, 'g': 128}, 'Null', -1]
        #   ...
        #   ['C:\\terrain', 0, {'r': 0, 'b': 128, 'g': 0}, 'Texture']
        #   ]
        # ]
        #
        # [[terrain, azimuth, altitude, z-factor,model shadows,cellsize,output],
        #  [[layer, z-index, color dictionary,
        #    texture type, randomness, density, size, height],
        #   ...
        #   [terrain, z-index, color dictionary, texture type]
        #   ]
        # ]
        return data

    def final_data_check(self, event):
        """
        Description:
        Checks if data are correctly specified and only then enables OK button.

        Arguments:
        (event) event:
            - which widget is processed
            - in this case a mouse click is expected

        Used in:
        add_basic_widget()
        """
        output = str(event.GetString())
        # 1. test config--------------------------------------------------------
        # config not OK
        if not self.configContent:
            # if the TextCtrl was cleared by this method
            if output != "":
                event.ClientObject.SetValue("")
                self.add_message("Please specify a configuration file first.")
        # config OK
        else:
            data = self.get_values()
            # 2. test terrain---------------------------------------------------
            # terrain not OK
            if data[0][0] == "":
                # if the TextCtrl was cleared by this method
                if output != "":
                    event.ClientObject.SetValue("")
                    self.add_message("Please specify a terrain first.")
            # terrain OK
            else:
                # 3. test textures----------------------------------------------
                # data OK - at least one texture is fully specified
                if len(data[1]) != 1:
                    self.FindWindowById(-255).Enable()
                    dataStr = "\n".join(", ".join(map(str,d))
                                        for d in data[1][:-1])
                    message = "Data to process:\n" + dataStr
                    self.add_message(message)
                # data not OK
                else:
                    # if the TextCtrl was cleared by this method
                    if output != "":
                        event.ClientObject.SetValue("")
                        self.add_message("Textures data specification "
                                         "is incorrect.")

    def create_TPR(self, event):
        """
        Description:
        Runs TPR creation.

        Arguments:
        (event) event:
            - click on OK button
        """
        # get data
        data = self.get_values()
        # run TPR creation
        self.processor = processor.Processor(data)
        self.processor.main()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# if run as a standalone script (outside of ArcMap)
if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = TprtFrame()
    frame.SetFocus()
    frame.Centre()
    frame.Show()
    app.MainLoop()