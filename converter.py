import json
import sys
import os


def ens_mesh_to_ed(ens_mesh_type: str) -> str:
    if ens_mesh_type == 'string':
        return 'exdeorum:string_mesh'
    elif ens_mesh_type == 'flint':
        return 'exdeorum:flint_mesh'
    elif ens_mesh_type == 'iron':
        return 'exdeorum:iron_mesh'
    elif ens_mesh_type == 'diamond':
        return 'exdeorum:diamond_mesh'
    elif ens_mesh_type == 'netherite':
        return 'exdeorum:netherite_mesh'
    elif ens_mesh_type == 'emerald':
        if 'CONVERT_EMERALD_TO_GOLD' not in globals():
            globals()['CONVERT_EMERALD_TO_GOLD'] = input('Found a Sieve recipe that requires an Emerald Mesh, but Ex Deorum does not add an Emerald Mesh. \nUse Gold Mesh instead? (y/n)\n').lower() == 'y'

        if globals()['CONVERT_EMERALD_TO_GOLD']:
            return 'exdeorum:golden_mesh'
        else:
            return ''
    else:
        return input(f"Unknown mesh type '{ens_mesh_type}', please enter item ID of correct mesh: ")


def ens_rolls_to_number_provider(ens_rolls: list) -> object:
    const = 0
    summation = []
    for roll in ens_rolls:
        if 'amount' in roll:
            n = roll['amount']
        else:
            n = 1
        if roll['chance'] == 1.0:
            const += n
        else:
            summation.append({
                'type': 'minecraft:binomial',
                'n': n,
                'p': roll['chance']
            })

    # Dedupe constant rolls
    if const > 0:
        summation.append(str(const))

    if len(summation) == 1:
        return summation[0]
    else:
        return {
            'type': 'exdeorum:summation',
            'values': summation
        }


# Return a list of JSON recipes representing Ex Deorum recipes for the given ENS recipe
def ens_convert_sieve_recipe(recipe_json: dict) -> list:
    recipe_list = []
    ingredient = recipe_json['input']
    result_item_id = recipe_json['result']['item']

    # Map of mesh type to rolls
    mesh_roll_lists = {}

    # Split rolls into sub lists based on the mesh type
    for roll in recipe_json['rolls']:
        roll_mesh = ens_mesh_to_ed(roll['mesh'])

        if roll_mesh not in mesh_roll_lists and roll_mesh != '':
            mesh_roll_lists[roll_mesh] = []

        mesh_roll_lists[roll_mesh].append(roll)

    for mesh_type in mesh_roll_lists.keys():
        recipe = {
            'type': 'exdeorum:sieve',
            'ingredient': ingredient,
            'mesh': mesh_type,
            'result': result_item_id,
            'result_amount': ens_rolls_to_number_provider(mesh_roll_lists[mesh_type])
        }

        recipe_list.append(recipe)

    return recipe_list


def ens_convert_heat_recipe(recipe_json: dict) -> dict:
    recipe = {
        'type': 'exdeorum:crucible_heat_source',
        'heat_value': recipe_json['amount'],
        'block_predicate': {
            'block': recipe_json['block']
        }
    }
    if 'state' in recipe_json:
        recipe['block_predicate']['state'] = recipe_json['state']
    return recipe


def ens_convert_crucible_recipe(recipe_json: dict) -> dict:
    recipe = {
        'ingredient': recipe_json['input'],
        'fluid': {
            'FluidName': recipe_json['fluidResult']['fluid']
        }
    }
    # Schema is different on 1.20.1
    if 'amount' in recipe_json['fluidResult']:
        recipe['fluid']['Amount'] = recipe_json['fluidResult']['amount']
    else:
        recipe['fluid']['Amount'] = recipe_json['amount']
    # Ex Deorum uses two separate recipe types, ENS puts it all into one
    if recipe_json['crucibleType'] == 'fired':
        recipe['type'] = 'exdeorum:lava_crucible'
    else:
        recipe['type'] = 'exdeorum:water_crucible'

    return recipe


def ens_convert_hammer_recipe(recipe_json: dict) -> list:
    recipe_list = []

    recipe_input = recipe_json['input']

    item_to_counts = {}

    for result in recipe_json['results']:
        result_item = result['item']
        if result_item not in item_to_counts:
            item_to_counts[result_item] = []
        item_to_counts[result_item].append(result)

    for (item, chances) in item_to_counts.items():
        recipe_list.append({
            'type': 'exdeorum:hammer',
            'ingredient': recipe_input,
            'result': item,
            'result_amount': ens_rolls_to_number_provider(chances)
        })

    return recipe_list


def ens_convert_compost_recipe(recipe_json: dict) -> dict:
    return {
        'type': 'exdeorum:barrel_compost',
        'ingredient': recipe_json['input'],
        'amount': recipe_json['amount']
    }


def ens_convert_fluid_item_recipe(recipe_json: dict) -> dict:
    recipe = {
        'type': 'exdeorum:barrel_mixing',
        'fluid': recipe_json['fluid']['fluid'],
        'ingredient': recipe_json['input'],
        'result': recipe_json['result']['item']
    }

    if 'amount' in recipe_json['fluid']:
        recipe['fluid_amount'] = recipe_json['fluid']['amount']
    else:
        recipe['fluid_amount'] = 1000

    return recipe


def ens_convert_fluid_on_top(recipe_json: dict) -> dict:
    recipe = {
        'type': 'exdeorum:barrel_fluid_mixing',
        'additive_fluid': recipe_json['fluidOnTop']['fluid'],
        'base_fluid': recipe_json['fluidInTank']['fluid'],
        'result': recipe_json['result']['item']
    }

    if 'amount' in recipe_json['fluidInTank']:
        recipe['base_fluid_amount'] = recipe_json['fluidInTank']['amount']
    else:
        recipe['base_fluid_amount'] = 1000

    return recipe


def main():
    input_folder = os.path.abspath('input')
    output_folder = os.path.abspath('output')
    autorun = '-y' in sys.argv
    verbose = '-v' in sys.argv or '--verbose'
    if '-m' in sys.argv or '--minify' in sys.argv:
        globals()['MINIFY_OUTPUT'] = True
    if '-yg' in sys.argv:
        if '-ng' in sys.argv:
            print('Warning: Specified both \'-yg\' and \'-ng\': ignoring \'-ng\', emerald mesh sieve recipes will use golden mesh')
        globals()['CONVERT_EMERALD_TO_GOLD'] = True
    elif '-ng' in sys.argv:
        globals()['CONVERT_EMERALD_TO_GOLD'] = False

    if not os.path.isdir(input_folder):
        print('Failed to start converter: converter.py must be placed next to (not inside) of a folder called input, '
              'containing the Ex Nihilo Sequentia recipes to convert.')
        exit(-1)

    if not autorun:
        if 'y' != input(f"Reading Ex Nihilo Sequentia recipes from...\n{input_folder}\n...and exporting converted Ex Deorum recipes to...\n{output_folder}\nIs this okay? (y/n, or rerun command with -y)\n"):
            print('Aborting file conversions.')
            return

    for root, subdirs, files in os.walk(input_folder):
        print(f"Found {len(files)} recipes in {root} to convert...")

        for file_name in files:
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)

                with open(file_path) as file:
                    # useful for debugging
                    if verbose:
                        print(f"Attempting to convert file {file_path}")

                    try:
                        ens_recipe_json = json.load(file)
                    except json.decoder.JSONDecodeError:
                        print(f"Unable to parse {file_name} as JSON - skipping")
                    ens_recipe_type = ens_recipe_json['type']

                    # Sifting / Sieve
                    if ens_recipe_type == 'exnihilosequentia:sifting' or ens_recipe_type == 'exnihilosequentia:sieve':
                        export_multiple_recipes(ens_recipe_json, ens_convert_sieve_recipe, output_folder, 'sieve', file_name)
                    # Crushing / Hammer
                    elif ens_recipe_type == 'exnihilosequentia:crushing' or ens_recipe_type == 'exnihilosequentia:hammer':
                        export_multiple_recipes(ens_recipe_json, ens_convert_hammer_recipe, output_folder, 'hammer', file_name)
                    else:
                        # Heat     (why didn't they come up with a stupid name for this one too ?)
                        if ens_recipe_type == 'exnihilosequentia:heat':
                            export_recipe(ens_convert_heat_recipe(ens_recipe_json), output_folder, 'crucible_heat_source', file_name)
                        # Compost     (how about "decomposing" as a new name ?)
                        elif ens_recipe_type == 'exnihilosequentia:compost':
                            export_recipe(ens_convert_compost_recipe(ens_recipe_json), output_folder, 'barrel_compost', file_name)
                        # Precipitate / Fluid Item     (wtf were they thinking when they named these recipe categories XD)
                        elif ens_recipe_type == 'exnihilosequentia:precipitate' or ens_recipe_type == 'exnihilosequentia:fluid_item':
                            export_recipe(ens_convert_fluid_item_recipe(ens_recipe_json), output_folder, 'barrel_mixing', file_name)
                        # Solidifying / Fluid on top
                        elif ens_recipe_type == 'exnihilosequentia:fluid_on_top' or ens_recipe_type == 'exnihilosequentia:solidifying':
                            export_recipe(ens_convert_fluid_on_top(ens_recipe_json), output_folder, 'barrel_fluid_mixing', file_name)
                        # Melting / Crucible
                        elif ens_recipe_type == 'exnihilosequentia:melting' or ens_recipe_type == 'exnihilosequentia:crucible':
                            result_recipe = ens_convert_crucible_recipe(ens_recipe_json)

                            if result_recipe['type'] == 'exdeorum:lava_crucible':
                                export_recipe(result_recipe, output_folder, 'lava_crucible', file_name)
                            else:
                                export_recipe(result_recipe, output_folder, 'water_crucible', file_name)
                        # Transition / Fluid transform
                        elif ens_recipe_type == 'exnihilosequentia:transition' or ens_recipe_type == 'exnihilosequentia:fluid_transform':
                            print(f"Could not convert {ens_recipe_type} recipe {file_path}: Barrel fluid conversion recipes are not yet implemented in Ex Deorum. See issue #4 on Ex Deorum GitHub for updates")
                        else:
                            print(f"Could not convert recipe {file_path} unknown recipe type {ens_recipe_type}")


def export_recipe(converted_recipe: dict, output_folder: str, result_folder: str, result_name: str):
    result_folder = os.path.join(output_folder, result_folder)
    if not os.path.isdir(result_folder):
        os.mkdir(result_folder)
        print(f"Created directory {result_folder} at {os.path.abspath(result_folder)}")
    if 'MINIFY_OUTPUT' in globals():
        indent = None
    else:
        indent = 2
    json.dump(converted_recipe, open(os.path.join(output_folder, result_folder, result_name), mode='w'), indent=indent)


def export_multiple_recipes(recipe_json: dict, conversion_function, output_folder: str, result_folder: str, file_name: str):
    result_number = 1

    for converted_recipe in conversion_function(recipe_json):
        result_name = file_name[:-5] + '_' + str(result_number) + '.json'
        result_number += 1
        export_recipe(converted_recipe, output_folder, result_folder, result_name)


if __name__ == '__main__':
    main()
