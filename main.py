"""A simple program for archiving your google photos"""
# change pageSize to 100
import io
import json
import requests
import httplib2

from pathlib import Path
from googleapiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage as CredentialStorage
from oauth2client.tools import run_flow as run_oauth2
from PIL import Image

CLIENT_SECRETS_FILE = "/home/mike/.secrets/gphotograba/oauth/client_secret_6537"\
                      "60331440-dlcjalai9vc0mihun0k68qpbdlgiq1n4.apps.googleuse"\
                      "rcontent.com.json"
CREDENTIALS_FILE = "./credentials.json"
SCOPE = 'https://www.googleapis.com/auth/photoslibrary.readonly'

OUTPUT_DIR = Path("/home/mike/Pictures/g_photos")

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


def get_img_from_bytes(byte_data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(byte_data))


if __name__ == "__main__":
    MAX_IMAGES = 1
    photos_service = get_authenticated_service(SCOPE)
    mediaItems_resource = photos_service.mediaItems()
    media_items = mediaItems_resource.list(pageSize=100)
    i = 0
    img_nbr = 0
    while media_items is not None:
        i += 1
        print(f"accessing page {i}")
        current_photos = media_items.execute()
        next_page = current_photos["nextPageToken"]
        try:
            mediaItems = current_photos["mediaItems"]
        except KeyError as e:
            print(f"Failed to find 'mediaItems' key in page {i} response."
                  f"pageToken: {next_page}"
                  )
            print(current_photos)
            print(repr(e))
            with open("./log", "a") as log_file:
                log_file.write(json.dumps(current_photos))
        else:
            for media in mediaItems:
                img_nbr += 1
                if img_nbr > MAX_IMAGES:
                    quit()
                time_created = media['mediaMetadata']['creationTime']
                img_width = media['mediaMetadata']['width']
                img_height = media['mediaMetadata']['height']
                name = media['filename']
                base_url = media["baseUrl"] + "=d" + f"-w{img_width}-h{img_height}"
                print(base_url)
                img_data_url = base_url
                print(f"Downloading image {img_nbr}: {name}"
                      f"Created: {time_created}")
                img_data = requests.get(img_data_url, timeout=1000).content
                img = get_img_from_bytes(img_data)
                print(f"Downloading {name}")
                if name[:-4] == ".mp4":
                    with open("test_video_bytes", "w", encoding="utf-8") as file:
                        file.write(img_data.decode("utf-8"))
                try:
                    img.save(f"/home/mike/extra-storage/google_photos/{name[:-4]}.png")
                except ValueError as e:
                    print(current_photos)
                    print(e.__repr__())
                    with open("./log", "a", encoding="utf-8") as log_file:
                        log_file.write(json.dumps(media))
        finally:
            next_page = current_photos["nextPageToken"]
            media_items = mediaItems_resource\
                                            .list_next(media_items,
                                                       current_photos)
