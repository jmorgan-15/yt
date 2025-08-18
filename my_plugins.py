from yt.frontends.arepo.data_structures import ArepoHDF5Dataset
import yt
import numpy as np
import unyt


#This script handles adding a large amount of new fields to particle data, including new coordinate systems, past particle data, and a comprehensive unit system for all particle quantities (gas, stars, and black holes). This file and yt.yaml should be placed in ~/.config/yt/ if possible; if plugins cannot be loaded from this location or you want to put it somewhere else, just specify the location when you enable plugins like:

#>>>yt.enable_plugins('plugins_file_location/my_plugins.py')
orientation='baryonic_L_orientation'
h=0.6774
#Info on converting scalar
gas_scalar_conversions={'Density':(1, 'code_density', 'Msun/pc**3', '_msun_pc3'), 'SubfindDMDensity':(1, 'code_density', 'Msun/pc**3', '_msun_pc3'), 'SubfindDensity':(1, 'code_density', 'Msun/pc**3', '_msun_pc3'), 'GFM_AGNRadiation':(4*np.pi, 'erg/s/cm**2','erg/s/cm**2', '_flux_erg_s_cm2'), 'GFM_CoolingRate':(1, 'erg*cm**3/s', 'erg*cm**3/s', '_ergcm3_s'), 'GFM_Metallicity':(1, 'code_metallicity', 'Zsun', '_solar'), 'InternalEnergy':(1, 'code_specific_energy', 'km**2/s**2', '_km2_s2'), 'MagneticFieldDivergence': (1, 'code_magnetic/code_length', 'gauss/km', '_g_km'), 'Masses':(1, 'code_mass', 'Msun', '_msun'), 'Potential':(1, 'code_velocity**2', 'km**2/s**2', '_km2_s2'), 'StarFormationRate':(1, 'Msun/yr', 'Msun/yr', '_msun_yr'), 'SubfindHsml':(1, 'code_length', 'kpc', '_kpc'), 'SubfindVelDisp':(1, 'km/s', 'km/s', '_km_s'), 'EnergyDissipation':(1, '(code_mass/code_length)*(km/s)**3', 'erg/s', '_erg_s'), 'velocity_los':(1, 'code_velocity', 'km/s', '_km_s'), 'l': (1, 'code_length', 'kpc', '_kpc'), 'dl':(1, 'code_length', 'kpc', '_kpc')}
gas_scalar_conversions_78={field+'_78':(unit_info[0], unit_info[1], unit_info[2], unit_info[3]+'_78') for field, unit_info in gas_scalar_conversions.items()}


star_scalar_conversions={'Masses':(1, 'code_mass', 'Msun', '_msun'), 'GFM_InitialMass':(1, 'code_mass', 'Msun', '_msun'), 'GFM_Metallicity':(1, 'code_metallicity', 'Zsun', '_solar'), 'Potential':(1, 'code_velocity**2', 'km**2/s**2', '_km2_s2'), 'Stellar_Hsml':(1, 'code_length', 'kpc', '_kpc'), 'SubfindHsml':(1, 'code_length', 'kpc', '_kpc'), 'SubfindDMDensity':(1, 'code_density', 'Msun/pc**3', '_msun_pc3'), 'SubfindDensity':(1, 'code_density', 'Msun/pc**3', '_msun_pc3'), 'SubfindVelDisp':(1, 'km/s', 'km/s', '_km_s')}

bh_scalar_conversions={'BH_BPressure':(4*np.pi, 'code_magnetic**2', 'gauss**2', '_gauss2'), 'BH_CumEgyInjection_QM':(1, 'code_mass*code_length**2/code_time**2', 'Msun*kpc**2/Gyr**2', '_msunkpc2_gyr2'), 'BH_CumEgyInjection_RM':(1, 'code_mass*code_length**2/code_time**2', 'Msun*kpc**2/Gyr**2', '_msunkpc2_gyr2'), 'Masses':(1, 'code_mass', 'Msun', '_msun'), 'BH_Mass':(1, 'code_mass', 'Msun', '_msun'), 'BH_CumMassGrowth_QM':(1, 'code_mass', 'Msun', '_msun'), 'BH_CumMassGrowth_RM':(1, 'code_mass', 'Msun', '_msun'), 'BH_Density':(1, 'code_density', 'Msun/pc**3', '_msun_pc3'), 'SubfindDMDensity':(1, 'code_density', 'Msun/pc**3', '_msun_pc3'), 'SubfindDensity':(1, 'code_density', 'Msun/pc**3', '_msun_pc3'), 'BH_HostHaloMass':(1, 'code_mass', 'Msun', '_msun'), 'BH_Hsml':(1, 'code_length', 'kpc', '_kpc'), 'SubfindHsml':(1, 'code_length', 'kpc', '_kpc'), 'BH_Mdot':(1, 'code_mass/code_time', 'Msun/Gyr', '_msun_gyr'), 'BH_MdotBondi':(1, 'code_mass/code_time', 'Msun/Gyr', '_msun_gyr'), 'BH_MdotEddington':(1, 'code_mass/code_time', 'Msun/Gyr', '_msun_gyr'), 'BH_Pressure':(1, 'code_mass/code_length/code_time**2', 'Msun/kpc/Gyr**2', '_msun_kpc_gyr2'), 'BH_U':(1, 'code_specific_energy', 'km**2/s**2', '_km2_s2'), 'Potential':(1, 'code_velocity**2', 'km**2/s**2', '_km2_s2'), 'SubfindVelDisp':(1, 'km/s', 'km/s', '_km_s')}



#Info on converting vectors
#Can't update same dict twice like this or get prop_78_84orientation_78, etc
gas_vector_conversions={'Coordinates':(1, 'code_length', 'kpc', '_kpc'), 'CenterOfMass':(1, 'code_length', 'kpc', '_kpc'), 'Velocities':(1, 'code_velocity', 'km/s', '_km_s'),  'MagneticField':(1, 'code_magnetic', 'gauss', '_gauss')}

gas_vector_conversions_78={field+'_78':(unit_info[0], unit_info[1], unit_info[2], unit_info[3]+'_78') for field, unit_info in gas_vector_conversions.items()}
gas_vector_conversions_84orientation_78={field+'_84orientation_78':(unit_info[0], unit_info[1], unit_info[2], unit_info[3]+'_84orientation_78') for field, unit_info in gas_vector_conversions.items()}

star_vector_conversions={'Coordinates':(1, 'code_length', 'kpc', '_kpc'), 'BirthPos':(1, 'code_length', 'kpc', '_kpc'), 'Velocities':(1, 'code_velocity', 'km/s', '_km_s'), 'BirthVel':(1, 'code_velocity', 'km/s', '_km_s')}

bh_vector_conversions={'Coordinates':(1, 'code_length', 'kpc', '_kpc'), 'Velocities':(1, 'code_velocity', 'km/s', '_km_s')}


#Info on CREATING spherical/cylindrical coord systems. This works a bit differently than the above, so slightly different structure
coord_names_units_dict={'spherical':[['spherical_r', 'spherical_theta', 'spherical_phi'], ['kpc', 'dimensionless', 'dimensionless']], 'cylindrical':[['cylindrical_R', 'cylindrical_phi', 'cylindrical_z'], ['kpc', 'dimensionless', 'kpc']]}
vel_names_units_dict={'spherical':[['spherical_rdot', 'spherical_thetadot', 'spherical_vtan'], ['km/s', '1/s', 'km/s']], 'cylindrical':[['cylindrical_Rdot', 'cylindrical_vtan', 'cylindrical_zdot'], ['km/s', 'km/s', 'km/s']]}

#sim_origin=unyt.unyt_array(75000/2, units='code_length', registry=ds.unit_registry)
def _get_scalar_func(_ptype, field_name, unit_dict):
  def _scalar(field, data):
    old_data=data[_ptype, field_name]
    x_old_units=unyt.unyt_array(old_data.value*unit_dict[field_name][0], units=unit_dict[field_name][1], registry=data.ds.unit_registry)
    return x_old_units.to(unit_dict[field_name][2])
  return _scalar
  
def _get_cart_func(_ptype, field_name, unit_dict):
  def rel_quantities(field, data):
    initial_units=unit_dict[field_name][1]
    old_data=unyt.unyt_array(data[_ptype, field_name].value, units=initial_units, registry=data.ds.unit_registry)    
    #Coordinates
    if field_name in ('Coordinates', 'BirthPos', 'Coordinates_84orientation_78', 'CenterOfMass', 'CenterOfMass_84orientation_78'):
      origin=data.ds.hs('SubhaloPos')[0]
    elif field_name in ('Coordinates_78', 'CenterOfMass_78'):
      origin=data.ds.hs('SubhaloPos_78')[0]
    #Velocities
    elif field_name in ('Velocities', 'BirthVel', 'Velocities_84orientation_78'):  
      origin=data.ds.hs('SubhaloVel')[0]
    elif field_name=='Velocities_78':
      origin=data.ds.hs('SubhaloVel_78')[0]
    #B field
    elif field_name in ('MagneticField', 'MagneticField_78', 'MagneticField_84orientation_78'):
      origin=unyt.unyt_array([0]*3, units=unit_dict[field_name][1], registry=data.ds.unit_registry)
    delta=(old_data-origin).to(unit_dict[field_name][2])
    return delta
  return rel_quantities


#The spherical and cylindrical coordinate systems are a bit harder to deal with because they have mixed units (distance/angle). NOTE: this function uses Coords_kpc, Vels_km_s, so they must be initiated first, or cylindrical/spherical coords will not populate. 

coord_types=('Coordinates', 'CenterOfMass', 'BirthPos')
vel_types=('Velocities', 'BirthVel')
def _get_sphercyl_func(_ptype, field_name, coord_sys, index):
  if coord_sys=='spherical':
    def spher_co_vel(field, data):
      #These relative cartesean coordinates/velocities are already scaled appropriately from _get_cart_func, so we shouldn't need anything with units/unyt.unyt_arrays
#coordinates
      if any(c_type in field_name for c_type in coord_types):
        x, y, z=data[_ptype, field_name][:, 0], data[_ptype, field_name][:, 1], data[_ptype, field_name][:, 2]
        r, R=np.sqrt(x**2+y**2+z**2), np.sqrt(x**2+y**2)
        if index==0:
          return r
        elif index==1:
          theta=np.arctan2(np.sqrt(x**2+y**2), z)
          return theta 
        elif index==2:
          phi=np.arctan2(y, x) 
          return phi
#velocities
      elif any(v_type in field_name for v_type in vel_types):  #Because of vtan's dependence on r, we need to get both velocities AND coordinates and correctly match them
        vx, vy, vz=data[_ptype, field_name][:, 0], data[_ptype, field_name][:, 1], data[_ptype, field_name][:, 2]  
        if field_name=='BirthVel_km_s':
          x, y, z=data[_ptype, 'BirthPos_kpc'][:, 0], data[_ptype, 'BirthPos_kpc'][:, 1], data[_ptype, 'BirthPos_kpc'][:, 2]
        elif '_84orientation_78' in field_name:
          x, y, z=data[_ptype, 'Coordinates_84orientation_78_kpc'][:, 0], data[_ptype, 'Coordinates_84orientation_78_kpc'][:, 1], data[_ptype, 'Coordinates_84orientation_78_kpc'][:, 2] 
        elif '_78' in field_name:
          x, y, z=data[_ptype, 'Coordinates_78_kpc'][:, 0], data[_ptype, 'Coordinates_78_kpc'][:, 1], data[_ptype, 'Coordinates_78_kpc'][:, 2]
        else:
          x, y, z=data[_ptype, 'Coordinates_kpc'][:, 0], data[_ptype, 'Coordinates_kpc'][:, 1], data[_ptype, 'Coordinates_kpc'][:, 2]          
        r, R=np.sqrt(x**2+y**2+z**2), np.sqrt(x**2+y**2)
        if index==0:
          rdot=(x*vx+y*vy+z*vz)/r
          return rdot
        elif index==1:
          #this is for ease of reading. thetadot is annoying to compute
          form_of_arctan=1./((x**2+y**2)/z**2+1.) #looks like 1/(x**2+1)
          ddtsqrtx2plusy2=(x*vx+y*vy)/np.sqrt(x**2+y**2)
          first_term=ddtsqrtx2plusy2/z
          second_term=vz*np.sqrt(x**2+y**2)/z**2
          thetadot=form_of_arctan*(first_term-second_term) #Finally! NOTE: Both thetadot and phidot *would* have a conversion factor because we have speeds in km/s and distances in kpc. But unyt.unyt_arrays should take care of this for us
          return thetadot.to('1/s') #trig velocities returns as 1/s, need to convert to rad/s
          #return unyt.unyt_array(thetadot, units='1/s')
        elif index==2:
          phidot=(1./((y/x)**2+1.))*(vy/x-vx*y/x**2)
          return unyt.unyt_array((phidot*R).value, units='kpc/s').to('km/s')     
          #return phidot 
          #return x
    return spher_co_vel

  elif coord_sys=='cylindrical':
    def cyl_co_vel(field, data):
      #relco, relvel=relco_func(field, data), relvel_func(field, data)   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
      if any(c_type in field_name for c_type in coord_types):
        x, y, z=data[_ptype, field_name][:, 0], data[_ptype, field_name][:, 1], data[_ptype, field_name][:, 2]
        r, R=np.sqrt(x**2+y**2+z**2), np.sqrt(x**2+y**2)
        if index==0:
          return R
        elif index==1:
          phi=np.arctan2(y, x)
          return phi
        elif index==2:
          return z
      elif any(v_type in field_name for v_type in vel_types):
        vx, vy, vz=data[_ptype, field_name][:, 0], data[_ptype, field_name][:, 1], data[_ptype, field_name][:, 2]  
        if field_name=='BirthVel_km_s':
          x, y, z=data[_ptype, 'BirthPos_kpc'][:, 0], data[_ptype, 'BirthPos_kpc'][:, 1], data[_ptype, 'BirthPos_kpc'][:, 2]
        elif '_84orientation_78' in field_name:
          x, y, z=data[_ptype, 'Coordinates_84orientation_78_kpc'][:, 0], data[_ptype, 'Coordinates_84orientation_78_kpc'][:, 1], data[_ptype, 'Coordinates_84orientation_78_kpc'][:, 2] 
        elif '_78' in field_name:
          x, y, z=data[_ptype, 'Coordinates_78_kpc'][:, 0], data[_ptype, 'Coordinates_78_kpc'][:, 1], data[_ptype, 'Coordinates_78_kpc'][:, 2]
        else:
          x, y, z=data[_ptype, 'Coordinates_kpc'][:, 0], data[_ptype, 'Coordinates_kpc'][:, 1], data[_ptype, 'Coordinates_kpc'][:, 2]
        r, R=np.sqrt(x**2+y**2+z**2), np.sqrt(x**2+y**2)
        if index==0:
          Rdot=(x*vx+y*vy)/R
          return Rdot
        elif index==1:
          phidot=(1./((y/x)**2+1.))*(vy/x-vx*y/x**2)   
          return unyt.unyt_array((phidot*R).value, units='kpc/s').to('km/s')
          #return phidot
          #return x
        elif index==2:
          return vz         
    return cyl_co_vel





#First, add scalar gas fields:
for field_name, unit_info in gas_scalar_conversions.items():
  add_field(
    ('PartType0', field_name+unit_info[3]),  #for snapshot 78 quantities, field_name
    function=_get_scalar_func('PartType0', field_name, gas_scalar_conversions),
    sampling_type='particle',
    units=unit_info[2],
    )
#Now, add past scalar gas fields:
for field_name, unit_info in gas_scalar_conversions_78.items():
  add_field(
    ('PartType0', field_name[:-3]+unit_info[3]),  #for snapshot 78 quantities, field_name
    function=_get_scalar_func('PartType0', field_name, gas_scalar_conversions_78),
    sampling_type='particle',
    units=unit_info[2],
    )
#Now all gas cartesean vector fields:
for field_name, unit_info in gas_vector_conversions.items():
  add_field(
    ('PartType0', field_name+unit_info[3]),
    function=_get_cart_func('PartType0', field_name, gas_vector_conversions),
    sampling_type='particle',
    units=unit_info[2],
    )

#Now all past gas carteasian vector fields
for field_name, unit_info in gas_vector_conversions_78.items():
  add_field(
    ('PartType0', field_name[:-3]+unit_info[3]),
    function=_get_cart_func('PartType0', field_name, gas_vector_conversions_78),
    sampling_type='particle',
    units=unit_info[2],
    )
    
#past gas vector quantities with 84 orientation 
for field_name, unit_info in gas_vector_conversions_84orientation_78.items():
  add_field(
    ('PartType0', field_name[:-17]+unit_info[3]),
    function=_get_cart_func('PartType0', field_name, gas_vector_conversions_84orientation_78),
    sampling_type='particle',
    units=unit_info[2],
    )
    
#Stellar scalars:
for field_name, unit_info in star_scalar_conversions.items():
  add_field(
    ('PartType4', field_name+unit_info[3]),
    function=_get_scalar_func('PartType4', field_name, star_scalar_conversions),
    sampling_type='particle',
    units=unit_info[2],
    )
    
#Stellar vectors:
for field_name, unit_info in star_vector_conversions.items():
  add_field(
    ('PartType4', field_name+unit_info[3]),
    function=_get_cart_func('PartType4', field_name, star_vector_conversions),
    sampling_type='particle',
    units=unit_info[2],
    )

#BH scalars:
for field_name, unit_info in bh_scalar_conversions.items():
  add_field(
    ('PartType5', field_name+unit_info[3]),
    function=_get_scalar_func('PartType5', field_name, bh_scalar_conversions),
    sampling_type='particle',
    units=unit_info[2],
    )
    
#BH vectors:
for field_name, unit_info in bh_vector_conversions.items():
  add_field(
    ('PartType5', field_name+unit_info[3]),
    function=_get_cart_func('PartType5', field_name, bh_vector_conversions),
    sampling_type='particle',
    units=unit_info[2],
    )
    
#Now we add the spherical/cylindrical coordinates. These are a bit harder because some are angular and some are not  
for i in range(3):  
  for coord_type, coord_names_units in coord_names_units_dict.items():
    #First, coordinates that are common between particle types
    for _ptype in ['PartType0', 'PartType4', 'PartType5']:
      add_field(
        (_ptype, coord_names_units[0][i]),
        function=_get_sphercyl_func(_ptype, 'Coordinates_kpc', coord_type, i),
        sampling_type='particle', 
        units=coord_names_units[1][i],
        )
    #Next, coordinates specific to certain particle types:
    #Gas, CenterOfMass
    add_field(
      ('PartType0', coord_names_units[0][i]+'_com'),
      function=_get_sphercyl_func('PartType0', 'CenterOfMass_kpc', coord_type, i),
      sampling_type='particle',
      units=coord_names_units[1][i],
      )
    #Gas, past coordinates with orientation defined by snapshot 84  
    add_field(
      ('PartType0', coord_names_units[0][i]+'_84orientation_78'),
      function=_get_sphercyl_func('PartType0', 'Coordinates_84orientation_78_kpc', coord_type, i),
      sampling_type='particle',
      units=coord_names_units[1][i],
      )
    #Gas, past coordinates defined by orientation at snapshot 78
    add_field(
      ('PartType0', coord_names_units[0][i]+'_78'),
      function=_get_sphercyl_func('PartType0', 'Coordinates_78_kpc', coord_type, i),
      sampling_type='particle',
      units=coord_names_units[1][i],
      )   
    #Gas, past coordinates defined by orientation at snapshot 84, COM
    #DECIDED NOT TO ADD THESE FOR NOW; Current position matters a lot because of cloud finding, so include both Pos and COM, but past position much less sensitive
    
    #Stars, birth position
    add_field(
      ('PartType4', coord_names_units[0][i]+'_birth'),
      function=_get_sphercyl_func('PartType4', 'BirthPos_kpc', coord_type, i),
      sampling_type='particle',
      units=coord_names_units[1][i],
      )
    #BH, CenterOfMass
    add_field(
      ('PartType5', coord_names_units[0][i]+'_com'),
      function=_get_sphercyl_func('PartType5', 'CenterOfMass_kpc', coord_type, i),
      sampling_type='particle',
      units=coord_names_units[1][i],
      )
    
  for vel_type, vel_names_units in vel_names_units_dict.items():
    #First, velocities common to all particle types:
    for _ptype in ['PartType0', 'PartType4', 'PartType5']:
      add_field(
        (_ptype, vel_names_units[0][i]),
        function=_get_sphercyl_func(_ptype, 'Velocities_km_s', vel_type, i),
        sampling_type='particle',
        units=vel_names_units[1][i],
        )
    #Next, velocities specific to certain particle types:
    #Gas, past velocities defined by orientation at snapshot 84  
    add_field(
      ('PartType0', vel_names_units[0][i]+'_84orientation_78'),
      function=_get_sphercyl_func('PartType0', 'Velocities_84orientation_78_km_s', vel_type, i),
      sampling_type='particle',
      units=vel_names_units[1][i],
      )
    #Gas, past velocities defined by orientation at snapshot 78
    add_field(
      ('PartType0', vel_names_units[0][i]+'_78'),
      function=_get_sphercyl_func('PartType0', 'Velocities_78_km_s', vel_type, i),
      sampling_type='particle',
      units=vel_names_units[1][i],
      )
    #Stars, birth velocity
    add_field(
      ('PartType4', vel_names_units[0][i]+'_birth'),
      function=_get_sphercyl_func('PartType4', 'BirthVel_km_s', vel_type, i),
      sampling_type='particle',
      units=vel_names_units[1][i],
      )
    
    
    













