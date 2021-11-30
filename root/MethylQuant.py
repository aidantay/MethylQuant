#--------------------------------------------------------------------------------------------------------------------
#MethylQuant version 1.00
#MethylQuant written by Vincent Geoghegan
#University of York
#
#MethylQuant updated by Aidan Tay
#University of New South Wales
#--------------------------------------------------------------------------------------------------------------------

#See Help menu for information and guidance

#Running requirements:

    #MethylQuant runs ONLY on Windows 7 32-bit and 64-bit platforms.
    #We recommend running MethylQuant on 64-bit platforms, as memory allocation
    #on 32-bit platforms may not be sufficient for large data sets.
    #Preprocessing or filtering peptide search results prior to
    #running MethylQuant may help.

    #Thermo MSFileReader v3.1 SP4 (32-bit or 64-bit as appropriate)
    #MSFileReader and its reference guide can be found on Thermo's website.
    #For more details on installation, see the following:
    #https://github.com/frallain/pymsfilereader
    #If you have installed MSFileReader in 64-bit version, 
    #then your Python version should also be 64-bit. Same for 23-bit versions
    #Running MSFilereader in 32-bit and using 64-bit Python can cause problems.

    #MethylQuant was tested using Python 3.7.6 (64-bit version)
    #To run the source code:
    # * Install Anaconda
    # * Set the Conda and Python PATH environment variables
    # * Activate the Conda environment in command prompt
    # * Run MethylQuant.py via command prompt

    #Python packages:
    #MethylQuant uses several popular third-party packages. Most packages can
    #can be installed via Anaconda. The versions of each package
    #are listed below:
    # * wxpython (v4.0.4)    * pandas         (v1.0.1)
    # * numpy    (v1.18.1)   * maptplotlib    (v3.1.3)
    # * scipy    (v1.4.1)    * pymsfilereader (v1.0.1)

#------------------ Dependencies ----------------------------#

## External dependencies
import wx
import unittest
 
## Internal dependencies
from src import controller
import tests

#------------------- Global Variables -----------------------#
    
LOG_FILE = "MethylQuant_log_file.txt"                                   # Use for testing

#------------------ Classes & Functions ---------------------#
   
class MethylQuantApp(wx.App):
     
    def __init__(self):
        wx.App.__init__(self)     #redirect=True, filename=LOG_FILE     # Use for testing
 
    def OnInit(self):
        self.frame = controller.MethylQuantFrame()
        self.frame.Show()         #Make the UI visible to the user
        return True

#########################################################################################################
 
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(tests.TestPeptideReader, 'test'))
    suite.addTest(unittest.makeSuite(tests.TestCsvWriter, 'test'))
    suite.addTest(unittest.makeSuite(tests.TestMassCalculations, 'test'))
    suite.addTest(unittest.makeSuite(tests.TestRawReader, 'test'))
    suite.addTest(unittest.makeSuite(tests.TestConfidenceCalculations, 'test'))
    return suite

#########################################################################################################
  
def main():
    ## Run unit tests
#     unittest.main(defaultTest='suite')
    app = MethylQuantApp()
    app.MainLoop()

#------------------- Main -----------------------------------#
 
if __name__ == "__main__":
    main()
