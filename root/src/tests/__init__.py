#--------------------------------------------------------------------------------------------------------------------

#This module contains classes for testing MethylQuant functionality

#------------------ Dependencies ----------------------------#

## External dependencies
import unittest
import os
import pandas
import filecmp

## Internal dependencies
from mq.io.reader import PeptidesReader, RawReader, MzIdentMlReader
from mq.io.writer import CsvWriter
from mq.model.core import MassShifts
from mq.model.menu import DEFAULT_LABEL_LIST, DEFAULT_MOD_LIST
from mq.task.experiment import CorrelationTask
import mq.task as mqt

#------------------- Global Variables -----------------------#

DIR_PATH          = os.path.dirname(os.path.realpath(__file__)) + "\\.test_files"
RAW_FILE_PATH     = DIR_PATH + "\\" + "raw"

PEPTIDE_FILE_PATH_1 = DIR_PATH + "\\" + "test_file_01.csv"
PEPTIDE_FILE_PATH_2 = DIR_PATH + "\\" + "test_file_02.csv"
PEPTIDE_FILE_PATH_3 = DIR_PATH + "\\" + "test_file_03.csv"
PEPTIDE_FILE_PATH_4 = DIR_PATH + "\\" + "test_file_04.csv"
PEPTIDE_FILE_PATH_5 = DIR_PATH + "\\" + "test_file_05.csv"
PEPTIDE_FILE_PATH_6 = DIR_PATH + "\\" + "test_file_06.csv"
PEPTIDE_FILE_PATH_7 = DIR_PATH + "\\" + "nostaingels_orbi_metK.mzid" 

#------------------ Classes & Functions ---------------------#
""" Class for testing functionality of PeptideReader
"""
class TestPeptideReader(unittest.TestCase):
    
    def testInit(self):
        self.mzIdent_reader = PeptidesReader(PEPTIDE_FILE_PATH_7)

        self.assertRaises(KeyError, lambda: PeptidesReader(PEPTIDE_FILE_PATH_1))
        try:
            PeptidesReader(PEPTIDE_FILE_PATH_2)
            PeptidesReader(PEPTIDE_FILE_PATH_3)
 
        except Exception:
            self.fail()

    def testHeaderIndexes(self):
        csv_reader = PeptidesReader(PEPTIDE_FILE_PATH_2)
        row        = csv_reader.seq_peptides.iloc[0]
        (peptide_seq, modifications, charge, calc_mz, start_scan) = csv_reader.getRowInfo(row)
  
        self.assertEquals(start_scan, 16154)
        self.assertEquals(calc_mz, 986.99609)
        self.assertEquals(peptide_seq, 'AANLGGVAVSGLEMAQNSQR')
        self.assertEquals(modifications, '')
        self.assertEquals(charge, 2)
 
    def testSequencedPeptidesInRaw(self):
        csv_reader       = PeptidesReader(PEPTIDE_FILE_PATH_3)        
        raw_files_in_csv = csv_reader.getDataFiles()
        total = 0
  
        for raw_file in raw_files_in_csv:
            sorted_seq_peptides_in_raw = csv_reader.getSortedRowsInRaw(raw_file)
            total = total + len(sorted_seq_peptides_in_raw)
  
        self.assertEquals(total, len(csv_reader.seq_peptides)) 

#########################################################################################################

""" Class for testing functionality of a CsvWriter   
"""
class TestCsvWriter(unittest.TestCase):

    def testInit(self):
        exp_path = DIR_PATH + "\\" + "test_file_03_MethylQuant.csv"

        seq_peptides_reader = PeptidesReader(PEPTIDE_FILE_PATH_3)
        seq_peptides_writer = CsvWriter(PEPTIDE_FILE_PATH_3)
        seq_peptides_writer.writeFile(seq_peptides_reader.seq_peptides)
        
        self.assertTrue(filecmp.cmp(PEPTIDE_FILE_PATH_3, exp_path))

#########################################################################################################

""" Class for testing calculations for mass shift and peptide isotopes   
"""
class TestMassCalculations(unittest.TestCase):

    def setUp(self):
        self.label_set   = set([(DEFAULT_LABEL_LIST[0][1], DEFAULT_LABEL_LIST[0][2])])
        self.mod_set     = set(DEFAULT_MOD_LIST)
        self.mass_shifts = MassShifts(self.label_set, self.mod_set)

        self.seq_peptides_reader = PeptidesReader(PEPTIDE_FILE_PATH_3)        
        self.seq_peptides_in_raw = self.seq_peptides_reader.seq_peptides

    def testMassShift(self):
        for row_idx, row in self.seq_peptides_in_raw.iterrows():
            (peptide_sequence, modifications, charge, calc_mz, start_scan) \
                            = self.seq_peptides_reader.getRowInfo(row)

            exp_mass_shift  = row['Mass Difference']
            calc_mass_shift = mqt.calculateMassShift(peptide_sequence, modifications, charge, 
                                                     1, self.mass_shifts)

            self.assertAlmostEqual(exp_mass_shift, calc_mass_shift)

    def testIsotopesMases(self):
        precursor_masses      = [986.99609, 986.99609, 466.73138, 641.87811, 400.74695, 830.12988]
   
        for row_idx, row in self.seq_peptides_in_raw.iterrows():
            (peptide_sequence, modifications, charge, calc_mz, start_scan) \
                            = self.seq_peptides_reader.getRowInfo(row)

            mass_shift     = row['Mass Difference']
            precursor_mass = precursor_masses[row_idx]
            peptide_isotope_masses = mqt.calculatePeptideIsotopeMasses(precursor_mass, charge, calc_mz, mass_shift)
            
            #Check that we have 2 sets of peptide isotope masses (for Light and Heavy)
            self.assertTrue(len(peptide_isotope_masses) == 2)
                    
            #separate the light and heavy isotope masses
            self.assertTrue(len(peptide_isotope_masses[0]) == 3)
            self.assertTrue(len(peptide_isotope_masses[1]) == 3)

#########################################################################################################

""" Class for testing functionality of a RawReader
    Unfortunately, this test WILL NOT WORK without the proper raw file...
    Which are too big to upload into the repository
"""
class TestRawReader(unittest.TestCase):
    
    def setUp(self):
        self.raw_file = '3to1_rpt_qexactive_11.raw'
        self.raw_dirs = {}
        self.raw_dirs[RAW_FILE_PATH] = set([self.raw_file])        
    
    def testInit(self):
        #get a XR object containing all the RAW file information
        raw_reader = RawReader(self.raw_file, self.raw_dirs)
        
        xr_info    = raw_reader.xr_info
        self.assertEqual(xr_info.getNumSpectra(), 21821)

#########################################################################################################

""" Class for testing calculations for MethylQuant Confidence and MethylQuant Score   
"""
class TestConfidenceCalculations(unittest.TestCase):

    def setUp(self):
        self.task = CorrelationTask(None, None, None, None, None, None, None)

    def checkScore(self, isotope_correlation, isotope_H_to_L_ratio, 
                   elution_correlation_count, elution_H_to_L_ratio,
                   exp_score):
        calc_score = self.task.calculateMethylQuantScore(isotope_correlation, 
                                                         isotope_H_to_L_ratio, 
                                                         elution_correlation_count, 
                                                         elution_H_to_L_ratio)
        self.assertAlmostEqual(calc_score, exp_score)

    def checkConfidence(self, isotope_correlation, isotope_H_to_L_ratio, 
                        elution_correlation_count, elution_H_to_L_ratio,
                        exp_confidence):
        calc_confidence = self.task.calculateMethylQuantConfidence(isotope_correlation, 
                                                                   isotope_H_to_L_ratio, 
                                                                   elution_correlation_count, 
                                                                   elution_H_to_L_ratio)
        self.assertEqual(calc_confidence, exp_confidence)        

    def testScoreConfidence(self):
        isotope_correlation_list       = ['NA' , -0.9999851553,         'NA', 0.9999999994,  0.999586079,  0.996150963, 0.923886253]
        isotope_H_to_L_ratio_list      = ['NA' ,  0.0829385229,         'NA', 0.4802811623,  0.201447525,  0.230766806, 0.43755239]
        elution_correlation_count_list = [0    ,             0,            1,            3,            3,            3, 2]
        elution_H_to_L_ratio_list      = ['NA' ,          'NA', 0.0008943356, 0.4842563636,  0.203510655,  0.226031095, 0.368289828]
        exp_score_list                 = [0    ,             0,            0, 49.0855525298, 49.08528309,  49.08304402, 44.61194669]
        exp_confidence_list            = ['Low',         'Low',        'Low',   'Very High', 'Very High',  'Very High', 'High']

        for i in range(0, len(isotope_correlation_list)):
            isotope_correlation       = isotope_correlation_list[i]
            isotope_H_to_L_ratio      = isotope_H_to_L_ratio_list[i]
            elution_correlation_count = elution_correlation_count_list[i]
            elution_H_to_L_ratio      = elution_H_to_L_ratio_list[i]
            exp_score                 = exp_score_list[i]
            exp_confidence            = exp_confidence_list[i]

            self.checkScore(isotope_correlation, isotope_H_to_L_ratio, 
                            elution_correlation_count, elution_H_to_L_ratio,
                            exp_score)
        
            self.checkConfidence(isotope_correlation, isotope_H_to_L_ratio, 
                                 elution_correlation_count, elution_H_to_L_ratio,
                                 exp_confidence)
