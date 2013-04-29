#-------------------------------------------------------------------------------
# Name:         TexturedPaintedRelief_logic.py
# Purpose:      Creates Textured Painted Relief.
#
# Author:       dm
# Version:      1.0
#
# Created:      01/04/2012
# Updated:      22/09/2012 - added Plough()
#               22/02/2013 - added show_message()
#               04/03/2013 - edited show_message()
#               05/03/2013 - edited self.size formula in Squares, Cones, Spheres
#               05/03/2013 - edited points_distribution()
#               11/03/2013 - edited Dem documentation
#               18/03/2013 - edited Processor.init(), prepare_wrokspace_dir()
#               26/03/2013 - added PointBasedTexture() = edited textures logic
#               26/03/2013 - edited create_textures()
#               23/04/2013 - edited Plough()
#
# Copyright:    (c) dm 2012
# Licence:      public :)
#-------------------------------------------------------------------------------
# standard modules
import os
import sys
import math
import time
from datetime import timedelta
import shutil
import operator
# wxPython
from wx.lib.pubsub import Publisher as pub
# arcpy
import arcpy
#-------------------------------------------------------------------------------
class Texture(object):
    """
    Description:
    Textures parent class.

    Arguments:
    (path string) areaOfInterest:
        - target area (path to geodata)

    (integer) zIndex:
        - used to set layers order

    (dictionary) colors:
        - RGB color values
        - e.g. {'r': 26, 'b': 38, 'g': 118}
    """
    def __init__(self, areaOfInterest, zIndex, colors):
        # user referenced arguments
        self.areaOfInterest = areaOfInterest
        self.zIndex = zIndex
        self.colors = colors
        # user independent arguments; just referenced, will be overrided
        self.dataType = str(arcpy.Describe(areaOfInterest).dataType)
        self.texture = None      # texture raster
        self.landuse = None      # landuse raster
        self.cellSize = 9999.0   # cellSize - just a dum number to avoid errors

    def to_raster(self, sourceFile, value=1):
        """
        Description:
        Converts ShapeFile to raster.

        Arguments:
        (path string) sourceFile:
            - target area (path to geodata)

        (integer) value:
            - output raster value
            - default value = 1

        Returns:
        (raster) outRaster/sourceFile - converted/original raster
        """
        if self.dataType == "ShapeFile":
            # get ShapeFile name
            inShapeName = str(arcpy.Describe(sourceFile).baseName)
            outShapeName = "copy" + inShapeName + ".shp"
            outRastername = inShapeName[:13]
            # copy ShapeFile to 'Scratch' dir
            helperPath = os.path.join(arcpy.env.workspace, outShapeName)
            helperFile = arcpy.CopyFeatures_management(sourceFile, helperPath)
            # prepare and calculate _TPR_ field values
            arcpy.AddField_management(helperFile, "_TPR_", "LONG")
            arcpy.CalculateField_management(helperFile, "_TPR_", value)
            # convert to raster
            outRaster = arcpy.FeatureToRaster_conversion(helperFile, "_TPR_",
                        outRastername, self.cellSize)
            # delete helperFile and return outRaster
            arcpy.Delete_management(helperFile)
            return outRaster
        else:
            return sourceFile

    def create(self):
        """
        Description:
        Creates default 'texture' - this will be used in areas where no texture
        will be generated to change hillshade default grayscale color.
        No actual texture is generated - just constant raster with same extent
        as DEM, so it can be used when merging textures by z-index and eventualy
        when creating landuse raster.

        Returns:
        (raster) default - constant value (0) raster with same extent as DEM

        Note:
        This method is overrided in each subclass of 'Texture' class.
        """
        default = arcpy.sa.CreateConstantRaster(0)
        return default


class PointBasedTexture(Texture):
    """
    Description:
    PointBasedTexture (Squares, Cones, Spheres + Plough) parent class.

    Arguments:
    (integer) randomness:
        - objects distribution type
        - 0 - regular, 1 - random, 10 - very random, ...

    (integer) density:
        - objects centroids distance in map units
        - STRONGLY affected by randomness

    (integer) size:
        - square side in map units

    Note:
    Object size != self.size because of self.cellSize (raster can't use cell
    slices), it is always +/- 1 self.cellSize bigger/smaller than self.size.
    """
    def __init__(self, areaOfInterest, zIndex, colors,
                 randomness, density, size):
        # initialize parent class
        Texture.__init__(self, areaOfInterest, zIndex, colors)
        # set own attributes
        self.randomness = randomness
        self.density = density
        self.size = float(size) / 2
        self.normalRaster = None    # same raster for all PointBasedTextures
        self.xmap = None            # created and overrided by
        self.ymap = None            # Processor.create_textures()

    def points_distribution(self, randomness, density):
        """
        Description:
        Creates points distribution - CORE function for point based textures.

        Returns:
        (raster) points - cells definning points are 1, others are NoData

        Note:
        self.areaOfInterest must have values > 1 else points won't be created.
        """
        # reclassify 0 (zero) values if needed
        areaMin = arcpy.Raster(self.areaOfInterest).minimum
        if areaMin < 1:
            fix = arcpy.sa.Reclassify(self.areaOfInterest, "VALUE",
                                      "{0} 1".format(areaMin))
            # set new areaOfInterest attribute
            setattr(self, "areaOfInterest", fix)
        # generate points
        densityFix = round(self.density / self.cellSize, 2)
        nrmDsr = arcpy.sa.Int(self.normalRaster * self.randomness + densityFix)
        points = arcpy.sa.Con((arcpy.sa.Mod(self.xmap, nrmDsr) == 0) &
                              (arcpy.sa.Mod(self.ymap, nrmDsr) == 0) &
                              self.areaOfInterest, 1)
        return points


class Squares(PointBasedTexture):
    """
    Description:
    Squares texture.

    Arguments:
    All of PointBasedTexture class arguments +

    (integer) height:
        - square height in map units
    """
    def __init__(self, areaOfInterest, zIndex, colors,
                 randomness, density, size, height):
        # initialize parent class
        PointBasedTexture.__init__(self, areaOfInterest, zIndex, colors,
                                   randomness, density, size)
        # set own cellSize and height
        self.cellSize = self.size
        self.height = height

    def create(self):
        """
        Description:
        Creates squares texture (constant size squares).

        Returns:
        (raster) squares - texture raster, cells with no objects are NoData
        """
        # check data type - raster needed
        fix = self.to_raster(self.areaOfInterest)
        setattr(self, "areaOfInterest", fix)
        # create own texture
        size = (self.size * 2) / self.cellSize
        squares = arcpy.sa.FocalStatistics(
                  self.points_distribution(self.randomness, self.density),
                  arcpy.sa.NbrRectangle(size, size)) * self.height
        return squares


class Cones(PointBasedTexture):
    """
    Description:
    Cones texture.

    Arguments:
    All of PointBasedTexture class arguments +

    (integer) height:
        - cone height in map units
    """
    def __init__(self, areaOfInterest, zIndex, colors,
                 randomness, density, size, height):
        # initialize parent class
        PointBasedTexture.__init__(self, areaOfInterest, zIndex, colors,
                                   randomness, density, size)
        # set own cellSize and height
        self.cellSize = round(self.size * 2 / 11, 2)
        self.height = height

    def create(self):
        """
        Description:
        Creates regular cones texture (cones with constant diameter and height).

        Returns:
        (raster) cones - texture raster, cells with no objects are NoData
        """
        # check data type - raster needed
        fix = self.to_raster(self.areaOfInterest)
        setattr(self, "areaOfInterest", fix)
        # create own texture
        cones1 = arcpy.sa.Abs(arcpy.sa.EucDistance(
                 self.points_distribution(self.randomness, self.density),
                 self.size))
        # invert and fix cones highs
        maxHeight = float(str(arcpy.GetRasterProperties_management(cones1,
                    "MAXIMUM")).replace(",", "."))
        cones = (maxHeight - cones1) / (maxHeight / self.height)
        return cones


class Spheres(PointBasedTexture):
    """
    Description:
    Spheres texture.

    Arguments:
    All of PointBasedTexture class arguments.
    """
    def __init__(self, areaOfInterest, zIndex, colors,
                 randomness, density, size):
        # initialize parent class
        PointBasedTexture.__init__(self, areaOfInterest, zIndex, colors,
                                   randomness, density, size)
        # set own cellSize
        self.cellSize = round(self.size * 2 / 11, 2)

    def create(self, specialPoints=False):
        """
        Description:
        Creates regular shperes texture (spheres with constant diameter).

        Arguments:
        (raster) specialPoints:
            - optional argument
            - dermines points distribution raster for spheres creation
            - default set to "classic" points_distribution()

        Returns:
        (raster) spheres - texture raster, cells with no objects are NoData
        """
        # check data type - raster needed
        fix = self.to_raster(self.areaOfInterest)
        setattr(self, "areaOfInterest", fix)
        # check if use "classic" points distribution or some "special"
        if specialPoints:
            points = specialPoints
        else:
            points = self.points_distribution(self.randomness, self.density)
        # create own texture
        spheres = arcpy.sa.SquareRoot(arcpy.sa.Power(self.size ,2) -
                  arcpy.sa.Power(arcpy.sa.EucDistance(points, self.size), 2))
        # fix spheres highs
        fix1 = spheres - float(str(arcpy.GetRasterProperties_management(spheres,
               "MINIMUM")).replace(",", "."))
        fix2 = float(str(arcpy.GetRasterProperties_management(fix1,
               "MAXIMUM")).replace(",", ".")) / (self.size * 2)
        spheres = fix1 / fix2
        return spheres


class Plough(Spheres):
    """
    Description:
    Plough texture (texture similar to ploughed field).

    Arguments:
    All of Spheres class arguments +

    (integer) angle:
        - ploughing orientation in degrees
        - 0 degrees means ploughing is parallel with Y-axis
        - values in interval <0,180>

    (integer) interval:
        - distance between individual "lines"
    """
    def __init__(self, areaOfInterest, zIndex, colors, interval, angle):
        # initialize parent class
        Spheres.__init__(self, areaOfInterest, zIndex, colors, 0.4,
                         interval, interval * 2.5)
        # set own attributes
        self.angle = angle

    def create(self):
        """
        Description:
        Creates polughing texture.

        Returns:
        (raster) plough - texture raster with none NoData cells
        """
        # prepare helper raster-------------------------------------------------
        # helper raster name
        hlpName = str("hlp" + arcpy.Describe(self.areaOfInterest).baseName)[:13]
        # set new extent side (Pythagorean theorem)
        extent = arcpy.Describe(self.areaOfInterest).extent
        deltaX = abs(extent.XMax - extent.XMin)
        deltaY = abs(extent.YMax - extent.YMin)
        newExtentSide = math.sqrt(pow(deltaX, 2) + pow(deltaY, 2)) / 2
        # get extent centeroid
        centerX = extent.XMin + deltaX / 2
        centerY = extent.YMin + deltaY / 2
        center = "{0} {1}".format(centerX, centerY)
        # set new extent values
        newXMin = centerX - newExtentSide * 1.5
        newYMin = centerY - newExtentSide * 1.5
        newXMax = centerX + newExtentSide * 1.5
        newYMax = centerY + newExtentSide * 1.5
        # create helper raster - extent equal square raster
        hlpRaster = arcpy.sa.CreateConstantRaster(1, "INTEGER", self.cellSize,
                    arcpy.Extent(newXMin, newYMin, newXMax, newYMax))
        # generate points-------------------------------------------------------
        # quit ymap, set mask and helper areaOfInterest
        setattr(self, "ymap", self.xmap)
        mask = self.to_raster(self.areaOfInterest)
        setattr(self, "areaOfInterest", str(hlpRaster))
        # create, rotate and crop points
        pts = self.points_distribution(self.randomness, self.density)
        ptsRot = arcpy.Rotate_management(pts, "rotated", self.angle, center)
        ptsRotCrp = arcpy.sa.Con(mask, ptsRot)
        ptsRotCrp.save(hlpName)
        #set proper areaOfInterest and dataType, delete points rasters
        setattr(self, "areaOfInterest", str(ptsRotCrp))
        setattr(self, "dataType", arcpy.Describe(self.areaOfInterest).dataType)
        # create Plough texture based on rotated points-------------------------
        # plough values in interval <-1, 0>
        spheres = super(Plough, self).create(self.areaOfInterest)
        plough = (spheres / (self.size * 2)) * -1
        # delete helper rasters, return plough texture
        del pts, ptsRot, ptsRotCrp, spheres
        return plough


class Lines(Texture):
    """
    Description:
    Lines texture.
    Can be used only with LINE SHAPEFILES.

    Arguments:
    All of Texture class arguments +

    (integer) width:
        - line width in map units

    (integer) height:
        - line height in map units
    """
    def __init__(self, areaOfInterest, zIndex, colors, width, height):
        # initialize parent class
        Texture.__init__(self, areaOfInterest, zIndex, colors)
        # set own attributes
        self.width = float(width)
        self.height = height
        # set own cellSize
        self.cellSize = round(self.width / 2, 2)

    def create(self):
        """
        Description:
        Creates buffered line texture.

        Returns:
        (raster) lines - texture raster
        """
        outputName = arcpy.Describe(self.areaOfInterest).name[:-4]
        # buffer
        lineBuff = arcpy.Buffer_analysis(self.areaOfInterest, outputName,
                   self.width / 2, "FULL", "ROUND", "NONE")
        # convert to raster
        lines = self.to_raster(lineBuff, self.height)
        # delete helper file
        arcpy.Delete_management(lineBuff)
        return lines


class Noise(Texture):
    """
    Description:
    Noise texture - random raster.

    Arguments:
    All of Texture class arguments +

    (integer) minimum:
        - minimum texture value

    (integer) maximum:
        - maximum texture value
    """
    def __init__(self, areaOfInterest, zIndex, colors, minimum, maximum):
        # initialize parent class
        Texture.__init__(self, areaOfInterest, zIndex, colors)
        # set own attributes
        self.min = int(minimum)
        self.max = int(maximum)

    def create(self):
        """
        Description:
        Creates random raster texture.

        Returns:
        (raster) noise - texture raster, cells with no objects are NoData
        """
        # check data type - raster needed
        fix = self.to_raster(self.areaOfInterest)
        setattr(self, "areaOfInterest", fix)
        # create own texture
        outName = (arcpy.Describe(self.areaOfInterest).baseName)[:5] + "_rand"
        outExtent = arcpy.Raster(self.areaOfInterest).extent
        distribution = "INTEGER {0} {1}".format(self.min, self.max)
        noise1 = arcpy.CreateRandomRaster_management(arcpy.env.workspace,
                 outName, distribution, outExtent, arcpy.env.cellSize)
        # cropp random raster to self.areaOfInterest and return texture
        noise = arcpy.sa.Con(self.areaOfInterest, noise1)
        return noise


class Null(Texture):
    """
    Description:
    Null texture.
    None texture is generated.

    Arguments:
    All of Texture class arguments +

    (integer) value:
        - output raster value
    """
    def __init__(self, areaOfInterest, zIndex, colors, value):
        # initialize parent class
        Texture.__init__(self, areaOfInterest, zIndex, colors)
        # set own attributes
        self.value = int(value)

    def create(self):
        """
        Description:
        Creates null texture - just converts Shapefile to raster or resamples
        referenced raster.

        Returns:
        (raster) null - texture raster, cells with no objects are NoData
        """
        if self.dataType == "ShapeFile":
            null = self.to_raster(self.areaOfInterest, self.value)
        else:
            inRaster = self.areaOfInterest
            reclassValue = self.value
            inMin = arcpy.GetRasterProperties_management(inRaster, "MINIMUM")
            inMax = arcpy.GetRasterProperties_management(inRaster, "MAXIMUM")
            remap = "{0} {1} {2}".format(inMin, inMax, reclassValue)
            null = arcpy.sa.Reclassify(inRaster, "Value", remap, "NODATA")
        return null


class Dem():
    """
    Description:
    Class for singleton DEM object (Digital Elevation Model) manipulation.

    Arguments:
    (path string) sourceFile:
        - path to the terrain

    (integer) azimuth:
        - azimuth angle of the light source

    (integer) altitude:
        - altitude angle of the light source above the horizon

    (float) zfactor:
        - adjusts the units of measure for the Z units when they are different
          from the x,y units of the input surface

    (string) shadows:
        - type of shaded relief to be generated - w/ ot w/out shadows

    (float) cellSize:
        - cellSize returned by Processor.set_cellSize()
    """
    def __init__(self,sourceFile,azimuth,altitude,zfactor,shadows,cellSize):
        terrainType = str(arcpy.Describe(sourceFile).dataType)
        # Tin processing
        if terrainType  == "Tin":
            self.dem = arcpy.TinRaster_3d(sourceFile, "dem", "INT", "LINEAR",
                       "CELLSIZE {0}".format(str(cellSize).replace(".", ",")))
        # RasterDataset processing
        elif terrainType == "RasterDataset":
            rasterObject = arcpy.Raster(sourceFile)
            # if cells are squares
            if rasterObject.meanCellHeight == rasterObject.meanCellWidth:
                # but not the right size
                if rasterObject.meanCellHeight != cellSize:
                    self.dem = arcpy.Resample_management(sourceFile, "dem",
                                                         cellSize, "BILINEAR")
                # and right size
                else:
                    self.dem = sourceFile
            # if cells are not squares
            else:
                self.dem = arcpy.Resample_management(sourceFile, "dem",
                                                     cellSize, "BILINEAR")
        # proper DEM extent for processing
        self.extent = arcpy.Raster(self.dem).extent
        # hillshading attributes of the textured DEM
        self.hillshade = None   ## will be set by Dem.hillshade_to_percent()
        self.azimuth = azimuth
        self.alitude = altitude
        self.zfactor = zfactor
        if shadows == "No":
            self.shadows = False
        if shadows == "Yes":
            self.shadows = True

    def add_textures(self, textures):
        """
        Description:
        Orders, merges and add textures to the DEM.

        Arguments:
        (list of lists) textures:
            - textures by Processor.initialize_textures()

        Returns:
        (raster) texturedDEM - texturedDEM = DEM + textures

        Note:
        Raster 'bumpmap' must be 32b so it can represents negative values.
        """
        try:
            # sort textures
            inRasters = ";".join([str(t.texture) for t in sorted(textures,
                        key=operator.attrgetter("zIndex"), reverse=True)])
            # join textures
            joinedTextures = arcpy.MosaicToNewRaster_management(inRasters,
                             arcpy.env.workspace, "jnttxtrs", "",
                             "32_BIT_SIGNED", "", 1, "First")
            # merge textures with terrain
            texturedDEM = arcpy.sa.Con(arcpy.sa.IsNull(joinedTextures),
                          self.dem, joinedTextures + arcpy.Raster(self.dem))
            return texturedDEM
        # if something went wrong ...
        except Exception as exception:
            message = "Merging rasters failed - {0}.".format(exception)
            if __name__ == "__main__":
                sys.exit(message)
            else:
                pub.sendMessage("CHANGE", message)

    def hillshade_to_percent(self, texturedDEM):
        """
        Description:
        Converts the Hillshade to percent values (0 - 1).

        Arguments:
        (raster) texturedDEM:
            - texturedDEM returned by Dem.add_textures()

        Returns:
        (raster) hsPer - raster with values in 0 - 1 range
        """
        # create and save hillshade
        self.hillshade = arcpy.sa.Hillshade(texturedDEM, self.azimuth,
                         self.alitude, self.shadows, self.zfactor)
        self.hillshade.save("hillshade")
        # convert hillshade to percent
        hsPer = self.hillshade / 255.0
        return hsPer


class Processor():
    """
    Description:
    Basic Processing Class.
    Contains methods for all batch processings and utilities.

    Arguments:
    (list) uData:
        - user data
    """
    def __init__(self, uData):
        self.data = uData
        # initialize textures
        self.textures = self.initialize_textures()
        # set cellSize
        self.cellSize = self.set_cellSize()
        # set workspace directory
        self.workspace = self.prepare_workspace()
        # set output path
        self.output = str(self.data[0][6])

    def prepare_workspace(self):
        """
        Description:
        Tests if 'Scratch' dir exists, if not, creates it.

        Returns:
        (path string) workspaceDir - path to the workspaceDir
        """
        outDir = os.path.abspath(os.path.join(self.data[0][6], os.path.pardir))
        workspaceDir = os.path.join(outDir, "tprScratch")
        #-----------------------------------------------------------------------
        def create_workspace_dir():
            """
            Description:
            Creates workspace directory.
            """
            try:
                os.mkdir(workspaceDir)
            except OSError as oserror:
                message = "Directory creation failed: {0}".format(oserror)
                self.show_message(message, True)
        #-----------------------------------------------------------------------
        # if 'tprScratch' does not exists - just create it
        if not os.path.exists(workspaceDir):
            create_workspace_dir()
        # if 'tprScratch' exists - delete it and create a new one
        else:
            shutil.rmtree(workspaceDir)
            create_workspace_dir()
        # return workspaceDir
        return workspaceDir

    def set_cellSize(self):
        """
        Description:
        Sets processing cellSize.

        Returns:
        (float) cellSize - processing cellSize
        """
        minCellSize = []
        for texture in self.textures:
            minCellSize.append(texture.cellSize)
        # return processing cellSize
        if sorted(minCellSize)[0] == 9999.0:
            return self.data[0][5]
        else:
            return sorted(minCellSize)[0]

    def initialize_textures(self):
        """
        Description:
        Creates instance for each referenced texture.

        Returns:
        (list) textures - list of texture objects
        """
        # initialize textures and append textures list
        textures = []
        for t in self.data[1]:
            # style, areaOfInterst, zIndex, colors, texture arguments
            # t[3]   t[0]           t[1]    t[2]    *t[4:]
            textures.append(eval(t[3])(t[0], t[1], t[2], *t[4:]))
        # return textures objects list
        return textures

    def create_textures(self):
        """
        Description:
        Creates texture raster for each referenced texture.

        Returns:
        (raster) texture - texture raster
        """
        # basic rasters - same for all pointbased textures
        xmap = arcpy.sa.FlowAccumulation(
               arcpy.sa.CreateConstantRaster(1,"INTEGER"))
        ymap = arcpy.sa.FlowAccumulation(
               arcpy.sa.CreateConstantRaster(64, "INTEGER"))
        normalRaster = arcpy.sa.CreateNormalRaster()
        # loop through referenced textures and create texture raster
        for texture in self.textures:
            if isinstance(texture, PointBasedTexture):
                texture.normalRaster = normalRaster #
                texture.xmap = xmap                 #
                texture.ymap = ymap                 # overriding
            texture.cellSize = self.cellSize        #
            texture.texture = texture.create()      #

    def create_landuse(self):
        """
        Description:
        Merges textures ordered and reclassified by z-index.
        Updates (overrides) property Texture.landuse so from now on it
        refers to an actual raster reclassified by z-index.

        Returns:
        (raster) landuse - merged and ordered textures with z-index values
        """
        # reclass texture by it's z-index value to identify it later
        for t in self.textures:
            # prepare reclass params
            inRaster = t.texture
            reclassValue = t.zIndex
            inMin = arcpy.GetRasterProperties_management(inRaster, "MINIMUM")
            inMax = arcpy.GetRasterProperties_management(inRaster, "MAXIMUM")
            remap = "{0} {1} {2}".format(inMin, inMax, reclassValue)
            # reclass
            t.landuse = arcpy.sa.Reclassify(inRaster, "Value", remap, "NODATA")
            outRas = str("lnd" + arcpy.Describe(t.areaOfInterest).baseName)[:13]
            t.landuse.save(outRas)
        # merge textures together
        try:
            inRasters = ";".join([str(t.landuse) for t in sorted(self.textures,
                        key=operator.attrgetter('zIndex'), reverse=True)])
            landuse = arcpy.MosaicToNewRaster_management(inRasters,
                      arcpy.env.workspace, "landuse","", "16_BIT_UNSIGNED",
                      self.cellSize, 1, "First")
            return landuse
        except Exception as exception:
            message = "Landuse creation failed - {0}.".format(exception)
            self.show_message(message, True)

    def create_tpr(self, landuse, hillshadePer, hillshade):
        """
        Description:
        Creates TPR raster (RGB composite).

        Arguments:
        (raster) landuse:
            - landuse raster by Processor.create_landuse()

        (raster) hillshadePer:
            - raster by Dem.hillshade_to_percent()

        (raster) hillshade:
            - raster referenced by Dem.hillshade property

        Returns:
        (raster) tpr - final Textured Painted Relief
        """
        r = []
        g = []
        b = []
        colors = []
        # get values for each color and each z-index----------------------------
        for t in self.textures:
            for color in t.colors:
                remapValue = "{0} {1}".format(t.zIndex, t.colors[color])
                if color == "r":
                    r.append(remapValue)
                elif color == "g":
                    g.append(remapValue)
                elif color == "b":
                    b.append(remapValue)
        colors.extend([r, g, b])
        # prepare r, g, b components--------------------------------------------
        for color in colors:
            # prepare reclass params
            inRaster =  landuse
            reclassField = "Value"
            remap = ";".join([c for c in color])
            # reclass by color and multiply by hillshadePercent to get
            # appropriate color change
            colorEdited = arcpy.sa.Int(arcpy.sa.Reclassify(inRaster,
                          reclassField, remap, "NODATA") * hillshadePer)
            # merge together with hillshade and append to color list
            color.append(arcpy.sa.Con(arcpy.sa.IsNull(colorEdited),
                                      hillshade, colorEdited))
        # tpr = RGB composite---------------------------------------------------
        inRasters = ";".join([str(color[-1]) for color in colors])
        try:
            arcpy.env.addOutputsToMap = True
            tpr = arcpy.CompositeBands_management(inRasters, self.output)
        except Exception as exception:
            message = "Textured painted relief error - {0}.".format(exception)
            self.show_message(message, True)

    def show_message(self, message, terminate=False):
        """
        Manages message sending - send to GUI or to standard output.

        Arguments:
        (string) message:
            - message to be displayed
        (boolean) terminate:
            - determines if just print the message or use sys.exit()

        Used in:
        prepare_workspace(), create_landuse(), create_tpr(), main()
        """
        if __name__ == "__main__":
            if terminate == True:
                sys.exit(message)
            else:
                print message
        else:
            pub.sendMessage("CHANGE", message)

    def cleanup(self):
        """
        Description:
        Deletes temporary rasters and workspace directory.
        """
        # get rasters to delete
        toDel = []
        for outRaster in arcpy.ListFiles():
            if str(arcpy.Describe(outRaster).dataType) == "RasterDataset":
                toDel.append(outRaster)
        # delete rasters
        for delRaster in toDel:
            arcpy.Delete_management(delRaster)
        # delete scratch folder
        shutil.rmtree(self.workspace)

    def main(self):
        """
        Description:
        Main processing method. Implements tool logic.
        """
        try:
            extensions = ["Spatial","3D"]
            for extension in extensions:
                if arcpy.CheckExtension(extension) == "Available":
                    arcpy.CheckOutExtension(extension)
            #-------------------------------------------------------------------
            # Preparations
            #-------------------------------------------------------------------
            t0 = time.time()
            self.show_message("Starting processing!")
            # basic environments
            arcpy.env.addOutputsToMap = False
            arcpy.env.overwriteOutput = True
            arcpy.env.cellSize = self.cellSize
            arcpy.env.workspace = self.workspace
            arcpy.env.scratchWorkspace = self.workspace
            # create Dem object, set working extent
            dem = Dem(self.data[0][0], self.data[0][1], self.data[0][2],
                      self.data[0][3], self.data[0][4], self.cellSize)
            arcpy.env.extent = dem.extent
            #-------------------------------------------------------------------
            # Processing
            #-------------------------------------------------------------------
            # create and add textures to DEM
            t1 = time.time()
            textures = self.create_textures()
            self.show_message("Duration: {0} | Textures OK.".format(
                              timedelta(seconds=round(time.time()-t1))))
            t1 = time.time()
            texturedDEM = dem.add_textures(self.textures)
            self.show_message("Duration: {0} | Bumpmap OK.".format(
                              timedelta(seconds=round(time.time()-t1))))
            # hillshadePercent
            t1 = time.time()
            hsper = dem.hillshade_to_percent(texturedDEM)
            self.show_message("Duration: {0} | Hillshade OK.".format(
                              timedelta(seconds=round(time.time()-t1))))
            # create landuse
            t1 = time.time()
            landuse = self.create_landuse()
            self.show_message("Duration: {0} | Landuse OK.".format(
                              timedelta(seconds=round(time.time()-t1))))
            # create tpr
            t1 = time.time()
            tpr = self.create_tpr(landuse, hsper, dem.hillshade)
            self.show_message("Duration: {0} | TPR OK.".format(
                              timedelta(seconds=round(time.time()-t1))))
            self.show_message("Processing finished!")
            #-------------------------------------------------------------------
        except Exception as exception:
            self.show_message(arcpy.GetMessage(0))
            self.show_message(arcpy.GetMessage(1))
            self.show_message(arcpy.GetMessage(2))
            self.show_message(str(exception))
        finally:
            # return extensions
            for extension in extensions:
                arcpy.CheckInExtension(extension)
            # show totol duration
            self.show_message("Total duration: {0}.".format(
                               timedelta(seconds=round(time.time()-t0))))
            # cleanup - remove objects (to loose locks) and files
            del dem, textures, texturedDEM, hsper, landuse, tpr
            self.cleanup()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# Uncomment code below and change data definition to run as standalone script
##if __name__ == "__main__":
##    data = [[u'D:\\someTerrain', 315, 45, 1.0, u'No', 10, u'D:\\someDirectory\\tpr.png'],
##            [[u'D:\\someData1', 800, {'r': 0, 'b': 255, 'g': 0}, 'Squares', 2, 20, 10, 40],
##             [u'D:\\someData2', 600, {'r': 255, 'b': 0, 'g': 0}, 'Cones', 5, 20, 20, 30]]
##           ]
##    processor = Processor(data)
##    processor.main()