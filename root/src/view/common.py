#--------------------------------------------------------------------------------------------------------------------

#This package contains controller-related classes and functions for the core UI

#------------------ Dependencies ----------------------------#

# Standard library imports

# External imports
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin 
from wx.lib.agw import ultimatelistctrl as ULC

# Internal imports

#------------------- Global Variables -----------------------#

#------------------ Classes & Functions ---------------------#

class OkCancelPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.ok_btn     = wx.Button(self, label="OK")
        self.cancel_btn = wx.Button(self, label="Cancel")

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.ok_btn, flag=wx.ALL, border=10)
        hbox.Add(self.cancel_btn, flag=wx.ALL, border=10)
        self.SetSizer(hbox)

#########################################################################################################

class AddRemovePanel(wx.Panel):

    REMOVE_BUTTON_TOOLTIP = "Highlight a row and click to remove"

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.add_btn = wx.Button(self, label="Add")        
        self.remove_btn = wx.Button(self, label="Remove")
        self.remove_btn.SetToolTip(wx.ToolTip(self.REMOVE_BUTTON_TOOLTIP))

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.add_btn, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(self.remove_btn, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        self.SetSizer(vbox)

#########################################################################################################

class MQListCtrl(ULC.UltimateListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent):
        ULC.UltimateListCtrl.__init__(self, parent, 
                                      agwStyle=ULC.ULC_REPORT | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT | 
                                               ULC.ULC_VRULES | ULC.ULC_HRULES)
        ListCtrlAutoWidthMixin.__init__(self)

        self.createColumns()
        self.SetBackgroundColour((255, 255, 255, 255))

    def getWidth(self, columnWidth):
        x = self.GetSize()[0] * columnWidth
        return x

    def getColumnIndex(self, columnName):
        column_idxs = range(0, self.GetColumnCount())
        f           = lambda x: (self.GetColumn(x).GetText() == columnName)
        columns     = list(filter(f, column_idxs))
        return columns[0]

    def createCheckboxColumn(self):
        columnItem = self.createColumnItem("", 0.25)
        self.InsertColumnInfo(0, columnItem)

#########################################################################################################

class FormPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.txt_ctrl_list = []             # Keep track of all the TextCtrls

    def getFormTuple(self):
        f = lambda x: str(x.GetValue())
        form_list = map(f, self.txt_ctrl_list)        
        return tuple(form_list)

#########################################################################################################

def showInvalidPeptidesFileDialog(peptides_file_path):
    invalid_file_dialog = wx.MessageDialog(None, peptides_file_path + " is invalid.\n\n" +
                                           "Please check:\n" + 
                                           "* File type is correct\n" + 
                                           "* File has not been added\n" +                                                   
                                           "* File contains headers as required\n\n" + 
                                           "For more information, See Help.",
                                           "Error", style=wx.ICON_ERROR)
    invalid_file_dialog.ShowModal()

#########################################################################################################

def showInvalidRawDirDialog(raw_dir_path):
    invalid_file_dialog = wx.MessageDialog(None, raw_dir_path + " is invalid.\n\n" + 
                                           "Please check:\n" +
                                           "* File type is directory\n" +                                                    
                                           "* Directory contains .RAW files\n" +                                                   
                                           "* Directory has not been added\n\n" +
                                           "For more information, See Help.",
                                           "Error", style=wx.ICON_ERROR)
    invalid_file_dialog.ShowModal()

#########################################################################################################
