import boto3


s3 = boto3.resource(
    's3',
    aws_access_key_id="ZTLX8H5A81FYG5T685DN",
    aws_secret_access_key="1LaI1FNFGc2KcN0aTOjDIWU7fJdila5XwgDm30Dk",
    endpoint_url="https://s3.timeweb.cloud",
    region_name='ru-1',

)
bucket_name = 'a7f02a62-e15c7451-cea6-4e82-9754-31fa55629677'

# for bucket in s3.buckets.all():
#     print(bucket.name)



def upload_static_file(file_path, key):
    s3.Object(bucket_name, key).upload_file(file_path)


def get_static_file_url(key):
    return f"https://{bucket_name}.s3.timeweb.cloud/{key}"
#
#

key = 'photos/photo.jpg'
upload_static_file("static/uploads/story_1e6c6e840bf34518_media_1.jpg", key)
print(get_static_file_url(key))