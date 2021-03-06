# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Tests of lib.storage_helpers methods."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import unit_base

import mock


class StorageHelpersUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for lib.storage_helpers."""

  BASE_GCS_PATH = 'gs://test-bucket/test/object-name'
  GCS_PATH = 'gs://test-bucket/test/object-name.000000000'
  GCS_BUCKET_NAME = 'test-bucket'
  GCS_OBJECT_NAME = 'test/object-name.000000000'
  NEXT_GCS_OBJECT_NAME = 'test/object-name.000000001'

  def SetUp(self):
    self.mock_gcs_client = apitools_mock.Client(
        core_apis.GetClientClass('storage', 'v1'),
        real_client=core_apis.GetClientInstance('storage', 'v1', no_http=True))
    self.mock_gcs_client.Mock()
    self.addCleanup(self.mock_gcs_client.Unmock)
    self.mock_exec = self.StartPatch(
        'googlecloudsdk.core.execution_utils.Exec')
    self.mock_config_bin_path = self.StartPropertyPatch(
        config.Paths, 'sdk_bin_path')
    self.mock_config_bin_path.return_value = 'bin'

    self.storage_client = storage_helpers.StorageClient()
    self.storage_stream = storage_helpers.StorageObjectSeriesStream(
        self.BASE_GCS_PATH, self.storage_client)
    self.storage_messages = core_apis.GetMessagesModule('storage', 'v1')

    self.storage_api_client = storage_api.StorageClient()
    self.copy_file_mock = self.StartObjectPatch(self.storage_api_client,
                                                'CopyFileToGCS')
    self.storage_bucket = 'foo'

  def MakeObject(self, **kwargs):
    return self.storage_messages.Object(
        bucket=kwargs.get('bucket', self.GCS_BUCKET_NAME),
        name=kwargs.get('name', self.GCS_OBJECT_NAME),
        size=kwargs.get('size', None))

  def ExpectGetObject(
      self, object_ref=None, response=None, exception=None, return_object=True):
    if not object_ref:
      object_ref = self.MakeObject()
    request = self.storage_messages.StorageObjectsGetRequest(
        bucket=object_ref.bucket,
        object=object_ref.name)
    if not (response or exception) and return_object:
      response = object_ref
    self.mock_gcs_client.objects.Get.Expect(
        request=request, response=response, exception=exception)

  @sdk_test_base.Filters.DoNotRunOnWindows
  def testUpload(self):
    storage_helpers.Upload(
        ['foo', '/tmp/bar', 'baz.txt'], 'gs://foo/bar/',
        storage_client=self.storage_api_client)
    self.copy_file_mock.assert_has_calls(
        [mock.call('foo', storage_util.ObjectReference(
            self.storage_bucket, 'bar/foo')),
         mock.call('/tmp/bar', storage_util.ObjectReference(
             self.storage_bucket, 'bar/bar')),
         mock.call('baz.txt', storage_util.ObjectReference(
             self.storage_bucket, 'bar/baz.txt'))])

  @sdk_test_base.Filters.RunOnlyOnWindows
  def testUploadWindows(self):
    storage_helpers.Upload(
        ['\\temp\\foo', 'C:\\temp\\bar', 'baz.txt'], 'gs://foo/bar/',
        storage_client=self.storage_api_client)
    self.copy_file_mock.assert_has_calls(
        [mock.call('\\temp\\foo', storage_util.ObjectReference(
            self.storage_bucket, 'bar/foo')),
         mock.call('C:\\temp\\bar', storage_util.ObjectReference(
             self.storage_bucket, 'bar/bar')),
         mock.call('baz.txt', storage_util.ObjectReference(
             self.storage_bucket, 'bar/baz.txt'))])

  def testUploadException(self):
    self.copy_file_mock.side_effect = calliope_exceptions.BadFileException()
    with self.AssertRaisesExceptionMatches(
        exceptions.FileUploadError,
        r"Failed to upload files ['foo', '/tmp/bar', 'baz.txt'] "
        r"to 'gs://foo/bar/'."):
      storage_helpers.Upload(['foo', '/tmp/bar', 'baz.txt'], 'gs://foo/bar/')

  def testGetObject(self):
    expected_object = self.MakeObject()
    self.ExpectGetObject()
    object_info = self.storage_client.GetObject(self.MakeObject())
    self.assertEqual(expected_object, object_info)

  def testGetNonExistentObject(self):
    self.ExpectGetObject(exception=self.MakeHttpError(404))
    object_info = self.storage_client.GetObject(self.MakeObject())
    self.assertIsNone(object_info)

  def testBuildObjectStream(self):
    # apitools Expect does not yet support extra kwargs such as "download."
    get_object_mock = self.StartObjectPatch(
        self.storage_client.client.objects,
        'Get')
    stream = io.StringIO()
    mock_object_size = 42
    object_info = self.MakeObject(size=mock_object_size)

    download = self.storage_client.BuildObjectStream(stream, object_info)

    # Check the correctness of the Get request.
    get_object_mock.assert_called_once_with(
        request=self.storage_messages.StorageObjectsGetRequest(
            bucket=self.GCS_BUCKET_NAME, object=self.GCS_OBJECT_NAME),
        download=mock.ANY)
    # Check the correctness of the download creation.
    self.assertEqual(
        stream,
        get_object_mock.call_args_list[0][1]['download'].stream)
    self.assertFalse(
        get_object_mock.call_args_list[0][1]['download'].auto_transfer)
    # Check the metadata of the returned download.
    self.assertEqual(download.total_size, mock_object_size)

  # StorageObjectSeriesStream tests

  def test_GetObject(self):
    expected_object = self.MakeObject()
    self.ExpectGetObject()
    object_info = self.storage_stream._GetObject(0)
    self.assertEqual(expected_object, object_info)

  def test_GetObject1(self):
    expected_object = self.MakeObject(name=self.NEXT_GCS_OBJECT_NAME)
    self.ExpectGetObject(expected_object)
    object_info = self.storage_stream._GetObject(1)
    self.assertEqual(expected_object, object_info)

  def testOpen(self):
    self.assertTrue(self.storage_stream.open)

  def testClose(self):
    self.storage_stream.Close()
    self.assertFalse(self.storage_stream.open)

  # TODO(b/33202933): There's a TODO in the apitools testing code to add
  # support for upload/download in mocked apitools clients; when that is
  # resolved, test a non-empty mocked stream here.

  def testReadIntoWritableEmptyStream(self):
    stream = io.StringIO()
    object1 = self.MakeObject()
    object2 = self.MakeObject(name=self.NEXT_GCS_OBJECT_NAME)
    self.ExpectGetObject(object2, exception=self.MakeHttpError(404))
    self.ExpectGetObject(object1, exception=self.MakeHttpError(404))
    bytes_read = self.storage_stream.ReadIntoWritable(stream)
    self.assertTrue(self.storage_stream.open)
    self.assertEqual(0, bytes_read)
    self.assertEqual('', stream.getvalue())

  def testReadIntoWritableInternalError(self):
    stream = io.StringIO()
    message = "Oops that wasn't supposed to Happen"
    error = self.MakeHttpError(500, message)
    object1 = self.MakeObject()
    object2 = self.MakeObject(name=self.NEXT_GCS_OBJECT_NAME)
    self.ExpectGetObject(object2, exception=self.MakeHttpError(404))
    self.ExpectGetObject(object1, exception=error)
    self.storage_stream.ReadIntoWritable(stream)
    self.assertTrue(self.storage_stream.open)
    self.AssertErrContains(message)

  def testReadIntoWritableClosed(self):
    self.storage_stream.Close()
    stream = io.StringIO()
    with self.assertRaises(ValueError):
      self.storage_stream.ReadIntoWritable(stream)

  @sdk_test_base.Filters.DoNotRunOnWindows
  def testUploadWithGsutil(self):
    properties.VALUES.storage.use_gsutil.Set(True)
    expected_command = ['bin/gsutil', 'cp', 'foo', '/tmp/bar',
                        'baz.txt', 'gs://foo/bar/']
    self.mock_exec.return_value = 0
    storage_helpers.Upload(['foo', '/tmp/bar', 'baz.txt'], 'gs://foo/bar/')
    self.mock_exec.assert_called_once_with(
        expected_command, no_exit=True, out_func=mock.ANY, err_func=mock.ANY)

  @sdk_test_base.Filters.RunOnlyOnWindows
  def testUploadWindowsWithGsutil(self):
    properties.VALUES.storage.use_gsutil.Set(True)
    expected_command = ['cmd', '/c', 'bin\\gsutil.cmd', 'cp', '\\temp\\foo',
                        'C:\\temp\\bar', 'baz.txt', 'gs://foo/bar/']
    self.mock_exec.return_value = 0
    storage_helpers.Upload(
        ['\\temp\\foo', 'C:\\temp\\bar', 'baz.txt'], 'gs://foo/bar/')
    self.mock_exec.assert_called_once_with(
        expected_command, no_exit=True, out_func=mock.ANY, err_func=mock.ANY)

  def testUploadExceptionWithGsutil(self):
    properties.VALUES.storage.use_gsutil.Set(True)
    self.mock_exec.return_value = 1
    with self.AssertRaisesExceptionMatches(
        exceptions.FileUploadError,
        "Failed to upload files ['foo', '/tmp/bar', 'baz.txt', "
        "'gs://foo/bar/'] to 'gs://foo/bar/' using gsutil."):
      storage_helpers.Upload(['foo', '/tmp/bar', 'baz.txt'], 'gs://foo/bar/')


if __name__ == '__main__':
  sdk_test_base.main()
