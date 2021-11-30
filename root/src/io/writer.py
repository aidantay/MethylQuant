#--------------------------------------------------------------------------------------------------------------------

#This module contains IO-related classes and functions for writing files

#------------------ Dependencies ----------------------------#

## External dependencies
import os

## Internal dependencies

#------------------- Global Variables -----------------------#

#------------------ Classes & Functions ---------------------#

""" Sequenced peptides file (.CSV) writer  
"""
class CsvWriter():
    
    def __init__(self, seq_peptides_path):
        #generate the file name for the output file
        input_dir        = os.path.dirname(seq_peptides_path)
        input_name       = os.path.basename(seq_peptides_path).split('.')[0]     #get basename without the file extension
        output_name      = input_name + "_MethylQuant.csv"
        self.output_path = os.path.join(input_dir, output_name)

        output_filehandle = open(self.output_path, "w")
        output_filehandle.close()

    def writeFile(self, matched_seq_peptides):
        # If the file is empty, then write with header
        if os.path.getsize(self.output_path) == 0:
            matched_seq_peptides.to_csv(self.output_path, index=False)
            
        # otherwise, append without header
        else:
            matched_seq_peptides.to_csv(self.output_path, mode='a', index=False, header=False)

#########################################################################################################
