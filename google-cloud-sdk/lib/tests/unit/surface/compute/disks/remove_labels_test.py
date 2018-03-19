# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for the disks remove-labels subcommand."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import disks_labels_test_base


class RemoveLabelsTest(disks_labels_test_base.DisksLabelsTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)

  def testZonalUpdateValidDisksWithLabelsAndRemoveLabels(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    edited_labels = (('key2', 'value2'), ('key3', 'value3'))

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint='fingerprint-42')
    updated_disk = self._MakeDiskProto(disk_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1', zone='atlanta')
    operation = self._MakeOperationMessage(operation_ref, disk_ref)

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref, edited_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(disk_ref, updated_disk)

    response = self.Run(
        'compute disks remove-labels {} --labels key1,key0'
        .format(disk_ref.SelfLink()))
    self.assertEqual(response, updated_disk)

  def testRemoveAll(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint='fingerprint-42')
    updated_disk = self._MakeDiskProto(disk_ref, labels=())
    operation_ref = self._GetOperationRef('operation-1', zone='atlanta')
    operation = self._MakeOperationMessage(operation_ref, disk_ref)

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref, {}, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(disk_ref, updated_disk)

    response = self.Run(
        'compute disks remove-labels {} --all'
        .format(disk_ref.SelfLink()))
    self.assertEqual(response, updated_disk)

  def testRemoveAllEmpty(self):
    # Removing all labels when the disk has no labels to start with.
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')
    disk = self._MakeDiskProto(
        disk_ref, labels=(), fingerprint='fingerprint-42')
    self._ExpectGetRequest(disk_ref, disk)

    self.Run(
        'compute disks remove-labels {} --all'
        .format(disk_ref.SelfLink()))

  def testRemoveNonExisting(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint='fingerprint-42')

    self._ExpectGetRequest(disk_ref, disk)

    response = self.Run(
        'compute disks remove-labels {} --labels DoesNotExist'
        .format(disk_ref.SelfLink()))
    self.assertEqual(response, disk)

  def testRemoveWithNoLabelsOnDisk(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')
    disk = self._MakeDiskProto(
        disk_ref, labels={}, fingerprint='fingerprint-42')

    self._ExpectGetRequest(disk_ref, disk)

    response = self.Run(
        'compute disks remove-labels {} --labels DoesNotExist'
        .format(disk_ref.SelfLink()))
    self.assertEqual(response, disk)

  def testNoLabelsOrAllSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--all | --labels) must be specified.'
        ):
      self.Run('compute disks remove-labels disk-1')

  def testResourceNotFound(self):
    disk_ref = self._GetDiskRef('some-disk', zone='atlanta')
    error = http_error.MakeHttpError(
        code=404,
        message='some-disk was not found',
        reason='NOT FOUND',
        content={},
        url='')

    self._ExpectGetRequest(disk_ref=disk_ref, disk=None, exception=error)

    with self.AssertRaisesHttpExceptionMatches(
        'NOT FOUND: some-disk was not found'):
      self.Run(
          'compute disks remove-labels {} --all'
          .format(disk_ref.SelfLink()))

  def testScopePromptWithZone(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')
    disk = self._MakeDiskProto(disk_ref, labels=[])
    self._ExpectGetRequest(disk_ref, disk)

    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.StartPatch('googlecloudsdk.api_lib.compute.zones.service.List',
                    return_value=[
                        self.messages.Zone(name='atlanta'),
                        self.messages.Zone(name='charlotte')],
                   )
    self.StartPatch('googlecloudsdk.api_lib.compute.regions.service.List',
                    return_value=[
                        self.messages.Region(name='georgia')],
                   )
    self.WriteInput('1\n')
    self.Run('compute disks remove-labels disk-1 --labels key0')
    self.AssertErrContains('atlanta')
    self.AssertErrContains('charlotte')
    self.AssertErrNotContains('georgia')


class RemoveLabelsTestAlpha(disks_labels_test_base.DisksLabelsTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)

  def testRegionalUpdateValidDisksWithLabelsAndRemoveLabels(self):
    disk_ref = self._GetDiskRef('disk-1', region='us-central')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    edited_labels = (('key2', 'value2'), ('key3', 'value3'))

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint='fingerprint-42')
    updated_disk = self._MakeDiskProto(disk_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1', region='us-central')
    operation = self._MakeOperationMessage(operation_ref, disk_ref)

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref, edited_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(disk_ref, updated_disk)

    response = self.Run(
        'compute disks remove-labels {} --labels key1,key0'
        .format(disk_ref.SelfLink()))
    self.assertEqual(response, updated_disk)

  def testScopePromptWithRegionAndZone(self):
    disk_ref = self._GetDiskRef('disk-1', region='us-central')
    disk = self._MakeDiskProto(disk_ref, labels=[])
    self._ExpectGetRequest(disk_ref, disk)

    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.StartPatch('googlecloudsdk.api_lib.compute.zones.service.List',
                    return_value=[
                        self.messages.Zone(name='us-central1'),
                        self.messages.Zone(name='us-central2')],
                   )
    self.StartPatch('googlecloudsdk.api_lib.compute.regions.service.List',
                    return_value=[
                        self.messages.Region(name='us-central')],
                   )
    self.WriteInput('1\n')
    self.Run('compute disks remove-labels disk-1 --labels key0')
    self.AssertErrContains('us-central1')
    self.AssertErrContains('us-central2')
    self.AssertErrContains('us-central')


if __name__ == '__main__':
  test_case.main()