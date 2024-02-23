# Ex Deorum Recipe Converter
This repository contains a Python script to convert Ex Nihilo: Sequentia recipes to Ex Deorum recipes.

## Features
This script supports converting a folder of Ex Nihilo: Sequentia recipes, including subdirectories, and outputting 
the equivalent recipes in an output folder. For sieve recipes that use the Emerald mesh, it is also possible to convert
those recipes to use Ex Deorum's Golden mesh instead.

The following recipe types are supported:
- Barrel composting recipes (`exnihilosequentia:compost` -> `exdeorum:barrel_compost`)
- Hammer recipes (`exnihilosequentia:hammer`, `exnihilosequentia:crushing` -> `exdeorum:barrel_compost`)
- Crucible heat source recipes (`exnihilosequentia:heat` -> `exdeorum:crucible_heat_source`)

Some features that still need to be implemented:
- Option to maintain directory sorting of the input files so that outputted files will appear in the same directory structure
- Support for Barrel Fluid Transformation recipes (not yet implemented as of Ex Deorum 1.25)
- Support for Crook Harvesting recipes
- Automatically converting Ex Nihilo: Sequentia items like pebbles, ore chunks, etc. to Ex Deorum equivalents
- Support for ZIP files

## How to use
You will need Python 3.x installed to run this script. Download the `converter.py` script from this repository.

Next, create a directory called `input` next to where you saved `converter.py`. Add the Ex Nihilo: Sequentia 
recipes you want to convert to this directory.

To convert the input files, run `converter.py`. You can do this by double-clicking the file or, in your command line
of choice, run `py converter.py`. The converted files will appear in a newly created `output` directory.

### Additional options
**To export minified/compressed JSONs**: Run `py converter.py -m` or `py converter.py --minify`.

**To skip "Is this okay?" prompt**: Run `py converter.py -y`

**To skip "Golden mesh" prompt**: Run `py converter.py -yg` for yes, or `py converter.py -ng` for no.