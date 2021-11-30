#--------------------------------------------------------------------------------------------------------------------

#This package contains view-related classes and functions for the menu bar

#------------------ Dependencies ----------------------------#

# Standard library imports
import sys

# External imports
from wx.lib.agw import ultimatelistctrl as ULC

# Internal imports
from .common import *

#------------------- Global Variables -----------------------#

#------------------ Classes & Functions ---------------------#

class ModificationsPanel(wx.Panel):

    def __init__(self, parent, curr_mod_list):
        wx.Panel.__init__(self, parent)

        ##Create all other widgets
        hbox                 = self.createListSizer(curr_mod_list)   # Modifications ListCtrl
        self.ok_cancel_panel = OkCancelPanel(self)                   # OK/Cancel buttons

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.ok_cancel_panel, flag=wx.ALIGN_RIGHT)
        self.SetSizer(vbox)

    def createListSizer(self, curr_mod_list):
        self.add_remove_panel = AddRemovePanel(self)        # Add/Remove buttons        
        self.add_remove_panel.add_btn.SetToolTip(wx.ToolTip("Click to add a modification."))

        self.modification_listbox = ModificationsListCtrl(self, curr_mod_list)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.modification_listbox, proportion=1, flag=wx.EXPAND)
        hbox.Add(self.add_remove_panel)
        return hbox

#########################################################################################################

class AddModificationPanel(FormPanel):

    def __init__(self, parent):
        FormPanel.__init__(self, parent)
     
        ##Create all other widgets
        fgrid                = self.createFormSizer()
        self.ok_cancel_panel = OkCancelPanel(self)      # OK/Cancel buttons
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(fgrid, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.ok_cancel_panel, flag=wx.ALIGN_RIGHT)
        self.SetSizer(vbox)

    def getFormData(self):
        return ("Modification", "Mass")
    
    def createFormSizer(self):
        fgrid = wx.FlexGridSizer(2, 5, 10)
        for i in range(0, len(self.getFormData())):
            label   = self.getFormData()[i]
            stTxt   = wx.StaticText(self, wx.ID_ANY, label)
            txtCtrl = wx.TextCtrl(self, wx.ID_ANY)
            fgrid.Add(stTxt, proportion=1)
            fgrid.Add(txtCtrl, proportion=2)
            self.txt_ctrl_list.append(txtCtrl)
        return fgrid

#########################################################################################################

class ModificationsListCtrl(MQListCtrl):

    TYPE_COLUMN_NAME = "Type"
    MASS_COLUMN_NAME = "Mass"
    
    def __init__(self, parent, curr_mod_list):
        MQListCtrl.__init__(self, parent)
        
        self.initList(curr_mod_list)

    def getColumnData(self):
        return ((self.TYPE_COLUMN_NAME, 1),
                (self.MASS_COLUMN_NAME, 1))

    def createColumns(self):
        for i in range(0, len(self.getColumnData())):
            (columnName, columnWidth) = self.getColumnData()[i]
            columnItem = self.createColumnItem(columnName, columnWidth)
            self.InsertColumnInfo(i, columnItem)
             
    def createColumnItem(self, columnName, columnWidth):
        columnItem = ULC.UltimateListItem()
        columnItem.SetText(columnName)
        columnItem.SetWidth(self.getWidth(columnWidth))
        return columnItem

    def initList(self, curr_mod_list):
        for mod_type, mod_mass in curr_mod_list:
            self.insertModification(mod_type, str(mod_mass))

    def insertModification(self, mod_type, mod_mass):
        row_idx = self.InsertStringItem(sys.maxsize, mod_type)
        self.SetStringItem(row_idx, self.getColumnIndex(self.MASS_COLUMN_NAME), mod_mass)

    def insertCheckbox(self):
        for row_idx in range(0, self.GetItemCount()):
            checkbox = wx.CheckBox(self)
            ## Automatically set these to True; Default values
            if (self.getModType(row_idx) == "Methyl" or
                self.getModType(row_idx) == "Dimethyl" or
                self.getModType(row_idx) == "Trimethyl"):
                checkbox.SetValue(True)
                
            self.SetItemWindow(row_idx, 0, checkbox, expand=True)

    def removeModification(self):
        prev_item_idx = wx.NOT_FOUND
        while True:
            #get the index of the next item in the listbox that is selected
            curr_item_idx = self.GetNextItem(prev_item_idx, state=ULC.ULC_STATE_SELECTED) 
            if curr_item_idx == wx.NOT_FOUND:
                break;

            #Get experiments that should not be in the listbox
            self.DeleteItem(curr_item_idx)

    def getModSet(self):
        mod_set = set()
        for row_idx in range(0, self.GetItemCount()):
            mod_type = self.getModType(row_idx)
            mod_mass = self.getMass(row_idx)
            mod_set.add((mod_type, mod_mass))
        return mod_set
 
    def getModType(self, row_idx):
        return self.GetItem(row_idx, self.getColumnIndex(self.TYPE_COLUMN_NAME)).GetText()
   
    def getMass(self, row_idx):
        return self.GetItem(row_idx, self.getColumnIndex(self.MASS_COLUMN_NAME)).GetText()

    def getCheckboxRows(self):
        mod_set = set()
        for row_idx in range(0, self.GetItemCount()):            
            item  = self.GetItem(row_idx, 0)
            value = bool(self.GetItemWindow(item).GetValue())   #Convert to unicode before returning
            if value:
                mod_type = self.getModType(row_idx)
                mod_mass = float(self.getMass(row_idx))
                mod_set.add((mod_type, mod_mass))

        return mod_set

#########################################################################################################

class LabelsPanel(wx.Panel):

    def __init__(self, parent, curr_label_list):
        wx.Panel.__init__(self, parent)

        ##Create all other widgets
        hbox                 = self.createListSizer(curr_label_list)    # Labels ListCtrl
        self.ok_cancel_panel = OkCancelPanel(self)                      # OK/Cancel buttons

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.ok_cancel_panel, flag=wx.ALIGN_RIGHT)
        self.SetSizer(vbox)

    def createListSizer(self, curr_label_list):
        self.add_remove_panel = AddRemovePanel(self)        # Add/Remove buttons        
        self.add_remove_panel.add_btn.SetToolTip(wx.ToolTip("Click to add a label."))

        self.label_listbox = LabelsListCtrl(self, curr_label_list)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.label_listbox, proportion=1, flag=wx.EXPAND)
        hbox.Add(self.add_remove_panel)
        return hbox

#########################################################################################################

class AddLabelsPanel(FormPanel):
    
    def __init__(self, parent):
        FormPanel.__init__(self, parent)        

        ##Create all other widgets
        fgrid                = self.createFormSizer()
        self.ok_cancel_panel = OkCancelPanel(self)        # OK/Cancel buttons
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(fgrid, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.ok_cancel_panel, flag=wx.ALIGN_RIGHT)
        self.SetSizer(vbox)
                
    def getFormData(self):
        return ("Label name", "Residue", "Mass")

    def createFormSizer(self):
        fgrid = wx.FlexGridSizer(2, 5, 10)
        for i in range(0, len(self.getFormData())):
            label   = self.getFormData()[i]
            stTxt   = wx.StaticText(self, wx.ID_ANY, label)
            txtCtrl = wx.TextCtrl(self, wx.ID_ANY)
            fgrid.Add(stTxt, proportion=1)
            fgrid.Add(txtCtrl, proportion=2)
            self.txt_ctrl_list.append(txtCtrl)
        return fgrid

#########################################################################################################

class LabelsListCtrl(MQListCtrl):

    LABEL_NAME_COLUMN_NAME = "Label name"
    RESIDUE_COLUMN_NAME    = "Residue"
    MASS_COLUMN_NAME       = "Mass"
    
    def __init__(self, parent, curr_label_list):
        MQListCtrl.__init__(self, parent)

        self.initList(curr_label_list)

    def getColumnData(self):
        return ((self.LABEL_NAME_COLUMN_NAME, 0.8),
                (self.RESIDUE_COLUMN_NAME, 0.8),
                (self.MASS_COLUMN_NAME, 1))

    def createColumns(self):
        for i in range(0, len(self.getColumnData())):
            (columnName, columnWidth) = self.getColumnData()[i]
            columnItem = self.createColumnItem(columnName, columnWidth)
            self.InsertColumnInfo(i, columnItem)
             
    def createColumnItem(self, columnName, columnWidth):
        columnItem = ULC.UltimateListItem()
        columnItem.SetText(columnName)
        columnItem.SetWidth(self.getWidth(columnWidth))
        return columnItem
    
    def initList(self, curr_label_list):
        for label_name, residue, mass in curr_label_list:
            self.insertLabel(label_name, residue, str(mass))

    def insertLabel(self, label_name, residue, mass):
        row_idx = self.InsertStringItem(sys.maxsize, label_name)
        self.SetStringItem(row_idx, self.getColumnIndex(self.RESIDUE_COLUMN_NAME), residue)
        self.SetStringItem(row_idx, self.getColumnIndex(self.MASS_COLUMN_NAME), mass)

    def insertCheckbox(self):
        for row_idx in range(0, self.GetItemCount()):
            checkbox = wx.CheckBox(self)
            if self.getLabelName(row_idx) == "13CD3":   ## Automatically set these to True; Default values
                checkbox.SetValue(True)
            self.SetItemWindow(row_idx, 0, checkbox, expand=True)
            
    def removeLabel(self):
        prev_item_idx = wx.NOT_FOUND
        while True:
            #get the index of the next item in the listbox that is selected
            curr_item_idx = self.GetNextItem(prev_item_idx, state=ULC.ULC_STATE_SELECTED) 
            if curr_item_idx == wx.NOT_FOUND:
                break;

            #Get experiments that should not be in the listbox
            self.DeleteItem(curr_item_idx)

    def getLabelSet(self):
        label_set = set()
        for row_idx in range(0, self.GetItemCount()):
            label_name = self.getLabelName(row_idx)
            residue    = self.getResidue(row_idx)
            mass       = self.getMass(row_idx)
            label_set.add((label_name, residue, mass))
                         
        return label_set
 
    def getLabelName(self, row_idx):
        return self.GetItem(row_idx, self.getColumnIndex(self.LABEL_NAME_COLUMN_NAME)).GetText()
   
    def getResidue(self, row_idx):
        return self.GetItem(row_idx, self.getColumnIndex(self.RESIDUE_COLUMN_NAME)).GetText()
 
    def getMass(self, row_idx):
        return self.GetItem(row_idx, self.getColumnIndex(self.MASS_COLUMN_NAME)).GetText()

    def getCheckboxRows(self):
        label_set = set()
        for row_idx in range(0, self.GetItemCount()):
            item  = self.GetItem(row_idx, 0)
            value = bool(self.GetItemWindow(item).GetValue())   #Convert to unicode before returning
            if value:
                residue = self.getResidue(row_idx)
                mass    = float(self.getMass(row_idx))
                label_set.add((residue, mass))  # We only need the residue and mass for labels
                
        return label_set
