# s3-clone-bucket

`s3-clone-bucket` is a tool that allows coping objects from one AWS S3 bucket to another 
including all object's versions.

## Features
* copy all object's versions
* copy tags
  * it also adds 3 tags
    * `src-bucket-name` with value of source bucket name
    * `last-modified` which equals to LastModified value fo source object
    * `src-object-versionId` with the versionId of the source object's version
* copy ACL
* preserve `StorageClass`

## Requirements
 * python 3.x, pip
 * Credentials. Could be provided in a few ways:
   * Credentials could be provided as environment variables, i.e. `AWS_ACCESS_KEY_ID` 
     and `AWS_SECRET_ACCESS_KEY`
   * Shared credential file (`~/.aws/credentials`)
   * AWS config file (`~/.aws/config`)
   * For more details see 
   [Boto3 credentials configuration guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#guide-credentials)

## Installation
To use it just clone the repo and install all dependencies:
```shell script
pip install -r requirements.txt
```

## Usage

### Options

| name | type | required | default | description |
|------|------|----------|---------|-------------|
| --src | str | yes | - | The name of the source bucket |
| --dst | str | yes | - | The name of the destination bucket |
| --start-date | datetime.datetime.fromisoformat | no | None | If specified, copy only objects that were modified after datetime |
| --end-date | datetime.datetime.fromisoformat | no | None | If specified, copy only objects that were modified before datetime |
| --log-level | ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'] | no | INFO | Specifies the log level |
| --dry-run | bool | no | False | Specifies whether actually do anything. If it is True, do not do anything but show what would be done |

### Usage examples
- Copy all versions of all object from `bucket1` to `bucket2`
```shell script
s3_clone_bucket.py --src bucket1 --dst bucket2
```
- Copy only objects/versions that were last modified after `2021-01-03 17:40:22` `UTC`
```shell script
s3_clone_bucket.py --src bucket1 --dst bucket2 --start-date "2020-12-27 17:40:22"
``` 

## License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE.md) file for details

## TODO
* Check ETag to avoid copying object's versions that are in the `dst` bucket already
* Use multiprocessing for better performance
* Think over how to deal with delete markers
