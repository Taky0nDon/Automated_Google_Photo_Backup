from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SECRET = "/home/mike/.secrets/gphotograba/oauth/client_secret_653760331440-dlcjalai9vc0mihun0k68qpbdlgiq1n4.apps.googleusercontent.com.json"

flow = InstalledAppFlow.from_client_secrets_file(SECRET,
                                                 scopes=["https://www.googleapis.com/auth/photoslibrary.readonly"]
                                                 )
credentials = flow.run_local_server()




print(credentials)


resource_object = build("photoslibrary",
                        "v1",
                        credentials=credentials,
                        static_discovery=False
                        )

mediaItems = resource_object.mediaItems()
