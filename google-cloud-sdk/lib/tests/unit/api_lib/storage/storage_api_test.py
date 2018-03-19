# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for googlecloudsdk.api_lib.storage.storage_api."""
import io
import os
import re
import subprocess

from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import files as files_util
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.app import cloud_storage_util
import mock


class GetObjectTest(sdk_test_base.SdkBase):

  _OBJECT = storage_util.ObjectReference.FromUrl('gs://mybucket/myobject')

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

    self.storage_client = storage_api.StorageClient(self.apitools_client)
    self.storage_msgs = core_apis.GetMessagesModule('storage', 'v1')

  def testGetObject(self):
    self.apitools_client.objects.Get.Expect(
        self.storage_msgs.StorageObjectsGetRequest(
            bucket='mybucket', object='myobject'),
        self.storage_msgs.Object(name='myobject'))

    self.assertEquals(
        self.storage_client.GetObject(self._OBJECT),
        self.storage_msgs.Object(name='myobject'))


class CopyFileTest(sdk_test_base.SdkBase):

  _BUCKET = storage_util.BucketReference.FromBucketUrl('gs://mybucket/')

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

    self.storage_client = storage_api.StorageClient(self.apitools_client)
    self.storage_msgs = core_apis.GetMessagesModule('storage', 'v1')

    self.object_name = 'foobar'
    self.target_path = 'mytargetpath'
    self.local_path = self.Touch(
        self.temp_path, self.object_name, contents='somecontentshere')
    self.file_size = os.path.getsize(self.local_path)
    self.insert_request = self.storage_msgs.StorageObjectsInsertRequest(
        bucket=self._BUCKET.bucket,
        name=self.target_path,
        object=self.storage_msgs.Object(size=self.file_size)
    )

  def testSuccess(self):
    self.apitools_client.objects.Insert.Expect(
        self.insert_request,
        self.storage_msgs.Object(size=self.file_size)
    )
    self.storage_client.CopyFileToGCS(self._BUCKET,
                                      self.local_path,
                                      self.target_path)

  def testApiError(self):
    exception = http_error.MakeHttpError()

    self.apitools_client.objects.Insert.Expect(
        self.insert_request,
        exception=exception
    )

    with self.assertRaisesRegexp(
        exceptions.BadFileException,
        r'Could not copy \[{}\] to \[{}\]. Please retry: Invalid request API '
        r'reason: Invalid request.'.format(
            re.escape(self.local_path), self.target_path)):
      self.storage_client.CopyFileToGCS(self._BUCKET,
                                        self.local_path,
                                        self.target_path)

  def testSizeMismatch(self):
    self.apitools_client.objects.Insert.Expect(
        self.insert_request,
        # Return an object with a different size.
        self.storage_msgs.Object(size=self.file_size - 1)
    )

    with self.assertRaises(exceptions.BadFileException):
      self.storage_client.CopyFileToGCS(self._BUCKET,
                                        self.local_path,
                                        self.target_path)


class CopyFileFromGCSTest(sdk_test_base.SdkBase):

  _BUCKET = storage_util.BucketReference.FromBucketUrl('gs://mybucket/')

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

    self.storage_client = storage_api.StorageClient(self.apitools_client)
    self.storage_msgs = self.apitools_client.MESSAGES_MODULE

    self.object_name = 'foobar'
    self.target_path = 'mytargetpath'
    self.local_path = os.path.join(self.temp_path, self.object_name)
    self.get_request = self.storage_msgs.StorageObjectsGetRequest(
        bucket=self._BUCKET.bucket,
        object=self.target_path)

  def testSuccess(self):
    # TODO(b/33202933): There's a TODO in the apitools testing code to add
    # support for upload/download in mocked apitools clients; when that is
    # resolved, test a non-empty mocked file here.
    # Use object() instead of None because when the mock is given None, it uses
    # a real client
    response = object()
    self.apitools_client.objects.Get.Expect(
        self.get_request,
        response)
    self.apitools_client.objects.Get.Expect(
        self.get_request,
        self.storage_msgs.Object(size=0))
    self.storage_client.CopyFileFromGCS(self._BUCKET,
                                        self.target_path,
                                        self.local_path)

  def testApiError(self):
    exception = http_error.MakeHttpError()

    self.apitools_client.objects.Get.Expect(
        self.get_request,
        exception=exception
    )

    with self.assertRaises(exceptions.BadFileException):
      self.storage_client.CopyFileFromGCS(self._BUCKET,
                                          self.target_path,
                                          self.local_path)

  def testSizeMismatch(self):
    # Use object() instead of None because when the mock is given None, it uses
    # a real client
    response = object()
    self.apitools_client.objects.Get.Expect(
        self.get_request,
        response)
    self.apitools_client.objects.Get.Expect(
        self.get_request,
        # Return an object with a different size.
        self.storage_msgs.Object(size=-1))

    with self.assertRaises(exceptions.BadFileException):
      self.storage_client.CopyFileFromGCS(self._BUCKET,
                                          self.target_path,
                                          self.local_path)


class ReadObjectTest(sdk_test_base.SdkBase):

  _OBJECT = storage_util.ObjectReference.FromUrl('gs://bucket/object')

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

    self.storage_client = storage_api.StorageClient(self.apitools_client)
    self.storage_msgs = self.apitools_client.MESSAGES_MODULE

    self.get_request = self.storage_msgs.StorageObjectsGetRequest(
        bucket='bucket',
        object='object')

  def testSuccess(self):
    # TODO(b/33202933): There's a TODO in the apitools testing code to add
    # support for upload/download in mocked apitools clients; when that is
    # resolved, test a non-empty mocked file here.
    # Use object() instead of None because when the mock is given None, it uses
    # a real client
    response = object()
    self.apitools_client.objects.Get.Expect(
        self.get_request,
        response)
    self.assertEqual(
        self.storage_client.ReadObject(self._OBJECT).read(),
        '')

  def testApiError(self):
    exception = http_error.MakeHttpError()

    self.apitools_client.objects.Get.Expect(
        self.get_request,
        exception=exception
    )

    with self.assertRaises(exceptions.BadFileException):
      self.storage_client.ReadObject(self._OBJECT)


class ListBucketTest(cloud_storage_util.WithGCSCalls):

  _BUCKET_NAME = 'testbucket'

  _SHA1_SUMS = {
      'content': '040f06fd774092478d450774f5ba30c5da78acc8',
      'content2': '6dc99d4757bcb35eaaf4cd3cb7907189fab8d254',
      'content3': '32c5ff3108bcea43b1c4826d66f43a3ae570e663'
  }

  def SetUp(self):
    self.bucket = storage_util.BucketReference.FromBucketUrl(
        'gs://{0}/'.format(self._BUCKET_NAME))
    self.storage_client = storage_api.StorageClient()

  def testListBucket(self):
    self.ExpectList([('a', 'content'), ('b', 'content'), ('c', 'content2')])

    self.assertEquals(
        self.storage_client.ListBucket(self.bucket),
        set([self._SHA1_SUMS['content'], self._SHA1_SUMS['content2']]))

  def testListBucketMultiplePages(self):
    self.ExpectListMulti([
        [('a', 'content'), ('b', 'content')],
        [('c', 'content2'), ('d', 'content3')]])
    self.assertEquals(
        self.storage_client.ListBucket(self.bucket),
        set([self._SHA1_SUMS['content'], self._SHA1_SUMS['content2'],
             self._SHA1_SUMS['content3']]))


class DeleteBucketTest(test_case.TestCase):

  _BUCKET_NAME = 'testbucket'

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

    self.storage_client = storage_api.StorageClient(self.apitools_client)

  def testDeleteBucket(self):
    bucket = storage_util.BucketReference.FromBucketUrl(
        'gs://{0}/'.format(self._BUCKET_NAME))
    self.apitools_client.buckets.Delete.Expect(
        self.apitools_client.MESSAGES_MODULE.StorageBucketsDeleteRequest(
            bucket=self._BUCKET_NAME),
        self.apitools_client.MESSAGES_MODULE.StorageBucketsDeleteResponse()
    )

    self.storage_client.DeleteBucket(bucket)


class RsyncTest(test_case.TestCase):

  def _MockPopen(self):
    popen_mock = mock.Mock(spec=subprocess.Popen)
    popen_mock.stdin = io.StringIO()
    popen_mock.communicate.return_value = ('[]\n', '')
    popen_mock.returncode = 0
    return self.StartObjectPatch(subprocess, 'Popen',
                                 return_value=popen_mock, autospec=True)

  def _MockFindExecutableOnPath(self):
    return self.StartObjectPatch(files_util, 'FindExecutableOnPath',
                                 return_value='/usr/bin/gsutil')

  def testRsyncMakesCorrectGcloudCall(self):
    popen_mock = self._MockPopen()
    self._MockFindExecutableOnPath()
    storage_api.Rsync('./sourcedir', 'gs://bucket/destdir')
    self.assertEqual(popen_mock.call_count, 1)
    args, _ = popen_mock.call_args
    self.assertEqual(
        args[0][-5:],
        ['rsync', '-R', '-c', './sourcedir', 'gs://bucket/destdir'])

  def testRsyncMakesCorrectGcloudCallWithExcludePattern(self):
    popen_mock = self._MockPopen()
    self._MockFindExecutableOnPath()
    storage_api.Rsync('./sourcedir', 'gs://bucket/destdir', 'excludeme.*')
    self.assertEqual(popen_mock.call_count, 1)
    args, _ = popen_mock.call_args
    self.assertEqual(
        args[0][-7:], ['rsync', '-R', '-c', '-x', 'excludeme.*',
                       './sourcedir', 'gs://bucket/destdir'])
