This file assumes you have passing familiarity with the content of the base yt readme and it's contents-- specifically about installing yt and using basic functions. DO NOT follow the base yt installation guide, but read it so this one will be easier to understand!

Assuming you have some version of yt/trident installed, we first UNINSTALL it and start from scratch. If you're doing a totally new install you can skip steps 1-4. 
1) BEFORE UNINSTALLING ANYTHING find the file locations:

  >>>import trident
  >>>import yt
  >>>trident.__file__
  >>>yt.__file__
Record these locations so that after uninstalling you can check them for any remaining folder/files and delete those.

2) Uninstall Trident. On command line:

  $pip uninstall trident 
  
Now, check your location for trident from Step 1 and delete any related files still there

3) Uninstall yt. Now this should have been done through anaconda before, but I also found that pip uninstall yt did something​ after conda uninstall yt. If your yt folder is under an anaconda/miniconda folder, then conda uninstall should work. But to be safe we'll just do both:

  $conda uninstall yt
  $pip uninstall yt
  
Check your yt location and ALSO this directory for errant yt files and delete them (if you can get to it-- yours may be different, but this is where my packages installed with pip end up):

~/.local/lib/python3.8/site-packages/yt

4) Check to be sure everything is really gone:

  >>>import yt (should fail)
  >>>import trident (should fail)
  
If the above works you still have some bits of yt/Trident around. Try .__file__ again and check that location for anything related to yt/Trident.

5) We will build our special version of yt from source. First, navigate to the folder you want to install yt into. Then:

$git clone https://github.com/jmorgan-15/yt
$cd yt
$git checkout -b bailin_research_group_yt
$python -m pip install --upgrade pip
$python -m pip install --user -e .


6) Now we should be able to import yt.....but I also note that in my setup, "$which yt" no longer returns anything, despite my code which absolutely needs yt running correctly, so....it is​ somewhere. Try

  >>>import yt (should work)
  
If yt doesn't import right, it may be issues with: matplotlib, h5py, or astropy. I got errors about those packages on my first attempt:

  A. An error that looks like: "ValueError: Trying to reregister the built-in cmap 'cubehelix'...." this is due to yt and matplotlib using the same names for certain colormaps. This should be solved by updating both matplotlib and yt:

    $python -m install -U pip    (this part may be redundant because we just updated pip in part 5, but this syntax is slightly different so I'm leaving it)
    $python -m pip install --upgrade matplotlib
    $python -m pip install --upgrade yt

  B. An error that says, "h5py has no attribute 'version'". This happens when h5py is essentially gutted, but the parent folder still exists. My initial try at installing yt did this, but I think most people should be fine. If not though, check:

    >>>import h5py
    >>>h5py.__file__

  If it's under your conda folder, then

    $conda uninstall h5py

  If not, use pip:

    $pip uninstall h5py

  Now, REinstall with pip either way:

    $pip install h5py

  C. An error that mentions astropy. I honestly forget what it was, but it does mention astropy by name. Similar solution:

    $python -m pip install --upgrade astropy

  If that doesn't fix it, uninstall astropy with pip, reinstall it with pip, and update it with pip as we did with some packages above.
  
7) Navigate to yt installation directory and move my_plugins.py and yt.yaml files to ~/.config/yt/ (make directory if necessary). Then, import yt and enable plugins:

  >>>import yt
  >>>yt.enable_plugins()

If this fails, try explicitely defining the path (total path, relative path may work but not stable in other scripts)

  >>>yt.enable_plugins('path/to/plugins_file.py')


8) Enter python and load up a data file

  >>>import yt
  >>>yt.enable_plugins()
  >>>ds=yt.load('path/to_HDF5_file.hdf5')
  >>>ds.gas('spherical_r')

If everything has gone correctly so far, this should print out a correctly unit-ed array of radial coordinates for the gas. Spherical and cylindrical coordinates are an exception, but most quantities with physical units have the units specified in their name:

  >>>ds.gas('Velocities_km_s') 

9) New yt features

ray fields and halo/subhalo fields can be found by:

  >>>ray_properties=ray_info.rayvals.keys()
  >>>halo_and_subhalos_properties=ray_info.hsvals.keys()


There is no '.gasvals', '.bhvals' etc objects. To get properties of gas, star, or black hole particles is a bit more annoying because yt makes a lot of fields on its own:
  >>>gas_properties=[]
  >>>for entry in ray_info.derived_field_list:
  >>>  if entry[0]=='PartType0':
  >>>    gas_properties.append(entry[1])
derived_field_list is an array of len 2 tuples where the first entry specifies particle type by number and the second is the property.

The .gas(), .star(), .bh(), and .hs() methods handle any last-minute adjustments that need to be made before displaying data, such as giving units to spectral properties derived by Trident. Use them instead of the standard .r['particle_type', 'field_name'] method. 

Past particle properties are also available. To get the previous coordinates of gas particles *in the current coordinate system, which is based on current galaxy angular momentum*:

  >>>ds.gas(property_name, snapshot_number)   

For our purposes, our "base" properties are in snapshot 84 (so the default), the only other available is 78, so snapshot+number is always either 78 or left out. 

To get the previous coordinates of gas particles *in their native coordinate system, which is based on the past galaxy angular momentum*:

  >>>ds.gas(property_name, snapshot_number, snapshot_number)  #yes, snapshot number is repeated; the second instance tells what snapshot to take the coordinate system from

So if I wanted to know the galactocentric coordinates of the gas in the past, IN the coordinate system the galaxy had in the past:

  >>>ds.gas('Coordinates_kpc', 78, 78)


I am also proud to announce: everything​ should have units now! Quantities straight from the simulation are in code units, and the physical units version of that property is named after those units, ie, 'MagneticField'-->'MagneticField_gauss'. Coords and vels are a bit weirder because TNG uses one version, yt uses a different version, and we think​ in a third version of the coordinates/velocities. So coords/vels straight from TNG are labelled "_TNG". Coords/vels used by yt (which we shouldn't ever need to use) are 'Coordinates', 'Velocites'. Galactocentric coordinates/velocities are 'Coordinates_kpc' and 'Velocities_km_s'. In each case, the unyt_array returned should also list the units used. The only "dimensionless" quantities are mass ratios (GFM_Metals, GFM_MetalsTagged; total metallicity does have a version with units: 'GFM_Metallicity_zsun'), and angles/frequencies, because I don't like how unyt does radians. 


In the custom ray hdf5 files that Trident now makes, you can use the same syntax to find spectral properties:

  >>>my_ray=yt.load('ray.hdf5')
  >>>my_ray.los(instrument_name, spectral_property)

Will tell you ie, the flux as a function of wavelength for instrument_name. If observables were stored when making the ray initially, that data about individual particle contributions can also be accessed:

  >>>my_ray.los(instrument_name, line=line_name, line_spectral_prop=spectral_prop)
  
To see a list of available lines for a given instrument:

  >>>my_ray.rayvals[instrument_name].keys()
  
And to see a list of spectral properties for that line:

  >>>my_ray.rayvals[instrument_name][line_name].keys()

The generation of Trident rays is discussed in more detail in the Trident bailin_research_group_trident_readme.txt file
