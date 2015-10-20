import os
import unittest
from azrcmd import *

class TestInvalidBlobStorageURL(unittest.TestCase):
    def setUp(self):
        os.environ['AZURE_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_STORAGE_ACCESS_KEY'] = 'key'

    def test_put(self):
        with self.assertRaises(InvalidBlobStorePath):
            put(['example.txt', 'wasbs://container/example.txt'])

    def test_get(self):
        with self.assertRaises(InvalidBlobStorePath):
            get(['wasbs://container/example.txt', 'example.txt'])

    def test_ls(self):
        with self.assertRaises(InvalidBlobStorePath):
            ls(['wasbs://container/example'])

    def test_rm(self):
        with self.assertRaises(InvalidBlobStorePath):
            rm(['wasbs://container/example.txt'])

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
            rm(['wasbs://container@example.txt'])

class TestPutPaths(unittest.TestCase):
    def setUp(self):
        os.environ['AZURE_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_STORAGE_ACCESS_KEY'] = 'key'

    def test_single_file(self):
        service = BlobStorage('wasbs://container@file.txt')
        res = list(service.get_upload_path_pairs(['file.txt']))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','file.txt'))

    def test_single_file_renamed(self):
        service = BlobStorage('wasbs://container@renamed.txt')
        res = list(service.get_upload_path_pairs(['file.txt']))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','renamed.txt'))

    def test_single_file_into_directory(self):
        service = BlobStorage('wasbs://container@directory/')
        res = list(service.get_upload_path_pairs(['file.txt']))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ('file.txt','directory/file.txt'))

    def test_single_file_renamed_into_directory(self):
        service = BlobStorage('wasbs://container@directory/renamed.txt')
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
        service = BlobStorage('wasbs://container@directory/')
        res = list(service.get_upload_path_pairs(['f1.txt','f2.txt','f3.txt']))

        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('f1.txt','directory/f1.txt'))
        self.assertEqual(res[1], ('f2.txt','directory/f2.txt'))
        self.assertEqual(res[2], ('f3.txt','directory/f3.txt'))

    def test_multiple_file_into_directory_without_slash(self):
        service = BlobStorage('wasbs://container@directory')
        res = list(service.get_upload_path_pairs(['f1.txt','f2.txt','f3.txt']))

        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], ('f1.txt','directory/f1.txt'))
        self.assertEqual(res[1], ('f2.txt','directory/f2.txt'))
        self.assertEqual(res[2], ('f3.txt','directory/f3.txt'))

    def test_multiple_file_from_dir_into_directory(self):
        service = BlobStorage('wasbs://container@directory/')
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
        service = BlobStorage('wasbs://container@folder')
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
    pass

