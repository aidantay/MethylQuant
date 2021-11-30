#--------------------------------------------------------------------------------------------------------------------

#This module contains IO-related classes and functions for reading files

#------------------ Dependencies ----------------------------#

# Standard library imports
import gc
import os
import re
from pathlib import Path

# External imports
import pandas as pd
import wx
import comtypes
from lxml import etree
from pymsfilereader import MSFileReader

# Internal imports
from .. import model

#------------------- Global Variables -----------------------#

#------------------ Classes & Functions ---------------------#

""" Sequenced peptides file reader
"""
class PeptidesReader():
    
    PROTEIN_COLUMN_NAME         = "Protein ID"
    PEPTIDE_COLUMN_NAME         = "Sequence"
    MODIFICATION_COLUMN_NAME    = "Modifications"
    CHARGE_COLUMN_NAME          = "Charge"
    DATA_FILE_COLUMN_NAME       = "Data File"
    START_SCAN_COLUMN_NAME      = "Start Scan"
    CALC_MZ_COLUMN_NAME         = "Calc m/z"
    MASS_DIFFERENCE_COLUMN_NAME = "Mass Difference"
    
    def __init__(self, seq_peptides_path):
        self.seq_peptides_path = Path(seq_peptides_path)
        self.init()

    def init(self):
        if (self.seq_peptides_path.suffix == '.csv'):
            reader = CsvReader(self.seq_peptides_path)

        elif (self.seq_peptides_path.suffix == '.mzIdentML'):
            reader   = MzIdentMlReader(self.seq_peptides_path)
            colNames = [self.PROTEIN_COLUMN_NAME, 
                        self.PEPTIDE_COLUMN_NAME, self.MODIFICATION_COLUMN_NAME,
                        self.CHARGE_COLUMN_NAME, self.DATA_FILE_COLUMN_NAME, 
                        self.START_SCAN_COLUMN_NAME, self.CALC_MZ_COLUMN_NAME]
            reader.seq_peptides_table.columns = colNames

        else:
            raise NotImplementedError("Invalid peptides file type")

        self.seq_peptides = reader.seq_peptides_table
        if (not self.hasHeader()):
            raise KeyError

        self.setHeaderIndices()

    def getColumns(self):
        return [x.lower() for x in self.seq_peptides.columns] 

    """ Check whether the file has a header row.
        The header row should have the required column names (as a minimum). 
        All other columns are optional.
        This shouldn't have an effect on mzIdentML files.
    """
    def hasHeader(self):
        columns = self.getColumns()
        if (self.PEPTIDE_COLUMN_NAME.lower() in columns and 
            self.MODIFICATION_COLUMN_NAME.lower() in columns and
            self.CHARGE_COLUMN_NAME.lower() in columns and
            self.DATA_FILE_COLUMN_NAME.lower() in columns and
            self.START_SCAN_COLUMN_NAME.lower() in columns and
            self.CALC_MZ_COLUMN_NAME.lower() in columns):
            return True
        
        return False

    """ Check whether the file has a 'Mass Difference' column. 
        The 'Mass Difference' column is optional 
    """    
    def hasMassDifferenceColumn(self):
        if self.MASS_DIFFERENCE_COLUMN_NAME.lower() in self.getColumns():
            return True
        return False

    """ Get all entries (.RAW files) listed in the 'Data File' column.
        The 'Data File' column is non-optional.
    """
    def getDataFiles(self):
        data_col_idx = self.getHeaderIndex(self.DATA_FILE_COLUMN_NAME)
        return set(self.seq_peptides.iloc[:, data_col_idx].unique().flatten())
 
    """ Get all sequenced peptides rows for a given .RAW file.
    """
    def getSortedRowsInRaw(self, raw_file):
        #get all rows in the sequenced peptides file that match to the raw file name and sort
        in_raw                     = self.seq_peptides.loc[:, self.DATA_FILE_COLUMN_NAME] == raw_file
        seq_peptides_in_raw        = self.seq_peptides.loc[in_raw]
        sorted_seq_peptides_in_raw = seq_peptides_in_raw.sort_values(self.START_SCAN_COLUMN_NAME, ascending=True)
        return sorted_seq_peptides_in_raw
 
    def getRowInfo(self, row):
        peptide_sequence = self.getPeptideSequenceValue(row)
        modifications    = self.getModificationValue(row)
        charge           = self.getChargeValue(row)
        calc_mz          = self.getCalcMzValue(row)
        start_scan       = self.getStartScanValue(row)        
        return (peptide_sequence, modifications, charge, calc_mz, start_scan)
    
    def setHeaderIndices(self):
        columns = self.getColumns()

        self.header_indices = {}
        self.header_indices[self.PEPTIDE_COLUMN_NAME]      = columns.index(self.PEPTIDE_COLUMN_NAME.lower())
        self.header_indices[self.MODIFICATION_COLUMN_NAME] = columns.index(self.MODIFICATION_COLUMN_NAME.lower())
        self.header_indices[self.CHARGE_COLUMN_NAME]       = columns.index(self.CHARGE_COLUMN_NAME.lower())
        self.header_indices[self.DATA_FILE_COLUMN_NAME]    = columns.index(self.DATA_FILE_COLUMN_NAME.lower())
        self.header_indices[self.START_SCAN_COLUMN_NAME]   = columns.index(self.START_SCAN_COLUMN_NAME.lower())
        self.header_indices[self.CALC_MZ_COLUMN_NAME]      = columns.index(self.CALC_MZ_COLUMN_NAME.lower())
        if self.hasMassDifferenceColumn():
            self.header_indices[self.MASS_DIFFERENCE_COLUMN_NAME] \
                = columns.index(self.MASS_DIFFERENCE_COLUMN_NAME.lower())

    def getHeaderIndex(self, column_name):
        return self.header_indices[column_name]

    def getPeptideSequenceValue(self, row):
        return row[self.getHeaderIndex(self.PEPTIDE_COLUMN_NAME)].upper()
    
    def getModificationValue(self, row):
        if not pd.isnull(row[self.getHeaderIndex(self.MODIFICATION_COLUMN_NAME)]):
            return row[self.getHeaderIndex(self.MODIFICATION_COLUMN_NAME)]
        return ""

    def getChargeValue(self, row):
        return int(row[self.getHeaderIndex(self.CHARGE_COLUMN_NAME)])
    
    def getStartScanValue(self, row):
        return int(row[self.getHeaderIndex(self.START_SCAN_COLUMN_NAME)])

    def getCalcMzValue(self, row):
        return float(row[self.getHeaderIndex(self.CALC_MZ_COLUMN_NAME)])

    def getMassDifferenceValue(self, row):
        return float(row[self.getHeaderIndex(self.MASS_DIFFERENCE_COLUMN_NAME)])

#########################################################################################################

""" Sequenced peptides file (.CSV) reader  
"""
class CsvReader(): 

    def __init__(self, seq_peptides_path):
        self.seq_peptides_path  = seq_peptides_path
        self.seq_peptides_table = pd.read_csv(self.seq_peptides_path)

#########################################################################################################

""" mzIdentML reader
"""
class MzIdentMlReader():
    
    SEQUENCE_COLLECTION_ELEMENT      = "SequenceCollection"
    DB_SEQUENCE_ELEMENT              = "DBSequence"
    PEPTIDE_ELEMENT                  = "Peptide"
    PEPTIDE_SEQUENCE_ELEMENT         = "PeptideSequence"
    MODIFICATION_ELEMENT             = "Modification"
    PEPTIDE_EVIDENCE_ELEMENT         = "PeptideEvidence"
    DATA_COLLECTION_ELEMENT          = "DataCollection"
    INPUTS_ELEMENT                   = "Inputs"
    SPECTRA_DATA_ELEMENT             = "SpectraData"    
    ANALYSIS_DATA_ELEMENT            = "AnalysisData"
    SPECTRUM_ID_LIST_ELEMENT         = "SpectrumIdentificationList"
    SPECTRUM_ID_RESULT_ELEMENT       = "SpectrumIdentificationResult"
    SPECTRUM_ID_ITEM_ELEMENT         = "SpectrumIdentificationItem"
    PEPTIDE_EVIDENCE_REF_ELEMENT     = "PeptideEvidenceRef"
    CV_PARAM_ELEMENT                 = "cvParam"
    
    ID_TAG                           = "id"
    ACCESSION_TAG                    = "accession"
    VALUE_TAG                        = "value"
    NAME_TAG                         = "name"
    DB_SEQUENCE_REF_TAG              = "dBSequence_ref"
    PEPTIDE_REF_TAG                  = "peptide_ref"
    SEQUENCE_REF_TAG                 = "sequence"
    MODIFICATION_REF_TAG             = "modification"
    RESIDUE_TAG                      = "residues"
    LOCATION_TAG                     = "location"
    SPECTRA_DATA_REF_TAG             = "spectraData_ref"
    SPECTRUM_ID_ITEM_REF_TAG         = "spectrumIdentificationItem_ref"
    CALC_MZ_TAG                      = "calculatedMassToCharge"
    CHARGE_TAG                       = "chargeState"
    PEPTIDE_EVIDENCE_REF_TAG         = "peptideEvidence_ref"
    
    CV_PROTEIN_DESCRIPTION_ACCESSION = "MS:1001088"
    CV_SCAN_ACESSION                 = "MS:1000796"
    CV_UNIMOD_ACCESSION              = "UNIMOD"

    def __init__(self, seq_peptides_path):
        self.seq_peptides_path = seq_peptides_path
        self.db_seq_table           = {}
        self.peptide_table          = {}
        self.peptide_evidence_table = {}
        self.spectra_data_table     = {}
        
        self.spectrum_result_table  = {}
        self.spectrum_item_table    = {}
        self.init()

    def init(self):
        tree           = etree.parse(self.seq_peptides_path)
        root           = tree.getroot()
        self.namespace = "{" + root.nsmap[None] + "}"
        self.parseRoot(root)
        
        peptides_table          = self.parseTables()
        self.seq_peptides_table = pd.DataFrame(peptides_table)

    def getElementTag(self, string):
        return self.namespace + string

    def putDbSeq(self, db_seq_id, db_seq_value):
        if (db_seq_id in self.db_seq_table):
            raise KeyError
        self.db_seq_table[db_seq_id] = db_seq_value

    def putPeptide(self, peptide_id, peptide_seq, modifications):
        if (peptide_id in self.peptide_table):
            raise KeyError
        self.peptide_table[peptide_id] = (peptide_seq, modifications)

    def putPeptideEvidence(self, peptide_evidence_id, db_seq_id, peptide_id):
        if (peptide_evidence_id in self.peptide_evidence_table):
            raise KeyError
        self.peptide_evidence_table[peptide_evidence_id] = (db_seq_id, peptide_id)

    def putSpectraData(self, spectra_data_id, spectra_data_location):
        if (spectra_data_id in self.spectra_data_table):
            raise KeyError
        self.spectra_data_table[spectra_data_id] = spectra_data_location

    def putSpectraResult(self, spectrum_result_id, spectra_data_id, scan_num):
        if (spectrum_result_id in self.spectrum_result_table):
            raise KeyError
        self.spectrum_result_table[spectrum_result_id] = (spectra_data_id, scan_num)

    def putSpectraItem(self, spectrum_item_id, calc_mz, charge, 
                       peptide_evidence_id):
        
        if (spectrum_item_id in self.spectrum_item_table):
            raise KeyError
        self.spectrum_item_table[spectrum_item_id] = (calc_mz, charge, peptide_evidence_id)

    def convertToSpectraResultId(self, spectrum_item_id):
        spectrum_result_id = re.sub('SII', 'SIR'  , spectrum_item_id)
        spectrum_result_id = re.sub('_[0-9]+$', '', spectrum_result_id)
        return spectrum_result_id

    def getSpectraDataValue(self, spectrum_item_id):
        spectrum_result_id          = self.convertToSpectraResultId(spectrum_item_id)        
        (spectra_data_id, scan_num) = self.spectrum_result_table[spectrum_result_id]        
        spectra_data_location       = self.spectra_data_table[spectra_data_id]
        return (spectra_data_location, scan_num)

    def getPeptideDataValue(self, peptide_evidence_id):
        (db_seq_id, peptide_id)      = self.peptide_evidence_table[peptide_evidence_id]        
        db_seq_value                 = self.db_seq_table[db_seq_id]
        (peptide_seq, modifications) = self.peptide_table[peptide_id]
        return (db_seq_value, peptide_seq, modifications)

    def parseRoot(self, root):
        seq_collection_element_tag = self.getElementTag(self.SEQUENCE_COLLECTION_ELEMENT)
        seq_collection_element = root.iter(seq_collection_element_tag).next()
        self.parseSequenceCollectionElement(seq_collection_element)

        data_collection_element_tag = self.getElementTag(self.DATA_COLLECTION_ELEMENT)
        data_collection_element = root.iter(data_collection_element_tag).next()
        self.parseDataCollectionElement(data_collection_element)
        
    def parseTables(self):
        peptides_table = []
        for spectrum_item_id in self.spectrum_item_table:
            (calc_mz, charge, peptide_evidence_id)     = self.spectrum_item_table[spectrum_item_id]
            (spectra_data_location, scan_num)          = self.getSpectraDataValue(spectrum_item_id)
            (db_seq_value, peptide_seq, modifications) = self.getPeptideDataValue(peptide_evidence_id)        
        
            row = [db_seq_value, peptide_seq, modifications, charge, spectra_data_location, scan_num, calc_mz]
            peptides_table.append(row)

        return peptides_table

    """ The following functions parses the SequenceCollection of the mzIdentML
    <SequenceCollection>
        <DBSequence id="DBSeq_1_RRF1_YEAST" searchDatabase_ref="SDB_Sprot" accession="RRF1_YEAST">
            <cvParam accession="MS:1001088" name="protein description" cvRef="PSI-MS" value="Ribosome-recycling factor, mitochondrial OS=Saccharomyces cerevisiae (strain ATCC 204508 / S288c) GN=RRF1 PE=1 SV=1"/>
        </DBSequence>    
        <Peptide id="peptide_844_2">
            <PeptideSequence>KDDAVR</PeptideSequence>
            <Modification location="1" residues="K" monoisotopicMassDelta="42.046950">
                <cvParam accession="UNIMOD:" name="Trimethyl" cvRef="UNIMOD" />
                <cvParam accession="MS:1001524" name="fragment neutral loss" cvRef="PSI-MS" value="0" unitAccession="UO:0000221" unitName="dalton" unitCvRef="UO" />
            </Modification>
        </Peptide>
        <PeptideEvidence id="PE_844_2_RRF1_YEAST_0_195_200" start="195" end="200" pre="K" post="K" peptide_ref="peptide_844_2" isDecoy="false" dBSequence_ref="DBSeq_1_RRF1_YEAST" />
    """
    def parseSequenceCollectionElement(self, seq_collection_element):
        db_seq_element_tag = self.getElementTag(self.DB_SEQUENCE_ELEMENT)
        for db_seq_element in seq_collection_element.iter(db_seq_element_tag):
            (db_seq_id, db_seq_value) = self.getDbSequenceInfo(db_seq_element)
            self.putDbSeq(db_seq_id, db_seq_value)
 
        peptide_element_tag = self.getElementTag(self.PEPTIDE_ELEMENT)
        for peptide_element in seq_collection_element.iter(peptide_element_tag):
            (peptide_id, peptide_seq, modifications) = self.getPeptideInfo(peptide_element)
            self.putPeptide(peptide_id, peptide_seq, modifications)

        peptide_evidence_element_tag = self.getElementTag(self.PEPTIDE_EVIDENCE_ELEMENT)
        for peptide_evidence_element in seq_collection_element.iter(peptide_evidence_element_tag):
            (peptide_evidence_id, db_seq_id, peptide_id) = self.getPeptideEvidenceInfo(peptide_evidence_element)
            self.putPeptideEvidence(peptide_evidence_id, db_seq_id, peptide_id)

    def getDbSequenceInfo(self, db_seq_element):
        db_seq_id      = db_seq_element.get(self.ID_TAG)
        cv_param_table = self.getCvParamInfo(db_seq_element)
        db_seq_value   = cv_param_table[self.CV_PROTEIN_DESCRIPTION_ACCESSION][0]    ## (value, name) pairs. DBSequence is in value
        return (db_seq_id, db_seq_value)
        
    def getPeptideInfo(self, peptide_element):
        peptide_id    = peptide_element.get(self.ID_TAG)
        peptide_seq   = self.getPeptideSequence(peptide_element)
        modifications = self.getModifications(peptide_element)
        return (peptide_id, peptide_seq, modifications)
    
    def getPeptideSequence(self, peptide_element):
        peptide_seq_element_tag = self.getElementTag(self.PEPTIDE_SEQUENCE_ELEMENT)
        peptide_seq_element     = peptide_element.iter(peptide_seq_element_tag).next()
        return peptide_seq_element.text
        
    def getModifications(self, peptide_element):
        mod_list        = []
        mod_element_tag = self.getElementTag(self.MODIFICATION_ELEMENT)
        for mod_element in peptide_element.iter(mod_element_tag):
            mod_info = self.getModificationInfo(mod_element)
            mod_list.append(mod_info)

        modifications = "; ".join(mod_list)
        return modifications
    
    def getModificationInfo(self, mod_element):
        mod_location   = mod_element.get(self.LOCATION_TAG)
        mod_residue    = mod_element.get(self.RESIDUE_TAG)
        cv_param_table = self.getCvParamInfo(mod_element)
        mod_type       = cv_param_table[self.CV_UNIMOD_ACCESSION][1]    ## (value, name) pairs. Modification is in name
        mod_info       = mod_residue + mod_location + "(" + mod_type + ")"
        return mod_info

    def getPeptideEvidenceInfo(self, peptide_evidence_element):
        peptide_evidence_id   = peptide_evidence_element.get(self.ID_TAG)
        db_seq_id            = peptide_evidence_element.get(self.DB_SEQUENCE_REF_TAG)
        peptide_id           = peptide_evidence_element.get(self.PEPTIDE_REF_TAG)
        return (peptide_evidence_id, db_seq_id, peptide_id)

    """ The following functions parses the DataCollection of the mzIdentML
        <DataCollection>
            <Inputs>..........</Inputs>
            <AnalysisData>..........</AnalysisData>
    """
    def parseDataCollectionElement(self, data_collection_element):
        inputs_element_tag = self.getElementTag(self.INPUTS_ELEMENT)
        inputs_element    = data_collection_element.iter(inputs_element_tag).next()
        self.parseInputsElement(inputs_element)

        analysis_data_element_tag = self.getElementTag(self.ANALYSIS_DATA_ELEMENT)
        analysis_data_element    = data_collection_element.iter(analysis_data_element_tag).next()
        self.parseAnalysisDataElement(analysis_data_element)

    def parseInputsElement(self, inputs_element):
        spectra_data_element_tag = self.getElementTag(self.SPECTRA_DATA_ELEMENT)
        for spectra_data_element in inputs_element.iter(spectra_data_element_tag):
            (spectra_data_id, spectra_data_location) = self.getSpectraInfo(spectra_data_element)
            self.putSpectraData(spectra_data_id, spectra_data_location)

    def getSpectraInfo(self, spectra_data_element):
        spectra_data_id       = spectra_data_element.get(self.ID_TAG)
        spectra_data_location = spectra_data_element.get(self.LOCATION_TAG)

        spectra_data_location = os.path.basename(spectra_data_location)           ## Get the file name
        spectra_data_location = re.sub('.* ', '', spectra_data_location)          ## Format file string. As a slight workaround for heterogeneous names, remove everything before the last whitespace 
        return (spectra_data_id, spectra_data_location)

    def parseAnalysisDataElement(self, analysisDataElement):
        spectrum_id_list_element_tag = self.getElementTag(self.SPECTRUM_ID_LIST_ELEMENT)
        spectrum_id_list_element     = analysisDataElement.iter(spectrum_id_list_element_tag).next()
        self.parseSpectrumIdListElement(spectrum_id_list_element)

    """ The following functions parses the SpectrumIdentificationList in DataCollection of the mzIdentML
        <SpectrumIdentificationList id="SIL_1" numSequencesSearched="7900">
            <FragmentationTable>..........</FragmentationTable>
            <SpectrumIdentificationResult id="SIR_3" spectrumID="index=43356" spectraData_ref="SD_1">
                <SpectrumIdentificationItem id="SII_3_1" calculatedMassToCharge="350.192846" chargeState="2" experimentalMassToCharge="350.19263" peptide_ref="peptide_3_1" rank="1" passThreshold="true">
                    <PeptideEvidenceRef peptideEvidence_ref="PE_3_1_RUVB2_YEAST_0_148_154"/>
                    <cvParam accession="MS:1001171" name="Mascot:score" cvRef="PSI-MS" value="23.86"/>
                    <cvParam accession="MS:1001172" name="Mascot:expectation value" cvRef="PSI-MS" value="0.0123344916331357"/>
                    <cvParam accession="MS:1001363" name="peptide unique to one protein" cvRef="PSI-MS"/>    

                <cvParam accession="MS:1001371" name="Mascot:identity threshold" cvRef="PSI-MS" value="17"/>
                <cvParam accession="MS:1001030" name="number of peptide seqs compared to each spectrum" cvRef="PSI-MS" value="60"/>
                <cvParam accession="MS:1000796" name="spectrum title" cvRef="PSI-MS" value="Spectrum43447 scans:1916,"/>
    """
    def parseSpectrumIdListElement(self, spectrum_id_list_element):
        spectrum_id_result_element_tag = self.getElementTag(self.SPECTRUM_ID_RESULT_ELEMENT)        
        for spectrum_id_result_element in spectrum_id_list_element.iter(spectrum_id_result_element_tag):
            (spectrum_result_id, spectra_data_id, scan_num) = self.getSpectrumIdResultInfo(spectrum_id_result_element)            
            self.putSpectraResult(spectrum_result_id, spectra_data_id, scan_num)
            
            self.parseSpectrumIdResultElement(spectrum_id_result_element)

    def getSpectrumIdResultInfo(self, spectrum_id_result_element):
        spectrum_result_id   = spectrum_id_result_element.get(self.ID_TAG)
        spectra_data_id      = spectrum_id_result_element.get(self.SPECTRA_DATA_REF_TAG)
        cv_param_table       = self.getCvParamInfo(spectrum_id_result_element)
        scan_num             = cv_param_table[self.CV_SCAN_ACESSION][0]           ## (value, name) pairs. Scan number is in value
        scan_num             = re.sub('.* scans:(.*),', '\\1', scan_num)          ## Format scan number string
        return (spectrum_result_id, spectra_data_id, scan_num)

    def parseSpectrumIdResultElement(self, spectrum_id_result_element):
        spectrum_id_item_element_tag = self.getElementTag(self.SPECTRUM_ID_ITEM_ELEMENT)        
        for spectrum_id_item_element in spectrum_id_result_element.iter(spectrum_id_item_element_tag):
            (spectrum_item_id, calc_mz, charge, peptide_evidence_id) = self.getSpectrumIdItemInfo(spectrum_id_item_element)
            self.putSpectraItem(spectrum_item_id, calc_mz, charge, peptide_evidence_id)

    def getSpectrumIdItemInfo(self, spectrum_id_item_element):
        spectrum_item_id     = spectrum_id_item_element.get(self.ID_TAG)
        calc_mz             = spectrum_id_item_element.get(self.CALC_MZ_TAG)
        charge               = spectrum_id_item_element.get(self.CHARGE_TAG)
        peptide_evidence_id  = self.getPeptideEvidenceRef(spectrum_id_item_element)
        return (spectrum_item_id, calc_mz, charge, peptide_evidence_id)

    def getPeptideEvidenceRef(self, spectrum_id_item_element):
        peptide_evidence_ref_element_tag = self.getElementTag(self.PEPTIDE_EVIDENCE_REF_ELEMENT)        
        peptide_evidence_ref_element     = spectrum_id_item_element.iter(peptide_evidence_ref_element_tag).next()
        return peptide_evidence_ref_element.get(self.PEPTIDE_EVIDENCE_REF_TAG)

    """ The following function parses any cvParam elements in the mzIdentML.
        These are typically nested within a parent element
    """
    def getCvParamInfo(self, parent_element):
        cv_param_table       = {}
        cv_param_element_tag = self.getElementTag(self.CV_PARAM_ELEMENT)
        for cv_param_element in parent_element.iter(cv_param_element_tag):
            accession = self.getCvParamAccession(cv_param_element)
            value     = cv_param_element.get(self.VALUE_TAG)
            name      = cv_param_element.get(self.NAME_TAG)            
            cv_param_table[accession] = (value, name)
        return cv_param_table
        
    def getCvParamAccession(self, cv_param_element):
        accession = cv_param_element.get(self.ACCESSION_TAG)
        if (re.match(self.CV_UNIMOD_ACCESSION, accession)):
            accession = self.CV_UNIMOD_ACCESSION
        return accession

#########################################################################################################

""" Raw file (.RAW) reader
"""
class RawReader():
    
    def __init__(self, raw_file, raw_dirs):
        #check raw file name format for consistency
        assert(".raw" in raw_file)
        raw_path = self.getRawPath(raw_file, raw_dirs)
        xr       = MSFileReader(raw_path)

        self.raw_file = raw_file
        self.xr_info  = model.XrInfo(xr)

    def getRawPath(self, raw_file, raw_dirs):
        '''There is a slight problem with this (when there's multiple RAW directories with the same RAW file names). 
           For now, this is OK. But I suspect we need to restructure the interface to accommodate for this. 
           * Possibly only allow 1 directory to be searched
        '''
        f = lambda x: raw_file in raw_dirs[x]
        raw_dir  = list(filter(f, raw_dirs.keys()))[0]  #get the first RAW file directory we encounter
        raw_path = raw_dir + "\\" + raw_file            #construct absolute path to raw file
        return raw_path

    def closeRawReader(self):
        gc.collect()                #garbage collect unnecessary memory usage
        self.xr_info.xr.close()
