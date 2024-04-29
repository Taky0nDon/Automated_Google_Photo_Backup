"""A simple program for archiving your google photos"""
# change pageSize to 100
import json
import requests
import httplib2

from pathlib import Path
from googleapiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage as CredentialStorage
from oauth2client.tools import run_flow as run_oauth2

CLIENT_SECRETS_FILE = "/home/mike/.secrets/gphotograba/oauth/client_secret_6537"\
                      "60331440-dlcjalai9vc0mihun0k68qpbdlgiq1n4.apps.googleuse"\
                      "rcontent.com.json"
CREDENTIALS_FILE = "../credentials.json"
SCOPE = 'https://www.googleapis.com/auth/photoslibrary.readonly'

IMG_OUTPUT_DIR = Path("/home/mike/extra-storage/google_photos/pics")
VID_OUTPUT_DIR = Path(IMG_OUTPUT_DIR, "vid")

VID_BASE_URL_SUFFIX = "=dv"

def get_img_url_params(width: str, height: str) -> str:
    """ Returns string to append to baseUrl for images before getting bytes from API """
    return f"=d-w{width}-h{height}"


VID_BASE_URL_SUFFIX = "=dv"

def get_img_url_params(width: str, height: str) -> str:
    """ Returns string to append to baseUrl for images before getting bytes from API """
    return f"=d-w{width}-h{height}"


def get_authenticated_service(scope):
    print( 'Authenticating...')
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=scope,)

    credential_storage = CredentialStorage(CREDENTIALS_FILE)
    credentials = credential_storage.get()
    if credentials is None or credentials.invalid:
        credentials = run_oauth2(flow, credential_storage)

    print('Constructing Google Cloud Storage service...')
    http = credentials.authorize(httplib2.Http())
    return build('photoslibrary',
                 'v1',
                 http=http,
                 static_discovery=False)


if __name__ == "__main__":
    MAX_IMAGES = 200
    photos_service = get_authenticated_service(SCOPE)
    mediaItems_resource = photos_service.mediaItems()
    media_items = mediaItems_resource.list(pageSize=100)
    page = 0
    img_nbr = 0
    while media_items is not None:
        page += 1
        print(f"accessing page {page}")
        current_photos = media_items.execute()
        next_page = current_photos["nextPageToken"]
        try:
            mediaItems = current_photos["mediaItems"]
        except KeyError as e:
            print(f"Failed to find 'mediaItems' key in page {page} response."
                  f"pageToken: {next_page}"
                  )
            with open("./log", "a") as log_file:
                log_file.write(json.dumps(current_photos))
                log_file.write(repr(e))
        else:
            for media in mediaItems:
                img_nbr += 1
                if img_nbr > MAX_IMAGES:
                    quit()

                base_url = media["baseUrl"] 
                time_created = media['mediaMetadata']['creationTime']
                name = media['filename']
<<<<<<< HEAD
                print(f"Downloading file {img_nbr}: {name}\n"
                      f"Created: {time_created}")

                if name[-4:] == ".mp4":
                    data_url = base_url + VID_BASE_URL_SUFFIX
                    raw_bytes = requests.get(data_url, timeout=1000).content
                    file_path = Path(VID_OUTPUT_DIR, name)
                    file_type = "video"
                else:
                    img_width = media['mediaMetadata']['width']
                    img_height = media['mediaMetadata']['height']
                    data_url = base_url + get_img_url_params(img_width, img_height)
                    raw_bytes = requests.get(data_url, timeout=1000).content
                    file_path = Path(IMG_OUTPUT_DIR, name)
                    file_type = "image"

                print(f"Writing {file_type} data to {file_path}.")
                with open(file_path, "wb") as vid_file:
                    vid_file.write(raw_bytes)
                print("Done.")
=======
                base_url = media["baseUrl"] 
                print(base_url)
                print(f"Downloading image {img_nbr}: {name}"
                      f"Created: {time_created}")
                img_base_url = base_url + get_img_url_params(img_width, img_height)
                img_data = requests.get(img_base_url,
                                        timeout=1000).content
                img = get_img_from_bytes(img_data)
                print(f"Downloading {name}")
                if name[-4:] == ".mp4":
                    video_data_url = base_url + VID_BASE_URL_SUFFIX
                    video_bytes = requests.get(video_data_url, timeout=1000).content
                    with open("./test_video_bytes", "wb") as file:
                        file.write(img_data)
                try:
                    img.save(f"/home/mike/extra-storage/google_photos/{name[:-4]}.png")
                except ValueError as e:
                    print(current_photos)
                    print(e.__repr__())
                    with open("./log", "a", encoding="utf-8") as log_file:
                        log_file.write(json.dumps(media))
>>>>>>> 7f8ee45 (small refactor, cleaned working directory)
        finally:
            next_page = current_photos["nextPageToken"]
            media_items = mediaItems_resource\
                                            .list_next(media_items,
                                                       current_photos)
