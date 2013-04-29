#-------------------------------------------------------------------------------
# Name:         TexturedPaintedRelief_validator.py
# Purpose:      Validates user data.
#
# Author:       dm
# Version:      1.0
#
# Created:      31/01/2013
# Updated:      19/12/2012 - added test_write_access()
#               05/04/2013 - added test_line_shapefile()
#
# Copyright:    (c) dm 2012
# Licence:      public :)
#-------------------------------------------------------------------------------
# standard modules
import os
# XML related
from lxml import etree
# arcpy
import arcpy
#-------------------------------------------------------------------------------
class Validator():
    """
    Description:
    Parse and validates user data and configurafion file.
    """
    def __init__(self):
        self.message = str
        self.state = bool
        self.default = 0

    def validate_config(self, configFile):
        """
        Description:
        Validates XML configuration file againts XSD schema.

        Arguments:
        (string) configFile:
            - path to selected file

        Returns:
        (string) message
        (boolean) state
        """
        # test referenced XML file existence
        if not os.path.exists(configFile):
            self.message = "Config file does not exist."
            self.state = False
        # validate XML
        try:
            xsd_doc_folder = os.path.dirname(os.path.realpath(__file__))
            xsd_doc_path = os.path.join(xsd_doc_folder, "settings.xsd")
            xsd_doc = etree.parse(xsd_doc_path)
            xsd = etree.XMLSchema(xsd_doc)
            xml = etree.parse(configFile)
            xsd.validate(xml)
            # set output message
            if xsd.error_log:
                self.message = ("Configuration file validation failed. \n"
                                "'{0}', line {1} - {2}".format(
                                xsd.error_log[0].filename,xsd.error_log[0].line,
                                xsd.error_log[0].message))
                self.state = False
            else:
                self.message = "Configuration file OK."
                self.state = True
        except StandardError as exception:
            self.message = ("Configuration file validation failed. \n" +
                            str(exception))
            self.state = False
        # return message to be printed to statusbar and validation state
        return self.message, self.state

    def read_config(self, configFile):
        """
        Description:
        Parse XML configuration file.

        Arguments:
        (string) configFile:
            - path to selected file

        Returns:
        (list of lists) texture - texture arguments
        (list of lists) landuse - landuse arguments
        """
        xml = etree.parse(configFile)
        texture = []
        landuse = []
        for child in xml.getroot().getchildren():
            # get texture attributes--------------------------------------------
            if child.tag == "textures":
                for child2 in child.getchildren():
                    elemList = [] ## helper list
                    elemList.append(child2.tag)
                    for child3 in child2.getchildren():
                        elemList.append(child3.text)
                    # switch elements order to get texture name first
                    elemList[0], elemList[1] = elemList[1], elemList[0]
                    texture.append(elemList)
            # get landuse attributes--------------------------------------------
            elif child.tag == "landuses":
                for child2 in child.getchildren():
                    elemList = [] ## helper list
                    elemList.append(child2.attrib["name"])
                    for child3 in child2.getchildren():
                         elemList.append(child3.text)
                    landuse.append(elemList)
        # return texture and landuse data
        # texture example:
        #   [['squares1', 'squares', '5', '13', '20', '40'],
        #    ['cones1', 'cones', '2', '13', '20', '40'], ...]
        # landuse example:
        #   [['road', '10'], ['water', '20'], ['field', '30'], ...]
        return texture, landuse

    def test_geodata(self, sourceFile):
        """
        Description:
        Check if referenced files exists and are supported.
        File types accepted:
            - terrain: 'RasterDataset', 'Tin'
            - layer: 'RasterDataset', 'ShapeFile'

        Arguments:
        (string) sourceFile:
            - path to selected file

        Returns:
        (string) message
        (boolean) state

        Used in:
        on_open_or_save_file()
        """
        # test existance
        if arcpy.Exists(sourceFile):
            # get type
            try:
                dType = arcpy.Describe(sourceFile).dataType
            except:
                dType = type(sourceFile)
            # test geodata support
            if (dType=="ShapeFile" or dType=="RasterDataset" or dType=="Tin"):
                self.message = ("{1} '{0}' OK.".format(sourceFile, dType))
                self.state = True
            # other than geodata
            else:
                self.message = ("{1} '{0}' is not supported."
                                .format(sourceFile, dType))
                self.state = False
        # not existing
        else:
            self.message = ("{1} '{0}' does not exist or is corrupted.\nHint: "
                            "do not include special characters or spaces in "
                            "file names.".format(sourceFile, dType))
            self.message = "fuck"
            self.state = False
        # return stage nad message
        return self.message, self.state

    def test_line_shapefile(self, sourceFile):
        """
        Description:
        Tests if ShapeFile is Polyline type.

        Arguments:
        (string) sourceFile:
            - ShapeFile to check

        Returns:
            boolean

        Used in:
        on_open_or_save_file()
        """
        if arcpy.Describe(sourceFile).dataType == "ShapeFile":
            if arcpy.Describe(sourceFile).shapeType == "Polyline":
                return True
            else:
                return False

    def test_hillshading_options(self, option, value):
        """
        Description:
        Validates hillshading options values.

        Arguments:
        (string) option:
            - which option is issued

        (integer) value:
            - value to be tested

        Returns:
        (string) message
        (boolean) state
        (integer) default

        Used in:
        on_change_hillshading()
        """
        if option == "Azimuth":
            if value > 360:
                self.message = ("Azimuth value must be from 0 to 360 degrees. "
                                "Default value was set.")
                self.state = False
                self.default = 315
            else:
                self.state = True
        elif option == "Altitude":
            if value > 90:
                self.message = ("Altitude value must be from 0 to 90 degrees. "
                                "Default value was set.")
                self.state = False
                self.default = 45
            else:
                self.state = True
        return self.message, self.state, self.default

    def test_write_access(self, path):
        """
        Description:
        Check for directory write access.

        Arguments:
        (string) path:
            - path to selected directory

        Returns:
        (string) message
        (boolean) state

        Used in:
        on_open_or_save_file()
        """
        self.state = os.access(path, os.W_OK)
        if self.state == False:
            self.message = ("Can't write to selected directory. Please select "
                            "a directory with write access.")
        return self.message, self.state