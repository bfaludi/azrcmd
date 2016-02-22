import io
import os
import pytz
import shutil
import hashlib
import datetime
import unittest
from azrcmd import *

class TestInvalidBlobStorageURL(unittest.TestCase):
    def setUp(self):
        os.environ['AZURE_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_STORAGE_ACCESS_KEY'] = 'key'

    def test_put(self):
        with self.assertRaises(InvalidBlobStorePath):
            put(['example.txt', 'https://container/example.txt'])

    def test_get(self):
        with self.assertRaises(InvalidBlobStorePath):
            get(['https://container/example.txt', 'example.txt'])

    def test_ls(self):
        with self.assertRaises(InvalidBlobStorePath):
            ls(['https://container/example'])

    def test_rm(self):
        with self.assertRaises(InvalidBlobStorePath):
            rm(['https://container/example.txt'])

class TestCredentials(unittest.TestCase):
    def setUp(self):
        for k in ['AZURE_STORAGE_ACCOUNT','AZURE_STORAGE_ACCESS_KEY']:
            if os.environ.get(k):
                del os.environ[k]

    def test_put(self):
        with self.assertRaises(CredentialsMissing):
            put(['example.txt', 'wasbs://container'])

    def test_get(self):
        with self.assertRaises(CredentialsMissing):
            get(['wasbs://container', 'example.txt'])

    def test_ls(self):
        with self.assertRaises(CredentialsMissing):
            ls(['wasbs://container'])

    def test_rm(self):
        with self.assertRaises(CredentialsMissing):
            rm(['wasbs://container/example.txt'])

class TestPutPaths(unittest.TestCase):
    def setUp(self):
        os.environ['AZURE_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_STORAGE_ACCESS_KEY'] = 'key'

    def test_single_file(self):
        service = BlobStorage('wasbs://container/file.txt')
        res = list(service.get_upload_path_pairs(['file.txt']))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','file.txt'))

    def test_single_file_renamed(self):
        service = BlobStorage('wasbs://container/renamed.txt')
        res = list(service.get_upload_path_pairs(['file.txt']))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','renamed.txt'))

    def test_single_file_into_directory(self):
        service = BlobStorage('wasbs://container/directory/')
        res = list(service.get_upload_path_pairs(['file.txt']))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','directory/file.txt'))

    def test_single_file_renamed_into_directory(self):
        service = BlobStorage('wasbs://container/directory/renamed.txt')
        res = list(service.get_upload_path_pairs(['file.txt']))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','directory/renamed.txt'))

    def test_single_file_without_path(self):
        service = BlobStorage('wasbs://container')
        res = list(service.get_upload_path_pairs(['file.txt']))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','file.txt'))

    def test_multiple_file_without_path(self):
        service = BlobStorage('wasbs://container')
        res = list(service.get_upload_path_pairs(['f1.txt','f2.txt','f3.txt']))

        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('f1.txt','f1.txt'))
        self.assertEqual(res[1], ('f2.txt','f2.txt'))
        self.assertEqual(res[2], ('f3.txt','f3.txt'))

    def test_multiple_file_into_directory(self):
        service = BlobStorage('wasbs://container/directory/')
        res = list(service.get_upload_path_pairs(['f1.txt','f2.txt','f3.txt']))

        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('f1.txt','directory/f1.txt'))
        self.assertEqual(res[1], ('f2.txt','directory/f2.txt'))
        self.assertEqual(res[2], ('f3.txt','directory/f3.txt'))

    def test_multiple_file_into_directory_without_slash(self):
        service = BlobStorage('wasbs://container/directory')
        res = list(service.get_upload_path_pairs(['f1.txt','f2.txt','f3.txt']))

        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('f1.txt','directory/f1.txt'))
        self.assertEqual(res[1], ('f2.txt','directory/f2.txt'))
        self.assertEqual(res[2], ('f3.txt','directory/f3.txt'))

    def test_multiple_file_from_dir_into_directory(self):
        service = BlobStorage('wasbs://container/directory/')
        res = list(service.get_upload_path_pairs(['directory/f1.txt','directory/f2.txt','directory/f3.txt']))

        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('directory/f1.txt','directory/f1.txt'))
        self.assertEqual(res[1], ('directory/f2.txt','directory/f2.txt'))
        self.assertEqual(res[2], ('directory/f3.txt','directory/f3.txt'))

    def test_multiple_file_from_dir_without_path(self):
        service = BlobStorage('wasbs://container')
        res = list(service.get_upload_path_pairs(['directory/f1.txt','directory/f2.txt','directory/f3.txt']))

        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('directory/f1.txt','f1.txt'))
        self.assertEqual(res[1], ('directory/f2.txt','f2.txt'))
        self.assertEqual(res[2], ('directory/f3.txt','f3.txt'))

    def test_multiple_file_from_different_dirs_into_directory(self):
        service = BlobStorage('wasbs://container/folder')
        res = list(service.get_upload_path_pairs(['dir1/f1.txt','dir1/subdir/f2.txt','dir2/f3.txt']))

        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('dir1/f1.txt','folder/dir1/f1.txt'))
        self.assertEqual(res[1], ('dir1/subdir/f2.txt','folder/dir1/subdir/f2.txt'))
        self.assertEqual(res[2], ('dir2/f3.txt','folder/dir2/f3.txt'))

    def test_multiple_file_from_different_dirs_without_path(self):
        service = BlobStorage('wasbs://container')
        res = list(service.get_upload_path_pairs(['dir1/f1.txt','dir1/subdir/f2.txt','dir2/f3.txt']))

        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('dir1/f1.txt','dir1/f1.txt'))
        self.assertEqual(res[1], ('dir1/subdir/f2.txt','dir1/subdir/f2.txt'))
        self.assertEqual(res[2], ('dir2/f3.txt','dir2/f3.txt'))

class TestGetPaths(unittest.TestCase):
    class Blob(object):
        def __init__(self, path):
            self.path = path
            self.url = None
            self.content_length = 0
            self.last_modified = None
            self.repr_last_modified = u''

    class BlobSync(object):
        def __init__(self, path, last_modified, content_length, content_md5):
            self.path = path
            self.url = None
            self.content_length = content_length
            self.last_modified = last_modified
            self.content_md5 = content_md5
            self.repr_last_modified = u''

    def setUp(self):
        os.environ['AZURE_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_STORAGE_ACCESS_KEY'] = 'key'

    def tearDown(self):
        if os.path.exists('directory'):
            shutil.rmtree('directory')
        if os.path.exists('folder'):
            shutil.rmtree('folder')

    def test_without_path(self):
        service = BlobStorage('wasbs://container')
        with self.assertRaises(BlobPathRequired):
            res = list(service.get_download_path_pairs('file.txt'))

    def test_single_file(self):
        service = BlobStorage('wasbs://container/file.txt')
        res = list(service.get_download_path_pairs('file.txt'))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','file.txt'))

    def test_single_file_into_directory_with_name(self):
        service = BlobStorage('wasbs://container/file.txt')
        res = list(service.get_download_path_pairs('directory/file.txt'))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','directory/file.txt'))

    def test_single_file_into_directory_with_name_skip_existing(self):
        service = BlobStorage('wasbs://container/file.txt')
        os.mkdir('directory')
        io.open('directory/file.txt','a').close()
        res = list(service.get_download_path_pairs('directory/file.txt', skip_existing=True))
        self.assertEqual(len(res), 0)

    def test_single_file_into_directory_without_name(self):
        service = BlobStorage('wasbs://container/file.txt')
        os.mkdir('directory')
        res = list(service.get_download_path_pairs('directory/'))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','directory/file.txt'))

    def test_single_file_into_directory_without_name_skip_existing(self):
        service = BlobStorage('wasbs://container/file.txt')
        os.mkdir('directory')
        io.open('directory/file.txt','a').close()
        res = list(service.get_download_path_pairs('directory/', skip_existing=True))
        self.assertEqual(len(res), 0)

    def _list_blobs_single_root(self):
        return map(self.Blob, [u'file.txt'])

    def test_prefixed_single_file_without_slash(self):
        service = BlobStorage('wasbs://container/file')
        service.list_blobs = self._list_blobs_single_root
        res = list(service.get_download_path_pairs('directory', prefix=True))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','directory/file.txt'))

    def test_prefixed_single_file_into_directory(self):
        service = BlobStorage('wasbs://container/file')
        service.list_blobs = self._list_blobs_single_root
        os.mkdir('directory')
        res = list(service.get_download_path_pairs('directory/', prefix=True))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','directory/file.txt'))

    def test_prefixed_single_file_into_directory_skip_exists(self):
        service = BlobStorage('wasbs://container/file')
        service.list_blobs = self._list_blobs_single_root
        os.mkdir('directory')
        io.open('directory/file.txt','a').close()
        res = list(service.get_download_path_pairs('directory/', prefix=True, skip_existing=True))
        self.assertEqual(len(res), 0)

    def _list_blobs_multiple_root(self):
        return map(self.Blob, [u'file-1.txt','file-2.txt','file-3.txt'])

    def test_prefixed_multiple_root_file(self):
        service = BlobStorage('wasbs://container/file')
        service.list_blobs = self._list_blobs_multiple_root
        res = list(service.get_download_path_pairs('.', prefix=True))

        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('file-1.txt','./file-1.txt'))
        self.assertEqual(res[1], ('file-2.txt','./file-2.txt'))
        self.assertEqual(res[2], ('file-3.txt','./file-3.txt'))

    def test_prefixed_multiple_root_file_into_directory(self):
        service = BlobStorage('wasbs://container/file')
        service.list_blobs = self._list_blobs_multiple_root
        os.mkdir('directory')
        res = list(service.get_download_path_pairs('directory/', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('file-1.txt','directory/file-1.txt'))
        self.assertEqual(res[1], ('file-2.txt','directory/file-2.txt'))
        self.assertEqual(res[2], ('file-3.txt','directory/file-3.txt'))

    def test_prefixed_multiple_root_file_into_directory_without_slash(self):
        service = BlobStorage('wasbs://container/file')
        service.list_blobs = self._list_blobs_multiple_root
        os.mkdir('directory')
        res = list(service.get_download_path_pairs('directory', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('file-1.txt','directory/file-1.txt'))
        self.assertEqual(res[1], ('file-2.txt','directory/file-2.txt'))
        self.assertEqual(res[2], ('file-3.txt','directory/file-3.txt'))

    def test_prefixed_multiple_file_into_not_existing_directory_without_slash(self):
        service = BlobStorage('wasbs://container/file')
        service.list_blobs = self._list_blobs_multiple_root
        res = list(service.get_download_path_pairs('directory', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('file-1.txt','directory/file-1.txt'))
        self.assertEqual(res[1], ('file-2.txt','directory/file-2.txt'))
        self.assertEqual(res[2], ('file-3.txt','directory/file-3.txt'))

    def _list_blobs_multiple_dirs(self):
        return map(self.Blob, [u'dir1/file-1.txt','dir1/subdir/file-2.txt','dir2/file-3.txt'])

    def test_prefixed_multiple_file_into_directory_with_slash(self):
        service = BlobStorage('wasbs://container/file')
        service.list_blobs = self._list_blobs_multiple_dirs
        os.mkdir('directory')
        res = list(service.get_download_path_pairs('directory/', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('dir1/file-1.txt','directory/dir1/file-1.txt'))
        self.assertEqual(res[1], ('dir1/subdir/file-2.txt','directory/dir1/subdir/file-2.txt'))
        self.assertEqual(res[2], ('dir2/file-3.txt','directory/dir2/file-3.txt'))

    def test_prefixed_multiple_file_into_directory_without_slash(self):
        service = BlobStorage('wasbs://container/file')
        service.list_blobs = self._list_blobs_multiple_dirs
        os.mkdir('directory')
        res = list(service.get_download_path_pairs('directory', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('dir1/file-1.txt','directory/dir1/file-1.txt'))
        self.assertEqual(res[1], ('dir1/subdir/file-2.txt','directory/dir1/subdir/file-2.txt'))
        self.assertEqual(res[2], ('dir2/file-3.txt','directory/dir2/file-3.txt'))

    def test_prefixed_multiple_root_file_into_not_existing_directory_without_slash(self):
        service = BlobStorage('wasbs://container/file')
        service.list_blobs = self._list_blobs_multiple_dirs
        res = list(service.get_download_path_pairs('directory', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('dir1/file-1.txt','directory/dir1/file-1.txt'))
        self.assertEqual(res[1], ('dir1/subdir/file-2.txt','directory/dir1/subdir/file-2.txt'))
        self.assertEqual(res[2], ('dir2/file-3.txt','directory/dir2/file-3.txt'))

    def test_prefixed_multiple_file_into_directory_skip_existing(self):
        service = BlobStorage('wasbs://container/file')
        service.list_blobs = self._list_blobs_multiple_dirs
        os.makedirs('directory/dir1/subdir')
        io.open('directory/dir1/subdir/file-2.txt','a').close()
        res = list(service.get_download_path_pairs('directory', prefix=True, skip_existing=True))
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0], ('dir1/file-1.txt','directory/dir1/file-1.txt'))
        self.assertEqual(res[1], ('dir2/file-3.txt','directory/dir2/file-3.txt'))

    def _list_blobs_multiple_dirs_with_same_root(self):
        return map(self.Blob, [u'upper/directory/file-1.txt','upper/directory/file-2.txt','upper/directory/file-3.txt'])

    def test_prefixed_multiple_file_from_prefix_without_slash(self):
        service = BlobStorage('wasbs://container/upper/direct')
        service.list_blobs = self._list_blobs_multiple_dirs_with_same_root
        os.mkdir('folder')

        # With directory with slash
        res = list(service.get_download_path_pairs('folder/', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','folder/directory/file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','folder/directory/file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','folder/directory/file-3.txt'))

        # With directory without slash
        res = list(service.get_download_path_pairs('folder', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','folder/directory/file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','folder/directory/file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','folder/directory/file-3.txt'))
        
    def test_prefixed_multiple_file_from_prefix_with_slash(self):
        service = BlobStorage('wasbs://container/upper/directory/')
        service.list_blobs = self._list_blobs_multiple_dirs_with_same_root
        os.mkdir('folder')

        # With directory with slash
        res = list(service.get_download_path_pairs('folder/', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','folder/file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','folder/file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','folder/file-3.txt'))

        # With directory without slash
        res = list(service.get_download_path_pairs('folder', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','folder/file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','folder/file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','folder/file-3.txt'))

    def test_prefixed_multiple_file_from_prefix_without_slash(self):
        service = BlobStorage('wasbs://container/upper/direct')
        service.list_blobs = self._list_blobs_multiple_dirs_with_same_root

        # With directory with slash
        res = list(service.get_download_path_pairs('folder/', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','folder/directory/file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','folder/directory/file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','folder/directory/file-3.txt'))

        # With directory without slash
        res = list(service.get_download_path_pairs('folder', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','folder/directory/file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','folder/directory/file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','folder/directory/file-3.txt'))
        
    def test_prefixed_multiple_file_from_prefix_with_slash(self):
        service = BlobStorage('wasbs://container/upper/directory/')
        service.list_blobs = self._list_blobs_multiple_dirs_with_same_root

        # With directory with slash
        res = list(service.get_download_path_pairs('folder/', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','folder/file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','folder/file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','folder/file-3.txt'))

        # With directory without slash
        res = list(service.get_download_path_pairs('folder', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','folder/file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','folder/file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','folder/file-3.txt'))

    def test_prefixed_multiple_file_from_prefix_without_slash_into_current(self):
        service = BlobStorage('wasbs://container/upper/direct')
        service.list_blobs = self._list_blobs_multiple_dirs_with_same_root

        res = list(service.get_download_path_pairs('.', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','./directory/file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','./directory/file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','./directory/file-3.txt'))
        
        res = list(service.get_download_path_pairs('./', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','./directory/file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','./directory/file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','./directory/file-3.txt'))

    def test_prefixed_multiple_file_from_prefix_with_slash_into_current(self):
        service = BlobStorage('wasbs://container/upper/directory/')
        service.list_blobs = self._list_blobs_multiple_dirs_with_same_root

        res = list(service.get_download_path_pairs('.', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','./file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','./file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','./file-3.txt'))
        
        res = list(service.get_download_path_pairs('./', prefix=True))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('upper/directory/file-1.txt','./file-1.txt'))
        self.assertEqual(res[1], ('upper/directory/file-2.txt','./file-2.txt'))
        self.assertEqual(res[2], ('upper/directory/file-3.txt','./file-3.txt'))

    def test_prefixed_multiple_file_from_directory_skip_existing(self):
        service = BlobStorage('wasbs://container/upper/directory/')
        service.list_blobs = self._list_blobs_multiple_dirs_with_same_root
        os.mkdir('folder')
        io.open('folder/file-1.txt','a').close()
        res = list(service.get_download_path_pairs('folder/', prefix=True, skip_existing=True))
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0], ('upper/directory/file-2.txt','folder/file-2.txt'))
        self.assertEqual(res[1], ('upper/directory/file-3.txt','folder/file-3.txt'))

    # Test --sync attribute
    def test_single_file_into_directory_with_name_sync_new_on_bs(self):
        def get_blob(self):
            return self.BlobSync('file.txt', datetime.datetime.now(), 111, 'md5hash')
        service = BlobStorage('wasbs://container/file.txt')
        service.get_blob = get_blob
        res = list(service.get_download_path_pairs('directory/file.txt', sync=True))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','directory/file.txt'))

    def _touch(self, file_name, content=u''):
        if not os.path.exists(os.path.dirname(file_name)):
            os.makedirs(os.path.dirname(file_name))
        f = io.open(file_name,'a',encoding='utf-8')
        f.write(content)
        f.close()

    def _get_fresh_small_blob(self):
        return self.BlobSync('file.txt', datetime.datetime.utcnow().replace(tzinfo=pytz.UTC) + datetime.timedelta(minutes=5), 1, hashlib.md5(b'a').digest())

    def _get_old_small_blob(self):
        return self.BlobSync('file.txt', datetime.datetime.utcnow().replace(tzinfo=pytz.UTC) - datetime.timedelta(minutes=5), 1, hashlib.md5(b'a').digest())

    def test_single_file_into_directory_with_name_sync_existing_same_md5_and_length(self):
        service = BlobStorage('wasbs://container/file.txt')
        service.get_blob = self._get_fresh_small_blob
        self._touch('directory/file.txt',u'a')
        res = list(service.get_download_path_pairs('directory/file.txt', sync=True))
        self.assertEqual(len(res), 0)

    def test_single_file_into_directory_with_name_sync_existing_diff_md5_and_same_length(self):
        service = BlobStorage('wasbs://container/file.txt')
        service.get_blob = self._get_fresh_small_blob
        self._touch('directory/file.txt',u'b')
        res = list(service.get_download_path_pairs('directory/file.txt', sync=True))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','directory/file.txt'))

    def test_single_file_into_directory_with_name_sync_existing_small_local_newer(self):
        service = BlobStorage('wasbs://container/file.txt')
        service.get_blob = self._get_old_small_blob
        self._touch('directory/file.txt',u'sth')
        res = list(service.get_download_path_pairs('directory/file.txt', sync=True))
        self.assertEqual(len(res), 0)

    def test_single_file_into_directory_with_name_sync_existing_small_blob_newer(self):
        service = BlobStorage('wasbs://container/file.txt')
        service.get_blob = self._get_fresh_small_blob
        self._touch('directory/file.txt',u'sth')
        res = list(service.get_download_path_pairs('directory/file.txt', sync=True))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','directory/file.txt'))

    def _get_small_blob(self):
        return [
            self.BlobSync('file-1.txt', datetime.datetime.utcnow().replace(tzinfo=pytz.UTC) + datetime.timedelta(minutes=5), 1, hashlib.md5(b'a').digest()),
            self.BlobSync('file-2.txt', datetime.datetime.utcnow().replace(tzinfo=pytz.UTC) - datetime.timedelta(minutes=5), 1, hashlib.md5(b'a').digest()),
            self.BlobSync('file-3.txt', datetime.datetime.utcnow().replace(tzinfo=pytz.UTC) - datetime.timedelta(minutes=5), 1, hashlib.md5(b'a').digest()),
        ]

    def test_prefixed_multiple_file_into_directory_sync_existing_do_nothing_and_get_the_missing(self):
        service = BlobStorage('wasbs://container/file.txt')
        service.list_blobs = self._get_small_blob
        self._touch('directory/file-1.txt',u'a')
        self._touch('directory/file-2.txt',u'a')
        res = list(service.get_download_path_pairs('directory/', prefix=True, sync=True))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file-3.txt','directory/file-3.txt'))

    def test_prefixed_multiple_file_into_directory_sync_existing_update_the_old_one_and_the_missing_one(self):
        service = BlobStorage('wasbs://container/file.txt')
        service.list_blobs = self._get_small_blob
        self._touch('directory/file-1.txt',u'b')
        self._touch('directory/file-2.txt',u'b')
        res = list(service.get_download_path_pairs('directory/', prefix=True, sync=True))
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0], ('file-1.txt','directory/file-1.txt'))
        self.assertEqual(res[1], ('file-3.txt','directory/file-3.txt'))
