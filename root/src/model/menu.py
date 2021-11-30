#--------------------------------------------------------------------------------------------------------------------

#This package contains model-related classes and functions for the menu bar

#------------------ Dependencies ----------------------------#

## External dependencies

## Internal dependencies

#------------------- Global Variables -----------------------#

DEFAULT_MOD_LIST   = [('Methyl', 4.022185), 
                      ('Dimethyl', 8.04437),
                      ('Trimethyl', 12.066555)]

DEFAULT_LABEL_LIST = [('13CD3', 'M', 4.022185), 
                      ('13C4',  'M', 0.008766)]

#------------------ Classes & Functions ---------------------#

class ModificationList():

    class __ModificationList():

        def __init__(self, mod_list):
            self.mod_list = mod_list

        def __str__(self):
            mod_list_str = map(lambda mod_info: "\t".join([mod_info]), self.mod_list)
            return "\n".join(mod_list_str)

    instance = None
    def __init__(self):
        if not ModificationList.instance:
            ## Default modifications
            ModificationList.instance = ModificationList.__ModificationList(DEFAULT_MOD_LIST)
            
        else:
            ModificationList.instance.mod_list = self.instance.mod_list

    def clear(self):
        ModificationList.instance.mod_list = []

    def addModification(self, mod_type, mod_mass):
        ModificationList.instance.mod_list.append((mod_type, mod_mass))

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(object, name)

    def __iter__(self):
        return iter(self.mod_list)
    
#########################################################################################################

class LabelList():

    class __LabelList():

        def __init__(self, label_list):
            self.label_list = label_list

        def __str__(self):
            "\n".join(self.label_list)

    instance = None
    def __init__(self):
        if not LabelList.instance:
            ## Default labels
            LabelList.instance = LabelList.__LabelList(DEFAULT_LABEL_LIST)
            
        else:
            LabelList.instance.label_list = self.instance.label_list

    def clear(self):
        LabelList.instance.label_list = []

    def addLabel(self, label_name, residue, mass):
        LabelList.instance.label_list.append((label_name, residue, mass))

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(object, name)

    def __iter__(self):
        return iter(self.label_list)
