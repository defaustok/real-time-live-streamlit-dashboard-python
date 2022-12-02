from google.cloud import storage
# Authenticate ourselves using the private key of the service account
files = []
path_to_private_key = './defaust-343537e24181.json'
client = storage.Client.from_service_account_json(json_credentials_path=path_to_private_key)
for blob in client.list_blobs(bucket_or_name='hedging-bot-statistics'):
    files.append((blob.name))
print(files)