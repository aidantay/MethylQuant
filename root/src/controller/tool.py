#--------------------------------------------------------------------------------------------------------------------

#This package contains controller-related classes and functions for the menu bar

#------------------ Dependencies ----------------------------#

# Standard library imports

# External imports

# Internal imports
from .. import view
from .. import model
from .common import *

#------------------- Global Variables -----------------------#

MODIFICATION_TABLE_DIALOG_TITLE    = "Modification Table"
MODIFICATION_TABLE_DIALOG_SIZE     = (0.2, 0.2)
ADD_MODIFICATION_DIALOG_TITLE      = "Add Modification"
ADD_MODIFICATION_DIALOG_SIZE       = (0.115, 0.13)
REMOVE_MODIFICATION_DIALOG_TITLE   = "Remove Modification"
REMOVE_MODIFICATION_DIALOG_MESSAGE = "Are you sure you want to remove this modification?"
LABEL_TABLE_DIALOG_TITLE           = "Label Table"
LABEL_TABLE_DIALOG_SIZE            = (0.2, 0.2)
ADD_LABEL_DIALOG_TITLE             = "Add Label"
ADD_LABEL_DIALOG_SIZE              = (0.11, 0.15)
REMOVE_LABEL_DIALOG_TITLE          = "Remove Label"
REMOVE_LABEL_DIALOG_MESSAGE        = "Are you sure you want to remove this label?"

#------------------ Classes & Functions ---------------------#

class ModificationsDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, 
                           title=MODIFICATION_TABLE_DIALOG_TITLE)

        (x, y) = getSize(MODIFICATION_TABLE_DIALOG_SIZE)
        self.SetSize(x, y)
        self.Centre()       #Center the UI        
        self.initUI()

    def initUI(self):
        self.curr_mod_list      = model.ModificationList()
        self.modification_panel = view.ModificationsPanel(self, self.curr_mod_list)
        self.Bind(wx.EVT_BUTTON, self.OnAdd, self.modification_panel.add_remove_panel.add_btn)
        self.Bind(wx.EVT_BUTTON, self.OnRemove, self.modification_panel.add_remove_panel.remove_btn)
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.modification_panel.ok_cancel_panel.ok_btn)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.modification_panel.ok_cancel_panel.cancel_btn)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnEsc)        

    def OnAdd(self, event):
        curr_mod_set            = self.modification_panel.modification_listbox.getModSet()        
        add_modification_dialog = AddModificationDialog(self, curr_mod_set)
        if add_modification_dialog.ShowModal() == wx.ID_OK:
            (mod_type, mod_mass) = add_modification_dialog.add_modification_panel.getFormTuple()
            self.modification_panel.modification_listbox.insertModification(mod_type, mod_mass)

    def OnRemove(self, event):
        remove_modification_dialog = wx.MessageDialog(None, REMOVE_MODIFICATION_DIALOG_MESSAGE,
                                                      caption=REMOVE_MODIFICATION_DIALOG_TITLE,
                                                      style=wx.YES_NO)

        if remove_modification_dialog.ShowModal() == wx.ID_YES:
            self.modification_panel.modification_listbox.removeModification()

    def OnOk(self, event):
        self.updateModList()
        self.EndModal(wx.ID_OK)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def OnEsc(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnCancel(event)
        event.Skip()

    def updateModList(self):
        self.curr_mod_list.clear()
        for mod_type, mass in self.modification_panel.modification_listbox.getModSet():
            self.curr_mod_list.addModification(mod_type, mass)

#########################################################################################################

class AddModificationDialog(wx.Dialog):

    def __init__(self, parent, curr_mod_set):
        wx.Dialog.__init__(self, parent, 
                           title=ADD_MODIFICATION_DIALOG_TITLE)

        self.curr_mod_set = curr_mod_set
        (x, y) = getSize(ADD_MODIFICATION_DIALOG_SIZE)
        self.SetSize(x, y)
        self.Centre()       #Center the UI
        self.initUI()

    def initUI(self):
        self.add_modification_panel = view.AddModificationPanel(self)
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.add_modification_panel.ok_cancel_panel.ok_btn)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.add_modification_panel.ok_cancel_panel.cancel_btn)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnEsc)

    def OnOk(self, event):
        if self.isValidModification():
            self.EndModal(wx.ID_OK)

        else:
            showInvalidModificationDialog()

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def OnEsc(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnCancel(event)
        event.Skip()
        
    def isValidModification(self):
        (mod_type, mod_mass) = self.add_modification_panel.getFormTuple()
        if (not self.isValidFormat(mod_type, mod_mass) or self.inCurrList(mod_type, mod_mass)):
            return False
        return True

    def isValidFormat(self, mod_type, mod_mass):
        try:
            #Check that it the inputs are valid
            str(mod_type)
            float(mod_mass)

        except ValueError:
            return False
        
        return True

    def inCurrList(self, mod_type, mod_mass):
        if (mod_type, mod_mass) not in self.curr_mod_set:
            return False
        return True

#########################################################################################################

class LabelsDialog(wx.Dialog):
     
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, 
                           title=LABEL_TABLE_DIALOG_TITLE)

        (x, y) = getSize(LABEL_TABLE_DIALOG_SIZE)
        self.SetSize(x, y)
        self.Centre()       #Center the UI
        self.initUI()

    def initUI(self):
        self.curr_label_list = model.LabelList()
        self.label_panel     = view.LabelsPanel(self, self.curr_label_list)
        self.Bind(wx.EVT_BUTTON, self.OnAdd, self.label_panel.add_remove_panel.add_btn)
        self.Bind(wx.EVT_BUTTON, self.OnRemove, self.label_panel.add_remove_panel.remove_btn)
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.label_panel.ok_cancel_panel.ok_btn)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.label_panel.ok_cancel_panel.cancel_btn)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnEsc)

    def OnAdd(self, event):
        curr_label_set   = self.label_panel.label_listbox.getLabelSet()        
        add_label_dialog = AddLabelDialog(self, curr_label_set)
        if add_label_dialog.ShowModal() == wx.ID_OK:
            (label_name, residue, mass) = add_label_dialog.add_label_panel.getFormTuple()
            self.label_panel.label_listbox.insertLabel(label_name, residue, mass)

    def OnRemove(self, event):
        remove_label_dialog = wx.MessageDialog(None, REMOVE_LABEL_DIALOG_MESSAGE,
                                               caption=REMOVE_LABEL_DIALOG_TITLE,
                                               style=wx.YES_NO)
        
        if remove_label_dialog.ShowModal() == wx.ID_YES:
            self.label_panel.label_listbox.removeLabel()
      
    def OnOk(self, event):
        self.updateLabelList()
        self.EndModal(wx.ID_OK)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnEsc(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnCancel(event)
        event.Skip()

    def updateLabelList(self):
        self.curr_label_list.clear()
        for label_name, residue, mass in self.label_panel.label_listbox.getLabelSet():
            self.curr_label_list.addLabel(label_name, residue, mass)

#########################################################################################################

class AddLabelDialog(wx.Dialog):

    def __init__(self, parent, curr_label_set):
        wx.Dialog.__init__(self, parent, 
                           title=ADD_LABEL_DIALOG_TITLE)

        self.curr_label_set  = curr_label_set
        (x, y) = getSize(ADD_LABEL_DIALOG_SIZE)
        self.SetSize(x, y)
        self.Centre()       #Center the UI
        self.initUI()

    def initUI(self):
        self.add_label_panel = view.AddLabelsPanel(self)
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.add_label_panel.ok_cancel_panel.ok_btn)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.add_label_panel.ok_cancel_panel.cancel_btn)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnEsc)

    def OnOk(self, event):
        if self.isValidLabel():
            self.EndModal(wx.ID_OK)

        else:
            showInvalidLabelDialog()

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnEsc(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnCancel(event)
        event.Skip()
        
    def isValidLabel(self):
        (label_name, residue, mass) = self.add_label_panel.getFormTuple()
        if (not self.isValidFormat(label_name, residue, mass) or 
            self.inCurrList(label_name, residue, mass) or 
            not residue.isalpha() or len(residue) != 1):
            return False
        return True

    def isValidFormat(self, label_name, residue, mass):
        try:
            #Check that it the inputs are valid
            str(label_name)
            str(residue)
            float(mass)

        except ValueError:
            return False

        return True

    def inCurrList(self, label_name, residue, mass):
        if (label_name, residue, mass) not in self.curr_label_set:
            return False
        return True

#########################################################################################################

