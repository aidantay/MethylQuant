#--------------------------------------------------------------------------------------------------------------------

#This package contains controller-related classes and functions for the core UI

#------------------ Dependencies ----------------------------#

# Standard library imports

# External imports
import wx
from pubsub import pub

# Internal imports
from .. import model
from .. import task
from .. import view
from . import info
from . import tool
from .common import *

#------------------- Global Variables -----------------------#

MQ_FRAME_TITLE                   = "MethylQuant " + getVersion()
MQ_FRAME_SIZE                    = (0.5, 0.7)
REMOVE_EXPERIMENT_DIALOG_TITLE   = "Remove Experiment"
REMOVE_EXPERIMENT_DIALOG_MESSAGE = "Are you sure you want to remove this experiment?"
ADD_EXPERIMENT_DIALOG_TITLE      = "Add Experiment"
ADD_EXPERIMENT_DIALOG_SIZE       = (0.26, 0.4)

#------------------ Classes & Functions ---------------------#

class MethylQuantFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, 
                          title=MQ_FRAME_TITLE)

        self.experiment_list = []
        pub.subscribe(self.UpdateExperimentList, view.UPDATE_EXPERIMENT_LIST_LISTENER)

        (x, y) = getSize(MQ_FRAME_SIZE)
        self.SetSize(x, y)
        self.Centre()       #Center the UI
        self.SetIcon(getIcon())
        self.initUI()       #Initialise UI

    def initUI(self):
        self.createMenuBar()        #Create the menubar
        self.createToolBar()        #Create the toolbar
        self.createStatusBar()      #Create the statusbar
     
        #Create the main panel that will hold all other widgets
        self.main_panel = view.MethylQuantPanel(self)
        self.Bind(wx.EVT_BUTTON, self.OnStart, self.main_panel.start_btn)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

    def getMenuData(self):
        # Underline hotkey letter with &
        return (("&File", 
                    (("About", wx.ART_INFORMATION, self.OnAbout), 
                     ("Exit", wx.ART_QUIT, self.OnExit))),
                ("&Tools", 
                    (("Modifications", None, self.OnModifications), 
                     ("Labels", None, self.OnLabels))),
                ("&Help", 
                    (("Quick start", None, self.OnQuickStart), 
                     ("Information and guidance", wx.ART_HELP, self.OnInfo))))

    def createMenuBar(self):
        menuBar = wx.MenuBar()
        for menuLabel, menuItems in self.getMenuData():
            menu = self.createMenu(menuItems)
            menuBar.Append(menu, menuLabel) 
        self.SetMenuBar(menuBar)

    def createMenu(self, menuItems):
        menu = wx.Menu()
        for itemLabel, itemArt, itemHandler in menuItems:
            menuItem = self.createMenuItem(itemLabel, itemArt, itemHandler)
            menu.Append(menuItem)
        return menu

    def createMenuItem(self, itemLabel, itemArt, itemHandler):
        menuItem = wx.MenuItem(id=wx.ID_ANY, text=itemLabel)
        self.Bind(wx.EVT_MENU, itemHandler, menuItem)
        if (itemArt != None):
            icon     = wx.ArtProvider.GetBitmap(itemArt, client=wx.ART_MENU, size=(16, 16))
            menuItem.SetBitmap(icon)
        return menuItem

    def getToolData(self):
        return (("Add", wx.ART_PLUS, "Add experiment", self.OnAdd),
                ("Remove", wx.ART_MINUS, "Remove experiment", self.OnRemove))

    def createToolBar(self):
        toolBar = wx.ToolBar(self, style=wx.TB_TEXT)
        for toolLabel, toolArt, toolTip, toolHandler in self.getToolData():
            tool = self.createTool(toolBar, toolLabel, toolArt, toolTip, toolHandler)
            toolBar.AddTool(tool)
        toolBar.Realize()           ## This function should be called after you have added tools.
        self.SetToolBar(toolBar)

    def createTool(self, toolBar, toolLabel, toolArt, toolTip, toolHandler):
        icon = wx.ArtProvider.GetBitmap(toolArt, client=wx.ART_TOOLBAR)
        tool = toolBar.CreateTool(wx.ID_ANY, toolLabel, icon, shortHelp=toolTip)
        self.Bind(wx.EVT_TOOL, toolHandler, tool)
        return tool

    def createStatusBar(self):
        statusBar = wx.StatusBar(self)
        statusBar.SetFieldsCount(2)
        self.SetStatusBar(statusBar)
        pub.subscribe(self.OnUpdateStatus, task.UPDATE_STATUS_LISTENER)

    """ The following functions define the actions that occur when 
        a menu item in the menubar is pressed
    """
    def OnExit(self, event):
        self.Destroy()

    def OnAbout(self, event):
        about_dialog = info.AboutDialog(None)
        about_dialog.ShowModal()

    def OnModifications(self, event):
        modifications_dialog = tool.ModificationsDialog(None)
        modifications_dialog.ShowModal()

    def OnLabels(self, event):
        labels_dialog = tool.LabelsDialog(None)
        labels_dialog.ShowModal()

    def OnQuickStart(self, event):
        quickstart = info.QuickStartFrame(None)
        quickstart.Show()

    def OnInfo(self, event):
        info_guidance = info.InfoGuidanceFrame(None)
        info_guidance.Show()

    """ The following functions define actions that occur when
        a tool in the toolbar is pressed
    """
    def OnAdd(self, event):
        add_experiment_dialog = AddExperimentDialog(None)
        if add_experiment_dialog.ShowModal() == wx.ID_OK:
            experiment = add_experiment_dialog.createExperiment()
            self.experiment_list.append(experiment)
            self.main_panel.experiment_summary_list.insertExperiment(experiment)

    def OnRemove(self, event):
        remove_experiment_dialog = wx.MessageDialog(None, REMOVE_EXPERIMENT_DIALOG_MESSAGE, 
                                                    caption=REMOVE_EXPERIMENT_DIALOG_TITLE, 
                                                    style=wx.YES_NO)

        if remove_experiment_dialog.ShowModal() == wx.ID_YES:
            self.main_panel.experiment_summary_list.removeExperiment()
            self.main_panel.experiment_summary_list.updateExperimentIds()

    def UpdateExperimentList(self, idx):
        del(self.experiment_list[idx])

    def OnUpdateStatus(self, status_box_id, status_text):
        self.GetStatusBar().SetStatusText(status_text, status_box_id)

    """ The following function defines what happens when
        the 'Find pairs' button is pressed 
    """
    def OnStart(self, event):
        self.enableWidgets(False)   #Disable all widgets once MethylQuant has started

        #------------------ This is the heart of MethylQuant ----------------------------#
        #------------------       Run for each experiment    ----------------------------#
        for i, e in enumerate(self.experiment_list):
            experimentTask = task.ExperimentTask(e)
            # try:
            experimentTask.run()
            self.main_panel.experiment_summary_list.updateExperimentStatus(i, e.PASSED)

            # # If, for whatever reason, we encounter an error, then update the experiment status to FAILED
            # except:
            #     self.main_panel.experiment_summary_list.updateExperimentStatus(i, experiment.FAILED)

        self.finaliseProgress()
        self.enableWidgets(True)    #Enable all widgets once MethylQuant has finished

    def enableWidgets(self, is_enabled):
        self.enableToolBar(is_enabled)
        self.enableMenuBar(is_enabled)
        self.main_panel.Enable() if is_enabled else self.main_panel.Disable()

    def enableToolBar(self, is_enabled):
        toolBar = self.GetToolBar()
        for i in range(0, toolBar.GetToolsCount()):
            tool = toolBar.GetToolByPos(i)
            toolBar.EnableTool(tool.GetId(), is_enabled)

    def enableMenuBar(self, is_enabled):
        menuBar = self.GetMenuBar()
        for i in range(0, menuBar.GetMenuCount()):
            menuBar.EnableTop(i, is_enabled)

    def finaliseProgress(self):
        #update the status and progress bar after processing all CSV files
        if len(self.experiment_list) == 0:
            self.OnUpdateStatus(0, "No experiments to process")
            self.OnUpdateStatus(1, "")
            self.main_panel.progress_gauge.UpdateGauge(False)

        else:
            self.OnUpdateStatus(0, "Done")
            self.OnUpdateStatus(1, "")
            self.main_panel.progress_gauge.UpdateGauge(True)

#########################################################################################################

class AddExperimentDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, 
                           title=ADD_EXPERIMENT_DIALOG_TITLE,
                           style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX)
         
        (x, y) = getSize(ADD_EXPERIMENT_DIALOG_SIZE)
        self.SetSize(x, y)
        self.Centre()       #Center the UI
        self.initUI()

    def initUI(self):
        curr_label_list = model.LabelList()
        curr_mod_list   = model.ModificationList()
        self.add_experiment_panel = view.AddExperimentPanel(self, curr_label_list, curr_mod_list)
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.add_experiment_panel.ok_cancel_panel.ok_btn)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.add_experiment_panel.ok_cancel_panel.cancel_btn)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnEsc)

    def createExperiment(self):
        experiment_info   = self.add_experiment_panel.add_experiment_notebook.getInfoTuple()
        peptides_file_map = self.add_experiment_panel.add_experiment_notebook.getPeptidesFileMap()
        raw_dir_map       = self.add_experiment_panel.add_experiment_notebook.getRawDirMap()
        silac_map         = self.add_experiment_panel.add_experiment_notebook.getSilacMap()
        output_map        = self.add_experiment_panel.add_experiment_notebook.getOutputMap()
        label_set         = self.add_experiment_panel.add_experiment_notebook.getLabelSet()
        mod_set           = self.add_experiment_panel.add_experiment_notebook.getModSet()
        parameter_tuple   = self.add_experiment_panel.add_experiment_notebook.getParameterTuple()
        experiment        = model.Experiment(experiment_info, peptides_file_map, raw_dir_map, 
                                       label_set, mod_set, output_map, silac_map, parameter_tuple)
        return experiment

    def OnOk(self, event):
        if (self.isValidExperiment()):
            self.EndModal(wx.ID_OK) # Send a signal telling the parent what happened to the dialog

        else:
            showInvalidExperimentDialog()

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnEsc(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnCancel(event)
        event.Skip()

    def isValidExperiment(self):
        if (self.isValidFiles() and 
            self.isValidParameters() and 
            self.isValidLabels() and
            self.isValidModifications()):
            return True
        return False

    def isValidFiles(self):
        peptide_file_map = self.add_experiment_panel.add_experiment_notebook.getPeptidesFileMap()
        raw_file_map     = self.add_experiment_panel.add_experiment_notebook.getRawDirMap()

        if (self.isEmpty(peptide_file_map) or self.isEmpty(raw_file_map) or
            not self.inMap(peptide_file_map, raw_file_map)):
            return False
        return True

    def inMap(self, peptide_file_map, raw_file_map):
        # Check that all raw files in CSVs are in the directories we are searching 
        raw_files_in_all_csv = set.union(*peptide_file_map.values())
        raw_files_in_all_dir = set.union(*raw_file_map.values())

        for raw_files_in_csv in raw_files_in_all_csv:
            if raw_files_in_csv not in raw_files_in_all_dir:
                return False
        return True

    def isEmpty(self, file_map):
        if (len(file_map.keys()) != 0):
            return False
        return True

    def isValidParameters(self):
        (mass_error, time_window_overlap,
         time_window, empty_ms_allowed, 
         min_isotopomers_allowed, pearson_threshold) \
            = self.add_experiment_panel.add_experiment_notebook.getParameterTuple()
          
        if not self.isValidFormat(mass_error, time_window_overlap,
                                  time_window, empty_ms_allowed, 
                                  min_isotopomers_allowed, pearson_threshold):
            return False
        return True

    def isValidFormat(self, mass_error, time_window_overlap, time_window, 
                      empty_ms_allowed, min_isotopomers_allowed, pearson_threshold):
        try:
            #Check that it the inputs are valid
            float(mass_error)
            float(time_window_overlap)
            float(time_window)
            int(empty_ms_allowed)
            int(min_isotopomers_allowed)
            float(pearson_threshold)

        except ValueError:
            return False

        return True

    def isValidLabels(self):
        label_set = self.add_experiment_panel.add_experiment_notebook.getLabelSet()
        #Check that the residues are unique. We cannot have more than one of the same residue
        labels = list(map(lambda x: x[0], label_set))
        if (len(labels)) != len(set(labels)):
            return False
        return True

    def isValidModifications(self):
        mod_set = self.add_experiment_panel.add_experiment_notebook.getModSet()
        #Check that the modifications are unique. We cannot have more than one of the same residue
        mods = list(map(lambda x: x[0], mod_set))
        if (len(mods)) != len(set(mods)):
            return False
        return True

#########################################################################################################
