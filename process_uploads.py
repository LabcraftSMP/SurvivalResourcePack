from dataclasses import dataclass
import json
import logging
import os
import urllib.request
import zipfile



@dataclass
class Params:
    group: str
    name: str
    uuid: str



SERVER_IP = 'mc.labsmp.net:12481'

path = os.path.dirname(os.path.realpath(__file__))
player_resources = path + '/player_resources/'
uploads = path + '/uploads/'
budgets = {}
usages = {}

def main():
    for upload in os.listdir(uploads):
        try:
            archive = zipfile.ZipFile(uploads + upload, 'r')
            params = json.loads(archive.read('params.json'))
            params = Params(
                params['group'],
                params['name'],
                params['uuid']
            )

            match params.group:
                case 'basic_texture':
                    run_upload_processor(archive, params, process_simple_texture, ['texture.png'])
                case 'tool_texture':
                    run_upload_processor(archive, params, process_simple_texture, ['texture.png'])
                case 'elytra_texture':
                    run_upload_processor(archive, params, process_elytra_texture, ['texture.png', 'wings.png'])
                case 'custom_model':
                    run_upload_processor(archive, params, process_custom_model, ['texture.png', 'model.json'])
                case _:
                    raise ValueError('Invalid group type ' + params.group)
        except:
            if isinstance(archive, zipfile.ZipFile):
                archive.close()
            logging.exception('Failed to process ' + upload)



def process_simple_texture(archive: zipfile.ZipFile, params: Params, folder_path: str):
    archive.getinfo('texture.png').filename = params.name + '.png'
    archive.extract('texture.png', folder_path)

    if 'texture.png.mcmeta' in archive.namelist():
        archive.getinfo('texture.png.mcmeta').filename = params.name + '.png.mcmeta'
        archive.extract('texture.png.mcmeta', folder_path)



def process_elytra_texture(archive: zipfile.ZipFile, params: Params, folder_path: str):
    archive.getinfo('texture.png').filename = params.name + '.png'
    archive.extract('texture.png', folder_path)

    archive.getinfo('wings.png').filename = params.name + '.png'
    archive.extract('wings.png', folder_path + '/wings')



def process_custom_model(archive: zipfile.ZipFile, params: Params, folder_path: str):
    archive.getinfo('texture.png').filename = params.name + '.png'
    archive.extract('texture.png', folder_path)

    archive.getinfo('model.json').filename = params.name + '.json'
    archive.extract('model.json', folder_path)

    if 'texture.png.mcmeta' in archive.namelist():
        archive.getinfo('texture.png.mcmeta').filename = params.name + '.png.mcmeta'
        archive.extract('texture.png.mcmeta', folder_path)



def run_upload_processor(archive: zipfile.ZipFile, params: Params, processor, requirements: list[str]):
    for requirement in requirements:
        if not requirement in archive.namelist():
            raise ValueError('Missing required file {requirement} in {file_name}'.format(
                requirement = requirement,
                file_name = archive.filename
            ))
    
    decrement_resource(params)
    processor(archive, params, player_resources + params.uuid + '/' + params.group)

    os.remove(archive.filename)
    archive.close()



def decrement_resource(params: Params):
    budget = get_budget(params.uuid)
    usage = get_usage(params.uuid)

    available = budget[params.group] - usage[params.group]
    if available <= 0:
        raise ValueError('Player with UUID {uuid} does not have the required {group} budget for {name}! ({used}/{max})'.format(
            uuid = params.uuid,
            group = params.group,
            name = params.name,
            used = usage[params.group],
            max = budget[params.group]
        ))
    
    usage[params.group] += 1



def get_budget(uuid: str):
    if uuid in budgets:
        return budgets[uuid]

    budgets[uuid] = json.loads(urllib.request.urlopen('http://' + SERVER_IP + '/resource/budget/' + uuid).read())
    return budgets[uuid]



def get_usage(uuid: str):
    if uuid in usages:
        return usages[uuid]
    
    usages[uuid] = calculate_usage(uuid)
    return usages[uuid]



def calculate_usage(uuid: str):
    folder_path = player_resources + uuid + '/'

    usage = {
        'basic_texture': 0,
        'tool_texture': 0,
        'elytra_texture': 0,
        'custom_model': 0
    }

    if not os.path.isdir(folder_path):
        return usage
    
    for key in usage:
        if os.path.isdir(folder_path + key):
            usage[key] = len([f for f in os.listdir(player_resources) if f.endswith('.png')])

    return usage



main()
