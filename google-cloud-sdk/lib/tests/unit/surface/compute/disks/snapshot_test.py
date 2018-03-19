# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the disks snapshot subcommand."""

import itertools
import os
import re

from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import name_generator
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions as core_exceptions
from tests.lib import cli_test_base
from tests.lib import mock_matchers
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.compute import utils


class DisksSnapshotTestBase(sdk_test_base.WithFakeAuth,
                            cli_test_base.CliTestBase,
                            waiter_test_base.Base):
  API_VERSION = 'v1'

  def SetUp(self):
    self.api_mock = utils.ComputeApiMock(
        self.API_VERSION, project=self.Project(), zone='central2-a').Start()
    self.addCleanup(self.api_mock.Stop)

    self.StartObjectPatch(
        name_generator, 'GenerateRandomName',
        side_effect=('random-name-{}'.format(x) for x in itertools.count()))

    self.status_enum = self.api_mock.messages.Operation.StatusValueValuesEnum

  def TearDown(self):
    self.api_mock.batch_responder.AssertDone()

  def _GetCreateSnapshotRequest(self, disk_ref, snapshot_ref, description=None,
                                guest_flush=False,
                                raw_encryption_key=None,
                                rsa_encryption_key=None,):
    if disk_ref.Collection() == 'compute.regionDisks':
      service = self.api_mock.adapter.apitools_client.regionDisks
      request_type = (
          self.api_mock.messages.ComputeRegionDisksCreateSnapshotRequest)
    else:
      service = self.api_mock.adapter.apitools_client.disks
      request_type = (
          self.api_mock.messages.ComputeDisksCreateSnapshotRequest)
    snapshot = self.api_mock.messages.Snapshot(name=snapshot_ref.Name())
    payload = request_type(snapshot=snapshot, **disk_ref.AsDict())
    payload.guestFlush = guest_flush
    if description is not None:
      payload.snapshot.description = description
    if raw_encryption_key:
      payload.snapshot.sourceDiskEncryptionKey = (
          self.api_mock.messages.CustomerEncryptionKey(
              rawKey=raw_encryption_key))
    elif rsa_encryption_key:
      payload.snapshot.sourceDiskEncryptionKey = (
          self.api_mock.messages.CustomerEncryptionKey(
              rsaEncryptedKey=rsa_encryption_key))

    return service, 'CreateSnapshot', payload

  def _GetOperationRef(self, name, zone=None, region=None):
    params = {'project': self.Project()}
    if region:
      collection = 'compute.regionOperations'
      params['region'] = region
    elif zone:
      collection = 'compute.zoneOperations'
      params['zone'] = zone
    else:
      collection = 'compute.zoneOperations'
      params['zone'] = self.api_mock.zone

    return self.api_mock.resources.Parse(
        name, params, collection=collection)

  def _GetOperationMessage(self, operation_ref, status, errors=None):
    operation_cls = self.api_mock.messages.Operation
    operation = operation_cls(
        name=operation_ref.Name(),
        status=status,
        selfLink=operation_ref.SelfLink())
    if errors:
      operation.error = operation_cls.ErrorValue(errors=[
          operation_cls.ErrorValue.ErrorsValueListEntry(
              code=e['code'], message=e['message']
          ) for e in errors])
    return operation

  def _GetOperationGetRequest(self, operation_ref):
    return (
        self.api_mock.adapter.apitools_client.zoneOperations,
        'Get',
        self.api_mock.messages.ComputeZoneOperationsGetRequest(
            **operation_ref.AsDict()))

  def _GetSnapshotRef(self, name):
    return self.api_mock.resources.Parse(
        name,
        params={'project': self.Project()},
        collection='compute.snapshots')

  def _GetSnapshotMessage(self, snapshot_ref, disk_ref):
    return self.api_mock.messages.Snapshot(
        name=snapshot_ref.Name(),
        sourceDisk=disk_ref.SelfLink(),
        selfLink=snapshot_ref.SelfLink())

  def _GetDiskRef(self, name, zone=None, region=None):
    params = {'project': self.Project()}
    if region:
      collection = 'compute.regionDisks'
      params['region'] = region
    elif zone:
      collection = 'compute.disks'
      params['zone'] = zone
    else:
      collection = 'compute.disks'
      params['zone'] = self.api_mock.zone
    return self.api_mock.resources.Parse(
        name, params, collection=collection)

  def _GetSnapshotGetRequest(self, snapshot_ref):
    return (self.api_mock.adapter.apitools_client.snapshots,
            'Get',
            self.api_mock.messages.ComputeSnapshotsGetRequest(
                **snapshot_ref.AsDict()))

  def _GetZoneList(self, zones):
    return self.api_mock.messages.ZoneList(
        items=[self.api_mock.messages.Zone(name=z) for z in zones])


class DisksSnapshotTest(DisksSnapshotTestBase):

  def Setup(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testSnapshotOfOneDiskWithDefaultName(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])
    self.api_mock.batch_responder.ExpectBatch([
        (self._GetOperationGetRequest(operation_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.DONE)),
    ])
    self.api_mock.batch_responder.ExpectBatch([
        (self._GetSnapshotGetRequest(snapshot_ref),
         self._GetSnapshotMessage(snapshot_ref, disk_ref)),
    ])

    self.Run('compute disks snapshot disk-1 --zone central2-a')

    self.AssertOutputEquals('')
    self.AssertErrContains('Creating snapshot(s) random-name-0')

  def testOneDiskDefaultNameAsync(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    self.Run('compute disks snapshot {disk} --async'
             .format(disk=disk_ref.SelfLink()))

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Disk snapshot in progress for [{}].\n'
        'Use [gcloud compute operations describe URI] command to check '
        'the status of the operation(s).\n'.format(operation_ref.SelfLink()))

  def testOneDiskErrorAsync(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         Exception('booboo'))
    ])

    with self.assertRaisesRegexp(core_exceptions.MultiError, 'booboo'):
      self.Run('compute disks snapshot {disk} --async'
               .format(disk=disk_ref.SelfLink()))

    self.AssertOutputEquals('')
    self.AssertErrContains('booboo')

  def testOneDiskImmediateOperationError(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         self._GetOperationMessage(
             operation_ref,
             self.status_enum.DONE,
             errors=[{
                 'code': 'GUEST_FLUSH_NOT_SUPPORTED',
                 'message': 'booboo.'}]))
    ])

    with self.assertRaisesRegexp(
        core_exceptions.MultiError,
        'booboo.'):
      self.Run('compute disks snapshot {disk}'
               .format(disk=disk_ref.SelfLink()))

    self.AssertOutputEquals('')
    self.AssertErrContains('booboo.')

  def testOneDiskImmediateMultipleErrors(self):
    disk_ref1 = self._GetDiskRef('disk-1')
    disk_ref2 = self._GetDiskRef('disk-2')
    snapshot_ref1 = self._GetSnapshotRef('random-name-0')
    snapshot_ref2 = self._GetSnapshotRef('random-name-1')
    operation_ref1 = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref1, snapshot_ref1),
         self._GetOperationMessage(
             operation_ref1,
             self.status_enum.DONE,
             errors=[{
                 'code': 'GUEST_FLUSH_NOT_SUPPORTED',
                 'message': 'operation error.'}])),
        (self._GetCreateSnapshotRequest(disk_ref2, snapshot_ref2),
         Exception('http error'))

    ])

    with self.assertRaisesRegexp(
        core_exceptions.MultiError,
        'http error, operation error.'):
      self.Run('compute disks snapshot {disk1} {disk2}'
               .format(disk1=disk_ref1.SelfLink(),
                       disk2=disk_ref2.SelfLink()))

    self.AssertOutputEquals('')
    self.AssertErrContains('http error, operation error.')

  def testOneDiskSecondPollOperationError(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING))])
    self.api_mock.batch_responder.ExpectBatch([
        (self._GetOperationGetRequest(operation_ref),
         self._GetOperationMessage(
             operation_ref,
             self.status_enum.DONE,
             errors=[{
                 'code': 'GUEST_FLUSH_NOT_SUPPORTED',
                 'message': 'booboo.'
             }]
         )
        )
    ])

    with self.assertRaisesRegexp(
        core_exceptions.MultiError,
        'booboo.'):
      self.Run('compute disks snapshot {disk}'
               .format(disk=disk_ref.SelfLink()))

    self.AssertOutputEquals('')
    self.AssertErrContains('booboo.')

  def testSnapshotOfManyDisksWithDefaultNames(self):
    n_disks = 3
    disk_refs = [self._GetDiskRef('disk-{}'.format(c))
                 for c in xrange(n_disks)]
    snapshot_refs = [self._GetSnapshotRef('random-name-{}'.format(c))
                     for c in xrange(n_disks)]
    operation_refs = [self._GetOperationRef('operation-{}'.format(c))
                      for c in xrange(n_disks)]

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_refs[c], snapshot_refs[c]),
         self._GetOperationMessage(operation_refs[c], self.status_enum.PENDING))
        for c in xrange(n_disks)
    ])
    self.api_mock.batch_responder.ExpectBatch([
        (self._GetOperationGetRequest(operation_refs[c]),
         self._GetOperationMessage(operation_refs[c], self.status_enum.DONE))
        for c in xrange(n_disks)
    ])
    self.api_mock.batch_responder.ExpectBatch([
        (self._GetSnapshotGetRequest(snapshot_refs[c]),
         self._GetSnapshotMessage(snapshot_refs[c], disk_refs[c]))
        for c in xrange(n_disks)
    ])

    self.Run('compute disks snapshot {disks} --zone {zone}'
             .format(disks=' '.join(r.Name() for r in disk_refs),
                     zone=disk_refs[0].zone))

    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Creating snapshot(s) random-name-0, random-name-1, random-name-2')

  def testSnapshotOfOneDiskWithCustomNameAsync(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('my-snapshot-1')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    self.Run('compute disks snapshot {disk} --zone {zone} '
             '--snapshot-names {snapshot} --async'
             .format(disk=disk_ref.Name(),
                     snapshot=snapshot_ref.Name(),
                     zone=disk_ref.zone))

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Disk snapshot in progress for [{}].\n'
        'Use [gcloud compute operations describe URI] command to check '
        'the status of the operation(s).\n'.format(operation_ref.SelfLink()))

  def testSnapshotOfManyDisksWithCustomNames(self):
    n_disks = 3
    disk_refs = [self._GetDiskRef('disk-{}'.format(c))
                 for c in xrange(n_disks)]
    snapshot_refs = [self._GetSnapshotRef('snapshot-{}'.format(c))
                     for c in xrange(n_disks)]
    operation_refs = [self._GetOperationRef('operation-{}'.format(c))
                      for c in xrange(n_disks)]

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_refs[c], snapshot_refs[c]),
         self._GetOperationMessage(operation_refs[c], self.status_enum.PENDING))
        for c in xrange(n_disks)
    ])

    self.Run('compute disks snapshot {disks} '
             '--snapshot-names {snapshots} --zone {zone} --async'
             .format(disks=' '.join(r.Name() for r in disk_refs),
                     snapshots=','.join(r.Name() for r in snapshot_refs),
                     zone=disk_refs[0].zone))

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        '{}\n'
        'Use [gcloud compute operations describe URI] command to check '
        'the status of the operation(s).\n'
        .format('\n'.join('Disk snapshot in progress for [{}].'
                          .format(r.SelfLink()) for r in operation_refs)))

  def testIncorrectNumberOfSnapshotNames(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--snapshot-names\] must have the same number of values as disks '
        'being snapshotted'):
      self.Run("""
          compute disks snapshot disk-1
            --snapshot-names my-snapshot-1,my-snapshot-2
            --zone central2-a
        """)

  def testSnapshotOfOneDiskWithLongDescription(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(
            disk_ref, snapshot_ref, description='my snappy snapshot'),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    self.Run('compute disks snapshot {disk} '
             '--zone {zone} '
             '--description "my snappy snapshot" --async'
             .format(disk=disk_ref.Name(), zone=disk_ref.zone))

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Disk snapshot in progress for [{}].\n'
        'Use [gcloud compute operations describe URI] command to check '
        'the status of the operation(s).\n'.format(operation_ref.SelfLink()))

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('2\n')

    self.api_mock.make_requests.side_effect = iter([
        [
            self.api_mock.messages.Zone(name='central2-a'),
            self.api_mock.messages.Zone(name='central2-b'),
        ],
    ])

    disk_ref = self._GetDiskRef('disk-1', zone='central2-b')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    self.Run('compute disks snapshot disk-1 --async')

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'For the following disk:\n'
        ' - [disk-1]\n'
        'choose a zone:\n'
        ' [1] central2-a\n'
        ' [2] central2-b\n'
        'Please enter your numeric choice:  \n'
        'Disk snapshot in progress for [{}].\n'
        'Use [gcloud compute operations describe URI] command to check '
        'the status of the operation(s).\n'.format(operation_ref.SelfLink()))

  def testUriSupport(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('snapshot-1')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    self.Run('compute disks snapshot {disk} --snapshot-names {snapshot} --async'
             .format(disk=disk_ref.SelfLink(),
                     snapshot=snapshot_ref.SelfLink()))

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Disk snapshot in progress for [{}].\n'
        'Use [gcloud compute operations describe URI] command to check '
        'the status of the operation(s).\n'.format(operation_ref.SelfLink()))

  def testSnapshotCsekKeyFile(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    customer_encryption_key = self.api_mock.messages.CustomerEncryptionKey(
        rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(
            disk_ref, snapshot_ref,
            raw_encryption_key=customer_encryption_key.rawKey),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    csek_key_file = os.path.join(self.temp_path, 'key-file.json')
    key_store = utils.CsekKeyStore()
    key_store.AddKey(disk_ref.SelfLink(), customer_encryption_key.rawKey)
    key_store.WriteToFile(csek_key_file)

    self.Run('compute disks snapshot {disk} --zone {zone} '
             '--csek-key-file={keyfile} --async'
             .format(disk=disk_ref.Name(), zone=disk_ref.zone,
                     keyfile=csek_key_file))

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Disk snapshot in progress for [{}].\n'
        'Use [gcloud compute operations describe URI] command to check '
        'the status of the operation(s).\n'.format(operation_ref.SelfLink()))

  def testSnapshotCsekStdin(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    customer_encryption_key = self.api_mock.messages.CustomerEncryptionKey(
        rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(
            disk_ref, snapshot_ref,
            raw_encryption_key=customer_encryption_key.rawKey),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    key_store = utils.CsekKeyStore()
    key_store.AddKey(disk_ref.SelfLink(), customer_encryption_key.rawKey)
    self.WriteInput(key_store.AsString())

    self.Run('compute disks snapshot {disk} --zone {zone} '
             '--csek-key-file - --async'
             .format(disk=disk_ref.Name(), zone=disk_ref.zone,))

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Disk snapshot in progress for [{}].\n'
        'Use [gcloud compute operations describe URI] command to check '
        'the status of the operation(s).\n'.format(operation_ref.SelfLink()))

  def testSnapshotCsekKeyFileRsaWrappedKey(self):
    disk_ref = self._GetDiskRef('disk-1')

    csek_key_file = os.path.join(self.temp_path, 'key-file.json')
    key_store = utils.CsekKeyStore()
    key_store.AddKey(disk_ref.SelfLink(), key_type='rsa-encrypted')
    key_store.WriteToFile(csek_key_file)

    with self.assertRaisesRegexp(csek_utils.BadKeyTypeException, re.escape(
        'Invalid key type [rsa-encrypted]: this feature is only allowed in the '
        'alpha and beta versions of this command.')):
      self.Run('compute disks snapshot {disk} --zone {zone} '
               '--csek-key-file={keyfile}'
               .format(disk=disk_ref.Name(), zone=disk_ref.zone,
                       keyfile=csek_key_file))

    self.AssertOutputEquals('')

  def testSnapshotWithGuestFlush(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(
            disk_ref, snapshot_ref, guest_flush=True),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    self.Run('compute disks snapshot {disk} --guest-flush --async'
             .format(disk=disk_ref.SelfLink()))

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Disk snapshot in progress for [{}].\n'
        'Use [gcloud compute operations describe URI] command to check '
        'the status of the operation(s).\n'.format(operation_ref.SelfLink()))

  def testTimeout(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    waiter_mock = self.StartPatch(
        'googlecloudsdk.api_lib.util.waiter.WaitFor',
        autospec=True)

    self.Run('compute disks snapshot disk-1 --zone central2-a')

    waiter_mock.assert_called_once_with(
        mock_matchers.TypeMatcher(poller.BatchPoller),
        mock_matchers.TypeMatcher(poller.OperationBatch),
        'Creating snapshot(s) random-name-0',
        max_wait_ms=None
    )


class DisksSnapshotBetaTest(DisksSnapshotTestBase):

  API_VERSION = 'beta'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testSnapshotCsekKeyFileRsaWrappedKey(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    csek_key_file = os.path.join(self.temp_path, 'key-file.json')
    key_store = utils.CsekKeyStore()
    key_store.AddKey(disk_ref.SelfLink(), key_type='rsa-encrypted')
    key_store.WriteToFile(csek_key_file)

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(
            disk_ref, snapshot_ref,
            rsa_encryption_key=utils.SAMPLE_WRAPPED_CSEK_KEY),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    self.Run('compute disks snapshot {disk} '
             '--csek-key-file={keyfile} --async'
             .format(disk=disk_ref.SelfLink(), keyfile=csek_key_file))

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Disk snapshot in progress for [{}].\n'
        'Use [gcloud compute operations describe URI] command to check '
        'the status of the operation(s).\n'.format(operation_ref.SelfLink()))

  def testTimeout(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    waiter_mock = self.StartPatch(
        'googlecloudsdk.api_lib.util.waiter.WaitFor',
        autospec=True)

    self.Run('compute disks snapshot disk-1 --zone central2-a')

    waiter_mock.assert_called_once_with(
        mock_matchers.TypeMatcher(poller.BatchPoller),
        mock_matchers.TypeMatcher(poller.OperationBatch),
        'Creating snapshot(s) random-name-0',
        max_wait_ms=None
    )


class DisksSnapshotTestAlpha(DisksSnapshotTestBase):

  API_VERSION = 'alpha'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testRegional(self):
    disk_ref = self._GetDiskRef('disk-1', region='central2')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1', region='central2')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    self.Run('compute disks snapshot {disk} --region {region} --async'
             .format(disk=disk_ref.Name(), region=disk_ref.region))

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Disk snapshot in progress for [{}].\n'
        'Use [gcloud compute operations describe URI] command to check '
        'the status of the operation(s).\n'.format(operation_ref.SelfLink()))

  def testTimeout(self):
    disk_ref = self._GetDiskRef('disk-1')
    snapshot_ref = self._GetSnapshotRef('random-name-0')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetCreateSnapshotRequest(disk_ref, snapshot_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    waiter_mock = self.StartPatch(
        'googlecloudsdk.api_lib.util.waiter.WaitFor',
        autospec=True)

    self.Run('compute disks snapshot disk-1 --zone central2-a')

    waiter_mock.assert_called_once_with(
        mock_matchers.TypeMatcher(poller.BatchPoller),
        mock_matchers.TypeMatcher(poller.OperationBatch),
        'Creating snapshot(s) random-name-0',
        max_wait_ms=None
    )


if __name__ == '__main__':
  test_case.main()