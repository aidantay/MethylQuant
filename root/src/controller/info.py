#--------------------------------------------------------------------------------------------------------------------

#This package contains controller-related classes and functions for the menu bar

#------------------ Dependencies ----------------------------#

# Standard library imports

# External imports
import wx.html

# Internal imports
from .common import *

#------------------- Global Variables -----------------------#

ABOUT_DIALOG_TITLE                 = "About"
ABOUT_DIALOG_SIZE                  = (0.15, 0.2)
QUICK_START_FRAME_TITLE            = "Quick start"
QUICK_START_FRAME_SIZE             = (0.4, 0.6)
INFO_FRAME_TITLE                   = "Information and guidance" 
INFO_FRAME_SIZE                    = (0.4, 0.6)

#------------------ Classes & Functions ---------------------#

class AboutDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, 
                           title=ABOUT_DIALOG_TITLE)

        (x, y) = getSize(ABOUT_DIALOG_SIZE)
        self.SetSize(x, y)
        self.Centre()       #Center the UI
        self.SetIcon(getIcon())
        self.Bind(wx.EVT_CHAR_HOOK, self.OnEsc)
        
        html = wx.html.HtmlWindow(self)
        html.SetPage("<h2>MethylQuant</h2>"
                     "Version: " + getVersion() + "<br><br>"
                     "Written by Vincent Geoghegan<br>"
                     "University of York<br><br>"
                     "Updated by Aidan Tay<br>"
                     "University of New South Wales")

    def OnEsc(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        event.Skip()

#########################################################################################################

class QuickStartFrame(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, 
                          title=QUICK_START_FRAME_TITLE,
                          style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.RESIZE_BORDER)

        (x, y) = getSize(QUICK_START_FRAME_SIZE)
        self.SetSize(x, y)
        self.Centre()       #Center the UI
        self.SetIcon(getIcon())
        self.Bind(wx.EVT_CHAR_HOOK, self.OnEsc)

        html = wx.html.HtmlWindow(self)
        html.SetPage("<h2>Quick start guide</h2>"
                     "<ol>" 
                        "<li>Ensure you have installed all required software."
                            "<ul>"
                                "<li>"
                                    "If you are running the .exe distribution of MethylQuant, "
                                    "then no requirements are needed."
                                "</li>"
                                "<li>"
                                    "If you are running the python source code of MethylQuant, "
                                    "then ensure wxpython, comtypes and MSFileReader are installed. "
                                    "For 64-bit systems, ensure that you have installed the 64-bit "
                                    "versions for all packages.</li>"
                            "</ul>"
                        "<\li>"
                        "<br>"
                        "<li>"
                            "Click the <b>Add</b> button to set up a new MethylQuant search."
                        "<\li>"
                        "<br>"
                        "<li>"
                            "In the <b>Peptides Files</b> tab, drag and drop one or more .csv or "
                            ".mzid (mzIdentML) files containing search results for your sequenced (and " 
                            "putatively methylated) peptides into the upper box. Ensure that your "
                            "sequenced peptides files DO NOT contain a mixture of light and heavy peptides. "
                            "Note that all .csv files should have the following exact column headers (See "
                            "table); these can appear in any order. Additional columns may also be present; "
                            "these will be ignored but appear in the results file to preserve the original layout."
                            "<p></p>"
                            "A list of the required .raw files will also appear in the box below. "
                            "Choose whether light or heavy peptides have been sequenced in your "
                            "input file. Additionally, choose whether MethylQuant will output a "
                            "summary, or the full list of MethylQuant outputs."
                            "<p></p>"
                            "<table border=1>"
                            "<tr>"
                                "<td>Sequence</td>"
                                "<td>Modifications</td>"
                                "<td>Charge</td>"
                                "<td>Data File*</td>"
                                "<td>Start Scan</td>"
                                "<td>Calc m/z</td>"
                                "<td>Mass Difference**</td>"
                            "</tr>"
                            "<tr>"
                                "<td>GGDRGGGYGGDRGGGY</td>"
                                "<td>R4(Methyl); R12(Methyl)</td>"
                                "<td>2</td>"
                                "<td>20140120_001.raw</td>"
                                "<td>2128</td>"
                                "<td>743.33</td>"
                                "<td>4.02</td>"
                            "</table>"
                            "<p></p>"
                            "* The <b>Data File column</b> contains the name of the .raw file from "
                            "which the peptide was identified."
                            "<p></p>"
                            "* The <b>Mass Difference column</b> is optional; use it if MethylQuant "
                            "cannot calculate the correct m/z shift from the modified peptide sequence. "
                            "If supplied, MethylQuant will use the mass differences given in this column "
                            "to determine the masses for the light or heavy partner. The column should "
                            "contain the expected m/z difference (i.e. mass difference/charge). If a "
                            "heavy peptide has been sequenced, then the expected m/z difference "
                            "MUST BE negative. If you have supplied your own mass shift, then MethylQuant "
                            "will not attempt to calculate the mass shift from the peptide sequence "
                            "and the list of modifications."
                            "<p></p>"
                            "If a mass difference is not given, MethylQuant will attempt to determine "
                            "the expected m/z difference from the peptide sequence and the list of "
                            "modifications. In this case, modifications should be indicated in brackets, "
                            "and listed in the <b>Modifications column</b> as shown above. By default, "
                            "normal methyl-SILAC is assumed and methylation sites should be indicated "
                            "by either <b>Methyl</b>, <b>Dimethyl</b> or <b>Trimethyl</b> (See below). "
                            "Other modifications may be present in the Modification column but these will "
                            "not be counted. Additionally, methionines will be counted in methyl-SILAC "
                            "searches as they will contribute to the mass shift."
                            "<ul>"
                                "<li>(Methyl):    monomethylation site</li>"
                                "<li>(Dimethyl):  dimethylation site</li>"
                                "<li>(Trimethyl): trimethylation site</li>"
                            "</ul>"
                        "<\li>"
                        "<br>"
                        "<li>"
                            "In the <b>Raw Files</b> tab, drag and drop the folder containing all " 
                            "the required .raw files into the upper box. Other types of files may "
                            "be present in the folder; these will be ignored. A list of all .raw "
                            "files present in the folder will appear in the box below."
                        "<\li>"
                        "<br>"
                        "<li>"
                            "In the <b>Parameters</b> tab, alter the MethylQuant parameters to your "
                            "needs. The supplied parameters will perform well for most datasets but "
                            "may be altered for tailored searches. Please refer to the <b>Information and "
                            "guidance</b> guide for a detailed description on the parameters."
                        "<\li>"
                        "<br>"
                        "<li>"
                            "In the <b>Mass Shifts</b> tab, choose the labelling used for the sequenced "
                            "peptides and your modifications of interest. By default, normal methyl-SILAC "
                            "labelling (light methionine + 13CD3 methionine) and modifications are assumed "
                            "to be used. Please refer to the <b>Information and guidance</b> guide for "
                            "a detailed description on how the mass shifts work."
                        "<\li>"
                        "<br>"
                        "<li>"
                            "Click the <b>OK</b> button to finalise your experiment."
                        "<\li>"
                        "<br>"
                        "<li>"
                            "Click the <b>Find Pairs</b> button to start the program "
                            "and begin searching!"
                        "<\li>"
                        "<br>"
                        "<li>"
                            "After each search, MethylQuant will indicate whether the search was "
                            "successful or not in the <b>Status</b> column in the main window. "
                            "The status of a search will either be a <b>Tick</b> for successful searches, "
                            "or a <b>Cross</b> for unsuccessful searches. If your search was unsuccessful, "
                            "please check the format of your files and search parameters. For any ongoing "
                            "issues, please contact the authors directly."
                        "<\li>"
                     "</ol>")

    def OnEsc(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Destroy()
        event.Skip()

#########################################################################################################

class InfoGuidanceFrame(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, 
                          title=INFO_FRAME_TITLE,
                          style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.RESIZE_BORDER)

        (x, y) = getSize(INFO_FRAME_SIZE)
        self.SetSize(x, y)
        self.Centre()       #Center the UI
        self.SetIcon(getIcon())
        self.Bind(wx.EVT_CHAR_HOOK, self.OnEsc)

        html = wx.html.HtmlWindow(self)
        html.SetPage("<h2>Information and guidance for MethylQuant</h2>"
                    "<h3>Introduction</h3>"
                    "<p>"
                        "Do we really need yet another mass spectrometry quantitation software? "
                        "Generally, no, we don't. There is plenty of good software for doing routine "
                        "quantitation of mass spectrometry data (label free, SILAC, dimethyl labelled), "
                        "such as MaxQuant and Proteome Discoverer. The motivation behind MethylQuant "
                        "came from the need to find methyl-SILAC pairs for methylated peptides. None "
                        "of the widely used software are able to find SILAC pairs for a variable "
                        "modification (i.e. where only some of the residues in a peptide have the label) " 
                        "I stumbled across XiQ from the Rappsilber group which looked quite good but "
                        "I couldn't get it to run on my computer. There was also very little documentation, "
                        "no gui and no way to easily play around with the parameters (although perhaps "
                        "they have improved it now). In short, at the time it was not very user friendly. "
                        "However, reading their paper did inspire me to try something similar for "
                        "methyl-SILAC data, so I'm grateful they published XiQ. There may be other "
                        "software for methyl-SILAC quantitation but at the time of writing I am "
                        "unaware of it."
                    "</p>"
                    "<h3>Limitations</h3>"
                    "<p>"
                        "MethylQuant was designed primarily to be very sensitive at finding "
                        "methyl-SILAC pairs. It does so by finding the scans where both light and "
                        "heavy peptides co-elute and quantitates based on these. Testing of MethylQuant "
                        "showed that it does a good job of finding 1:1 pairs. However, MethylQuant "
                        "might not be as sensitive when looking for 1:10 pairs in a quantitation "
                        "experiment. Also, the program does not check the correlation between the "
                        "measured isotope envelope and the theoretical isotope envelope."
                    "</p>"
                    "<h3>How MethylQuant works</h3>"
                    "<ol>"
                        "<li>"
                            "The precursor mass for the sequenced peptide is retrieved using the MS/MS "
                            "scan number. This is compared to the calculated m/z (theoretical m/z) to "
                            "determine which isotopic peak of the peptide was chosen for sequencing. "
                            "The m/z values for the first, second and third isotopomers of the peptide "
                            "are calculated. Using the expected mass shift, the m/z value for the first, "
                            "second and third isotopomers of the light/heavy partner are calculated."
                        "</li>"
                        "<br>"
                        "<li>"
                            "There is now a set of 6 m/z values to search for (3 for the light, 3 for "
                            "the heavy). Using the time at which the MS/MS took place as a starting point, "
                            "the .raw data file is searched for the point at which the light and heavy "
                            "peptides are at their maximum intensity (point of maximum overlap between "
                            "light and heavy). The exact number of masses to search for may be less "
                            "than 6 if the minimum number of isotopomers has been set to less than " 
                            "6."
                        "</li>"
                        "<br>"
                        "<li>"
                            "From the point of maximum overlap, the start and stop elution point of "
                            "the methyl-SILAC pair is determined."
                        "</li>"
                        "<br>"
                        "<li>"
                            "A spectrum (m/z vs. intensity) is then obtained, averaged between the "
                            "start and stop elution points of the methyl-SILAC pair."
                        "</li>"
                        "<br>"
                        "<li>"
                            "The averaged spectrum is searched for all 6 m/z values of the "
                            "methyl-SILAC pair."
                        "</li>"
                        "<br>"
                        "<li>"
                            "The average intensities of the first 3 isotopomers of the light are "
                            "summed, the same is done for the heavy partner. The H/L Rratio #1 is "
                            "then determined by dividing the sum of the heavy intensities by the sum of "
                            "the light intensities."
                        "</li>"
                        "<br>"
                        "<li>"
                            "XICs across the start and stop elution points are then obtained for each "
                            "isotopomer in the peptide pair. The H/L ratio #2 is then determined by "
                            "dividing the sum of the heavy intensities by the sum of the light intensities "
                            "for well correlated XIC pairs."
                        "</li>"
                    "</ol>"
                    "<h3>Required input</h3>"
                    "<p>"
                        "MethylQuant takes a .csv or .mzid (mzIdentML) file containing search results "
                        "for your sequenced (and putatively methylated) peptides and a folder containing "
                        ".raw files as its input. Please refer to the <b>Quick Start</b> guide for "
                        "detailed instructions on the required format of the .csv files and on how to "
                        "set up MethylQuant searches."
                    "<\p>"
                    "<h3>Parameters</h3>"
                    "<ul>"
                        "<li>"
                            "<b>Mass error (ppm)</b><br>"
                            "Sets the mass tolerance when matching up the theoretical masses of the "
                            "peptides with m/z signals in the .raw file."
                        "</li>"
                        "<li>"
                            "<b>Pair overlap search window (min)</b><br>"
                            "Sets the maximum time window in minutes over which MethylQuant tries to find "
                            "the point of maximum overlap between light and heavy peptides in a methyl-SILAC "
                            "pair for each sequenced peptide. The MS/MS scan is used as the start point, the "
                            "search window is set either side of this."
                        "</li>"
                        "<li>"
                            "<b>Pair elution search window (min)</b><br>"
                            "Sets the maximum time window in minutes over which MethylQuant tries to find "
                            "the methyl-SILAC pair for a sequenced peptide. The start point is either "
                            "the point of maximum overlap between light and heavy (if found), or the MS/MS "
                            "scan for the peptide (if not found)."
                        "</li>"
                        "<li>"
                            "<b>Empty MS allowed</b><br>"
                            "When searching for the elution window of the methyl-SILAC pair, this is the "
                            "maximum number of allowed MS scans that do not contain the minimum number "
                            "of isotopomers from light and heavy peptides. This is to help find weak "
                            "peptides, whose isotope envelopes may not be consistently present in consecutive "
                            "MS scans. If this is set too high, the program might start taking noise as a "
                            "methyl-SILAC pair, or might join together adjacently eluting pairs."
                        "</li>"
                        "<li>"
                            "<b>Minimum isotopomers</b><br>"
                            "Sets the minimum number of isotopomers (members of the isotope envelope of "
                            "a peptide) required when searching for elution of the methyl-SILAC pair. "
                            "When searching for the methyl-SILAC pair, the masses of the first three "
                            "isotopomers of the light and the first three of the heavy peptide are "
                            "calculated, giving a total of 6 masses to search for. If a light and heavy "
                            "peptides are co-eluting all 6 masses should be present. Setting the minimum "
                            "number too low will make MethylQuant measure the intensity of noise "
                            "or peptides which are not part of a methyl-SILAC pair but have the same mass "
                            "as the light or heavy peptide. Note that requiring at least 5 isotopomers "
                            "for quantitation means that the methyl-SILAC pair is only quantitated over "
                            "the MS scans in which the light and heavy peptide co-elute."
                        "</li>"
                        "<li>"
                            "<b>Pearson correlation coefficient threshold</b><br>"
                            "Extracted ion chromatograms (XICs) across the start and stop elution "
                            "points are obtained for each isotopomer in the putative methyl-SILAC "
                            "pair. The Pearson correlation coefficients for the XICs of each "
                            "isotopomer pair are calculated. XICs are considered well correlated if "
                            "the calculated Pearson correlation coefficient is greater than the threshold." 
                        "<\li>"
                    "</ul>"
                    "<h3>Mass Shifts</h3>"
                        "If a mass difference is not given, MethylQuant will attempt to determine "
                        "the expected m/z difference from the peptide sequence and the list of "
                        "modifications. In this case, modifications should be indicated in brackets, "
                        "and listed in the <b>Modifications column</b>."
                        "<p></p>"
                        "By default, the expected m/z difference is calculated by MethylQuant based "
                        "on normal methyl-SILAC labelling (light methionine + 13CD3 methionine) and "
                        "modifications. For other SILAC experiments however, different labels and/or "
                        "modifications may be used. In these cases, the expected m/z difference can be "
                        "calculated by selecting the labels and modifications that contribute to "
                        "the expected m/z difference. Please note that custom labels and modifications "
                        "must be added into MethylQuant through the <b>Tools</b> menu before they "
                        "can be selected."
                    "<h3>Output</h3>"
                    "<p>"
                        "Results are written as a .csv file in the same location as the input file. "
                        "The file name is the input file name with \"_MethylQuant\" appended. "
                        "If you are having trouble opening the results file in excel it may be because "
                        "the file path + file name is too long, you can move the file to another "
                        "location with a shorter file path. If the full list of MethylQuant outputs is "
                        "requested, the results file will contain all the information in the input "
                        "file with the following additional columns added to each row:"
                        "<p></p>"
                        "<table border=1>"
                            "<tr>"
                                "<td>Peptide Start Scan*</td>"
                                "<td>Peptide Stop Scan*</td>"
                                "<td>Peptide Start RT (min)</td>"
                                "<td>Peptide Stop RT (min)</td>"
                                "<td>Light m/z 1 IsotopeCorrelation</td>"
                                "<td>Light Intensity 1 IsotopeCorrelation**</td>"
                                "<td>Light m/z 2 IsotopeCorrelation</td>"
                                "<td>Light Intensity 2 IsotopeCorrelation**</td>"
                                "<td>Light m/z 3 IsotopeCorrelation</td>"
                                "<td>Light Intensity 3 IsotopeCorrelation**</td>"
                                "<td>Heavy m/z 1 IsotopeCorrelation</td>"
                                "<td>Heavy Intensity 1 IsotopeCorrelation**</td>"
                                "<td>Heavy m/z 2 IsotopeCorrelation</td>"
                                "<td>Heavy Intensity 2 IsotopeCorrelation**</td>"
                                "<td>Heavy m/z 3 IsotopeCorrelation</td>"
                                "<td>Heavy Intensity 3 IsotopeCorrelation**</td>"
                                "<td>Isotope Distribution Correlation</td>"
                                "<td>H/L ratio #1***</td>"
                                "<td>Light m/z 1 ElutionCorrelation</td>"
                                "<td>Light Intensity 1 ElutionCorrelation</td>"
                                "<td>Light m/z 2 ElutionCorrelation</td>"
                                "<td>Light Intensity 2 ElutionCorrelation</td>"
                                "<td>Light m/z 3 ElutionCorrelation</td>"
                                "<td>Light Intensity 3 ElutionCorrelation</td>"
                                "<td>Heavy m/z 1 ElutionCorrelation</td>"
                                "<td>Heavy Intensity 1 ElutionCorrelation</td>"
                                "<td>Heavy m/z 2 ElutionCorrelation</td>"
                                "<td>Heavy Intensity 2 ElutionCorrelation</td>"
                                "<td>Heavy m/z 3 ElutionCorrelation</td>"
                                "<td>Heavy Intensity 3 ElutionCorrelation</td>"
                                "<td>Elution Profile Correlation 1</td>"
                                "<td>Elution Profile Correlation 2</td>"
                                "<td>Elution Profile Correlation 3</td>"
                                "<td># Good Elution Profile Correlations</td>"
                                "<td>H/L ratio #2****</td>"
                                "<td>MethylQuant Score</td>"
                                "<td>MethylQuant Confidence</td>"
                            "</tr>"
                            "<tr>"
                                "<td>Scan number where methyl-SILAC pair starts</td>"
                                "<td>Scan number where methyl-SILAC pair stops</td>"
                                "<td>Retention time where methyl-SILAC pair starts</td>"
                                "<td>Retention time where methyl-SILAC pair stops</td>"
                                "<td>1st isotopic m/z (monoisotopic m/z) of light peptide</td>"
                                "<td>Intensity of 1st isotope of light peptide</td>"
                                "<td>2nd isotopic m/z of light peptide</td>"
                                "<td>Intensity of 2nd isotope of light peptide</td>"
                                "<td>3rd isotopic m/z of light peptide</td>"
                                "<td>Intensity of 3rd isotope of light peptide</td>"
                                "<td>1st isotopic m/z (monoisotopic m/z) of heavy peptide</td>"
                                "<td>Intensity of 1st isotope of heavy peptide</td>"
                                "<td>2nd isotopic m/z of heavy peptide</td>"
                                "<td>Intensity of 2nd isotope of heavy peptide</td>"
                                "<td>3rd isotopic m/z of heavy peptide</td>"
                                "<td>Intensity of 3rd isotope of heavy peptide</td>"
                                "<td>Pearson correlation coefficient for intensities of the first 3 isotopes of light and heavy peptides</td>"
                                "<td>The sum of the intensities of the first 3 isotopes of heavy divided by the corresponding sum of the light peptide</td>"
                                "<td>1st isotopic m/z (monoisotopic m/z) of light peptide</td>"
                                "<td>XIC area of 1st isotope of light peptide</td>"
                                "<td>2nd isotopic m/z of light peptide</td>"
                                "<td>XIC area of 2nd isotope of light peptide</td>"
                                "<td>3rd isotopic m/z of light peptide</td>"
                                "<td>XIC area of 3rd isotope of light peptide</td>"
                                "<td>1st isotopic m/z (monoisotopic m/z) of heavy peptide</td>"
                                "<td>XIC area of 1st isotope of heavy peptide</td>"
                                "<td>2nd isotopic m/z of heavy peptide</td>"
                                "<td>XIC area of 2nd isotope of heavy peptide</td>"
                                "<td>3rd isotopic m/z of heavy peptide</td>"
                                "<td>XIC area of 3rd isotope of heavy peptide</td>"
                                "<td>Pearson correlation coefficient for the XICs of the 1st isotopic m/z of the light and heavy peptides</td>"
                                "<td>Pearson correlation coefficient for the XICs of the 2nd isotopic m/z of the light and heavy peptides</td>"
                                "<td>Pearson correlation coefficient for the XICs of the 3rd isotopic m/z of the light and heavy peptides</td>"
                                "<td>Number of Pearson correlation coefficients for XIC pairs above the set threshold (0.5 by default)</td>"
                                "<td>The sum of the XIC area of heavy divided by the corresponding sum of the light peptide for well correlated XIC pairs</td>"  
                                "<td>Methyl-SILAC pair identification score</td>"
                                "<td>Confidence of methyl-SILAC pair detection</td>"
                            "</tr>"
                        "</table>"
                        "<p></p>"
                        "* Start and stop points determined for the methyl-SILAC pair by MethylQuant "
                        "are either the points where the program can no longer find the set minimum "
                        "number of isotopomers from the pair, or the boundaries of the search window "
                        "as set in the parameters, whichever occurs sooner."
                        "<p></p>"
                        "** Intensity values are average intensities over the elution window of the "
                        "methyl-SILAC pair. If an m/z matching the theoretical m/z is not found, the "
                        "intensity is displayed as 0."    
                        "<p><\p>"
                        "*** MethylQuant requires all 6 isotopomers to have been found before "
                        "calculating its H/L Ratio #1 output. If one or more are missing, \"NA\" is "
                        "displayed."
                        "<p><\p>"
                        "**** MethylQuant's H/L Ratio #2 output is calculated using XIC areas of "
                        "well correlated isotopomer pairs only. If no such pairs exist, \"NA\" is "
                        "displayed.")

    def OnEsc(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Destroy()
        event.Skip()

#########################################################################################################

