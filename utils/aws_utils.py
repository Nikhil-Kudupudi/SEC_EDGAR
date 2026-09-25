import boto3 
import logging 




def get_s3_client():
    """
    Returns the s3 client session
    """
    s3_client = boto3.client("s3")
    return s3_client

def get_files(bucket_name:str, prefix:str):
    """reutrns the file data in bytes"""

    s3_client  = get_s3_client()
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name,Prefix = prefix):
        for obj in page.get('Contents', []):
            file_key= obj["Key"]
            print(file_key)
def get_file(bucket_name:str, key:str):
    s3_client = get_s3_client()
    file = s3_client.get_object(Bucket = bucket_name, Key = key) 
    return file['Body'].read().decode("utf-8")





if __name__ == "__main__":
    # get_files(bucket_name="secedgar-nikhil", prefix = "raw/companyfacts")
    file_content = get_file(bucket_name="secedgar-nikhil", key = "raw/companyfacts/CIK0000881695.json")
    


