#--------------------------------------------------------------------------------------------------------------------

#This module contains task-related classes and functions for MethylQuant experiments

#------------------ Dependencies ----------------------------#

# Standard library imports
import math
import os

# External imports
import pandas
from pubsub import pub

# Internal imports
from ..io.reader import PeptidesReader
from ..io.reader import RawReader
from ..io.writer import CsvWriter
from ..view.constants import *
from .correlation import IsotopeCorrelationTask
from .correlation import ElutionCorrelationTask
from .constants import *
from .common import *

#------------------ Global Variables ------------------------#

MQ_VERY_HIGH_CONFIDENCE = 'Very High'
MQ_HIGH_CONFIDENCE      = 'High'
MQ_LOW_CONFIDENCE       = 'Low'

#------------------ Classes & Functions ---------------------#

class ExperimentTask():

    def __init__(self, experiment):
        self.file_info   = experiment.file_info
        self.mass_shifts = experiment.mass_shifts
        self.parameters  = experiment.parameters

    def initGauge(self, seq_peptides_reader):
        #reset the gauge (progress bar) 
        pub.sendMessage(UPDATE_GAUGE_LISTENER, filled=False)
        pub.sendMessage(UPDATE_GAUGE_STEPSIZE_LISTENER, seq_peptides_reader=seq_peptides_reader)
        
    def initStatus(self, seq_peptides_path):
        #update the status text
        file_path   = seq_peptides_path.split("\\")[0]
        file_path   = file_path + "\\...\\" + os.path.basename(seq_peptides_path)    
        status_text = "Processing %s" % (file_path)
        pub.sendMessage(UPDATE_STATUS_LISTENER, status_box_id=0, status_text=status_text)
        pub.sendMessage(UPDATE_STATUS_LISTENER, status_box_id=1, status_text="")
        
    def updateProgress(self, peptide_seq, raw_file):
        #update gauge (progress bar) and status text
        status_text = "Searching for %s in %s" % (peptide_seq, raw_file)
        pub.sendMessage(INCREMENT_GAUGE_LISTENER)
        pub.sendMessage(UPDATE_STATUS_LISTENER, status_box_id=1, status_text=status_text)

    def run(self):
        for seq_peptides_path in self.file_info.getPeptideFiles():
            self.raw_dir_map        = self.file_info.raw_dir_map
            self.silac_type         = self.file_info.silac_map[seq_peptides_path]
            self.output_style       = self.file_info.output_map[seq_peptides_path]
            self.default_mass_shift = self.mass_shifts.isDefault()

            #------------------ This is the heart of MethylQuant ----------------------------#
            self.identifyPairsInCsv(seq_peptides_path)

            #due to calculations with floating point numbers, 
            #the task will finish before the gauge (progress bar) gets to the end. 
            #this (attempts to) ensure that they occur simultaneously
            pub.sendMessage(UPDATE_GAUGE_LISTENER, filled=True)

    """ Begin quantification on a given CSV file
       
        NOTE: There is an issue where if we have multiple CSV files 
        that are using information from the same RAW file/s.
        Due to memory and run-time efficiency, we can't really avoid this....
        
        Keyword arguments:
        seq_peptides_path -- File path of CSV file 
        raw_dirs          -- Map of file paths to each MS raw files
        labelling         -- Labelling used as defined by user
        silac_type        -- Light or heavy peptide sequenced
    """
    def identifyPairsInCsv(self, seq_peptides_path):
        #parse sequenced peptides file and create the output table for results
        #reading the file SHOULD NOT error. 
        #We already checked for this when the user inputs their files
        seq_peptides_reader = PeptidesReader(seq_peptides_path)
        seq_peptides_writer = CsvWriter(seq_peptides_path)

        #send intialisation messages to status and gauge panels
        self.initGauge(seq_peptides_reader)
        self.initStatus(seq_peptides_path)

        #iterate through the list of all raw files in the sequenced peptides file
        raw_files_in_csv = seq_peptides_reader.getDataFiles()
        for raw_file in sorted(raw_files_in_csv):
            #get a XR object containing all the RAW file information
            raw_reader = RawReader(raw_file, self.raw_dir_map)

            # Find matched peptides and write the results for a RAW to file 
            # This is based on original sequenced peptides file, just with extra columns
            matched_seq_peptides_in_raw = self.identifyPairsInRaw(seq_peptides_reader, raw_reader)
            seq_peptides_writer.writeFile(matched_seq_peptides_in_raw)

            # #since we are done with xr_info, close it
            # raw_reader.closeRawReader()

    """ Search for SILAC pairs in subsets of the sequenced peptides file.
        These are based on the peptides that are in a specified RAW file
        
        Keyword arguments:
        seq_peptides_reader -- File path of CSV file 
        raw_file            -- Raw file that we want to look into
        xr_info             -- XR object containing all information for a specified RAW file    
        labelling           -- Labelling used as defined by user
        silac_type          -- Light or heavy peptide sequenced
    """
    def identifyPairsInRaw(self, seq_peptides_reader, raw_reader):
        #Reset indexes so that we can join the tables correctly
        sorted_seq_peptides_in_raw       = seq_peptides_reader.getSortedRowsInRaw(raw_reader.raw_file)
        sorted_seq_peptides_in_raw.index = range(len(sorted_seq_peptides_in_raw))
        matched_table                    = pandas.DataFrame()

        for row_idx, row in sorted_seq_peptides_in_raw.iterrows():
            (peptide_seq, modifications, charge, calc_mz, start_scan) \
                                      = seq_peptides_reader.getRowInfo(row)             
            mass_shift                = self.getMassShift(seq_peptides_reader, row, 
                                                          peptide_seq, modifications, charge)
            (RT_MSMS, precursor_mass) = self.getScanTuple(raw_reader.xr_info, start_scan)

            #calculate expected set of isotope masses for light and heavy peptides
            #we only calculate 3 isotope masses for light and heavy peptides
            peptide_isotope_masses = calculatePeptideIsotopeMasses(precursor_mass, charge, 
                                                                       calc_mz, mass_shift)

            #Inform the user about what is happening and begin finding pairs 
            self.updateProgress(peptide_seq, raw_reader.raw_file)
            matched_row   = self.identifyPair(raw_reader.xr_info, start_scan, 
                                              RT_MSMS, peptide_isotope_masses)
            matched_row.insert(0, MASS_DIFFERENCE_COLUMN_NAME, mass_shift)
            matched_table = matched_table.append(matched_row)
 
        return self.rearrangeOutput(seq_peptides_reader, sorted_seq_peptides_in_raw, matched_table)
    
    """ Search for SILAC pair for peptide
        
        Keyword arguments:   
        raw_file         -- Raw file that we want to look into
        xr_info          -- XR object containing all information for a specified RAW file
        peptide_sequence -- Peptide sequence
        charge           -- Charge of sequenced peptide
        calc_mz          -- Calculated m/z of sequenced peptide
        start_scan       -- Start scan number of sequenced peptide
        mass_shift       -- Expected mass shift of sequenced peptide
    """
    def identifyPair(self, xr_info, MS_MS_scan_num, RT_MSMS, peptide_isotope_masses):
        correlation_task = CorrelationTask(self.parameters, self.output_style, self.default_mass_shift,
                                           xr_info, MS_MS_scan_num, RT_MSMS, peptide_isotope_masses)
        correlation_task.run()
        return correlation_task.outputRow

    def getMassShift(self, seq_peptides_reader, row, peptide_seq, modifications, charge):
        try:
            mass_shift = seq_peptides_reader.getMassDifferenceValue(row)
            #if we have the column but there's no value, then calculate for us
            if pandas.isnull(mass_shift):
                mass_shift = calculateMassShift(peptide_seq, modifications, charge, 
                                                    self.silac_type, self.mass_shifts)
          
        except KeyError:
            mass_shift = calculateMassShift(peptide_seq, modifications, charge,
                                                self.silac_type, self.mass_shifts)
        return mass_shift

    def getScanTuple(self, xr_info, MS_MS_scan_num):
        RT_MSMS        = xr_info.getScanInfo(MS_MS_scan_num).getRT()
        precursor_mass = xr_info.getScanInfo(MS_MS_scan_num).getPrecursorMass()
        return (RT_MSMS, precursor_mass)
    
    def rearrangeOutput(self, seq_peptides_reader, sorted_seq_peptides_in_raw, matched_table):
        #Reset indexes so that the tables can be joined correctly
        matched_table.index = range(len(matched_table))
        if seq_peptides_reader.hasMassDifferenceColumn():
            matched_table = matched_table.drop(MASS_DIFFERENCE_COLUMN_NAME, axis=1)
  
        matched_seq_peptides_in_raw = sorted_seq_peptides_in_raw.join(matched_table)
        return matched_seq_peptides_in_raw

#########################################################################################################

class CorrelationTask():
    
    def __init__(self, parameters, output_style, default_mass_shift, 
                 xr_info, MS_MS_scan_num, RT_MSMS, peptide_isotope_masses):
        self.parameters             = parameters
        self.output_style           = output_style
        self.default_mass_shifts    = default_mass_shift
        self.xr_info                = xr_info
        self.MS_MS_scan_num         = MS_MS_scan_num
        self.RT_MSMS                = RT_MSMS
        self.peptide_isotope_masses = peptide_isotope_masses
        
    def run(self):
        ## Run the original algorithm by Vincent
        isotope_correlation_task \
            = IsotopeCorrelationTask(self.parameters, self.xr_info, self.MS_MS_scan_num, 
                                     self.RT_MSMS, self.peptide_isotope_masses)
        isotope_correlation_task.runTask()

        ## Run the updated algorithm by Aidan
        elution_correlation_task \
            = ElutionCorrelationTask(self.parameters, self.xr_info, self.MS_MS_scan_num, 
                                     self.RT_MSMS, self.peptide_isotope_masses)
        elution_correlation_task.runTask()
 
        self.formatRow(isotope_correlation_task.outputRow, elution_correlation_task.outputRow)

    def formatRow(self, isotope_correlation_row, elution_correlation_row):
        isotope_correlation       = isotope_correlation_row.iloc[0][ISOTOPE_CORRELATION_COLUMN_NAME]
        isotope_H_to_L_ratio      = isotope_correlation_row.iloc[0][H_L_RATIO_COLUMN_NAME + ' #1']
        elution_correlation_count = elution_correlation_row.iloc[0][ELUTION_COUNT_COLUMN_NAME]
        elution_H_to_L_ratio      = elution_correlation_row.iloc[0][H_L_RATIO_COLUMN_NAME + ' #2']
        
        mq_score \
            = self.calculateMethylQuantScore(isotope_correlation, isotope_H_to_L_ratio,
                                             elution_correlation_count, elution_H_to_L_ratio)

        mq_confidence \
            = self.calculateMethylQuantConfidence(isotope_correlation, isotope_H_to_L_ratio,
                                                  elution_correlation_count, elution_H_to_L_ratio)
        
        self.outputRow = isotope_correlation_row.join(elution_correlation_row, 
                                                      lsuffix=' IsotopeCorrelation', 
                                                      rsuffix=' ElutionCorrelation')
 
        self.outputRow.insert(len(self.outputRow.columns), MQ_SCORE_COLUMN_NAME, mq_score)        
        self.outputRow.insert(len(self.outputRow.columns), MQ_CONFIDENCE_COLUMN_NAME, mq_confidence)
        if (self.output_style == ID_SUMMARY):
            correlation_columns = [ISOTOPE_CORRELATION_COLUMN_NAME, ELUTION_COUNT_COLUMN_NAME, 
                                   H_L_RATIO_COLUMN_NAME + ' #1', H_L_RATIO_COLUMN_NAME + ' #2',
                                   MQ_SCORE_COLUMN_NAME, MQ_CONFIDENCE_COLUMN_NAME]
            self.outputRow = self.outputRow.loc[:, correlation_columns]

    def calculateMethylQuantScore(self, isotope_correlation, isotope_H_to_L_ratio,
                                  elution_correlation_count, elution_H_to_L_ratio):
        
        if (isotope_correlation != 'NA' and elution_correlation_count != 0):
            multiplier = 0
            if (isotope_H_to_L_ratio != 'NA' and elution_H_to_L_ratio != 'NA'):
                multiplier = 1
    
            top = -3.399 + (0.725*isotope_correlation) \
                  + (1.814*elution_correlation_count) + (1.215*multiplier)
            top = math.exp(top)
    
            bottom = -3.399 + (0.725*isotope_correlation) \
                     + (1.814*elution_correlation_count) + (1.215*multiplier)
            bottom = 1 + math.exp(bottom)
            return (top / bottom) * 50
        return 0

    def calculateMethylQuantConfidence(self, isotope_correlation, isotope_H_to_L_ratio,
                                       elution_correlation_count, elution_H_to_L_ratio):

        if (isotope_H_to_L_ratio != 'NA' and elution_H_to_L_ratio != 'NA'):
            # We could probably use this as a user-defined threshold for simplicity
            # with the default for methylSILAC as 0.06
            if (self.default_mass_shifts and isotope_H_to_L_ratio >= 0.06):
                return self.getConfidenceLevel(isotope_correlation, elution_correlation_count)
            
            else:
                # What do we do if we are not using default mass shifts?
                return self.getConfidenceLevel(isotope_correlation, elution_correlation_count)
        
        return MQ_LOW_CONFIDENCE

    def getConfidenceLevel(self, isotope_correlation, elution_correlation_count):
        if (self.isVeryHighConfidence(isotope_correlation, elution_correlation_count)):
            return MQ_VERY_HIGH_CONFIDENCE
        
        elif (self.isHighConfidence(isotope_correlation, elution_correlation_count)):
            return MQ_HIGH_CONFIDENCE
        
        return MQ_LOW_CONFIDENCE

    def isVeryHighConfidence(self, isotope_correlation, elution_correlation_count):
        if (isotope_correlation >= 0.99 and elution_correlation_count == 3):
            return True

        return False
        
    def isHighConfidence(self, isotope_correlation, elution_correlation_count):
        if (isotope_correlation >= 0.75 and elution_correlation_count >= 2):
            return True

        return False
        
#########################################################################################################

