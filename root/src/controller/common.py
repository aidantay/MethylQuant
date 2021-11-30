#--------------------------------------------------------------------------------------------------------------------

#This package contains controller-related classes and functions for the core UI

#------------------ Dependencies ----------------------------#

# Standard library imports
import base64
import io

# External imports
import wx

# Internal imports

#------------------- Global Variables -----------------------#

VERSION = 1.00

#------------------ Classes & Functions ---------------------#

def getVersion():
    return str('%.2f' % VERSION)

def getSize(size_tuple):
    x = wx.DisplaySize()[0] * size_tuple[0]
    y = wx.DisplaySize()[1] * size_tuple[1]
    return (x, y)

"""The MethylQuant icon
"""
def getIcon():
    base64_encoded_icon = \
    '''AAABAAEAEBAAAAEACABoBQAAFgAAACgAAAAQAAAAIAAAAAEACAAAAAAAQAUAAAAAAAAAAAAAAAEA
       AAABAAAAAAAAAABmAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAEBAQEBAQEBAAEBAAABAQAAAAEBAQEBAQABAQAAAQEAAQEBAQEAAAAA
       AQEAAAEBAAAAAQEBAAAAAAEBAAABAQAAAAEBAQAAAAABAQAAAQEAAQEBAQEAAAAAAQEBAQEBAAAA
       AAEBAAAAAAEBAQEBAQAAAAABAQAAAAABAQAAAQEAAAAAAQEAAAAAAQEAAAEBAAAAAAEBAAAAAAEB
       AAABAQAAAAABAQAAAAABAQAAAQEAAAAAAQEBAQEAAQEAAAEBAAAAAAEBAQEBAAEBAAABAQAAAAAA
       AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/4//8Ezv//BMj//zzO//88zv//PMj//zwP
       //88D///PM///zzP//88z///PM///wTP//8Ez/////////////8='''
    icon = base64.b64decode(base64_encoded_icon)

    #the icon (now embedded)
    myStream = io.BytesIO(icon)
    myStream.write(icon)
    myImage  = wx.Image(myStream)
    myBitmap = wx.Bitmap(myImage) 
    icon     = wx.Icon() 
    icon.CopyFromBitmap(myBitmap)
    return icon 

#########################################################################################################

def showInvalidExperimentDialog():
    invalid_experiment_dialog = wx.MessageDialog(None, "Experiment is invalid.\n\n" +
                                                 "Please check:\n" +
                                                 "* Peptides files are not empty\n" +
                                                 "* Directory containing .RAW files are not empty\n" +
                                                 "* Parameters are valid\n\n" +
                                                 "For more information, See Help.",
                                                 "Error", style=wx.ICON_ERROR)
    invalid_experiment_dialog.ShowModal()

#########################################################################################################

def showInvalidModificationDialog():
    invalid_modification_dialog = wx.MessageDialog(None, "Modification is invalid.\n\n" +
                                                   "Please check:\n" +
                                                   "* Modification type has not been added previously\n" +
                                                   "* Modification type is a text string\n" +
                                                   "* Mass is a number float\n\n" +
                                                   "For more information, See Help.",
                                                   "Error", style=wx.ICON_ERROR)
    invalid_modification_dialog.ShowModal()

#########################################################################################################

def showInvalidLabelDialog():
    invalid_label_dialog = wx.MessageDialog(None, "Label is invalid.\n\n" + 
                                            "Please check:\n" +
                                            "* Label has not been added previously\n" +
                                            "* Label name is a text string\n" +
                                            "* Mass is a number float\n\n" +
                                            "For more information, See Help.",
                                            "Error", style=wx.ICON_ERROR)
    invalid_label_dialog.ShowModal()

#########################################################################################################
    