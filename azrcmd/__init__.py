from __future__ import print_function
import io
import os
import re
import sys
import pytz
import base64
import hashlib
import argparse
import datetime
from math import log
from azure.storage.blob import BlockBlobService
from progressbar import ProgressBar, Percentage, Bar, ETA, FileTransferSpeed

if sys.version_info[0] == 3:
    import urllib.parse
    urlparse = urllib.parse.urlparse
else:
    import urlparse
    urlparse = urlparse.urlparse

class CredentialsMissing(RuntimeError):
    pass

class NotSupported(RuntimeError):
    pass

class InvalidBlobStorePath(AttributeError):
    pass

class BlobPathRequired(AttributeError):
    pass

class DirectoryRequired(AttributeError):
    pass

class FileIsNotExists(AttributeError):
    pass

# void
def check_credentials():
    if 'AZURE_STORAGE_ACCOUNT' not in os.environ:
        raise CredentialsMissing(u'Environment variable is missing: `AZURE_STORAGE_ACCOUNT`')

    if 'AZURE_STORAGE_ACCESS_KEY' not in os.environ:
        raise CredentialsMissing(u'Environment variable is missing: `AZURE_STORAGE_ACCESS_KEY`')

# genexp<list<str>>
def get_local_files(paths, recursive=False):
    for path in map(os.path.abspath, paths):
        if not os.path.exists(path):
            raise FileIsNotExists(u'File is not exits: `{}`'.format(os.path.relpath(path)))

        if os.path.isfile(path):
            yield path

        elif os.path.islink(path):
            raise NotSupported(u'Symlinks is not supported!')

        elif os.path.isdir(path) and not recursive:
            raise NotSupported(u'Uploading directories is not supported in this mode: `{}`\nPlease use `--recursive` attribute to upload directories.' \
                .format(os.path.relpath(path)))

        elif os.path.isdir(path) and recursive:
            sub_files = [ os.path.join(path, file_name) for file_name in os.listdir(path) ]
            for sub_path in get_local_files(sub_files, recursive=recursive):
                yield sub_path

# Blob|str
def get_fresher(blob, file_path):
    blob_dt = blob.last_modified
    file_dt = datetime.datetime.utcfromtimestamp(os.path.getmtime(file_path)).replace(tzinfo=pytz.UTC)
    blob_cl = blob.content_length
    file_cl = os.path.getsize(file_path)
    fresher = [file_path, None, blob][(blob_dt>file_dt)-(blob_dt<file_dt)+1]

    if file_cl != blob_cl:
        return fresher

    if file_cl > 1024*1024*64:
        return None

    if blob.content_md5 == md5(file_path):
        return None

    return fresher

# byte
def md5(fname):
    hash = hashlib.md5()
    with io.open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.digest()

class Blob(object):
    # void
    def __init__(self, service, blob):
        self.service = service
        self.blob = blob

    @property
    def last_modified(self):
        return self.blob.properties.last_modified.replace(tzinfo=pytz.UTC)

    @property
    def content_length(self):
        return self.blob.properties.content_length

    @property
    def content_md5(self):
        return base64.b64decode(self.blob.properties.content_md5)

    @property
    def path(self):
        return self.blob.name

    @property
    def url(self):
        return os.path.join(self.service.url, self.path.strip('/'))

    @property
    def repr_last_modified(self):
        return self.last_modified.strftime('%Y-%m-%d %H:%M')

class BlobStorage(object):
    # void
    def __init__(self, wasbs_path, dryrun=False):
        parsed = urlparse(wasbs_path)
        if parsed.scheme not in ('wasbs', 'wasb'):
            raise InvalidBlobStorePath('Remote path is not supported! Expected format: `wasb[s]://container/blob-path`')

        self.dryrun = dryrun
        self.schema, self.container, self.blob_path = parsed.scheme, parsed.netloc, parsed.path
        if self.blob_path and self.blob_path[0] == u'/':
            self.blob_path = self.blob_path[1:]

        self.blob_path = self.blob_path or None
        self.pbar = None
        self.service = BlockBlobService(
            account_name=os.environ['AZURE_STORAGE_ACCOUNT'], 
            account_key=os.environ['AZURE_STORAGE_ACCESS_KEY'])

    @property
    def url(self):
        return u'{}://{}'.format(self.schema, self.container)

    @property
    def path(self):
        return os.path.join(self.url, self.blob_path)

    # Blob
    def get_blob(self):
        for blob in self.list_blobs():
            if blob.path == self.blob_path:
                return blob

    # genexp<list<Blob>>
    def list_blobs(self):
        marker = None
        while True:
            batch = self.service.list_blobs(self.container, prefix=self.blob_path, marker=marker)
            for blob in batch:
                yield Blob(self, blob)
            if not batch.next_marker:
                break
            marker = batch.next_marker

    # void
    def execute(self, executable_fn, message, end=None, **kwargs):
        # Print the original message
        print(message % kwargs, end=end)

        # If dryrun, write the message and exit
        if self.dryrun:
            print('IGNORE (--dryrun)')
            return

        try:
            executable_fn(**kwargs)
            print('OK')
        except Exception as e:
            print('FAIL\n{}'.format(e))

    # void
    def remove_fn(self, path, url=None):
        self.service.delete_blob(self.container, path)

    # void
    def remove_blobs(self, prefix=False):
        if not self.blob_path:
            print(u'Have to specify the path of the blob.')
            sys.exit(1)

        if not prefix:
            return self.execute(self.remove_fn, 'Remove blob from `%(url)s` ... ', path=self.blob_path, url=self.path, end='')

        for blob in self.list_blobs():
            self.execute(self.remove_fn, 'Remove blob from `%(url)s` ... ', path=blob.path, url=blob.url, end='')

    # void
    def upload_fn(self, blob_path, file_path, rel_file_path=None, url=None):
        self.service.create_blob_from_path(self.container, blob_path, file_path, \
            max_connections=int(os.environ.get('AZURE_STORAGE_MAX_CONNECTIONS',1)), \
            progress_callback=self.show_progress)
        self.pbar.finish()
        self.pbar = None

    # tuple<str,str>
    def get_upload_path_pair(self, file_path, common_prefix=None):
        is_directory_ending = self.blob_path and self.blob_path.endswith('/')
        is_container_path = self.blob_path is None

        blob_path = os.path.join(self.blob_path or u'', os.path.split(file_path)[-1]) \
            if any([is_container_path, is_directory_ending]) and common_prefix is None \
            else self.blob_path

        if common_prefix and blob_path:
            blob_path = os.path.join(blob_path, file_path.split(common_prefix)[-1].strip('/'))
        elif common_prefix and not blob_path:
            blob_path = file_path.split(common_prefix)[-1].strip('/')
        elif common_prefix == u'' and blob_path:
            blob_path = os.path.join(blob_path, file_path.strip('/'))
        elif common_prefix == u'' and not blob_path:
            blob_path = file_path.strip('/')

        return (file_path, blob_path)

    # genexp<tuple<str,str>>
    def get_upload_path_pairs(self, file_paths):
        if len(file_paths) == 1:
            yield self.get_upload_path_pair(file_paths[0])
            return

        common_prefix = os.path.split(os.path.commonprefix(file_paths))[0]
        if self.blob_path and not self.blob_path.endswith('/'): self.blob_path += '/'
        for file_path in file_paths:
            yield self.get_upload_path_pair(file_path, common_prefix=common_prefix)

    # void
    def upload_blobs(self, file_paths):
        for file_path, blob_path in self.get_upload_path_pairs(file_paths):
            self.execute(self.upload_fn, 'Upload `%(rel_file_path)s` into `%(url)s`', \
                file_path=file_path, rel_file_path=os.path.relpath(file_path), blob_path=blob_path, \
                url=u'{}/{}'.format(self.url, blob_path))

    # void
    def show_progress(self, current, total):
        def filesize(n,pow=0,b=1024,u='B',pre=['']+[p+'i'for p in'KMGTPEZY']):
            pow,n=min(int(log(max(n*b**pow,1),b)),len(pre)-1),n*b**pow
            return "%%.%if %%s%%s"%abs(pow%(-pow-1))%(n/b**float(pow),pre[pow],u)

        if self.pbar is None:
            self.pbar = ProgressBar(widgets=[
                    ' '*5,
                    'Size: {}'.format(filesize(total)),
                    ' ',
                    Percentage(), 
                    ' ',
                    Bar(),
                    ' ', 
                    ETA(),
                    ' ', 
                    FileTransferSpeed(),
                    ' '*5
                ], 
                maxval=total
            ).start()

        self.pbar.update(current)

    # void
    def download_fn(self, blob_path, file_path, **kwargs):
        self.service.get_blob_to_path(self.container, blob_path, file_path, \
            max_connections=int(os.environ.get('AZURE_STORAGE_MAX_CONNECTIONS',1)), \
            progress_callback=self.show_progress)
        self.pbar.finish()
        self.pbar = None

    # tuple<str,str>
    def get_download_path_pair(self, blob_path, file_path, common_prefix=None):
        file_path = os.path.join(file_path, os.path.split(blob_path)[-1]) \
            if os.path.exists(file_path) and os.path.isdir(file_path) and common_prefix is None \
            else file_path

        if common_prefix:
            file_path = os.path.join(file_path, blob_path.split(common_prefix)[-1].strip('/'))
        elif common_prefix == u'':
            file_path = os.path.join(file_path, blob_path.strip('/'))

        dir_path = os.path.split(file_path)[0]
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        return blob_path, file_path

    # genexp<tuple<str,str>>
    def get_download_path_pairs(self, file_path, prefix=False, skip_existing=False, sync=False):
        # Ignore if no blob path is defined.
        if not self.blob_path:
            raise BlobPathRequired(u'Blob path is required for `get` command.')

        # Single file download scenario.
        if not prefix:
            # Skip if the file is already existing.
            if skip_existing and os.path.exists(file_path):
                return

            # Only downloads the not existing or the updated files (based on file size).
            if sync and os.path.exists(file_path):
                blob = self.get_blob()
                if blob and get_fresher(blob, file_path) != blob:
                    return

            # Return the caluclated path of the file.
            yield self.get_download_path_pair(self.blob_path, file_path)
            return

        # List the blobs with the given prefix in the ABS.
        blob_paths, blob_paths_dict = [], {}
        for blob in self.list_blobs():
            blob_paths.append(blob.path)
            blob_paths_dict[blob.path] = blob

        # Determine the common prefix between the blobs.
        common_prefix = os.path.dirname(self.blob_path) \
            if not self.blob_path.endswith('/') \
            else self.blob_path
        resolved_file_paths = []

        for blob_path in blob_paths:
            # Determine the input, output path pairs.
            bp, fp = self.get_download_path_pair(blob_path, file_path, common_prefix=common_prefix)

            # If any of the files want to write to the same file, raise an error.
            if fp in resolved_file_paths:
                raise DirectoryRequired('Can not use the same path (`{}`) for multiple blob!' \
                    .format(fp))

            # Ignore the files that already exists.
            if skip_existing and os.path.exists(fp):
                continue

            # Only downloads the not existing or the updated files (based on file size).
            if sync and os.path.exists(fp) and get_fresher(blob_paths_dict[blob_path], fp) != blob_paths_dict[blob_path]:
                continue

            resolved_file_paths.append(fp)
            yield bp, fp

    # void
    def download_blobs(self, file_path, prefix=False, skip_existing=False, sync=False):
        # Iterates over the final input, output paths and download them.
        for blob_path, file_path in self.get_download_path_pairs(file_path, prefix=prefix, skip_existing=skip_existing, sync=sync):
            self.execute(self.download_fn, 'Download `%(url)s` into `%(rel_file_path)s`', \
                blob_path=blob_path, file_path=file_path, rel_file_path=os.path.relpath(file_path), \
                url=u'{}/{}'.format(self.url, blob_path))

# void
def ls(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument('wasbs_path', help='remote path for Azure Blob Storage.')
    args = parser.parse_args(args)
    check_credentials()

    storage = BlobStorage(args.wasbs_path)
    for blob in storage.list_blobs():
        print('%s\t%12d\t%s' % (blob.repr_last_modified, blob.content_length, blob.url))

# void
def rm(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--prefix', help='download all blobs with prefix', action='store_true')
    parser.add_argument('--dryrun', help='just printing and not deleting.', action='store_true')
    parser.add_argument('wasbs_path', help='remote path for Azure Blob Storage.')
    args = parser.parse_args(args)
    check_credentials()

    storage = BlobStorage(args.wasbs_path, args.dryrun)
    storage.remove_blobs(args.prefix)

# void
def put(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument('-R', '--recursive', help='upload directories recursively.', action='store_true')
    parser.add_argument('--dryrun', help='just printing and not deleting.', action='store_true')
    parser.add_argument('file_path', nargs='+', help='local file or directory path.')
    parser.add_argument('wasbs_path', help='remote path for Azure Blob Storage.')
    args = parser.parse_args(args)
    check_credentials()

    storage = BlobStorage(args.wasbs_path, args.dryrun)
    paths = list(get_local_files(args.file_path, recursive=args.recursive))
    storage.upload_blobs(paths)

# void
def get(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--prefix', help='download all blobs with prefix', action='store_true')
    parser.add_argument('--dryrun', help='just printing and not deleting.', action='store_true')
    parser.add_argument('--skip_existing', help='skip the already existing files', action='store_true')
    parser.add_argument('--sync', help='download only the newer/changed files', action='store_true')
    parser.add_argument('wasbs_path', help='remote path for Azure Blob Storage.')
    parser.add_argument('file_path', help='local file or directory path.')
    args = parser.parse_args(args)
    check_credentials()

    if not os.path.exists(args.file_path) and args.file_path.endswith('/'):
        os.makedirs(args.file_path)

    storage = BlobStorage(args.wasbs_path, args.dryrun)
    storage.download_blobs(os.path.abspath(args.file_path), args.prefix, args.skip_existing, args.sync)
