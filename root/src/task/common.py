#--------------------------------------------------------------------------------------------------------------------

#This module contains task-related classes and functions

#------------------ Dependencies ----------------------------#

## External dependencies
import numpy
from scipy.stats.stats import pearsonr
 
## Internal dependencies

#------------------ Global Variables ------------------------#

ISOTOPE_MASS_ERROR_BOUNDARY_TABLE = {}
PPM                               = 1000000.0

MASS_DIFFERENCE_COLUMN_NAME     = 'Mass Difference'
ISOTOPE_CORRELATION_COLUMN_NAME = 'Isotope Distribution Correlation'
H_L_RATIO_COLUMN_NAME           = 'H/L Ratio'
ELUTION_CORRELATION_COLUMN_NAME = 'Elution Profile Correlation'
ELUTION_COUNT_COLUMN_NAME       = '# Good Elution Profile Correlations' 
MQ_CONFIDENCE_COLUMN_NAME       = 'MethylQuant Confidence'
MQ_SCORE_COLUMN_NAME            = 'MethylQuant Score'

#------------------ Classes & Functions ---------------------#

""" Returns expected mass difference between light and heavy methylSILAC partners 
  
    This is based on the number of Methionine(M) residues in the peptide sequence
  
    Keyword arguments:
    peptide_sequence -- Amino acid sequence of peptide from MS/MS searches
    modifications    -- Modifications identified on the peptide
    charge           -- Charge state of peptide
    labelling        -- Labelling
    silac_type       -- Light or heavy peptide sequenced
"""
def calculateMassShift(peptide_seq, modifications, charge, silac_type, mass_shifts):
    #adjust the expected mass shift based on the mass of the labels
    #adjust the expected mass shift based on the modifications that contribute to the mass shift
    expected_mass_shift = (mass_shifts.calculateMassShiftForLabels(peptide_seq) +
                           mass_shifts.calculateMassShiftForModifications(modifications)) 
    
    #adjust the expected mass shift based on the silac type
    #adjust the expected mass shift based on the peptide charge
    expected_mass_shift = (expected_mass_shift * silac_type) / float(charge)
    return expected_mass_shift

#########################################################################################################

""" Returns list of masses corresponding to isotope envelops of light and heavy methylSILAC partners 
  
    This is a list of 3 light and 3 heavy peaks based on a given mass shift
  
    Keyword arguments:
    precursor_mass       -- Precursor mass for a given scan
    calc_mz_pipeline     -- Calculated m/z value for a peptide
    charge               -- Charge state of peptide
    mz_shift_for_partner -- Mass difference between light and heavy methylSILAC partners
"""    
def calculatePeptideIsotopeMasses(precursor_mass, charge, calc_mz, mz_shift_for_partner):
    #Carbon 13 = +1.00335
    #calculate the minimum difference between the isotope peaks for the peptide
    isotope_states_mass_difference = 1.00335/charge
  
    #determine difference between exp and calc mz, then see how many times isotope state
    #mass difference divides into it to determine the isotope peak number that was selected for fragmentation
    #sometimes 2nd or 3rd isotopic peak and not the monoisotopic peak is selected for fragmentation
    isotope_peak_num = round((precursor_mass - calc_mz) / isotope_states_mass_difference)
  
    #calculate mz of first, second, third isotope peaks
    first_peak_mz  = precursor_mass - (isotope_peak_num * isotope_states_mass_difference)
    second_peak_mz = first_peak_mz  + isotope_states_mass_difference
    third_peak_mz  = first_peak_mz  + (2 * (isotope_states_mass_difference))
  
    #now calculate the peaks for heavy or light partner
    #if we initially have a light, then the mass shift will be in the positive direction  
    #if we initially have a heavy, then the mass shift will be in the negative direction (See CalculateMassShift function above)
    first_peak_mz_partner  = first_peak_mz  + mz_shift_for_partner
    second_peak_mz_partner = second_peak_mz + mz_shift_for_partner
    third_peak_mz_partner  = third_peak_mz  + mz_shift_for_partner
        
    #assemble all the masses to look for
    isotope_masses         = numpy.array([first_peak_mz, second_peak_mz, third_peak_mz])
    isotope_masses_partner = numpy.array([first_peak_mz_partner, second_peak_mz_partner, third_peak_mz_partner])        
    
    #Sort the masses such that it is always [Light, Heavy]
    peptide_isotope_masses = (numpy.array([isotope_masses_partner, isotope_masses]) 
                              if (isotope_masses_partner < isotope_masses).all() 
                              else numpy.array([isotope_masses, isotope_masses_partner]))
    return peptide_isotope_masses

#########################################################################################################

""" Returns tuple start and end RT 
     
    This is +- the time window overlap for a given RT
 
    Keyword arguments:
    time_window_overlap -- Time window
    RT_MSMS             -- Retention time for a MS/MS scan
    run_start_time      -- Run start time
    run_end_time        -- Run end time
"""
def calculateTimeWindow(time_window_overlap, RT_MSMS, run_start_time, run_end_time):      
    #scan back over 0.22min and forward 0.22min from MS/MS to search for maximum overlap
    #these times were chosen as 0.22min is the maximum delay between elution of heavy and elution of light
    time_window_start_RT = RT_MSMS - time_window_overlap
    time_window_stop_RT  = RT_MSMS + time_window_overlap
     
    #make sure search window is within range of the run time
    time_window_start_RT = run_start_time if time_window_start_RT < run_start_time else time_window_start_RT
    time_window_stop_RT  = run_end_time   if time_window_stop_RT  > run_end_time   else time_window_stop_RT

    return (time_window_start_RT, time_window_stop_RT)
     
#########################################################################################################

""" Returns tuple of upper and lower mass boundaries
 
    This is +- the mass error ppm for a given isotope
         
    Keyword arguments:
    mass_error -- Error tolerance
    isotope    -- Isotopic mass of a peptide
"""
def calculateIsotopeMassErrorBoundary(mass_error, isotope):
    if isotope not in ISOTOPE_MASS_ERROR_BOUNDARY_TABLE:
        #calculate upper and lower mass errors when searching for signals matching the predicted
        #masses of the peptide isotopomers, was set to 20ppm
        isotope_mass_error_ppm = (isotope/PPM) * mass_error
        mass_upper = isotope + isotope_mass_error_ppm
        mass_lower = isotope - isotope_mass_error_ppm            
        ISOTOPE_MASS_ERROR_BOUNDARY_TABLE[isotope] = (mass_upper, mass_lower)
 
    (mass_upper, mass_lower) = ISOTOPE_MASS_ERROR_BOUNDARY_TABLE[isotope]
    return (mass_upper, mass_lower)

#########################################################################################################

""" Returns the H/L ratio of light and heavy methylSILAC partners 
 
    H/L ratio = sum(intensities for heavy) / sum(intensities for light)
 
    Keyword arguments:
    light_average_mass_intensities -- numpy.array of averaged mass intensities for light isotope envelopes
    heavy_average_mass_intensities -- numpy.array of averaged mass intensities for heavy isotope envelopes
"""
def calculateHtoLRatio(light_average_mass_intensities, heavy_average_mass_intensities):
    light_average_intensities = light_average_mass_intensities[:, 1]
    heavy_average_intensities = heavy_average_mass_intensities[:, 1]
     
    #if there are any isotope envelope members missing, intensity of whole peptide is set to 0
    #this provides more specificity and minimises amount of rubbish being quantified
    light_intensity = 0 if 0 in light_average_intensities else numpy.sum(light_average_mass_intensities, axis = 0)[1]
    heavy_intensity = 0 if 0 in heavy_average_intensities else numpy.sum(heavy_average_mass_intensities, axis = 0)[1]

    if (float(heavy_intensity) != 0 and float(light_intensity) != 0):
        ratio = (float(heavy_intensity) / float(light_intensity))
        return ratio
    
    #partner wasn't found
    return 'NA'
 
#########################################################################################################

""" Returns pearson correlation coefficient
 
    This is a correlation between light and heavy isotope envelopes
    Code from dfrankow on stackoverflow
         
    Keyword arguments:
    light_average_mass_intensities -- numpy.array of averaged intensities for each light isotope envelopes
    heavy_average_mass_intensities -- numpy.array of averaged intensities for each heavy isotope envelopes
"""
def calculatePearsonCorrelationCoefficient(light_average_mass_intensities, heavy_average_mass_intensities):
    light_average_intensities = light_average_mass_intensities[:, 1]
    heavy_average_intensities = heavy_average_mass_intensities[:, 1]

    #the function returns a (coefficient, p-value) tuple
    pearson_correlation_coefficient = pearsonr(light_average_intensities, heavy_average_intensities)[0]
    if (pearson_correlation_coefficient is not None and not numpy.isnan(pearson_correlation_coefficient)):
        return pearson_correlation_coefficient
    
    #Correlation could not be calculated
    return 'NA'

