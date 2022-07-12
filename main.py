import requests
import os
import logging
from random import randint
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__file__)


def download_image(url, filename, params={}):
    Path('images').mkdir(parents=True, exist_ok=True)
    response = requests.get(url, params=params)
    response.raise_for_status()
    with open(f'images/{filename}', 'wb') as file:
        file.write(response.content)


def get_random_xkcd():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    random_xkcd_id = randint(1, response.json()['num'])
    logger.info(f'Getting XKCD # {random_xkcd_id}')
    url = f'https://xkcd.com/{random_xkcd_id}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    random_xkcd_issue = response.json()
    filename = f'{random_xkcd_id}.png'
    download_image(random_xkcd_issue['img'], filename)
    return filename, random_xkcd_issue['alt']


def vk_group_upload_image(group_id, access_token, api_version, filename):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {
        'group_id': group_id,
        'access_token': access_token,
        'v': api_version
    }
    logger.info('Uploading photo to VK server')
    response = requests.get(url, params=params)
    response.raise_for_status()
    with open(filename, 'rb') as file:
        upload_url = response.json()['response']['upload_url']
        files = {'photo': file}
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
        return response.json()


def vk_group_save_image(group_id, access_token, api_version,
                        uploaded_photo_parameters):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {
        'group_id': group_id,
        'access_token': access_token,
        'v': api_version,
        'photo': uploaded_photo_parameters['photo'],
        'server': uploaded_photo_parameters['server'],
        'hash': uploaded_photo_parameters['hash']
    }
    logger.info('Saving photo to the group')
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def vk_group_post_with_image(group_id, access_token, api_version, message,
                             saved_photo_parameters):
    attachments_string =\
        f'photo{saved_photo_parameters["response"][0]["owner_id"]}_' +\
        f'{saved_photo_parameters["response"][0]["id"]}'
    params = {
        'group_id': group_id,
        'access_token': access_token,
        'v': api_version,
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': message,
        'attachments': attachments_string
    }
    logger.info('Posting photo on the wall')
    url = 'https://api.vk.com/method/wall.post'
    response = requests.get(url, params=params)
    response.raise_for_status()


def main():
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )

    xkcd_filename, xkcd_alt = get_random_xkcd()

    group_id = os.getenv('VK_GROUP_ID')
    access_token = os.getenv('VK_ACCESS_TOKEN')
    api_version = '5.131'
    uploaded_photo_parameters = vk_group_upload_image(
        group_id, access_token, api_version, f'images/{xkcd_filename}'
    )
    saved_photo_parameters = vk_group_save_image(
        group_id, access_token, api_version, uploaded_photo_parameters
    )
    vk_group_post_with_image(group_id, access_token, api_version,
                             xkcd_alt, saved_photo_parameters)
    os.remove(f'images/{xkcd_filename}')


if __name__ == '__main__':
    main()
