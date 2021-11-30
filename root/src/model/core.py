#--------------------------------------------------------------------------------------------------------------------

#This package contains model-related classes and functions for the core UI

#------------------ Dependencies ----------------------------#

## External dependencies
import numpy
from comtypes.client import * 
from comtypes.automation import *

## Internal dependencies
from .menu import DEFAULT_LABEL_LIST
from .menu import DEFAULT_MOD_LIST

#------------------- Global Variables -----------------------#

#------------------ Classes & Functions ---------------------#

class Experiment():

    PASSED = 0
    FAILED = 1
    
    def __init__(self, experiment_info, peptides_file_map, raw_dir_map,
                 label_set, mod_set, output_map, silac_map, parameter_tuple):
        self.experiment_info   = experiment_info                    # Tuple containing experiment info
        self.file_info         = FileInfo(peptides_file_map, raw_dir_map, silac_map, output_map)    # Tables containing CSV file paths -> {Raw file names} or {silac type} or {output style}
        self.mass_shifts       = MassShifts(label_set, mod_set)     # Sets of label and modification masses
        self.parameters        = Parameters(parameter_tuple)        # Tuple containing parameters

    def getExperimentName(self):
        return self.experiment_info[0]

    def getExperimentDescription(self):
        return self.experiment_info[1]

    def __str__(self):
        return "\n".join([str(self.getExperimentName()), str(self.getExperimentDescription()),
                          str(self.file_info), str(self.mass_shifts),
                          str(self.parameters)])

#########################################################################################################

class FileInfo():
    
    def __init__(self, peptides_file_map, raw_dir_map, silac_map, output_map):
        self.peptides_file_map = peptides_file_map      # Table containing CSV file paths -> {Raw file names}
        self.raw_dir_map       = raw_dir_map            # Table containing Raw dir paths  -> {Raw file names}
        self.silac_map         = silac_map
        self.output_map        = output_map

    def getPeptideFiles(self):
        return self.peptides_file_map.keys()

    def getSilacType(self, seq_peptides_path):
        return self.silac_map[seq_peptides_path]

    def getOutputStyle(self, seq_peptides_path):
        return self.output_map[seq_peptides_path]

    def __str__(self):
        return "\n".join([str(self.peptides_file_map), str(self.raw_dir_map),                          
                          str(self.silac_map), str(self.output_map)])
                         
#########################################################################################################

class MassShifts():
    
    def __init__(self, label_set, mod_set):
        self.label_set = label_set
        self.mod_set   = mod_set
        
    def isDefault(self):
        if (not self.isDefaultModList() and 
            not self.isDefaultLabelList()):
            return False
        return True

    def isDefaultModList(self):
        if (self.mod_set != set(DEFAULT_MOD_LIST)):
            return False
        return True
    
    def isDefaultLabelList(self):
        default_label_set = set(map(lambda x: (x[1], x[2]), DEFAULT_LABEL_LIST))
        if (len(self.label_set) != 1 or 
            not self.label_set.issubset(default_label_set)):
            return False
        return True

    def calculateMassShiftForLabels(self, peptide_seq):
        mass_shift = 0
        for residue, mass in self.label_set:
            mass_shift = mass_shift + (peptide_seq.count(residue) * mass)
        return mass_shift
    
    def calculateMassShiftForModifications(self, modifications):
        mass_shift = 0
        for mod_type, mod_mass in self.mod_set:
            mass_shift = mass_shift + (modifications.count("(" + mod_type + ")") * mod_mass)
        return mass_shift
    
    def __str__(self):
        return "\t".join([str(self.label_set), str(self.mod_set)])

#########################################################################################################

class Parameters():

    def __init__(self, parameter_tuple):
        self.mass_error              = float(parameter_tuple[0])
        self.time_window_overlap     = float(parameter_tuple[1])
        self.time_window             = float(parameter_tuple[2])
        self.empty_ms_allowed        = int(parameter_tuple[3])
        self.min_isotopomers_allowed = int(parameter_tuple[4])
        self.pearson_threshold       = float(parameter_tuple[5])

    def __str__(self):
        return "\t".join([str(self.mass_error), str(self.time_window_overlap), 
                          str(self.time_window), str(self.empty_ms_allowed), 
                          str(self.min_isotopomers_allowed), str(self.pearson_threshold)])

#########################################################################################################

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
        self.num_spectra     = self.xr.GetNumSpectra()

        #get start time of the first scan
        self.run_start_time  = self.xr.GetStartTime()

        #get end time of the last (?) scan
        self.run_end_time    = self.xr.GetEndTime()

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
        return self.num_spectra

    def getRunStartTime(self):
        return self.run_start_time

    def getRunEndTime(self):
        return self.run_end_time

    def getScanNumFromRT(self, retention_time):
        scan_num = self.xr.ScanNumFromRT(retention_time)
        return scan_num

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
        if (not self.containsAverageMassList(key)):
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
        (average_mass_list, pl) = self.xr.GetAverageMassList(peptide_start_scan_num,
            peptide_end_scan_num, scanFilter='ms')

        average_masses_intensities = self.__formatMassList(average_mass_list)
        return average_masses_intensities

    """ The following functions get parameters for a specified scan number
    """   
    def __getRTFromScanNum(self, scan_num):
        retention_time = self.xr.RTFromScanNum(scan_num)
        return retention_time

    def __getPrecursorMassFromScanNum(self, scan_num):
        precursor_mass = self.xr.GetPrecursorMassForScanNum(scan_num, c_long(2))
        return precursor_mass

    def __getScanTypeFromScanNum(self, scan_num):
        scan_type = self.xr.GetMSOrderForScanNum(scan_num)
        return scan_type

    """ Returns numpy.array containing precursor mass intensities for a specified scan number
    
        Keyword arguments:
        scan_num -- MS/MS scan number 
    """
    def __getPrecursorMassListFromScanNum(self, scan_num):
        #Get precursor_mass_list
        (precursor_mass_list, pl)    = self.xr.GetMassListFromScanNum(scan_num)
        precursor_masses_intensities = self.__formatMassList(precursor_mass_list)
        return precursor_masses_intensities

    def __formatMassList(self, mass_list):
        ## Mass      = mass_list[0]
        ## Intensity = mass_list[1]
        mass_list = zip(mass_list[0], mass_list[1])

        ## Remove all values with intensity of 0. We don't use them...
        f = lambda x: x[1] != 0
        mass_list = filter(f, mass_list)

        ## Create a numpy matrix containing rows of (mass, intensity) 
        masses_intensities = numpy.array(list(mass_list))
        return masses_intensities

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

