import numpy as np
import unyt
from yt.frontends.gadget.api import GadgetHDF5Dataset
from yt.funcs import mylog
from yt.utilities.on_demand_imports import _h5py as h5py

from .fields import ArepoFieldInfo

#Large changes were made to AREPO frontend to accomodate the new halo/subhalo/(in ray files) line of sight metadata, revamp the unit system to be more comprehensive, and to facilitate using Trident. Other changes include giving units to spectral properties determined by Trident and defining convenience functions (gas(), stars(), bh(), los()) that make accessing data more uniform. To do this we use convenience funcions like gas() and hs(), which read the gas particle data and halo/subhalo metadata. 

#gas() and stars() use the standard yt ds.r['PartTypeN', 'Property'] syntax at their core, but the gas() function is complicated because it has to be defined slightly differently for halo vs ray files; we want to be able to access spectral properties derived by Trident; and because gas properties are "layered" with 2 snapshots in the same HDF5 file, giving vector properties multiple orientations. These functions also handle any last-minute unit corrections. 

#hs() and los() are used to load metadata which is usually not accessible in yt. So we have to construct data objects to hold this new info. This is done using _get_hsvals() and _get_rayvals() methods, which give properties correct units and vector properties the correct unit system. 


h=0.6774
mixed_orientation_fields=('CenterOfMass', 'Coordinates', 'MagneticField', 'Velocities', 'GroupCM', 'GroupPos', 'GroupVel', 'SubhaloCM', 'SubhaloPos', 'SubhaloSpin', 'SubhaloVel')

boolean_fields=('particle_found', 'in_inner_fuzz', 'in_other_halo', 'in_outer_fuzz', 'in_primary', 'in_satellite')


masses=['SubhaloBHMass', 'SubhaloMass', 'SubhaloMassInHalfRad', 'SubhaloMassInHalfRadType', 'SubhaloMassInMaxRad', 'SubhaloMassInMaxRadType', 'SubhaloMassInRad', 'SubhaloMassInRadType', 'SubhaloMassType', 'SubhaloStellarPhotometricsMassInRad', 'SubhaloWindMass', 'GroupBHMass', 'GroupMass', 'GroupMassType', 'GroupWindMass', 'Group_M_Crit200', 'Group_M_Crit500', 'Group_M_Mean200', 'Group_M_TopHat200']
lengths_positions=['SubhaloCM', 'SubhaloHalfmassRad', 'SubhaloHalfmassRadType',  'SubhaloPos', 'SubhaloHalfmassRadType', 'SubhaloPos', 'SubhaloStellarPhotometricsRad', 'SubhaloVmaxRad', 'GroupCM', 'GroupPos', 'Group_R_Crit200', 'Group_R_Crit500', 'Group_R_Mean200', 'Group_R_TopHat200']
velocities=['SubhaloVel', 'SubhaloVelDisp', 'SubhaloVmax', 'GroupVel']
magnetic=['SubhaloBfldDisk', 'SubhaloBfldHalo']
sfrs=['SubhaloSFR', 'SubhaloSFRinHalfRad', 'SubhaloSFRinMaxRad', 'SubhaloSFRinRad', 'GroupSFR']
special_SF_types, special_SF_times=['SFR_MsunPerYrs_in_r5pkpc_', 'SFR_MsunPerYrs_in_InRad_', 'SFR_MsunPerYrs_in_r30pkpc_', 'SFR_MsunPerYrs_in_all_'], [10,50,100,200,1000]
sfrs.extend([sftype+f'{x}Myrs' for sftype in special_SF_types for x in  special_SF_times])
spins=['SubhaloSpin']      
mdots=['SubhaloBHMdot', 'GroupBHMdot']
united_quantities=masses+lengths_positions+velocities+magnetic+sfrs+spins+mdots
united_quantities=tuple(united_quantities)

variable_orientation=('GroupCM', 'GroupPos', 'GroupVel', 'SubhaloCM', 'SubhaloPos', 'SubhaloSpin', 'SubhaloVel')

#fields that are only stored under the "gas" keyword
only_gas_fields=('entropy')
#desired coordinate system orientation
orientation='baryonic_L_orientation'

stored_observables={'EW':'A', 'column_density':'cm**-2', 'delta_lambda':'dimensionless*A', 'lambda_obs':'A', 'tau_ray':'dimensionless', 'thermal_b':'sqrt(erg)/sqrt(amu)', 'thermal_width':'A'}

class ArepoHDF5Dataset(GadgetHDF5Dataset):
    _field_info_class = ArepoFieldInfo

    def __init__(
        self,
        filename,
        dataset_type="arepo_hdf5",
        unit_base=None,
        smoothing_factor=2.0,
        index_order=None,
        index_filename=None,
        kernel_name=None,
        bounding_box=None,
        units_override=None,
        unit_system="cgs",
        default_species_fields=None,
    ):
        super().__init__(
            filename,
            dataset_type=dataset_type,
            unit_base=unit_base,
            index_order=index_order,
            index_filename=index_filename,
            kernel_name=kernel_name,
            bounding_box=bounding_box,
            units_override=units_override,
            unit_system=unit_system,
            default_species_fields=default_species_fields,
        )
        #self.hvals is inherited from way up the chain. We take the opportunity to rename it "headvals" to seperate it from "hsvals". 
        self.headvals=self._get_hvals()   #setting up data retreival methods happens in 3 basic parts, to make things as uniform as possible when accessing later. First, a "_get_" function 
        self.hsvals=self._get_hsvals()      #that organizes a dictionary structure. Then, we define the attribute ("vals" object) as this dictionary structure in the initialization function. 
        self.rayvals=self._get_rayvals()    #Then, we have another function (just 'gas' or 'header') which takes a single attribute as an argument and returns 
        self.gas=self._halo_or_ray()         #its value from the dictionary. 
        #this last "gas" line actually defines the method for getting gas properties, because the dictionary-like object is already generated by yt
        
        # The "smoothing_factor" is a user-configurable parameter which
        # is multiplied by the radius of the sphere with a volume equal
        # to that of the Voronoi cell to create smoothing lengths.
        self.smoothing_factor = smoothing_factor
        self.gamma = 5.0 / 3.0
        self.gamma_cr = self.parameters.get("GammaCR", 4.0 / 3.0)

    @classmethod
    def _is_valid(cls, filename, *args, **kwargs):
        need_groups = ["Header", "Config"]
        veto_groups = ["FOF", "Group", "Subhalo"]
        valid = True
        try:
            fh = h5py.File(filename, mode="r")
            valid = (
                all(ng in fh["/"] for ng in need_groups)
                and not any(vg in fh["/"] for vg in veto_groups)
                and (
                    "VORONOI" in fh["/Config"].attrs.keys()
                    or "AMR" in fh["/Config"].attrs.keys()
                )
                # Datasets with GFM_ fields present are AREPO
                or any(field.startswith("GFM_") for field in fh["/PartType0"])
            )
            fh.close()
        except Exception:
            valid = False
        return valid

    def _get_uvals(self):
        handle = h5py.File(self.parameter_filename, mode="r")
        uvals = {}
        missing = [True] * 3
        for i, unit in enumerate(
            ["UnitLength_in_cm", "UnitMass_in_g", "UnitVelocity_in_cm_per_s"]
        ):
            for grp in ["Header", "Parameters", "Units"]:
                if grp in handle and unit in handle[grp].attrs:
                    uvals[unit] = handle[grp].attrs[unit]
                    missing[i] = False
                    break
        if "UnitLength_in_cm" in uvals:
            # We assume this is comoving, because in the absence of comoving
            # integration the redshift will be zero.
            uvals["cmcm"] = 1.0 / uvals["UnitLength_in_cm"]
        handle.close()
        if all(missing):
            uvals = None
        return uvals


######################################MY MAIN ADDITIONAS BELOW#####################################################
    #NOTE THAT CODE UNITS OFTEN DECIDED BY THE 'TIME' ATTRIBUTE (IE, SCALE FACTOR) WHICH IS ONLY STORED FOR SNAPSHOT 84; SO SNAPSHOT 78 QUANTITIES ARE OFF BY ~8% FROM TRUE PHYSICAL QUANTITIES, BUT ARE COMPARABLE TO EACH OTHER ACROSS THE TWO SNAPSHOTS
    def unit_updater(self, hsvals, quant, snapshot=84):
      if snapshot!=84:
        snap=f'_{snapshot}'
      else:
        snap=''
      if quant in masses:
        hsvals[f'quant{snap}']=unyt.unyt_array(hsvals[quant], 'code_mass', registry=self.unit_registry)
        hsvals[f'{quant}_msun{snap}']=hsvals[f'quant{snap}'].to('Msun')
        
      elif quant in lengths_positions:
        hsvals[f'{quant}{snap}']=unyt.unyt_array(hsvals[f'{quant}{snap}'], 'code_length', registry=self.unit_registry)
        if 'Pos' in quant or 'CM' in quant:
          #If the quantity is relative to galactic center, have _TNG version as well; otherwise, _TNG version is just plain version
          #First, give units to _TNG version
          hsvals[f'{quant}_TNG{snap}']=unyt.unyt_array(hsvals[quant+'_TNG'+snap], 'code_length', registry=self.unit_registry)
          #Now calculate galactocentric, give units
          primary_pos=unyt.unyt_array(hsvals[f'SubhaloPos{snap}'][0], 'code_length', registry=self.unit_registry)    
          hsvals[f'{quant}_kpc{snap}']=(hsvals[f'{quant}{snap}']-primary_pos).to('kpc')
          
          if snapshot!=84:
            hsvals[f'{quant}_84orientation{snap}']=unyt.unyt_array(hsvals[f'{quant}_84orientation{snap}'][()], 'code_length', registry=self.unit_registry)
            primarypos=unyt.unyt_array(hsvals[f'SubhaloPos'][0], 'code_length', registry=self.unit_registry)
            hsvals[quant+f'_kpc_84orientation{snap}']=(hsvals[quant+f'_84orientation{snap}'][()]-primary_pos).to('kpc')            
        else:
          hsvals[f'{quant}_kpc{snap}']=hsvals[f'{quant}{snap}'][()].to('kpc')
          
      elif quant in velocities:
        hsvals[f'{quant}{snap}']=unyt.unyt_array(hsvals[f'{quant}{snap}'][()], 'code_velocity', registry=self.unit_registry)
        if 'Disp' in quant or 'Vmax' in quant:
          hsvals[f'{quant}_km_s{snap}']=hsvals[f'{quant}{snap}'][()].to('km/s')
        else:
          #If the quantity is relative to galactic center, have _TNG version as well; otherwise, _TNG version is just plain version
          #First, give units to _TNG version
          hsvals[f'{quant}_TNG{snap}']=unyt.unyt_array(hsvals[f'{quant}_TNG{snap}'][()], 'code_velocity', registry=self.unit_registry)
          #Now calculate galactocentric, give units
          primary_vel=unyt.unyt_array(hsvals[f'SubhaloVel{snap}'][0], 'code_velocity', registry=self.unit_registry)
          hsvals[f'{quant}_km_s{snap}']=(hsvals[f'{quant}{snap}'][()]-primary_vel).to('km/s')
          
          if snapshot!=84:
            hsvals[f'{quant}_84orientation{snap}']=unyt.unyt_array(hsvals[f'{quant}_84orientation{snap}'], 'code_velocity', registry=self.unit_registry)
            primary_vel=unyt.unyt_array(hsvals[f'SubhaloVel'][0], 'code_velocity', registry=self.unit_registry)
            hsvals[f'{quant}_km_s_84orientation{snap}']=(hsvals[f'{quant}_84orientation{snap}']-primary_vel).to('km/s')
        
      elif quant in magnetic:
        hsvals[f'{quant}{snap}']=unyt.unyt_array(hsvals[f'{quant}{snap}'], 'code_magnetic', registry=self.unit_registry)
        hsvals[quant+'_gauss'+snap]=hsvals[f'{quant}{snap}'][()].to('gauss')
        
      elif quant in sfrs:
        hsvals[f'{quant}{snap}']=unyt.unyt_array(hsvals[f'{quant}{snap}'], 'Msun/yr')  #all sfr quantities already in Msun/yr
        
      elif quant in spins:
        #just add units to base quantity
        hsvals[f'{quant}_TNG_kpc_km_s{snap}']=unyt.unyt_array(hsvals[f'{quant}_TNG{snap}'][()]/h, 'kpc*km/s')
        hsvals[f'{quant}_kpc_km_s{snap}']=unyt.unyt_array(hsvals[f'{quant}{snap}'][()]/h, 'kpc*km/s')
        if snapshot!=84:
          hsvals[f'{quant}_kpc_km_s_84orientation{snap}']=unyt.unyt_array(hsvals[f'{quant}_84orientation{snap}'], 'kpc*km/s')
          
      elif quant in mdots:
        hsvals[f'{quant}{snap}']=unyt.unyt_array(hsvals[f'{quant}{snap}'], 'code_mass/code_time', registry=self.unit_registry)
        hsvals[f'{quant}_msun_gyr{snap}']=hsvals[f'{quant}{snap}'][()].to('Msun/Gyr')
        
      
    #This is my function, meant to read supplementary data about subhalo/halo   
    def _get_hsvals(self):
      hsvals=dict(self.handle['/halo_and_sub_properties'].items())
      scale=self.handle['Header'].attrs['Time']
      primary_pos, primary_vel=unyt.unyt_array(hsvals['SubhaloPos'][0], 'code_length', registry=self.unit_registry), unyt.unyt_array(hsvals['SubhaloVel'][0], 'code_velocity', registry=self.unit_registry)
      #Now we fix units
      for quant in united_quantities:
        self.unit_updater(hsvals, quant)
      #Now, if we have a layered snapshot....
      if 'HaloID_78' in hsvals:
        for quant in united_quantities:
          self.unit_updater(hsvals, quant, 78)
      return hsvals
        
    #This is my addition to read data about ray properties. I wanted to define it with the 'gas' function below, but we want to use it to initialize the dictionary-like object housing the values first, like we do with hsvals. 
    def _get_rayvals(self):
      if self.handle['Config'].attrs['RAY']!=1:
        print('this is a dataset, not a ray file')
      else:
        rayvals=dict(self.handle['/ray_properties'].items())
        #scale=self.handle['Header'].attrs['Time']
        #primary_pos=unyt.unyt_array([75000/2]*3, units='code_length', registry=self.unit_registry)
        primary_pos=self.hs('SubhaloPos')[0]
        dimensionless_ray_props=['ip_uv', 'ray_uv'] 
        original_ray_props=['ip', 'ip_coordinate', 'ip_d_along_ray', 'start_position', 'end_position']
        new_ray_props=[prop+'_kpc' for prop in original_ray_props]
        original_units, new_units=['code_length']*5, ['kpc']*5
      
        #First, we give units to our code_unit quantities:
        rayvals.update((original_ray_props[i], unyt.unyt_array(rayvals[original_ray_props[i]], original_units[i], registry=self.unit_registry)) for i in range(len(original_ray_props)))
        rayvals.update((dimensionless_ray_props[i], unyt.unyt_array(rayvals[dimensionless_ray_props[i]], 'dimensionless')) for i in range(len(dimensionless_ray_props)))
        #Now, we create physical unit versions:
        for i in range(len(original_ray_props)):
          prop=original_ray_props[i]
          if prop=='ip_coordinate':
            rayvals[prop+'_kpc']=(rayvals[prop]-primary_pos).to(new_units[i])
          else:
            rayvals[prop+'_kpc']=rayvals[prop][()].to(new_units[i])
        return rayvals
        
        
        
    #last addition: just convenience functions for headvals, hsvals, rayvals, gas, bh. Gas convenience function expanded after adding ray functionality. Tried to put it in plugins file, but there's not an obvious way to access the list of all important ray properties (ie, 'H_p0_number_density', etc). 
    
    def head(self, attribute):
      x=self.headvals[attribute]
      if type(x)==np.bytes_:
        return x
      elif x.shape==():
        return self.headvals[attribute][()]
      else:
        return self.headvals[attribute][:]
    
    def hs(self, attribute, snap=84, orientation=84):
    #reduced attribuite is necessary!
      reduced_attr=attribute.split('_')[0]
      if snap==78 and orientation==84 and reduced_attr in mixed_orientation_fields:
      #if snap==78 and orientation==84 and attribute in mixed_orientation_fields:
        layered_attribute=attribute+'_84orientation_78'
      elif snap==78:
        layered_attribute=attribute+'_78'
      else:
        layered_attribute=attribute
      x=self.hsvals[layered_attribute][()]
      if hasattr(x, 'units'):   #if it has units just return x
        return x
      elif x.dtype=='bool':
        return x
      else:
        return x*unyt.dimensionless
      

    #everything SHOULD have proper units already, including physical quantities. Except for the actual spectral stuff, which we give unyts here 
    def los(self, instrubute, spectral_prop=None, line=None, line_spectral_prop=None):
      #First, ray properties:
      if spectral_prop==None:
        if line and line_spectral_prop:
          x=unyt.unyt_array(self.rayvals[instrubute][line][line_spectral_prop], units=stored_observables[line_spectral_prop])
        else:
          x=self.rayvals[instrubute]
      #Now, spectral properties     
      elif spectral_prop=='lambda':
        x=self.rayvals[instrubute][spectral_prop]*unyt.Angstrom    
      else:
        x=self.rayvals[instrubute][spectral_prop]*unyt.dimensionless    
      return x
      
        
    def _halo_or_ray(self): 
      #list of fields that are only under, 'gas', not 'PartType0'
      if self.handle['Config'].attrs['RAY']==1:
      #this is annoying and a bit confusing, but in DATASETS 'entropy' is stored under 'gas', in RAYS it is stored under 'PartType0'. But it is the same values either way
        def gas(attribute, snap=84, orientation=84):
        #reduced attribute is necessary!
          reduced_attr=attribute.split('_')[0]
          if snap==78 and orientation==84 and reduced_attr in mixed_orientation_fields:
          #if snap==78 and orientation==84 and attribute in mixed_orientation_fields:
            layered_attribute=attribute+'_84orientation_78'    
          elif snap==78:
            layered_attribute=attribute+'_78'
          else:
            layered_attribute=attribute 
          if 'GFM_Metals_' in attribute and snap==78:
            #expect attribute like GFM_Metals_02; this isolates index 2
            metalnum=int(attribute.rsplit('_', 1)[1])
            return self.r['PartType0', 'GFM_Metals_78'][:, metalnum]  
          
          if attribute=='count':
            return [len(self.r['PartType0', 'ParticleIDs'])]*unyt.dimensionless     
          elif attribute in ('l', 'dl'):
            return unyt.unyt_array(self.r['PartType0', layered_attribute].value, units='code_length', registry=self.unit_registry)
          #here, could use original attribute for ray/yt-derived fields to avoid getting errors, but it would be misleading, because these properties are not calculated for our past properties. Instead, if you ask for "velocity_los" at snapshot 78, it SHOULD give you an error, because that's not an available field. Similar with "entropy" below, which is calculated by yt
          elif attribute=='velocity_los':
            return unyt.unyt_array(self.r['PartType0', layered_attribute].value, units='code_velocity', registry=self.unit_registry)
          elif 'number_density' in attribute or 'nuclei_density' in attribute:
            return self.r['PartType0', layered_attribute]*unyt.cm**-3
          elif '_density' in attribute and 'momentum' not in attribute:
            return self.r['PartType0', layered_attribute]*unyt.g*unyt.cm**-3
          elif attribute=='ParticleIDs':
            return np.int64(self.r['PartType0', layered_attribute])
          #For some reason, gets real finicky about boolean fields, and they abolutely have to be accessed with the [()]. Not an issue for ds files, only rays, but for uniformity include [()] in both 
          elif attribute in boolean_fields:
            return np.array(self.r['PartType0', layered_attribute][()], dtype='bool')
            #return np.array(self.handle['PartType0'][layered_attribute], dtype='bool')
          elif attribute=='entropy':
            return self.r['PartType0', layered_attribute]*unyt.cm**2*unyt.keV
          else:
            return self.r['PartType0', layered_attribute]      
      else:
        def gas(attribute, snap=84, orientation=84):
        #reduced attribute is necessary!
          reduced_attr=attribute.split('_')[0]
          if snap==78 and orientation==84 and reduced_attr in mixed_orientation_fields:
          #if snap==78 and orientation==84 and attribute in mixed_orientation_fields:
            layered_attribute=attribute+'_84orientation_78'    
          elif snap==78:
            layered_attribute=attribute+'_78'
          else:
            layered_attribute=attribute 
          if 'GFM_Metals_' in attribute and snap==78:
            #expect attribute like GFM_Metals_02; this isolates index 2
            metalnum=int(attribute.rsplit('_', 1)[1])
            return self.r['PartType0', 'GFM_Metals_78'][:, metalnum]
          #this is annoying and a bit confusing, but in DATASETS 'entropy' is stored under 'gas', in RAYS it is stored under 'PartType0'. But it is the same values either way
          #this is only an issue for cutouts/halo datasets, not rays
          if attribute in only_gas_fields:
            return self.r['gas', layered_attribute]
          elif attribute=='count':
            return [len(self.r['PartType0', 'ParticleIDs'])]*unyt.dimensionless
          elif attribute=='ParticleIDs':
            return np.int64(self.r['PartType0', layered_attribute])
          #For some reason, gets real finicky about boolean fields, and they abolutely have to be accessed with the [()]. Not an issue for ds files, only rays, but for uniformity include [()] in both 
          elif attribute in boolean_fields:
            return np.array(self.r['PartType0', layered_attribute][()], dtype='bool')
          else:
            return self.r['PartType0', layered_attribute]
      return gas
          
      
    def bh(self, attribute):
      if attribute=='count':
        return [len(self.r['PartType5', 'ParticleIDs'])]*unyt.dimensionless
      else:
        return self.r['PartType5', attribute]
        
    def stars(self, attribute): #TEMPORARY PLACEHOLDER FUNCTION, WILL ADD TO LATER
      if attribute=='count':
        return [len(self.r['PartType4', 'ParticleIDs'])]*unyt.dimensionless
      elif attribute=='ParticleIDs':
        return np.int64(self.r['PartType4', attribute])
      else:
        return self.r['PartType4', attribute]
        
###################################MY MAIN ADDITIONS ABOVE#############################################################
       
    def _set_code_unit_attributes(self):
        arepo_unit_base = self._get_uvals()
        # This rather convoluted logic is required to ensure that
        # units which are present in the Arepo dataset will be used
        # no matter what but that the user gets warned
        if arepo_unit_base is not None:
            if self._unit_base is None:
                self._unit_base = arepo_unit_base
            else:
                for unit in arepo_unit_base:
                    if unit == "cmcm":
                        continue
                    short_unit = unit.split("_")[0][4:].lower()
                    if short_unit in self._unit_base:
                        which_unit = short_unit
                        self._unit_base.pop(short_unit, None)
                    elif unit in self._unit_base:
                        which_unit = unit
                    else:
                        which_unit = None
                    if which_unit is not None:
                        msg = f"Overwriting '{which_unit}' in unit_base with what we found in the dataset."
                        mylog.warning(msg)
                    self._unit_base[unit] = arepo_unit_base[unit]
                if "cmcm" in arepo_unit_base:
                    self._unit_base["cmcm"] = arepo_unit_base["cmcm"]
        super()._set_code_unit_attributes()
        munit = np.sqrt(self.mass_unit / (self.time_unit**2 * self.length_unit)).to(
            "gauss"
        )
        if self.cosmological_simulation:
            self.magnetic_unit = self.quan(munit.value, f"{munit.units}/a**2")
        else:
            self.magnetic_unit = munit
