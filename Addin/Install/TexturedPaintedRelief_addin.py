#-------------------------------------------------------------------------------
# Name:         TexturedPaintedRelief_addin.py
# Purpose:      ArcGIS addin for TexturedPaintedRelief tool.
#
# Author:       dm
# Version:      1.0
#
# Created:      26/10/2012
#
# Copyright:    (c) ESRI + dm 2012
# Licence:      public :)
#-------------------------------------------------------------------------------
# standard modules
import os
import sys
sys.path.append(os.path.dirname(__file__))
# pythonaddins
import pythonaddins
#-------------------------------------------------------------------------------
class TexturedPaintedReliefExt(object):
    """
    Implementation for TexturedPaintedRelief_addin.wxpyextension (Extension).
    """
    def __init__(self):
        self._wxApp = None
        self._enabled = None

    def startup(self):
        """
        On startup of ArcGIS, create the wxPython Simple app and start the
        mainloop.
        """
        try:
            from wx import PySimpleApp
            self._wxApp = PySimpleApp()
            self._wxApp.MainLoop()
        except Exception:
            pythonaddins.MessageBox("Error starting TexturedPaintedRelief "
                                    "extension.", "Extension Error", 0)

    @property
    def enabled(self):
        """
        Enable or disable the Textured Painted Relief Tool button when the
        extension is turned on or off.
        """
        if self._enabled == False:
            wxpybutton.enabled = False
        else:
            wxpybutton.enabled = True
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        """
        Set the enabled property of this extension when the extension is turned
        on or off in the Extension Dlalog of ArcMap.
        """
        self._enabled = value


class TexturedPaintedRelief(object):
    """
    Implementation for TexturedPaintedRelief_addin.wxpyextension (Button).
    """
    _dlg = None

    @property
    def dlg(self):
        """
        Return the Textured Painted Relief Tools dialog.
        """
        if self._dlg is None:
            from TexturedPaintedRelief_interface import TprtFrame
            self._dlg = TprtFrame()
        return self._dlg

    def __init__(self):
        """
        Initialize button and set it to enabled and unchecked by default.
        """
        self.enabled = True
        self.checked = False

    def onClick(self):
        """
        Show the TexturedPaintedRelief dialog.
        """
        try:
            self.dlg.Centre()
            self.dlg.Show()
            self.dlg.SetFocus()
        except Exception, e:
            pythonaddins.MessageBox("Can't show Textured Painted Relief Tool "
                                    "dialog.\nError: {0}.".format(e), "Error",0)
            pass