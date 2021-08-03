import os
import time
import boto3


class S3Helper(object):
    def __init__(
        self,
        bucket: str,
        region_name: str,
        datekey_partition: bool = True,
        hourkey_partition: bool = True,
    ):
        self.s3_client = boto3.client("s3", region_name=region_name)
        self.bucket = bucket
        self.region_name = region_name
        self.datekey_partition = datekey_partition
        self.hourkey_partition = hourkey_partition

    def generate_partition(self) -> str:
        """
        Generates the partition directories for files to be stored in S3.

        """

        partition = ""
        if self.datekey_partition:
            datekey = time.strftime("%Y-%m-%d")
            datekey_partition = f"datekey={datekey}"
            partition = os.path.join(partition, datekey_partition)

        if self.hourkey_partition:
            hourkey = time.strftime("%H")
            hourkey_partition = f"hourkey={hourkey}"
            partition = os.path.join(partition, hourkey_partition)

        return partition

    def download_from_s3(self, s3_key: str, local_filepath: str):
        """
        Given an S3 Key, this function will download the file
        and store it at local_filepath.

        """
        return self.s3_client.download_file(self.bucket, s3_key, local_filepath)

    def upload_to_s3(self, s3_key: str, local_filepath: str):
        """
        Given a Bucket and Key, this function will write the file
        and to the S3 bucket+key location.

        """
        return self.s3_client.put_object(
            Bucket=self.bucket, Key=s3_key, Body=local_filepath
        )
