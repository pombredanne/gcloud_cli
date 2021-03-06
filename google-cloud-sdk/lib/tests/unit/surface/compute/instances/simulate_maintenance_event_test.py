# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for the instances simulate-maintenance-event subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.compute import utils
from six.moves import range


class SimulateMaintenanceEventTest(sdk_test_base.WithFakeAuth,
                                   cli_test_base.CliTestBase,
                                   waiter_test_base.Base):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.zone = 'zone-2'
    self.api_mock = utils.ComputeApiMock(
        self.api_version, project=self.Project(), zone=self.zone).Start()
    self.addCleanup(self.api_mock.Stop)
    self.status_enum = self.api_mock.messages.Operation.StatusValueValuesEnum

  def TearDown(self):
    self.api_mock.batch_responder.AssertDone()

  def _GetOperationRef(self, name):
    return self.api_mock.resources.Parse(
        name,
        params={'project': self.Project(),
                'zone': self.zone},
        collection='compute.zoneOperations')

  def _GetInstanceRef(self, name):
    return self.api_mock.resources.Parse(
        name,
        params={'project': self.Project(),
                'zone': self.zone},
        collection='compute.instances')

  def _GetOperationMessage(self, operation_ref, status, resource_ref=None):
    return self.api_mock.messages.Operation(
        name=operation_ref.Name(),
        status=status,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)

  def _GetOperationGetRequest(self, operation_ref):
    return (self.api_mock.adapter.apitools_client.zoneOperations, 'Get',
            self.api_mock.messages.ComputeZoneOperationsGetRequest(
                **operation_ref.AsDict()))

  def _GetOperationWaitRequest(self, operation_ref):
    return (self.api_mock.adapter.apitools_client.zoneOperations, 'Wait',
            self.api_mock.messages.ComputeZoneOperationsWaitRequest(
                **operation_ref.AsDict()))

  def _GetOperationPollingRequest(self, operation_ref):
    return self._GetOperationWaitRequest(operation_ref)

  def _GetInstanceGetRequest(self, instance_ref):
    return (self.api_mock.adapter.apitools_client.instances, 'Get',
            self.api_mock.messages.ComputeInstancesGetRequest(
                **instance_ref.AsDict()))

  def _GetInstanceMessage(self, instance_ref):
    return self.api_mock.messages.Instance(name=instance_ref.Name())

  def _GetSimulateMaintenanceEventRequest(self, instance_ref):
    return (
        self.api_mock.adapter.apitools_client.instances,
        'SimulateMaintenanceEvent',
        self.api_mock.messages.ComputeInstancesSimulateMaintenanceEventRequest(
            project=self.Project(),
            instance=instance_ref.Name(),
            zone=self.zone))

  def testWithOperationPolling(self):
    """Test the synchronous version of the call."""
    instance_ref = self._GetInstanceRef('instance-1')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetSimulateMaintenanceEventRequest(instance_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])
    self.api_mock.batch_responder.ExpectBatch([
        (self._GetOperationPollingRequest(operation_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.DONE)),
    ])
    self.api_mock.batch_responder.ExpectBatch([
        (self._GetInstanceGetRequest(instance_ref),
         self._GetInstanceMessage(instance_ref)),
    ])

    self.Run("""
      compute instances simulate-maintenance-event instance-1
      --zone zone-2
    """)
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Simulating maintenance on instance(s) '
        '[https://compute.googleapis.com/compute/{}/projects/fake-project/'
        'zones/zone-2/instances/instance-1]'.format(self.api_version))

  def testAsync(self):
    """Test the asynchronous version of the call."""

    instance_ref = self._GetInstanceRef('instance-1')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetSimulateMaintenanceEventRequest(instance_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    self.Run("""
        compute instances simulate-maintenance-event instance-1
          --zone zone-2
          --async
          --format=disable
        """)

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Update in progress for gce instance [instance-1] '
        '[https://compute.googleapis.com/compute/{}/'
        'projects/fake-project/zones/zone-2/operations/operation-1] '
        'Use [gcloud compute operations describe] command to check the status '
        'of this operation.\n'.format(self.api_version))

  def testMultipleWithOperationPolling(self):
    """Test the synchronous version of the call with multiple instances."""
    n_instances = 3
    instance_refs = [
        self._GetInstanceRef('instance-{}'.format(c))
        for c in range(n_instances)
    ]
    operation_refs = [
        self._GetOperationRef('operation-{}'.format(c))
        for c in range(n_instances)
    ]

    self.api_mock.batch_responder.ExpectBatch([(
        self._GetSimulateMaintenanceEventRequest(instance_refs[c]),
        self._GetOperationMessage(operation_refs[c], self.status_enum.PENDING))
                                               for c in range(n_instances)])
    self.api_mock.batch_responder.ExpectBatch(
        [(self._GetOperationPollingRequest(operation_refs[c]),
          self._GetOperationMessage(operation_refs[c], self.status_enum.DONE))
         for c in range(n_instances)])
    self.api_mock.batch_responder.ExpectBatch(
        [(self._GetInstanceGetRequest(instance_refs[c]),
          self._GetInstanceMessage(instance_refs[c]))
         for c in range(n_instances)])

    self.Run('compute instances simulate-maintenance-event {instances} '
             '--zone zone-2'.format(instances=' '.join(r.Name()
                                                       for r in instance_refs)))

    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Simulating maintenance on instance(s) '
        '[https://compute.googleapis.com/compute/{}/projects/fake-project/'
        'zones/zone-2/instances/instance-0,'
        ' '
        'https://compute.googleapis.com/compute/{}/projects/fake-project/'
        'zones/zone-2/instances/instance-1,'
        ' '
        'https://compute.googleapis.com/compute/{}/projects/fake-project/'
        'zones/zone-2/instances/instance-2]'.format(
            self.api_version, self.api_version, self.api_version))

  def testMultipleAsync(self):
    """Test the asynchronous version of the call with multiple instances."""

    n_instances = 3
    instance_refs = [
        self._GetInstanceRef('instance-{}'.format(c))
        for c in range(n_instances)
    ]
    operation_refs = [
        self._GetOperationRef('operation-{}'.format(c))
        for c in range(n_instances)
    ]

    self.api_mock.batch_responder.ExpectBatch([(
        self._GetSimulateMaintenanceEventRequest(instance_refs[c]),
        self._GetOperationMessage(operation_refs[c], self.status_enum.PENDING))
                                               for c in range(n_instances)])

    self.Run('compute instances simulate-maintenance-event {instances} '
             '--zone zone-2 --async --format=disable'.format(
                 instances=' '.join(r.Name() for r in instance_refs)))

    self.AssertOutputEquals('')
    expected_err = ''
    for c in range(n_instances):
      expected_err += (
          'Update in progress for gce instance [instance-{inum}] '
          '[https://compute.googleapis.com/compute/{track}/projects/'
          'fake-project/zones/zone-2/operations/operation-{onum}]'
          ' Use [gcloud compute operations describe] command to '
          'check the status of this operation.\n').format(
              inum=c, onum=c, track=self.api_version)
    self.AssertErrEquals(expected_err)

  def testScopePrompt(self):
    """Test the zone prompt for the call."""
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.zones.service.List',
        return_value=[
            self.api_mock.messages.Zone(name='zone-1'),
            self.api_mock.messages.Zone(name='zone-2')
        ],)

    instance_ref = self._GetInstanceRef('instance-1')
    operation_ref = self._GetOperationRef('operation-1')

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetSimulateMaintenanceEventRequest(instance_ref),
         self._GetOperationMessage(operation_ref, self.status_enum.PENDING)),
    ])

    self.WriteInput('2\n')

    self.Run("""
          compute instances simulate-maintenance-event instance-1
            --async --format=disable
          """)

    self.AssertOutputEquals('')
    self.AssertErrContains('instance-1')
    self.AssertErrContains('zone-1')
    self.AssertErrContains('zone-2')


class SimulateMaintenanceEventTestBeta(SimulateMaintenanceEventTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class SimulateMaintenanceEventTestAlpha(SimulateMaintenanceEventTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
