#!/usr/bin/env python3

import boto3
import argparse
import logging
import sys
import datetime
import pytz


parser = argparse.ArgumentParser(description='Clone S3 bucket')
parser.add_argument('--src', '-s', type=str, required=True, help='The name of the source bucket')
parser.add_argument('--dst', '-d', type=str, required=True, help='The name of the destination bucket')
parser.add_argument('--start-date', type=datetime.datetime.fromisoformat,
                    required=False, default=None, dest='start_date',
                    help='Copy only objects that were last modified after datetime, '
                         'format YYYY-MM-DD[*HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]]')
parser.add_argument('--end-date', type=datetime.datetime.fromisoformat,
                    required=False, default=None, dest='end_date',
                    help='Copy only objects that were last modified before datetime, '
                         'format YYYY-MM-DD[*HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]]')
parser.add_argument('--log-level', '-l', dest='log_level', type=str,
                    choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'],
                    required=False, default='INFO',
                    help='Specifies the log level')
parser.add_argument('--dry-run', type=eval, choices=[True, False], required=False, default='False', dest='dry_run',
                    help='Specifies whether actually do anything. If it is True, do not do anything but show what '
                         'would be done')
args = parser.parse_args()

logger = logging.getLogger()
logger.setLevel(args.log_level)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


client = boto3.client('s3')
resource = boto3.resource('s3')

# convert to offset-aware datetime
if args.start_date is not None:
    start_date = pytz.utc.localize(args.start_date)
else:
    start_date = None

if args.end_date is not None:
    end_date = pytz.utc.localize(args.end_date)
else:
    end_date = None


def check_if_bucket_exists(bucket: str) -> bool:
    try:
        client.head_bucket(Bucket=bucket)
        return True
    except:
        logger.critical("No such bucket {} or can't access it".format(bucket))
    return False


def copy_object_version(version):
    if (start_date is None or version['LastModified'] > start_date) \
            and (end_date is None or version['LastModified'] < end_date):
        if bool(args.dry_run):
            logger.info("dry-run - would copy 'Key' {} 'VersionId' {} from {} to {}"
                        .format(version['Key'], version['VersionId'], args.src, args.dst))
        else:
            src_tag_set = client.get_object_tagging(Bucket=args.src, Key=version['Key'], VersionId=version['VersionId'])
            src_acl = client.get_object_acl(Bucket=args.src, Key=version['Key'], VersionId=version['VersionId'])
            dst_tag_set = "src-bucket-name={}&last-modified={}&src-object-versionId={}" \
                .format(args.src, version['LastModified'], version['VersionId'])

            # append original tags
            for tag in src_tag_set['TagSet']:
                dst_tag_set += "&{}={}".format(tag['Key'], tag['Value'])

            logger.info("Copy 'Key' {} 'VersionId' {} from {} to {}"
                        .format(version['Key'],
                                version['VersionId'], args.src, args.dst))
            try:
                response = resource.Object(bucket_name=args.dst, key=version['Key']) \
                    .copy_from(CopySource={'Bucket': args.src, 'Key': version['Key'], 'VersionId': version['VersionId']},
                               StorageClass=version['StorageClass'],
                               MetadataDirective='COPY',
                               TaggingDirective='REPLACE',
                               Tagging=dst_tag_set,
                               )
                # copy ACL
                client.put_object_acl(Bucket=args.dst, Key=version['Key'], VersionId=response['VersionId'],
                                      AccessControlPolicy={'Grants': src_acl['Grants'], 'Owner': src_acl['Owner']})
            except Exception as e:
                logger.error("Couldn't copy 'Key' {} 'VersionId' {} from {} to {}, failed with error {}"
                             .format(version['Key'],
                                     version['VersionId'], args.src, args.dst, e))


# check if the buckets exist and accessible
if not check_if_bucket_exists(args.src):
    logger.critical("Source bucket {} doesn't exist or not accessible".format(args.src))
    sys.exit(1)

if not check_if_bucket_exists(args.dst):
    logger.critical("Destination bucket {} doesn't exist or not accessible".format(args.dst))
    sys.exit(1)

objects = resource.Bucket(args.src).objects.all()
for obj in objects:
    paginator = client.get_paginator('list_object_versions')
    pages = paginator.paginate(Bucket=args.src,
                               Prefix=obj.key)

    # obj_latest_version = dict()
    for page in pages:
        for v in page['Versions']:
            if not v['IsLatest']:
                copy_object_version(v)
            else:
                obj_latest_version = v.copy()

    # copy latest version of the object last, so that the current version in dst bucket is the latest version
    copy_object_version(obj_latest_version)
