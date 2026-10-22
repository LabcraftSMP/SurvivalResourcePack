from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import shutil



@dataclass
class ResourceContext:
    group: str
    folder_path: str
    file_name: str
    name: str
    uuid: str



path = os.path.dirname(os.path.realpath(__file__))
export = path + '/export/resources'
player_resources = path + '/player_resources/'
resource_map = {}

def main():
    shutil.copytree(path + '/resources', export)

    if (os.path.isdir(player_resources)):
        for uuid in os.listdir(player_resources):
            process_player_folder(uuid)

    shutil.make_archive(export, 'zip', export)
    shutil.rmtree(path + '/export/resources')
    save_json(path + '/export/resource_map.json', resource_map)



def process_player_folder(uuid: str):
    folder_path = player_resources + uuid
    resource_map[uuid] = {}

    process_resource_group(folder_path, uuid, 'basic_texture', basic_texture_processor)
    process_resource_group(folder_path, uuid, 'tool_texture', tool_texture_processor)
    process_resource_group(folder_path, uuid, 'elytra_texture', elytra_texture_processor)
    process_resource_group(folder_path, uuid, 'custom_model', custom_model_processor)



def process_resource_group(folder_path: str, uuid: str, group: str, processor):
    group_path = folder_path + '/' + group + '/'
    if os.path.isdir(group_path):
        resource_map[uuid][group] = []
        run_player_resource_processor(group, group_path, uuid, processor)



def basic_texture_processor(context: ResourceContext):
    process_simple_item(context, 'item/generated')



def tool_texture_processor(context: ResourceContext):
    process_simple_item(context, 'item/handheld')



def elytra_texture_processor(context: ResourceContext):
    namespace = export + '/assets/' + context.uuid

    shutil.copyfile(
        context.folder_path + 'wings/' + context.file_name,
        prepare_path(namespace + '/textures/entity/equipment/wings/', context.file_name)
    )

    save_json(
        prepare_path(namespace + '/equipment/elytra/', context.name + '.json'),
        { 'layers': { 'wings': [{ 'texture': context.uuid + ':' + context.name }] } }
    )

    process_simple_item(context, 'item/generated')



def process_simple_item(context: ResourceContext, parent_model: str):
    model = {
        'parent': parent_model,
        'textures': {
            'layer0': context.uuid + ':item/' + context.group + '/' + context.name
        }
    }
    process_item(context, model)



def custom_model_processor(context: ResourceContext):
    model = json.loads(open(context.folder_path + context.name + '.json', 'r').read())

    texture_path = context.uuid + ':item/' + context.group + '/' + context.name
    if 'textures' in model:
        model['textures']['0'] = texture_path
    else:
        model['textures'] = { '0': texture_path }

    process_item(context, model)



def process_item(context: ResourceContext, model):
    namespace = export + '/assets/' + context.uuid

    shutil.copyfile(
        context.folder_path + context.file_name,
        prepare_path(namespace + '/textures/item/' + context.group + '/', context.file_name)
    )

    if os.path.isfile(context.folder_path + context.file_name + '.mcmeta'):
        shutil.copyfile(
            context.folder_path + context.file_name + '.mcmeta',
            prepare_path(namespace + '/textures/item/' + context.group + '/', context.file_name + '.mcmeta')
        )

    save_json(
        prepare_path(namespace + '/models/item/' + context.group + '/', context.name + '.json'),
        model
    )

    save_json(
        prepare_path(namespace + '/items/' + context.group + '/', context.name + '.json'),
        { 'model': {
            'type': 'model',
            'model': context.uuid + ':item/' + context.group + '/' + context.name
        } }
    )

    resource_map[context.uuid][context.group].append(context.name)



def run_player_resource_processor(group: str, folder_path: str, uuid: str, processor):
    for file_name in os.listdir(folder_path):
        try:
            if file_name.endswith('.png'):
                processor(ResourceContext(
                    group,
                    folder_path,
                    file_name,
                    file_name.removesuffix('.png'),
                    uuid
                ))
        except:
            logging.exception('Failed to process ' + file_name + ' in ' + folder_path)



def prepare_path(folder_path: str, file_name: str) -> str:
    Path(folder_path).mkdir(parents=True, exist_ok=True)
    return folder_path + file_name



def save_json(file_path, data):
    with open(file_path, 'w') as outfile:
        json.dump(data, outfile)



main()
