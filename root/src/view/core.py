#--------------------------------------------------------------------------------------------------------------------

#This package contains view-related classes and functions for the core UI

#------------------ Dependencies ----------------------------#

# Standard library imports
import os
import glob
import sys
import itertools

# External imports
from pubsub import pub
from wx.lib.agw import flatnotebook as FNB
from wx.lib.agw import ultimatelistctrl as ULC
from wx import Yield

# Internal imports
from .. import task
from ..io.reader import PeptidesReader
from .tool import LabelsListCtrl
from .tool import ModificationsListCtrl
from .common import *
from .constants import *

#------------------- Global Variables -----------------------#

#------------------ Classes & Functions ---------------------#

class MethylQuantPanel(wx.Panel):
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        ##Create all other widgets
        self.experiment_summary_list     = ExperimentSummaryListCtrl(self)      # List of experiments
        # self.experiment_summary_notebook = ExperimentSummaryNotebook(self)      # Details of experiments
        self.start_btn                   = wx.Button(self, label="Find pairs")  # Start button that starts the program!
        self.progress_gauge              = ProgressGauge(self)                  # Progress gauge
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(wx.StaticLine(self), flag=wx.EXPAND)           #Divider to partition the toolbar and the rest of the panel
        vbox.Add(self.experiment_summary_list, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        #vbox.Add(self.experiment_summary_notebook, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.start_btn, flag=wx.ALIGN_CENTER | wx.ALL, border=10)
        vbox.Add(self.progress_gauge, flag=wx.EXPAND)
        self.SetSizer(vbox)

#########################################################################################################

class ExperimentSummaryListCtrl(MQListCtrl):

    NUM_COLUMN_NAME    = "#"
    NAME_COLUMN_NAME   = "Name"
    DESC_COLUMN_NAME   = "Description"    
    STATUS_COLUMN_NAME = "Status"

    def __init__(self, parent):
        MQListCtrl.__init__(self, parent)  
        self.createImageList()
        
    def getColumnData(self):
        return ((self.NUM_COLUMN_NAME, 0.25),
                (self.NAME_COLUMN_NAME, 1.5),
                (self.DESC_COLUMN_NAME, 1.5),
                (self.STATUS_COLUMN_NAME, 1))

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

    def getImageData(self):
        return (wx.ART_TICK_MARK, wx.ART_CROSS_MARK)

    def createImageList(self):
        self.imageList = wx.ImageList(24, 24)
        for imageArt in self.getImageData():
            icon = wx.ArtProvider.GetBitmap(imageArt, client=wx.ART_TOOLBAR) 
            self.imageList.Add(icon)
        self.SetImageList(self.imageList, wx.IMAGE_LIST_SMALL)

    def insertExperiment(self, experiment):
        experiment_num = self.GetItemCount() + 1    ## Start at 1
        row_idx = self.InsertStringItem(sys.maxsize, str(experiment_num))
        self.SetStringItem(row_idx, self.getColumnIndex(self.NAME_COLUMN_NAME), experiment.getExperimentName())
        self.SetStringItem(row_idx, self.getColumnIndex(self.DESC_COLUMN_NAME), experiment.getExperimentDescription())

    def removeExperiment(self):
        prev_item_idx = wx.NOT_FOUND
        while True:
            #get the index of the next item in the listbox that is selected
            curr_item_idx = self.GetNextItem(prev_item_idx, state=ULC.ULC_STATE_SELECTED) 
            if curr_item_idx == wx.NOT_FOUND:
                break;

            #Get experiments that should not be in the listbox
            self.DeleteItem(curr_item_idx)
            pub.sendMessage(mq.UPDATE_EXPERIMENT_LIST_LISTENER, idx=curr_item_idx)

    def updateExperimentIds(self):
        for row_idx in range(0, self.GetItemCount()):
            self.SetStringItem(row_idx, self.getColumnIndex(self.NUM_COLUMN_NAME), str(row_idx + 1))

    def updateExperimentStatus(self, row_idx, experiment_status):
        self.SetStringItem(row_idx, self.getColumnIndex(self.STATUS_COLUMN_NAME), "", imageIds=experiment_status)

#########################################################################################################

# class ExperimentSummaryNotebook(FNB.FlatNotebook):
    
#     def __init__(self, parent):
#         FNB.FlatNotebook.__init__(self, parent, 
#                                   agwStyle=FNB.FNB_NO_NAV_BUTTONS | 
#                                            FNB.FNB_NO_X_BUTTON | FNB.FNB_NODRAG)

#         print("TODO - Experiment Summary Notebook")
#         self.peptides_panel   = PeptidesPanel(self)
#         self.raw_panel        = RawPanel(self)
#         self.parameters_panel = ParametersPanel(self)        
#         self.createTabs()

#     def getTabData(self):
#         return (("Peptides Files", self.peptides_panel),
#                 ("Raw Files", self.raw_panel),
#                 ("Parameters", self.parameters_panel))

#     def createTabs(self):
#         for tabName, tabPanel in self.getTabData():
#             self.AddPage(tabPanel, tabName)

#########################################################################################################

class ProgressGauge(wx.Gauge):
    
    MAX_GAUGE_VALUE = 1000000

    def __init__(self, parent):
        wx.Gauge.__init__(self, parent, wx.ID_ANY, self.MAX_GAUGE_VALUE, style=wx.GA_SMOOTH)
        pub.subscribe(self.UpdateStepsize, task.UPDATE_GAUGE_STEPSIZE_LISTENER)
        pub.subscribe(self.UpdateGauge, task.UPDATE_GAUGE_LISTENER)
        pub.subscribe(self.OnIncrement, task.INCREMENT_GAUGE_LISTENER)

    def getStepsize(self):
        return self.stepsize

    def UpdateGauge(self, filled):
        if filled:
            self.SetValue(self.MAX_GAUGE_VALUE)
        else:
            self.SetValue(0)
    
    def UpdateStepsize(self, seq_peptides_reader):
        self.stepsize = self.MAX_GAUGE_VALUE / len(seq_peptides_reader.seq_peptides)

    def OnIncrement(self):
        progress = self.GetValue() + self.getStepsize()
        self.SetValue(progress)  
        Yield()

#########################################################################################################

class AddExperimentPanel(wx.Panel):
    
    def __init__(self, parent, curr_label_list, curr_mod_list):
        wx.Panel.__init__(self, parent)

        ##Create all other widgets
        self.add_experiment_notebook = ExperimentNotebook(self, curr_label_list, curr_mod_list)     # Experiment notebook
        self.ok_cancel_panel         = OkCancelPanel(self)          # OK/Cancel buttons

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.add_experiment_notebook, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.ok_cancel_panel, flag=wx.ALIGN_RIGHT)
        self.SetSizer(vbox)

#########################################################################################################

class ExperimentNotebook(FNB.FlatNotebook):

    def __init__(self, parent, curr_label_list, curr_mod_list):
        FNB.FlatNotebook.__init__(self, parent, 
                                  agwStyle=FNB.FNB_NO_NAV_BUTTONS | 
                                           FNB.FNB_NO_X_BUTTON | FNB.FNB_NODRAG)

        self.experiment_info_panel = ExperimentInfoPanel(self)
        self.peptides_panel        = PeptidesPanel(self)
        self.raw_panel             = RawPanel(self)
        self.parameters_panel      = ParametersPanel(self)
        self.mass_panel            = MassPanel(self, curr_label_list, curr_mod_list)
        self.createTabs()

    def getTabData(self):
        return (("Experiment Info", self.experiment_info_panel),
                ("Peptides Files", self.peptides_panel),
                ("Raw Files", self.raw_panel),
                ("Parameters", self.parameters_panel),
                ("Mass Shifts", self.mass_panel))

    def createTabs(self):
        for tabName, tabPanel in self.getTabData():
            self.AddPage(tabPanel, tabName)

    def getInfoTuple(self):
        return self.experiment_info_panel.getInfoTuple()

    def getPeptidesFileMap(self):
        return self.peptides_panel.peptides_file_map

    def getLabelSet(self):
        return self.mass_panel.labels_listbox.getCheckboxRows()

    def getModSet(self):
        return self.mass_panel.modifications_listbox.getCheckboxRows()

    def getOutputMap(self):
        return self.peptides_panel.top_peptides_listbox.getOutputStyleMap()

    def getSilacMap(self):
        return self.peptides_panel.top_peptides_listbox.getSilacMap()

    def getRawDirMap(self):
        return self.raw_panel.raw_dir_map

    def getParameterTuple(self):
        return self.parameters_panel.getFormTuple()

#########################################################################################################

class ExperimentInfoPanel(wx.Panel):
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.txt_ctrl_list = []             # Keep track of all the TextCtrls

        ##Create all other widgets
        fgrid = self.createFormSizer()
        fgrid.AddGrowableCol(0, 1)
        fgrid.AddGrowableCol(1, 1)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(fgrid, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(vbox)

    def getFormData(self):
        return (("Experiment name (Optional)", "My Experiment"),
                ("Description (Optional)", "Methyl-SILAC"))

    def createFormSizer(self):
        fgrid = wx.FlexGridSizer(2, 5, 10)
        for label, initValue in self.getFormData():
            stTxt   = wx.StaticText(self, wx.ID_ANY, label)
            txtCtrl = wx.TextCtrl(self, wx.ID_ANY)
            txtCtrl.SetValue(str(initValue))
            fgrid.Add(stTxt, proportion=1)
            fgrid.Add(txtCtrl, proportion=1, flag=wx.EXPAND)
            self.txt_ctrl_list.append(txtCtrl)

        return fgrid

    def getInfoTuple(self):


        f = lambda x: str(x.GetValue())
        info_list = map(f, self.txt_ctrl_list)
        return tuple(info_list)

#########################################################################################################

class PeptidesPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Keep track of all the raw files from each CSV file
        self.peptides_file_map = {}  # Table containing CSV file paths -> {Raw file names}        

        ##Create all other widgets
        self.add_remove_panel = AddRemovePanel(self)      # Add/Remove buttons
        self.Bind(wx.EVT_BUTTON, self.OnAdd, self.add_remove_panel.add_btn)
        self.Bind(wx.EVT_BUTTON, self.OnRemove, self.add_remove_panel.remove_btn)
        vbox = self.createListSizer()                           # CSV file ListCtrl

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(vbox, proportion=1, flag=wx.EXPAND)
        hbox.Add(self.add_remove_panel)
        self.SetSizer(hbox)

    def createListSizer(self):
        self.top_peptides_listbox = PeptidesFilesListCtrl(self)
        self.top_peptides_listbox.SetDropTarget(PeptidesFilesDropTarget(self)) #Allow for the user to draw and drop files into the listbox
        
        stTxt_required_raws = wx.StaticText(self, label="Required .raw files:")
        self.bottom_peptides_listbox = RawFilesListCtrl(self)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.top_peptides_listbox, proportion=1, flag=wx.EXPAND | wx.TOP, border=10)
        vbox.Add(stTxt_required_raws, flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(self.bottom_peptides_listbox, proportion=1, flag=wx.EXPAND)
        return vbox

    def OnAdd(self, event):
        openFileDialog = wx.FileDialog(self, message="Import CSV file", 
                                       wildcard="CSV (*.csv)|*.csv|mzIdentML (*.mzid)|*.mzid", 
                                       style=wx.FD_DEFAULT_STYLE | wx.FD_FILE_MUST_EXIST | 
                                             wx.FD_MULTIPLE)

        if (openFileDialog.ShowModal() == wx.ID_OK):
            [self.addFile(f) for f in openFileDialog.GetPaths()]

    def addFile(self, peptides_file_path):
        try:
            #convert from unicode
            #if we can't then raise an error (See UnicodeDecodeError)
            peptides_file_path = str(peptides_file_path)

            #if the file has already been input by the user, 
            #then don't process it again and raise an error
            if peptides_file_path in self.top_peptides_listbox.getPeptidesFiles():
                raise ValueError

            #get set of RAW files that are in the file
            #check that have a header line with the 'Data File' column
            #if we don't, then raise an error (See KeyError)
            peptides_reader  = PeptidesReader(peptides_file_path)
            raw_files_in_csv = peptides_reader.getDataFiles()

            #insert row for CSV file
            self.top_peptides_listbox.insertPeptidesFile(peptides_file_path)
            self.addRawFiles(raw_files_in_csv)

            #update the model with files all the new files we've got
            #convert peptides_file_path to string to ensure we're not adding unicode string
            self.peptides_file_map[peptides_file_path] = raw_files_in_csv

        except (UnicodeDecodeError, KeyError, ValueError, IOError):
            showInvalidPeptidesFileDialog(peptides_file_path)

    def addRawFiles(self, raw_files_in_csv):
        #get set of RAW files that are already in the model                
        raw_files_in_all_csv = self.bottom_peptides_listbox.getRawFiles()
        
        #get RAW files that are not in the model and insert row/s for them
        for raw_file in raw_files_in_csv.difference(raw_files_in_all_csv):
            self.bottom_peptides_listbox.Append([raw_file])        

    """ Removes CSV files from the ListBox when the 'Remove' button is pressed 
    """
    def OnRemove(self, event):
        prev_item_idx = wx.NOT_FOUND
        while True:
            #get the index of the next item in the listbox that is selected
            curr_item_idx = self.top_peptides_listbox.GetNextItem(prev_item_idx,
                                                                  state=ULC.ULC_STATE_SELECTED) 
            if curr_item_idx == wx.NOT_FOUND:
                break;

            #get set of RAW files that are in the file. These SHOULD NOT be in the listbox
            #Get RAW files that should not be in the listbox
            peptides_file_path = self.top_peptides_listbox.getFileName(curr_item_idx)
            raw_files_in_csv = self.peptides_file_map[peptides_file_path]     

            self.top_peptides_listbox.DeleteItem(curr_item_idx)
            self.bottom_peptides_listbox.removeRawFiles(self.peptides_file_map, peptides_file_path, raw_files_in_csv)

#########################################################################################################

class PeptidesFilesListCtrl(MQListCtrl):

    FILE_PATH_COLUMN_NAME    = "File path"
    SILAC_TYPE_COLUMN_NAME   = "Light or Heavy?"
    OUTPUT_STYLE_COLUMN_NAME = "Summary or Full?"

    LIGHT_SILAC   = "Light"
    HEAVY_SILAC   = "Heavy"
    SUMMARY_STYLE = "Summary" 
    FULL_STYLE    = "Full"
    
    def __init__(self, parent):
        MQListCtrl.__init__(self, parent)               

    def getColumnData(self):
        return ((self.FILE_PATH_COLUMN_NAME, 1.5),
                (self.SILAC_TYPE_COLUMN_NAME, 1),
                (self.OUTPUT_STYLE_COLUMN_NAME, 0.1))

    def createColumns(self):
        for i in range(0, len(self.getColumnData())):
            (columnName, columnWidth) = self.getColumnData()[i]
            columnItem = self.createColumnItem(columnName, columnWidth)
            self.InsertColumnInfo(i, columnItem)

    def createColumnItem(self, columnName, columnWidth):
        columnItem = ULC.UltimateListItem()
        columnItem.SetText(columnName)
        columnItem.SetToolTip("Drag and drop a .csv or .mzid file containing sequenced peptides results")
        columnItem.SetWidth(self.getWidth(columnWidth))
        return columnItem

    def insertPeptidesFile(self, peptides_file_path):
        row_idx = self.InsertStringItem(sys.maxsize, "")
        self.SetStringItem(row_idx, self.getColumnIndex(self.FILE_PATH_COLUMN_NAME), peptides_file_path)

        silac_choice = wx.ComboBox(self, value=self.LIGHT_SILAC, 
                                   choices=[self.LIGHT_SILAC, self.HEAVY_SILAC], 
                                   style=wx.CB_READONLY)
        self.SetItemWindow(row_idx, self.getColumnIndex(self.SILAC_TYPE_COLUMN_NAME), 
                           silac_choice, expand=True)

        output_choice = wx.ComboBox(self, value=self.SUMMARY_STYLE, 
                                   choices=[self.SUMMARY_STYLE, self.FULL_STYLE], 
                                   style=wx.CB_READONLY)
        self.SetItemWindow(row_idx, self.getColumnIndex(self.OUTPUT_STYLE_COLUMN_NAME), 
                           output_choice, expand=True)

    def getPeptidesFiles(self):
        peptides_file_set = set()
        #Get labels for each row in the list
        for row_idx in range(0, self.GetItemCount()):
            peptides_file_path = self.getFileName(row_idx)
            peptides_file_set.add(peptides_file_path)
   
        return peptides_file_set
 
    def getFileName(self, row_idx):
        return self.GetItem(row_idx, self.getColumnIndex(self.FILE_PATH_COLUMN_NAME)).GetText()

    def getSilacType(self, row_idx):
        item  = self.GetItem(row_idx, self.getColumnIndex(self.SILAC_TYPE_COLUMN_NAME))
        value = str(self.GetItemWindow(item).GetStringSelection())   #Convert to unicode before returning
 
        #check if we have sequenced light or heavy peptide, and therefore what mass shift to expect    
        #we have sequenced heavy so expected mass shift will be negative 
        if value == self.HEAVY_SILAC:
            return ID_HEAVY
        return ID_LIGHT
 
    def getOutputStyle(self, row_idx):
        item  = self.GetItem(row_idx, self.getColumnIndex(self.OUTPUT_STYLE_COLUMN_NAME))
        value = str(self.GetItemWindow(item).GetStringSelection())   #Convert to unicode before returning
        
        if (value == self.FULL_STYLE):
            return ID_FULL
        return ID_SUMMARY
 
    def getSilacMap(self):
        silac_types = {} # Table containing CSV filenames -> {Silac type}
   
        #Get silac type for each row in the list
        for row_idx in range(0, self.GetItemCount()):
            #get the labelling status and the file path of the CSV file
            silac_type         = self.getSilacType(row_idx)
            peptides_file_path = self.getFileName(row_idx)
            silac_types[str(peptides_file_path)] = silac_type
   
        return silac_types
 
    def getOutputStyleMap(self):
        output_styles = {} # Table containing CSV filenames -> {Output style}
   
        #Get output style for each row in the list
        for row_idx in range(0, self.GetItemCount()):
            #get the labelling status and the file path of the CSV file
            output_style       = self.getOutputStyle(row_idx)
            peptides_file_path = self.getFileName(row_idx)
            output_styles[str(peptides_file_path)] = output_style
   
        return output_styles

#########################################################################################################

class PeptidesFilesDropTarget(wx.FileDropTarget):
  
    def __init__(self, parent):
        wx.FileDropTarget.__init__(self)
        self.parent = parent
        
    def OnDropFiles(self, x, y, filenames):
        [self.parent.addFile(f) for f in filenames]
        return True

#########################################################################################################

class RawPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Keep track of all the raw files from each directory
        self.raw_dir_map = {}  # Table containing Raw dir paths  -> {Raw file names}

        ##Create all other widgets
        self.add_remove_panel = AddRemovePanel(self)      # Add/Remove buttons
        self.Bind(wx.EVT_BUTTON, self.OnAdd, self.add_remove_panel.add_btn)
        self.Bind(wx.EVT_BUTTON, self.OnRemove, self.add_remove_panel.remove_btn)
        vbox = self.createListSizer()                           # CSV file ListCtrl

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(vbox, proportion=1, flag=wx.EXPAND)
        hbox.Add(self.add_remove_panel, flag=wx.EXPAND)
        self.SetSizer(hbox)

    def createListSizer(self):
        self.top_raw_listbox = RawDirsListCtrl(self)
        self.top_raw_listbox.SetDropTarget(RawDirsDropTarget(self))     #Allow for the user to draw and drop files into the listbox        

        stTxt_found_raw_files = wx.StaticText(self, label="Found .raw files:")
        self.bottom_raw_listbox = RawFilesListCtrl(self)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.top_raw_listbox, proportion=1, flag=wx.EXPAND | wx.TOP, border=10)
        vbox.Add(stTxt_found_raw_files, flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(self.bottom_raw_listbox, proportion=1, flag=wx.EXPAND)
        return vbox

    def OnAdd(self, event):
        openDirDialog = wx.DirDialog(self, message="Import directory", 
                                     style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        
        if openDirDialog.ShowModal() == wx.ID_OK:
            self.addDir(openDirDialog.GetPath())

    def addDir(self, raw_dir_path):
        try:
            #convert from unicode
            #if we can't then raise an error (See UnicodeDecodeError)
            raw_dir_path = str(raw_dir_path)

            #convert from unicode
            #if the file is not a directory, then raise an error (See IOError)
            if (not os.path.isdir(raw_dir_path)):
                raise IOError

            #if the dir has already been input by the user, or the dir 
            #contains no raw files, then don't process it again and raise an error
            raw_files_in_dir = glob.glob(raw_dir_path + "/*.raw")  
            if ((raw_dir_path in self.top_raw_listbox.getRawDirs())
                or (len(raw_files_in_dir) <= 0)):
                raise ValueError

            #get set of RAW files that are in the dir
            raw_files_in_dir = glob.glob(raw_dir_path + "/*.raw")
            f = lambda x: str(os.path.basename(x))
            raw_files_in_dir = set(map(f, raw_files_in_dir))

            self.top_raw_listbox.insertRawDir(raw_dir_path)
            self.addRawFiles(raw_files_in_dir)
            
            #update the model with files all the new files we've got
            #convert peptides_file_path to string to ensure its we're not adding unicode string
            self.raw_dir_map[raw_dir_path] = raw_files_in_dir

        except (UnicodeDecodeError, IOError, ValueError):
            showInvalidRawDirDialog(raw_dir_path)

    def addRawFiles(self, raw_files_in_dir):
        #get set of RAW files that are already in the model                
        raw_files_in_all_dir = self.bottom_raw_listbox.getRawFiles()
        
        #get RAW files that are not in the model and insert row/s for them
        for raw_file in raw_files_in_dir.difference(raw_files_in_all_dir):
            self.bottom_raw_listbox.Append([raw_file])        

    """ Removes RAW files from the ListBox when the 'Remove' button is pressed 
    """
    def OnRemove(self, event):
        prev_item_idx = wx.NOT_FOUND
        while True:
            #get the index of the next item in the listbox that is selected
            curr_item_idx = self.top_raw_listbox.GetNextItem(prev_item_idx,
                                                             state=ULC.ULC_STATE_SELECTED) 
            if curr_item_idx == wx.NOT_FOUND:
                break;
 
            #get set of RAW files that are in the directory. These SHOULD NOT be in the listbox
            raw_dir_path     = self.top_raw_listbox.getDirName(curr_item_idx)
            raw_files_in_dir = self.raw_dir_map[raw_dir_path]     
  
            self.top_raw_listbox.DeleteItem(curr_item_idx)
            self.bottom_raw_listbox.removeRawFiles(self.raw_dir_map, raw_dir_path, raw_files_in_dir)

#########################################################################################################

class RawDirsListCtrl(MQListCtrl):

    FILE_PATH_COLUMN_NAME  = "File path"

    def __init__(self, parent):
        MQListCtrl.__init__(self, parent)

    def getColumnData(self):
        return (self.FILE_PATH_COLUMN_NAME,)

    def createColumns(self):
        for i in range(0, len(self.getColumnData())):
            columnName = self.getColumnData()[i]
            columnItem = self.createColumnItem(columnName)
            self.InsertColumnInfo(i, columnItem)
             
    def createColumnItem(self, columnName):
        columnItem = ULC.UltimateListItem()
        columnItem.SetText(columnName)
        columnItem.SetToolTip("Drag and drop a directory containing .raw files here")
        columnItem.SetWidth(wx.LIST_AUTOSIZE_USEHEADER)
        return columnItem

    def insertRawDir(self, raw_file_path):
        row_idx = self.InsertStringItem(sys.maxsize, "")
        self.SetStringItem(row_idx, self.getColumnIndex(self.FILE_PATH_COLUMN_NAME), raw_file_path)
 
    def getRawDirs(self):
        raw_dir_set = set()
        #Get labels for each row in the list
        for row_idx in range(0, self.GetItemCount()):
            raw_dir_path = self.GetItem(row_idx).GetText()
            raw_dir_set.add(raw_dir_path)
   
        return raw_dir_set

    def getDirName(self, row_idx):
        return self.GetItem(row_idx, self.getColumnIndex(self.FILE_PATH_COLUMN_NAME)).GetText()

#########################################################################################################

class RawDirsDropTarget(wx.FileDropTarget):
       
    def __init__(self, parent):
        wx.FileDropTarget.__init__(self)
        self.parent = parent
            
    def OnDropFiles(self, x, y, filenames):
        [self.parent.addDir(f) for f in filenames]
        return True

#########################################################################################################

class RawFilesListCtrl(MQListCtrl):

    def __init__(self, parent):
        MQListCtrl.__init__(self, parent)

    def getColumnData(self):
        return (("Raw files", wx.LIST_AUTOSIZE_USEHEADER),)

    def createColumns(self):
        for i in range(0, len(self.getColumnData())):
            (columnName, columnWidth) = self.getColumnData()[i]
            columnItem = self.createColumnItem(columnName, columnWidth)
            self.InsertColumnInfo(i, columnItem)
             
    def createColumnItem(self, columnName, columnWidth):
        columnItem = ULC.UltimateListItem()
        columnItem.SetText(columnName)
        columnItem.SetWidth(columnWidth)
        columnItem.SetToolTip("Displays .raw files that MethylQuant knows")
        return columnItem

    def getRawFiles(self):
        raw_file_set = set()
        #Get labels for each row in the list
        for row_idx in range(0, self.GetItemCount()):
            raw_file_path = self.getFileName(row_idx)
            raw_file_set.add(raw_file_path)
   
        return raw_file_set

    def getFileName(self, row_idx):
        return self.GetItem(row_idx, 0).GetText()

    def removeRawFiles(self, file_or_dir_map, file_or_dir_path, raw_files_in_file_or_dir):
        #remove CSV files from the model
        del(file_or_dir_map[file_or_dir_path])        

        #get set of RAW files that should be in the listbox
        raw_files_in_all_file_or_dir = set(itertools.chain.from_iterable(file_or_dir_map.values()))

        #remove row/s of RAW files that should not be in the listbox
        for raw_file in raw_files_in_file_or_dir.difference(raw_files_in_all_file_or_dir):
            item_idx = self.FindItem(0, raw_file)
            self.DeleteItem(item_idx)

#########################################################################################################

class ParametersPanel(FormPanel):
    
    def __init__(self, parent):
        FormPanel.__init__(self, parent)

        ##Create all other widgets
        fgrid = self.createFormSizer()
        fgrid.AddGrowableCol(0, 1)
        fgrid.AddGrowableCol(1, 1)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(fgrid, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(vbox)

    def getFormData(self):
        return (("Mass error (ppm)", 10, "Error tolerance when trying to find mass signals in .raw file\nthat correspond to theoretical masses of light and heavy peptides"),
                ("Pair overlap search window (min) " + u'\u00B1', 0.14, "Maximum allowed time window over which the search \nfor maximum overlap between light and heavy partner takes place"),
                ("Pair elution search window (min) " + u'\u00B1', 1, "Maximum allowed time window over which the search \nfor light and heavy peptides takes place"),
                ("Empty MS allowed", 1, "Maximum number of MS scans in which signals for light and \nheavy peptide are not seen"),
                ("Minimum isotopomers", 5, "Minimum number of isotope envelope members required (of both light and heavy) for the scan to be classed as containing the methylSILAC pair"),
                ("Pearson correlation coefficient threshold", 0.5, "Pearson correlation coefficient threshold"))

    def createFormSizer(self):
        fgrid = wx.FlexGridSizer(2, 5, 10)
        for label, initValue, tooltip in self.getFormData():
            stTxt   = wx.StaticText(self, wx.ID_ANY, label)
            txtCtrl = wx.TextCtrl(self, wx.ID_ANY)
            txtCtrl.SetValue(str(initValue))
            txtCtrl.SetToolTip(wx.ToolTip(tooltip))                     
            fgrid.Add(stTxt, proportion=1)
            fgrid.Add(txtCtrl, proportion=1, flag=wx.EXPAND)
            self.txt_ctrl_list.append(txtCtrl)            
        return fgrid

#########################################################################################################

class MassPanel(wx.Panel):
    
    def __init__(self, parent, curr_label_list, curr_mod_list):
        wx.Panel.__init__(self, parent)

        self.labels_listbox        = self.createLabelCheckbox(curr_label_list)
        self.modifications_listbox = self.createModificationCheckbox(curr_mod_list)

        vbox = self.createListSizer()
        self.SetSizer(vbox)

    def getFormData(self):
        return (("Labels", self.labels_listbox), 
                ("Modifications", self.modifications_listbox))

    def createListSizer(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        for stTxt, listbox in self.getFormData():
            shbox = self.createStaticBoxSizer(stTxt, listbox)
            vbox.Add(shbox, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        return vbox
    
    def createStaticBoxSizer(self, stTxt, listbox):
        stBox = wx.StaticBox(self, wx.ID_ANY, stTxt)
        shbox = wx.StaticBoxSizer(stBox, wx.HORIZONTAL)
        shbox.Add(listbox, proportion=1, flag=wx.EXPAND, border=10)
        return shbox

    def createLabelCheckbox(self, curr_label_list):
        checkList = LabelsListCtrl(self, curr_label_list)
        checkList.createCheckboxColumn()
        checkList.insertCheckbox()
        return checkList

    def createModificationCheckbox(self, curr_mod_list):
        checkList = ModificationsListCtrl(self, curr_mod_list)
        checkList.createCheckboxColumn()
        checkList.insertCheckbox()
        return checkList

#########################################################################################################

