#--------------------------------------------------------------------------------------------------------------------

#This module contains correlation-related classes and functions

#------------------ Dependencies ----------------------------#

## External dependencies
import numpy
import pandas
from matplotlib import pyplot

## Internal dependencies
from .common import *

#------------------ Global Variables ------------------------#

SCAN_OVERLAP = 1
SCAN_START   = 2
SCAN_STOP    = 3

#------------------ Classes & Functions ---------------------#

class Task():
    
    def __init__(self, parameters, xr_info, MS_MS_scan_num, RT_MSMS, peptide_isotope_masses):
        self.xr_info                 = xr_info
        self.MS_MS_scan_num          = MS_MS_scan_num
        self.RT_MSMS                 = RT_MSMS
        self.peptide_isotope_masses  = peptide_isotope_masses
        self.initParameters(parameters)

    def initParameters(self, parameters):
        self.mass_error              = parameters.mass_error
        self.time_window_overlap     = parameters.time_window_overlap
        self.time_window             = parameters.time_window
        self.empty_ms_allowed        = parameters.empty_ms_allowed
        self.min_isotopomers_allowed = parameters.min_isotopomers_allowed
        self.pearson_threshold       = parameters.pearson_threshold

    def getLightIsotopeMasses(self):
        return self.peptide_isotope_masses[0]

    def getHeavyIsotopeMasses(self):
        return self.peptide_isotope_masses[1]
        
    """ Returns the MS/MS scan number that corresponds to the maximum overlap
        between light and heavy peptides (See below)
    """
    def getPointOfMaximumOverlap(self, light_isotope_masses, heavy_isotope_masses):
        key = (light_isotope_masses.__str__(), heavy_isotope_masses.__str__(), 
               self.MS_MS_scan_num, SCAN_OVERLAP)
 
        if not self.xr_info.containsPeptideScanNumber(key):
            maximum_overlap_scan \
                = self.calculatePointOfMaximumOverlap(light_isotope_masses, heavy_isotope_masses)
            self.xr_info.putPeptideScanNumber(key, maximum_overlap_scan)
 
        maximum_overlap_scan = self.xr_info.getPeptideScanNumber(key)
        return maximum_overlap_scan

    """ Returns the MS/MS scan number that corresponds to the maximum overlap
        between light and heavy peptides 
     
        This can then be used as a starting point to search for elution window of light heavy pair.
        The point of maximum overlap is the scan number with the highest cumulative intensity.
         
        Keyword arguments:
        light_isotope_masses -- numpy.array of masses corresponding to light isotope envelopes
        heavy_isotope_masses -- numpy.array of masses corresponding to heavy isotope envelopes        
    """
    def calculatePointOfMaximumOverlap(self, light_isotope_masses, heavy_isotope_masses):    
        #record the point (scan_num) that corresponds to the maximum intensity
        #between light and heavy peptides starting from the MS/MS scan number
        maximum_overlap_scan      = self.MS_MS_scan_num
        maximum_overlap_intensity = 0

        #search for the scan with the maximum amount of overlap
        #we do this by calculating the total intensity of light and heavy isotopes
        #this is based on the assumption that there is extensive overlap between light and heavy
        for scan_num in self.__getScanRangeForRT():
            total_overlap_intensity \
                = self.__getTotalOverlapIntensity(light_isotope_masses, heavy_isotope_masses, scan_num)

            #if we find a scan number with a greater intensity,
            #then we update the previous scan number to the new one
            if total_overlap_intensity > maximum_overlap_intensity:
                maximum_overlap_scan      = scan_num
                maximum_overlap_intensity = total_overlap_intensity

            #otherwise maintain the current scan number
            else:
                pass
            
        return maximum_overlap_scan
 
    """ Returns numpy array containing the maximum mass intensity
        of precursor masses for each isotope mass  
     
        Keyword arguments:
        light_or_heavy_isotope_masses -- numpy.array of masses corresponding to either 
                                         light or heavy isotope envelopes
        scan_num                      -- MS/MS scan number
    """
    def getMaxMassIntensityFromPrecursorMasses(self, light_or_heavy_isotope_masses, scan_num):
        #calculate the number of isotopes found and the total intensity of all isotopes
        light_or_heavy_mass_intensities = numpy.array([]).reshape(0, 2)

        #get the precursor mass list
        precursor_masses_intensities = self.xr_info.getScanInfo(scan_num).getPrecursorMassList()
     
        for isotope in light_or_heavy_isotope_masses:
            key = (isotope, scan_num)
            if not self.xr_info.containsPrecursorMaxMassIntensity(key):
                max_isotope_mass_intensity \
                    = self.getMaxMassIntensityForIsotope(isotope, precursor_masses_intensities)
                self.xr_info.putPrecursorMaxMassIntensity(key, max_isotope_mass_intensity)
     
            max_isotope_mass_intensity = self.xr_info.getPrecursorMaxMassIntensity(key)
            if max_isotope_mass_intensity is not None:
                light_or_heavy_mass_intensities \
                    = numpy.vstack([light_or_heavy_mass_intensities, max_isotope_mass_intensity])
     
        return light_or_heavy_mass_intensities

    """ Returns the MS/MS scan number for the start or stop of a given peptide (See below)
    """
    def getStartOrStopElutionForPeptide(self, light_isotope_masses, heavy_isotope_masses, 
                                        max_overlap_scan_num, start_or_stop):
        
        key = (light_isotope_masses.__str__(), heavy_isotope_masses.__str__(), 
               self.MS_MS_scan_num, start_or_stop)
        if not self.xr_info.containsPeptideScanNumber(key):
            peptide_start_or_stop \
                = self.calculateStartOrStopElutionForPeptide(light_isotope_masses, heavy_isotope_masses, 
                                                             max_overlap_scan_num, start_or_stop)
            self.xr_info.putPeptideScanNumber(key, peptide_start_or_stop)
         
        peptide_start_or_stop = self.xr_info.getPeptideScanNumber(key)
        return peptide_start_or_stop

    """ Returns the MS/MS scan number for the start or stop of a given peptide 
     
        The MS/MS scan number can be:
        -- The MS/MS scan number at the start or stop of a peptide or 
        -- The MS/MS scan number at the point of maximum overlap between light and heavy
         
        Keyword arguments:
        light_isotope_masses   -- numpy.array of masses corresponding to light isotope envelopes
        heavy_isotope_masses   -- numpy.array of masses corresponding to heavy isotope envelopes        
        MS_MS_scan_num         -- MS/MS scan number
        start_or_stop          -- Boolean of whether we want the MS/MS scan number 
                                  for the start or stop of a peptide
    """
    def calculateStartOrStopElutionForPeptide(self, light_isotope_masses, heavy_isotope_masses, 
                                              max_overlap_scan_num, start_or_stop):
                
        #set the peptide_start_or_stop to MSMS_scan num, this is to make sure that if we come across a peptide
        #with an msms scan number of 2 for example, we have a guaranteed scan start value, otherwise
        #it would fall through the code below without peptide_start_or_stop being assigned a value
        peptide_start_or_stop = max_overlap_scan_num
        empty_MS              = 0

        #scan either forwards or backwards from MS/MS depending on whether we are finding "start" or "stop"
        for scan_num in self.__getScanRangeForStartOrStop(max_overlap_scan_num, start_or_stop):
            #limit how far back or forward in RT we look for the peptide to +- 1 minute
            if not self.__isWithinTimeWindow(scan_num):
                peptide_start_or_stop = scan_num
                break

            #peak at 557.94 mz is 0.03125 mz wide
            #at 1332 mz it is 0.1 wide
            #~50ppm wide so ~+-20ppm
            else:
                #for both light and heavy methylSILAC partners:
                #count how many expected isotope masses we have found and get their observed mass intensities for each isotope
                light_mass_intensity = self.getMaxMassIntensityFromPrecursorMasses(light_isotope_masses, scan_num)
                heavy_mass_intensity = self.getMaxMassIntensityFromPrecursorMasses(heavy_isotope_masses, scan_num)
                total_light_heavy_isotopes_found = sum([len(light_mass_intensity), len(heavy_mass_intensity)])
     
                #if the number of isotope envelopes for light and heavy in the scan is:
                # * Less than the min_isotopomers_allowed
                # * Greater than 2. Why are we looking for 2? Is this an assumption that there will be at least 1 light and 1 heavy?
                #we categorise this scan as not containing our peptide
                if 2 < total_light_heavy_isotopes_found < self.min_isotopomers_allowed:
                    empty_MS += 1                       #peptide not found in this scan

                    #if X number of scans without finding any trace of the peptide is:
                    # * Greater than empty_ms_allowed
                    #then abort search                    
                    if empty_MS > self.empty_ms_allowed:
                        peptide_start_or_stop = scan_num
                        break

                #2 or fewer members of isotope envelope found, stop search
                elif total_light_heavy_isotopes_found < 3:
                    #return current MS scan
                    peptide_start_or_stop = scan_num
                    break

                #continue searching in next scan if we are still within the isotope envelope
                else:
                    pass
     
        return peptide_start_or_stop
  
    """ Returns numpy array containing the maximum mass intensity
        of average masses for each isotope mass  
     
        Keyword arguments:
        light_or_heavy_isotope_masses -- numpy.array of masses corresponding
                                         to either light or heavy isotope envelopes
        peptide_start_scan_num        -- starting scan number for methylSILAC pair
        peptide_stop_scan_num         -- stopping scan number for methylSILAC pair
    """    
    def getMaxMassIntensityFromAverageMasses(self, light_or_heavy_isotope_masses, 
                                             peptide_start_scan_num, peptide_stop_scan_num):
        
        #calculate the number of isotopes found and the total intensity of all isotopes
        light_or_heavy_mass_intensities = numpy.array([]).reshape(0, 2)
 
        #get the average mass list
        average_masses_intensities \
            = self.xr_info.getAverageMassListForPeptide(peptide_start_scan_num, peptide_stop_scan_num)
     
        for isotope in light_or_heavy_isotope_masses:
            key = (isotope, peptide_start_scan_num, peptide_stop_scan_num)
            if not self.xr_info.containsAverageMaxMassIntensity(key):
                max_isotope_mass_intensity \
                    = self.getMaxMassIntensityForIsotope(isotope, average_masses_intensities)
                if max_isotope_mass_intensity is None:
                    max_isotope_mass_intensity = numpy.array([isotope, 0])
                     
                self.xr_info.putAverageMaxMassIntensity(key, max_isotope_mass_intensity)
                  
            max_isotope_mass_intensity = self.xr_info.getAverageMaxMassIntensity(key)
            light_or_heavy_mass_intensities \
                = numpy.vstack([light_or_heavy_mass_intensities, max_isotope_mass_intensity])

        return light_or_heavy_mass_intensities
    
    """ Returns numpy.array containing the maximum mass intensity for a given isotope or None
     
        Keyword arguments:
        isotope_mass     -- Mass corresponding to an isotope envelope
        mass_intensities -- numpy.array of mass intensities (precursor or averaged) 
    """
    def getMaxMassIntensityForIsotope(self, isotope_mass, masses_intensities):
        assert(len(masses_intensities) != 0)        
        if (len(masses_intensities) > 0):
            #calculates the upper and lower mass error boundaries for a given isotope
            (mass_upper, mass_lower) = calculateIsotopeMassErrorBoundary(self.mass_error, isotope_mass)
         
            #look for isotopomers of isotope in mass list that are within the mass boundaries
            within_mass_boundaries   = numpy.logical_and(mass_lower < masses_intensities[:,0], 
                                                         masses_intensities[:, 0] < mass_upper)            
            matched_mass_intensities = masses_intensities[within_mass_boundaries]
         
            #found at least 1 isotopomer of isotope, so we take the one with the highest intensity           
            if len(matched_mass_intensities) > 0:
                max_isotope_mass_intensity_idx = numpy.argmax(matched_mass_intensities[:, 1])                                    
                max_isotope_mass_intensity     = matched_mass_intensities[max_isotope_mass_intensity_idx]
                return max_isotope_mass_intensity
    
        #didn't find an isotopomer, so keep track of it
        return None

    """ Returns the MS/MS scan number for the start or stop of a given isotope 
        The MS/MS scan number can be:
        -- The MS/MS scan number at the start or stop of an isotope or 
        -- The MS/MS scan number at the point of maximum intensity for an isotope
    
        Keyword arguments:
        isotope        -- Isotopic mass of a peptide 
        MS_MS_scan_num -- MS/MS scan number
        start_or_stop  -- Boolean of whether we want the MS/MS scan number 
                          for the start or stop of a peptide
    """
    def calculateStartOrStopElutionForIsotope(self, isotope, MS_MS_scan_num, start_or_stop):    
        #set the peptide_start_or_stop to MSMS_scan num, this is to make sure that if we come across a peptide
        #with an msms scan number of 2 for example, we have a guaranteed scan start value, otherwise
        #it would fall through the code below without peptide_start_or_stop being assigned a value
        peptide_start_or_stop = MS_MS_scan_num

        #scan either forwards or backwards from MS/MS depending on whether we are finding "start" or "Stop"
        for scan_num in self.__getScanRangeForStartOrStop(MS_MS_scan_num, start_or_stop):
            #limit how far back or forward in RT we look for the peptide to +- 1 minute
            if not self.__isWithinTimeWindow(scan_num):
                peptide_start_or_stop = scan_num
                break            

            #peak at 557.94 mz is 0.03125 mz wide
            #at 1332 mz it is 0.1 wide
            #~50ppm wide so ~+-20ppm
            else:
                #Stop searching as soon as we reach 0
                mass_intensity = self.getMaxMassIntensityFromPrecursorMasses(isotope, scan_num)
                if len(mass_intensity) == 0 or mass_intensity[0][1] == 0:
                    peptide_start_or_stop = scan_num
                    break;

        return peptide_start_or_stop 

    """ Returns the intensity profile for a given isotope over a range of MS/MS scan numbers 
     
        Keyword arguments:
        isotope        -- Isotopic mass of a peptide
        start_scan_num -- MS/MS scan number denoting the beginning of an isotope
        stop_scan_num  -- MS/MS scan number denoting the ending of an isotope 
    """
    def getIntensityProfileForIsotope(self, isotope, start_scan_num, stop_scan_num):
        scan_range = self.xr_info.getScanRange(start_scan_num, stop_scan_num)
        isotope_RT_intensities = numpy.array([]).reshape(0, 2)
        for scan_num in scan_range:
            RT_MS          = self.xr_info.getScanInfo(scan_num).getRT()
            mass_intensity = self.getMaxMassIntensityFromPrecursorMasses(isotope, scan_num)
 
            if len(mass_intensity) != 0:
                RT_intensity = numpy.array([RT_MS, mass_intensity[0][1]])
            else:
                RT_intensity = numpy.array([RT_MS, 0])
                                             
            isotope_RT_intensities = numpy.vstack([isotope_RT_intensities, RT_intensity])
         
        return isotope_RT_intensities

    """ Returns a range of MS/MS scan numbers over the RT window
    """
    def __getScanRangeForRT(self):
        #get the timing window around the RT 
        run_start_time = self.xr_info.getRunStartTime()
        run_end_time   = self.xr_info.getRunEndTime()
        (time_window_start_RT, time_window_stop_RT) = \
            calculateTimeWindow(self.time_window_overlap, self.RT_MSMS,
                                    run_start_time, run_end_time)
 
        #convert start and stop times to scan numbers, so that we can search the range of scans
        #to reduce search space, we only go through scans which are not MS2
        scan_start = self.xr_info.getScanNumFromRT(time_window_start_RT)
        scan_stop  = self.xr_info.getScanNumFromRT(time_window_stop_RT) 
        scan_range = self.xr_info.getScanRange(scan_start, scan_stop)
        return scan_range

    """ Returns a list of MS/MS scan numbers
     
        Keyword arguments:
        MS_MS_scan_num -- MS/MS scan number that determines the starting point
        start_or_stop  -- Boolean value that determines an increasing or decreasing scan number range
    """
    def __getScanRangeForStartOrStop(self, MS_MS_scan_num, start_or_stop):
        #construct range of scans to search for peptide
        #if looking for start of peptide, range of scans to look through decreases from the MS/MS scan
        #to reduce search space, we only go through scans in XR that are not MS2
        if start_or_stop is SCAN_START:
            scan_start = 0
            scan_stop  = MS_MS_scan_num
            #get all MS1 scans that are less than (or equal to) the MS_MS_scan_num
            scan_range = self.xr_info.getScanRange(scan_start, scan_stop)
            scan_range.reverse()
     
        #otherwise, range of scans increases from the MS/MS scan          
        else:
            scan_start = MS_MS_scan_num
            scan_stop  = self.xr_info.getNumSpectra() + 1
            #get all MS1 scans that are greater than (or equal to) the MS_MS_scan_num
            scan_range = self.xr_info.getScanRange(scan_start, scan_stop)
    
        return scan_range

    """ Returns the sum of light and heavy peak intensities for each isotope  
     
        Keyword arguments:
        light_isotope_masses -- numpy.array of masses corresponding to light isotope envelopes
        heavy_isotope_masses -- numpy.array of masses corresponding to heavy isotope envelopes
        scan_num             -- MS/MS scan number
    """
    def __getTotalOverlapIntensity(self, light_isotope_masses, heavy_isotope_masses, scan_num):
        #for both light and heavy methylSILAC partners:
        #count how many expected isotope masses we have found and get their observed mass intensities for each isotope
        light_mass_intensity = self.getMaxMassIntensityFromPrecursorMasses(light_isotope_masses, scan_num)
        heavy_mass_intensity = self.getMaxMassIntensityFromPrecursorMasses(heavy_isotope_masses, scan_num)        
        total_light_heavy_isotopes_found = sum([len(light_mass_intensity), len(heavy_mass_intensity)])

        #calculate the total intensity of light and heavy isotopes
        #only do this if there is at most 1 isotope envelope missing            
        if total_light_heavy_isotopes_found >= self.min_isotopomers_allowed:
            light_total_intensity       = numpy.sum(light_mass_intensity, axis = 0)
            heavy_total_intensity       = numpy.sum(heavy_mass_intensity, axis = 0)
            total_light_heavy_intensity = light_total_intensity[1] + heavy_total_intensity[1]
            return total_light_heavy_intensity

        #fewer than 5 members of isotope envelope found
        #we ignore them since we are only interested in those with intensity values
        #if all scans have 0 intensity, then we just return the MS_MS_scan number anyway
        return 0

    """ Returns whether RT_MS is within the time window
    """
    def __isWithinTimeWindow(self, scan_num):
        RT_MS = self.xr_info.getScanInfo(scan_num).getRT()
        
        if ((self.time_window * -1) > (self.RT_MSMS - RT_MS) 
            or (self.RT_MSMS - RT_MS) > self.time_window):
            
            return False
        return True

#########################################################################################################

class IsotopeCorrelationTask(Task):
    
    def __init__(self, parameters, xr_info, MS_MS_scan_num, RT_MSMS, peptide_isotope_masses):
        Task.__init__(self, parameters, xr_info, MS_MS_scan_num, RT_MSMS, peptide_isotope_masses)        
        self.columnnames = ['Peptide Start Scan', 'Peptide Stop Scan',
                            'Peptide Start RT (min)', 'Peptide Stop RT (min)',
                            'Light m/z 1', 'Light Intensity 1',
                            'Light m/z 2', 'Light Intensity 2',
                            'Light m/z 3', 'Light Intensity 3', 
                            'Heavy m/z 1', 'Heavy Intensity 1',
                            'Heavy m/z 2', 'Heavy Intensity 2',
                            'Heavy m/z 3', 'Heavy Intensity 3',
                            ISOTOPE_CORRELATION_COLUMN_NAME, H_L_RATIO_COLUMN_NAME + ' #1']
        
    """ Identify SILAC pairs based on Pearson correlation of average masses 
        Original algorithm by Vincent, updated by Aidan
    """
    def runTask(self):
        #separate the light and heavy isotope masses
        light_isotope_masses = self.getLightIsotopeMasses()
        heavy_isotope_masses = self.getHeavyIsotopeMasses()
         
        #find the MS scan number where there is maximum overlap between light and heavy peptide
        max_overlap_scan_num = self.getPointOfMaximumOverlap(light_isotope_masses, heavy_isotope_masses)

        #get the start and stop scan numbers for methylSILAC pair using the MS scan number returned above as the starting point
        peptide_start_scan_num \
            = self.getStartOrStopElutionForPeptide(light_isotope_masses, heavy_isotope_masses, 
                                                   max_overlap_scan_num, SCAN_START)
        peptide_stop_scan_num  \
            = self.getStartOrStopElutionForPeptide(light_isotope_masses, heavy_isotope_masses, 
                                                   max_overlap_scan_num, SCAN_STOP)

        #get average mass intensities for light and heavy isotopes
        light_average_mass_intensities \
            = self.getMaxMassIntensityFromAverageMasses(light_isotope_masses, 
                                                        peptide_start_scan_num, peptide_stop_scan_num)
        heavy_average_mass_intensities \
            = self.getMaxMassIntensityFromAverageMasses(heavy_isotope_masses, 
                                                        peptide_start_scan_num, peptide_stop_scan_num)

        #calculate the Pearson correlation and H/L ratio
        pearson_isotope_correlation \
            = calculatePearsonCorrelationCoefficient(light_average_mass_intensities, heavy_average_mass_intensities)
        H_to_L_ratio \
            = calculateHtoLRatio(light_average_mass_intensities, heavy_average_mass_intensities)
   
        #get the start and stop retention times for methylSILAC pair
        peptide_start_RT = self.xr_info.getScanInfo(peptide_start_scan_num).getRT()                
        peptide_stop_RT  = self.xr_info.getScanInfo(peptide_stop_scan_num).getRT()

        self.formatRow(light_average_mass_intensities, heavy_average_mass_intensities,
                       peptide_start_scan_num, peptide_stop_scan_num, 
                       peptide_start_RT, peptide_stop_RT, 
                       pearson_isotope_correlation, H_to_L_ratio)

    """ Format output for printing out to CSV file
    """
    def formatRow(self, light_average_mass_intensities, heavy_average_mass_intensities,
                  peptide_start_scan_num, peptide_stop_scan_num, 
                  peptide_start_RT, peptide_stop_RT, 
                  pearson_isotope_correlation, H_to_L_ratio):
        
        ## Format output for printing out to CSV file
        (light_mass_1, light_mass_2, light_mass_3) \
            = light_average_mass_intensities[:, 0].tolist()
        (light_intensity_1, light_intensity_2, light_intensity_3) \
            = light_average_mass_intensities[:, 1].tolist()

        (heavy_mass_1, heavy_mass_2, heavy_mass_3) \
            = heavy_average_mass_intensities[:, 0].tolist()
        (heavy_intensity_1, heavy_intensity_2, heavy_intensity_3) \
            = heavy_average_mass_intensities[:, 1].tolist()
 
        self.outputRow = pandas.DataFrame([[peptide_start_scan_num, peptide_stop_scan_num, 
                                            peptide_start_RT, peptide_stop_RT, 
                                            light_mass_1, light_intensity_1,
                                            light_mass_2, light_intensity_2, 
                                            light_mass_3, light_intensity_3, 
                                            heavy_mass_1, heavy_intensity_1, 
                                            heavy_mass_2, heavy_intensity_2,
                                            heavy_mass_3, heavy_intensity_3, 
                                            pearson_isotope_correlation, H_to_L_ratio]],
                                            columns=self.columnnames)

#########################################################################################################

class ElutionCorrelationTask(Task):
    
    def __init__(self, parameters, xr_info, MS_MS_scan_num, RT_MSMS, peptide_isotope_masses):
        Task.__init__(self, parameters, xr_info, MS_MS_scan_num, RT_MSMS, peptide_isotope_masses)  
        self.light_RT_intensities = []  # For testing purposes
        self.heavy_RT_intensities = []  # For testing purposes
        self.columnnames = ['Light m/z 1', 'Light Intensity 1', 
                            'Heavy m/z 1', 'Heavy Intensity 1',
                            'Light m/z 2', 'Light Intensity 2',                                        
                            'Heavy m/z 2', 'Heavy Intensity 2', 
                            'Light m/z 3', 'Light Intensity 3', 
                            'Heavy m/z 3', 'Heavy Intensity 3',
                            ELUTION_CORRELATION_COLUMN_NAME + ' 1',
                            ELUTION_CORRELATION_COLUMN_NAME + ' 2',
                            ELUTION_CORRELATION_COLUMN_NAME + ' 3',
                            ELUTION_COUNT_COLUMN_NAME,  H_L_RATIO_COLUMN_NAME + ' #2']

    """ Identify SILAC pairs based on Pearson correlation of RT-intensity profiles (Original algorithm by Aidan) """
    def runTask(self):
        #separate the light and heavy isotope masses
        light_isotope_masses = self.getLightIsotopeMasses()
        heavy_isotope_masses = self.getHeavyIsotopeMasses()
         
        #find the MS scan number where there is maximum overlap between light and heavy peptide
        max_overlap_scan_num = self.getPointOfMaximumOverlap(light_isotope_masses, 
                                                             heavy_isotope_masses)

        pearson_isotope_correlations   = []
        light_average_mass_intensities = numpy.array([]).reshape(0, 2)
        heavy_average_mass_intensities = numpy.array([]).reshape(0, 2)
        
        for i in range(0, numpy.size(self.peptide_isotope_masses[0])):
            light_isotope = numpy.array([light_isotope_masses[i]])
            heavy_isotope = numpy.array([heavy_isotope_masses[i]])
          
            (isotope_start_scan_num, isotope_stop_scan_num) \
                = self.getIsotopeStartAndStop(light_isotope, heavy_isotope, max_overlap_scan_num)          
          
            ## Get the RT-intensity profile
            (light_isotope_RT_intensities, heavy_isotope_RT_intensities) \
                = self.getIsotopeRTIntensities(light_isotope, heavy_isotope,
                                               isotope_start_scan_num, isotope_stop_scan_num) 

            ## Calculate the Pearson correlation for each RT-intensity distribution      
            pearson_isotope_correlation \
                = calculatePearsonCorrelationCoefficient(light_isotope_RT_intensities, 
                                                             heavy_isotope_RT_intensities)
            pearson_isotope_correlations.append(pearson_isotope_correlation)
     
            #get average mass intensities for light and heavy isotopes
            light_isotope_average_mass_intensities \
                = self.getMaxMassIntensityFromAverageMasses(light_isotope, isotope_start_scan_num, 
                                                            isotope_stop_scan_num)
            heavy_isotope_average_mass_intensities \
                = self.getMaxMassIntensityFromAverageMasses(heavy_isotope, isotope_start_scan_num, 
                                                            isotope_stop_scan_num)

            light_average_mass_intensities = numpy.vstack([light_average_mass_intensities, light_isotope_average_mass_intensities])
            heavy_average_mass_intensities = numpy.vstack([heavy_average_mass_intensities, heavy_isotope_average_mass_intensities])
     
        # Calculate the H/L ratio for isotopes with a good Pearson's correlation (non-NA values that are > pearson threshold input)
        good_correlation_indicies = [i for i, x in enumerate(pearson_isotope_correlations) if x != "NA" and x > self.pearson_threshold]
        num_good_correlations     = len(good_correlation_indicies) 
        H_to_L_ratio              = calculateHtoLRatio(light_average_mass_intensities[good_correlation_indicies], 
                                                           heavy_average_mass_intensities[good_correlation_indicies])

        self.formatRow(light_average_mass_intensities, heavy_average_mass_intensities, 
                       pearson_isotope_correlations, num_good_correlations, H_to_L_ratio);

        #self.__plotRTIntensities(light_RT_intensities, heavy_RT_intensities)

    def getIsotopeStartAndStop(self, light_isotope, heavy_isotope, max_overlap_scan_num):
        #get the start and stop scan numbers for methylSILAC pair using the MS scan number returned above as the starting point
        light_peptide_start_scan_num \
            = self.calculateStartOrStopElutionForIsotope(light_isotope, max_overlap_scan_num, SCAN_START)
        light_peptide_stop_scan_num \
            = self.calculateStartOrStopElutionForIsotope(light_isotope, max_overlap_scan_num, SCAN_STOP)
    
        heavy_peptide_start_scan_num \
            = self.calculateStartOrStopElutionForIsotope(heavy_isotope, max_overlap_scan_num, SCAN_START)
        heavy_peptide_stop_scan_num  \
            = self.calculateStartOrStopElutionForIsotope(heavy_isotope, max_overlap_scan_num, SCAN_STOP)
     
        ## We need the same number of points for pearson, so our waveforms should be taken over the same scan range
        isotope_start_scan_num = min(light_peptide_start_scan_num, heavy_peptide_start_scan_num)
        isotope_stop_scan_num  = max(light_peptide_stop_scan_num, heavy_peptide_stop_scan_num)
        return (isotope_start_scan_num, isotope_stop_scan_num)

    def getIsotopeRTIntensities(self, light_isotope, heavy_isotope, isotope_start_scan_num, isotope_stop_scan_num):
        light_isotope_RT_intensities \
            = self.getIntensityProfileForIsotope(light_isotope, isotope_start_scan_num, isotope_stop_scan_num)
        heavy_isotope_RT_intensities \
            = self.getIntensityProfileForIsotope(heavy_isotope, isotope_start_scan_num, isotope_stop_scan_num)

        # For testing purposes
        self.light_RT_intensities.append(light_isotope_RT_intensities)
        self.heavy_RT_intensities.append(heavy_isotope_RT_intensities)
        return (light_isotope_RT_intensities, heavy_isotope_RT_intensities)

    """ Format output for printing out to CSV file
    """
    def formatRow(self, light_average_mass_intensities, heavy_average_mass_intensities,
                  pearson_isotope_correlations, num_good_correlations, H_to_L_ratio):
         
        ## Format output for printing out to CSV file
        (light_mass_1, light_mass_2, light_mass_3) \
            = light_average_mass_intensities[:, 0].tolist()
        (light_intensity_1, light_intensity_2, light_intensity_3) \
            = light_average_mass_intensities[:, 1].tolist()

        (heavy_mass_1, heavy_mass_2, heavy_mass_3) \
            = heavy_average_mass_intensities[:, 0].tolist()
        (heavy_intensity_1, heavy_intensity_2, heavy_intensity_3) \
            = heavy_average_mass_intensities[:, 1].tolist()
 
        #pearson correlation for each isotopes
        (pearson_correlation_1, pearson_correlation_2, pearson_correlation_3) \
            = pearson_isotope_correlations
        
        self.outputRow = pandas.DataFrame([[light_mass_1, light_intensity_1,
                                            light_mass_2, light_intensity_2,
                                            light_mass_3, light_intensity_3,
                                            heavy_mass_1, heavy_intensity_1,
                                            heavy_mass_2, heavy_intensity_2,
                                            heavy_mass_3, heavy_intensity_3,
                                            pearson_correlation_1,
                                            pearson_correlation_2,
                                            pearson_correlation_3,
                                            num_good_correlations, H_to_L_ratio]],
                                            columns=self.columnnames)
  
    """ Create a RT vs intensity plot for each pair of light and heavy isotopes
     
        NOTE: This is mostly for testing and debugging purposes
    """  
    def __plotRTIntensities(self, light_RT_intensities, heavy_RT_intensities):
        fig        = pyplot.figure()
        subplot_id = 611
        for i in range(0, len(light_RT_intensities)):
            light_RT          = light_RT_intensities[i][:, 0]
            light_intensities = light_RT_intensities[i][:, 1]
            heavy_RT          = heavy_RT_intensities[i][:, 0]
            heavy_intensities = heavy_RT_intensities[i][:, 1]
        
            subplot_id = subplot_id + i
            ax = fig.add_subplot(subplot_id)
            ax.set_xlabel("RT")
            ax.set_ylabel("Intensity")        
            pyplot.plot(light_RT, light_intensities, 'r')
            pyplot.plot(heavy_RT, heavy_intensities, 'b')
            pyplot.autoscale()
        
        pyplot.show()        
        pyplot.clf()
