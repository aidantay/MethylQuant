#--------------------------------------------------------------------------------------------------------------------

#This package contains object-related classes and functions for XR objects

#------------------ Dependencies ----------------------------#

## External dependencies
import numpy
from comtypes.client import * 
from comtypes.automation import *

#------------------ Global Variables ------------------------#

#------------------ Classes & Functions ---------------------#

class XrInfo():
   
    def __init__(self, xr):
        self.xr = xr

        self.scan_table                         = {}   # Table of scan objects for a given scan number
        self.peptide_scan_num_table             = {}   # Table of maximum, start and stop scan numbers for a given peptide
        self.precursor_max_mass_intensity_table = {}   # Table containing the maximum mass intensity for a given isotope mass based on precursor mass list
        self.average_max_mass_intensity_table   = {}   # Table containing the maximum mass intensity for a given isotope mass based on average mass list
        self.average_mass_list_table            = {}   # Table containing the average mass list over a range of scan numbers
        self.MS1_scan_list                      = []
        self.init()
        self.initScanTable()
        self.initScanList()

    def init(self):        
        # Don't really understand what this does...
        # But we need to run this so that we can access the data
        self.xr.SetCurrentController(0, 1)

        #get number of spectra in raw file
        self.num_spectra    = c_long()
        self.xr.GetNumSpectra(self.num_spectra)       

        #get start time of the first scan
        self.run_start_time = c_double()
        self.xr.GetStartTime(self.run_start_time)

        #get end time of the last (?) scan
        self.run_end_time   = c_double()
        self.xr.GetEndTime(self.run_end_time)

    def initScanTable(self): 
        #pre-process the necessary information for ALL scan numbers
        for scan_num in range(1, self.getNumSpectra() + 1):
            rt                  = self.__getRTFromScanNum(scan_num)
            precursor_mass      = self.__getPrecursorMassFromScanNum(scan_num)
            scan_type           = self.__getScanTypeFromScanNum(scan_num)
            precursor_mass_list = self.__getPrecursorMassListFromScanNum(scan_num)

            scan_info = ScanInfo(scan_num, rt, precursor_mass, scan_type, precursor_mass_list)
            self.scan_table[scan_num] = scan_info

    def initScanList(self):
        #check whether scan is MS2 or higher
        #MS1 scan returns 1, MS2 returns 2
        f = lambda x: x.scan_type < 2
        g = lambda x: x.scan_num
        self.MS1_scan_list = filter(f, self.scan_table.values())        
        self.MS1_scan_list = list(map(g, self.MS1_scan_list))
        self.MS1_scan_list.sort()

    def __str__(self):
        xr_info = [str(self.xr), str(self.getNumSpectra()), 
                   str(self.getRunStartTime()), str(self.getRunEndTime())]
        return "\t".join(xr_info)

    def getScanRange(self, scan_start, scan_stop):
        f = lambda x: x >= scan_start and x <= scan_stop
        return list(filter(f, self.MS1_scan_list))

    def getPeptideScanNumber(self, key):
        return self.peptide_scan_num_table[key]

    def putPeptideScanNumber(self, key, scan_num_table):
        self.peptide_scan_num_table[key] = scan_num_table

    def containsPeptideScanNumber(self, key):
        return True if key in self.peptide_scan_num_table else False

    def getPrecursorMaxMassIntensity(self, key):
        return self.precursor_max_mass_intensity_table[key]

    def putPrecursorMaxMassIntensity(self, key, max_isotope_mass_intensity):
        self.precursor_max_mass_intensity_table[key] = max_isotope_mass_intensity

    def containsPrecursorMaxMassIntensity(self, key):
        return True if key in self.precursor_max_mass_intensity_table else False
    
    def getAverageMaxMassIntensity(self, key):
        return self.average_max_mass_intensity_table[key]

    def putAverageMaxMassIntensity(self, key, max_isotope_mass_intensity):
        self.average_max_mass_intensity_table[key] = max_isotope_mass_intensity

    def containsAverageMaxMassIntensity(self, key):
        return True if key in self.average_max_mass_intensity_table else False

    def getAverageMassList(self, key):
        return self.average_mass_list_table[key]

    def putAverageMassList(self, key, average_mass_list):
        self.average_mass_list_table[key] = average_mass_list

    def containsAverageMassList(self, key):
        return True if key in self.average_mass_list_table else False

    def getNumSpectra(self):
        return self.num_spectra.value
    
    def getRunStartTime(self):
        return self.run_start_time.value

    def getRunEndTime(self):
        return self.run_end_time.value
    
    def getScanNumFromRT(self, retention_time):
        scan_num = c_long()
        self.xr.ScanNumFromRT(c_double(retention_time), scan_num)
        return scan_num.value

    """ Returns ScanInfo object containing information about a specific scan. If there is none, we create one

        Briefly, the ScanInfo object contains:
        -- Retention time
        -- Precusor mass
        -- Scan type
        -- numpy.array of precursor mass intensities
    
        Keyword arguments:
        scan -- MS/MS scan number 
    """
    def getScanInfo(self, scan_num):
        return self.scan_table[scan_num]

    """ Returns numpy.array containing the average mass list for a given peptide
     
        Keyword arguments:
        peptide_start_scan_num -- starting scan number for methylSILAC pair
        peptide_stop_scan_num  -- stopping scan number for methylSILAC pair
    """
    def getAverageMassListForPeptide(self, peptide_start_scan_num, peptide_stop_scan_num):
        key = (peptide_start_scan_num, peptide_stop_scan_num)
        if not self.containsAverageMassList(key):
            average_masses_intensities = self.getAverageMassListFromPeptidePair(peptide_start_scan_num, peptide_stop_scan_num)
            self.putAverageMassList(key, average_masses_intensities)
     
        average_masses_intensities = self.getAverageMassList(key)
        return average_masses_intensities

    """ Returns numpy.array containing average mass intensities for a given range of MS/MS scan numbers
    
        Keyword arguments:
        peptide_start_scan_num -- Starting scan number for methylSILAC pair
        peptide_stop_scan_num  -- Stopping scan number for methylSILAC pair
    """
    def getAverageMassListFromPeptidePair(self, peptide_start_scan_num, peptide_end_scan_num):
        #Get average_mass_list
        average_mass_list = VARIANT()
        pl                = VARIANT()
        arsize            = c_long()
            
        #this function has 15 arguments, not 13 as shown in the documentation
        #either documentation or my version of msfilereader is out of date
        self.xr.GetAverageMassList(c_long(peptide_start_scan_num),
                                   c_long(peptide_end_scan_num),
                                   c_long(0),
                                   c_long(0),
                                   c_long(0),
                                   c_long(0),
                                   'ms',
                                   c_long(0),
                                   c_long(0),
                                   c_long(0),
                                   False, c_double(0),
                                   average_mass_list, pl, arsize) 
           
        ## Create a numpy matrix containing rows of (mass, intensity)
        ## Remove all values with intensity of 0. We don't use them...
        average_masses_intensities = numpy.array(zip(average_mass_list[0][0], average_mass_list[0][1]))
        average_masses_intensities = average_masses_intensities[numpy.all(average_masses_intensities != 0, axis = 1)]
        return average_masses_intensities

    """ The following functions get parameters for a specified scan number
    """   
    def __getRTFromScanNum(self, scan_num):
        retention_time = c_double()
        self.xr.RTFromScanNum(c_long(scan_num), retention_time)
        return retention_time.value

    def __getPrecursorMassFromScanNum(self, scan_num):
        precursor_mass = c_double(0)
        self.xr.GetPrecursorMassForScanNum(c_long(scan_num), c_long(2), precursor_mass)
        return precursor_mass.value

    def __getScanTypeFromScanNum(self, scan_num):
        scan_type = c_long()
        self.xr.GetMSOrderForScanNum(c_long(scan_num), scan_type)
        return scan_type.value

    """ Returns numpy.array containing precursor mass intensities for a specified scan number
    
        Keyword arguments:
        scan_num -- MS/MS scan number 
    """
    def __getPrecursorMassListFromScanNum(self, scan_num):
        #Get precursor_mass_list
        precursor_mass_list      = VARIANT()
        scanFilter               = ''   #we are only interested in precursor scans, can set scan filter to 'ms'
        scanIntensityCutoffType  = 0    # 0 = none, 1=Abs, 2=Rel. to basepk
        scanIntensityCutoffValue = 0
        scanMaxNumberOfPeaks     = 0
        arsize                   = c_long()
        pl                       = VARIANT() #Unused variable    
        
        self.xr.GetMassListFromScanNum(c_long(scan_num), scanFilter,
                                       c_long(scanIntensityCutoffType),
                                       c_long(scanIntensityCutoffValue),
                                       c_long(scanMaxNumberOfPeaks),
                                       False, c_double(0),
                                       precursor_mass_list, pl, arsize)

        ## Create a numpy matrix containing rows of (mass, intensity) 
        ## Remove all values with intensity of 0. We don't use them...
        precursor_masses_intensities = numpy.array(zip(precursor_mass_list[0][0], precursor_mass_list[0][1]))
        if (precursor_masses_intensities.size != 0):
            precursor_masses_intensities = precursor_masses_intensities[numpy.all(precursor_masses_intensities != 0, axis = 1)]

        return precursor_masses_intensities

#########################################################################################################

class ScanInfo():
    
    def __init__(self, scan_num, retention_time, precursor_mass, scan_type, precursor_mass_list):
        self.scan_num            = scan_num
        self.RT                  = retention_time
        self.precursor_mass      = precursor_mass
        self.scan_type           = scan_type
        self.precursor_mass_list = precursor_mass_list

    def __str__(self):
        return "\t".join(["SCANS:" + str(self.scan_num), 
                          "RT:" + str(self.getRT()), 
                          "PRECURSORMASS:" + str(self.getPrecursorMass()), 
                          "SCANTYPE:" + str(self.scan_type)])
    
    def __repr__(self):
        return self.__str__()

    def getRT(self):
        return self.RT

    def getPrecursorMass(self):
        return self.precursor_mass

    def getPrecursorMassList(self):
        return self.precursor_mass_list

#########################################################################################################

