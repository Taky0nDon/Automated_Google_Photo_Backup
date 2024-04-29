# 173 pages?flk
# change pageSize to 100
import io
import json
import requests
import httplib2
import os
import random
import sys
import time

from google.auth.transport.requests import Request
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import HttpRequest
from googleapiclient.http import MediaIoBaseDownload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage as CredentialStorage
from oauth2client.tools import run_flow as run_oauth2
from PIL import Image

CLIENT_SECRETS_FILE = "/home/mike/.secrets/gphotograba/oauth/client_secret_653760331440-dlcjalai9vc0mihun0k68qpbdlgiq1n4.apps.googleusercontent.com.json"
CREDENTIALS_FILE = "./credentials.json"
SCOPE = 'https://www.googleapis.com/auth/photoslibrary.readonly'

USAGE = """
Usage examples:
    $ python chunked_transfer.py source destination
  $ python chunked_transfer.py gs://bucket/object ~/Desktop/filename
  $ python chunked_transfer.py ~/Desktop/filename gs://bucket/object """

MISSING_CLIENT_SECRETS_MESSAGE = f"""
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

{os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))}

with information from the APIs Console
<https://code.google.com/apis/console#access>. """

# Retry transport and file IO errors.
RETRYABLE_ERRORS = (httplib2.HttpLib2Error, IOError)

# Number of times to retry failed downloads.
NUM_RETRIES = 5

# Number of bytes to send/receive in each request.
CHUNKSIZE = 2 * 1024 * 1024

# Mimetype to use if one can't be guessed from the file extension.
DEFAULT_MIMETYPE = 'application/octet-stream'

OUTPUT_DIR = Path("/home/mike/Pictures/g_photos")

def get_authenticated_service(scope):
    print( 'Authenticating...')
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=scope,
                             message=MISSING_CLIENT_SECRETS_MESSAGE)

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



def handle_progressless_iter(error, progressless_iters):
    if progressless_iters > NUM_RETRIES:
        print( 'Failed to make progress for too many consecutive iterations.')
        raise error

    sleeptime = random.random() * (2**progressless_iters)
    print (f'Caught exception ({str(error)}). Sleeping for {sleeptime} seconds before retry #{progressless_iters}.')
    time.sleep(sleeptime)


def print_with_carriage_return(s):
    sys.stdout.write('\r' + s)
    sys.stdout.flush()


def download(argv):
    bucket_name, object_name = argv[1][5:].split('/', 1)
    filename = argv[2]
    assert bucket_name and object_name
    
    service = get_authenticated_service(SCOPE)
    
    print( 'Building download request...')
    f = open(filename, 'w')
    request = service.objects().get_media(bucket=bucket_name,
                                          object=object_name)
    media = MediaIoBaseDownload(f, request, chunksize=CHUNKSIZE)
    
    print (f'Downloading bucket: {bucket_name} object: {object_name} to file: {filename}' )
    
    progressless_iters = 0
    done = False
    while not done:
        error = None
        try:
            progress, done = media.next_chunk()
            if progress:
                print_with_carriage_return(
                    'Download %d%%.' % int(progress.progress() * 100))
        except HttpError as err:
            error = err
            if err.resp.status < 500:
              raise
        except RETRYABLE_ERRORS as err:
            error = err
        
        if error:
            progressless_iters += 1
            handle_progressless_iter(error, progressless_iters)
        else:
            progressless_iters = 0
        
    print('\nDownload complete!')


def get_img_from_bytes(byte_data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(byte_data))


if __name__ == "__main__":
    photos_service = get_authenticated_service(SCOPE)
    mediaItems_resource = photos_service.mediaItems()
    mediaItems_resource_request = mediaItems_resource.list(pageSize=100)
    # mediaItems_response = mediaItems_resource_request.execute()
    i = 0
    img_nbr = 0
    while mediaItems_resource_request is not None:
        i += 1
        print(f"accessing page {i}")
        current_photos = mediaItems_resource_request.execute()
        try:
            mediaItems = current_photos["mediaItems"]
        except KeyError as e:
            print(f"Failed to find 'mediaItems' key in page {i} response."
                  f"pageToken: {next_page}"
                  )
            print(current_photos)
            print(e.__repr__())
            with open("./log", "a") as log_file:
                log_file.write(json.dumps(current_photos))
        else:
            for media in mediaItems:
                img_nbr += 1
                time_created = media['mediaMetadata']['creationTime']
                img_width = media['mediaMetadata']['width']
                img_height = media['mediaMetadata']['height']
                name = media['filename']
                base_url = media["baseUrl"] + "=d" + f"-w{img_width}-h{img_height}"
                print(base_url)
                img_data_url = base_url
                print(f"Downloading image {img_nbr}: {name}"
                      f"Created: {time_created}")
                img_data = requests.get(img_data_url).content
                img = get_img_from_bytes(img_data)
                print(f"Downloading {name}")
                if name[:-4] == ".mp4":
                    continue
                try:
                    img.save(f"/home/mike/extra-storage/google_photos/{name[:-4]}.png")
                except ValueError as e:
                    print(current_photos)
                    print(e.__repr__())
                    with open("./log", "a") as log_file:
                        log_file.write(json.dumps(media))
        finally:
            next_page = current_photos["nextPageToken"]
            mediaItems_resource_request = mediaItems_resource\
                                            .list_next(mediaItems_resource_request,
                                                       current_photos)
            break


    # breakpoint()
    # for i, item in enumerate(mediaItems):
    #     if i == len(mediaItems) - 1:
    #         print(json.dumps(item))
    #     img_data_url = item["baseUrl"]
    #     name = item["filename"]
    #     img_data = requests.get(img_data_url).content
    #     img = get_img_from_bytes(img_data)
    #     #img.save(f"test_images/1/{name}.jpeg")

        #TODO: write over image data in library?
