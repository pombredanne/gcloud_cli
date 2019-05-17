# -*- coding: utf-8 -*- #
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
"""Tests for the instance-groups managed instance-configs list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from mock import patch


class InstanceGroupsManagedInstancesConfigsListTestBase(test_base.BaseTest):

  _API_VERSION = 'alpha'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self._API_VERSION)

  def _MakePreservedStateDiskMapEntry(self, device_name, source, mode):
    mode_map = {
        'READ_ONLY': self.messages.PreservedStatePreservedDisk
                     .ModeValueValuesEnum.READ_ONLY,
        'READ_WRITE': self.messages.PreservedStatePreservedDisk
                      .ModeValueValuesEnum.READ_WRITE
    }
    return self.messages.PreservedState.DisksValue.AdditionalProperty(
        key=device_name,
        value=self.messages.PreservedStatePreservedDisk(
            autoDelete=self.messages.PreservedStatePreservedDisk \
              .AutoDeleteValueValuesEnum.NEVER,
            source=source,
            mode=mode_map[mode]
        )
    )

  def _MakePreservedStateMetadataMapEntry(self, key, value):
    return self.messages.PreservedState.MetadataValue.AdditionalProperty(
        key=key, value=value)

  def MakePerInstanceConfig(self, instance, override_disks, override_metadata,
                            override_origin):
    disk_overrides = []
    preserved_state_disks = []
    for override_disk in override_disks:
      disk_overrides.append(
          self.messages.ManagedInstanceOverrideDiskOverride(
              deviceName=override_disk['device_name'],
              source=override_disk['source'],
              mode=self.messages.ManagedInstanceOverrideDiskOverride\
              .ModeValueValuesEnum(override_disk['mode']),
          )
      )
      preserved_state_disks.append(
          self._MakePreservedStateDiskMapEntry(
              device_name=override_disk['device_name'],
              source=override_disk['source'],
              mode=override_disk['mode']
          )
      )
    metadata_overrides = [
        self.messages.ManagedInstanceOverride.MetadataValueListEntry(
            key=metadata['key'], value=metadata['value'])
        for metadata in override_metadata
    ]
    preserved_state_metadata = [
        self._MakePreservedStateMetadataMapEntry(
            key=metadata['key'], value=metadata['value'])
        for metadata in override_metadata
    ]
    return self.messages.PerInstanceConfig(
        instance=instance,
        name=instance.rsplit('/', 1)[-1],
        override=self.messages.ManagedInstanceOverride(
            disks=disk_overrides,
            metadata=metadata_overrides,
            origin=self.messages.ManagedInstanceOverride.OriginValueValuesEnum(
                override_origin),
        ),
        preservedState=self.messages.PreservedState(
            disks=self.messages.PreservedState.DisksValue(
                additionalProperties=preserved_state_disks
            ),
            metadata=self.messages.PreservedState.MetadataValue(
                additionalProperties=preserved_state_metadata
            )
        ),
    )


class InstanceGroupsManagedInstancesConfigsListZonalTest(
    InstanceGroupsManagedInstancesConfigsListTestBase):

  def SetUp(self):
    super(InstanceGroupsManagedInstancesConfigsListZonalTest, self).SetUp()
    self.make_requests.side_effect = iter([
        [
            self.messages.InstanceGroupManagersListPerInstanceConfigsResp(
                items=self._MakeInstanceConfigsInManagedInstanceGroupZonal(),)
        ],
    ])

  def _MakeInstanceConfigsInManagedInstanceGroupZonal(self):
    prefix = '{0}/projects/my-project/'.format(self.compute_uri)
    return [
        self.MakePerInstanceConfig(
            prefix + 'zones/us-central1-a/instances/inst-0001', [
                {
                    'device_name': 'my-disk-1',
                    'source': prefix + 'zones/us-central1-a/disks/inst-0001-1',
                    'mode': 'READ_WRITE'
                },
                {
                    'device_name': 'my-disk-2',
                    'source': prefix + 'zones/us-central1-a/disks/inst-0001-2',
                    'mode': 'READ_ONLY'
                },
            ], [
                {
                    'key': 'key-BAR',
                    'value': 'value BAR'
                },
                {
                    'key': 'key-foo',
                    'value': 'value foo'
                },
            ], 'AUTO_GENERATED'),
        self.MakePerInstanceConfig(
            prefix + 'zones/us-central1-a/instances/inst-0002', [
                {
                    'device_name': 'my-disk-1',
                    'source': prefix + 'zones/us-central1-a/disks/inst-0002-1',
                    'mode': 'READ_WRITE'
                },
                {
                    'device_name': 'my-disk-2',
                    'source': prefix + 'zones/us-central1-a/disks/inst-0002-2',
                    'mode': 'READ_ONLY'
                },
            ], [], 'AUTO_GENERATED'),
        self.MakePerInstanceConfig(
            prefix + 'zones/us-central1-a/instances/custom-inst-0003', [
                {
                    'device_name':
                        'my-custom-disk-1',
                    'source':
                        prefix + 'zones/us-central1-a/disks/custom-disk-1',
                    'mode':
                        'READ_ONLY'
                },
            ], [], 'USER_PROVIDED'),
    ]

  def testListInstanceConfigs(self):
    self.Run("""
        compute instance-groups managed instance-configs list
        group-a --zone us-central1-a
        """)
    request = (
        self.messages.ComputeInstanceGroupManagersListPerInstanceConfigsRequest(
            instanceGroupManager='group-a',
            project='my-project',
            zone='us-central1-a'))
    self.CheckRequests([(self.compute.instanceGroupManagers,
                         'ListPerInstanceConfigs', request)])

    self.AssertOutputMatches(
        """\
        ---
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0001
        name: inst-0001
        override:
          disks:
          - deviceName: my-disk-1
            mode: READ_WRITE
            source: {compute_uri}/projects/my-project/zones/us-central1-a/disks/inst-0001-1
          - deviceName: my-disk-2
            mode: READ_ONLY
            source: {compute_uri}/projects/my-project/zones/us-central1-a/disks/inst-0001-2
          metadata:
          - key: key-BAR
            value: value BAR
          - key: key-foo
            value: value foo
          origin: AUTO_GENERATED
        preservedState:
          disks:
            my-disk-1:
              autoDelete: NEVER
              mode: READ_WRITE
              source: https://www.googleapis.com/compute/alpha/projects/my-project/zones/us-central1-a/disks/inst-0001-1
            my-disk-2:
              autoDelete: NEVER
              mode: READ_ONLY
              source: https://www.googleapis.com/compute/alpha/projects/my-project/zones/us-central1-a/disks/inst-0001-2
          metadata:
            key-BAR: value BAR
            key-foo: value foo
        .*
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0002
        .*
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/custom-inst-0003
        .*
        """.format(compute_uri=self.compute_uri),
        normalize_space=True)

  def testListInstanceConfigsWithLimit(self):
    self.Run("""
        compute instance-groups managed instance-configs list
        group-a --zone us-central1-a --limit 1
        """)
    request = (
        self.messages.ComputeInstanceGroupManagersListPerInstanceConfigsRequest(
            instanceGroupManager='group-a',
            project='my-project',
            zone='us-central1-a'))
    self.CheckRequests([(self.compute.instanceGroupManagers,
                         'ListPerInstanceConfigs', request)])

    self.AssertOutputContains("""\
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0001
        """.format(compute_uri=self.compute_uri), normalize_space=True)
    self.AssertOutputNotContains("""\
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0002
        """.format(compute_uri=self.compute_uri), normalize_space=True)
    self.AssertOutputNotContains("""\
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/custom-inst-0003
        """.format(compute_uri=self.compute_uri), normalize_space=True)

  def testListInstanceConfigsUriOutput(self):
    self.Run("""
        compute instance-groups managed instance-configs list
        group-a --zone us-central1-a --uri
        """)
    request = (
        self.messages.ComputeInstanceGroupManagersListPerInstanceConfigsRequest(
            instanceGroupManager='group-a',
            project='my-project',
            zone='us-central1-a'))
    self.CheckRequests([(self.compute.instanceGroupManagers,
                         'ListPerInstanceConfigs', request)])

    self.AssertOutputEquals("""\
        {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0001
        {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0002
        {compute_uri}/projects/my-project/zones/us-central1-a/instances/custom-inst-0003
        """.format(compute_uri=self.compute_uri), normalize_space=True)

  def testListInstanceConfigsSortedOutput(self):
    self.Run("""
        compute instance-groups managed instance-configs list
        group-a --zone us-central1-a --sort-by ~instance
        """)
    request = (
        self.messages.ComputeInstanceGroupManagersListPerInstanceConfigsRequest(
            instanceGroupManager='group-a',
            project='my-project',
            zone='us-central1-a'))
    self.CheckRequests([(self.compute.instanceGroupManagers,
                         'ListPerInstanceConfigs', request)])

    self.AssertOutputMatches("""\
        .*
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0002
        .*
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0001
        .*
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/custom-inst-0003
        .*
        """.format(compute_uri=self.compute_uri), normalize_space=True)

  def testListInstanceConfigsWithFilter(self):
    self.Run("""
        compute instance-groups managed instance-configs list
        group-a --zone us-central1-a --filter "override.origin = USER_PROVIDED"
        """)
    request = (
        self.messages.ComputeInstanceGroupManagersListPerInstanceConfigsRequest(
            instanceGroupManager='group-a',
            project='my-project',
            zone='us-central1-a'))
    self.CheckRequests([(self.compute.instanceGroupManagers,
                         'ListPerInstanceConfigs', request)])

    self.AssertOutputMatches("""\
        ---
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/custom-inst-0003
        .*
        origin: USER_PROVIDED
        """.format(compute_uri=self.compute_uri), normalize_space=True)
    self.AssertOutputNotContains('origin: AUTO_GENERATED', normalize_space=True)

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run("""
        compute instance-groups managed instance-configs list group-a
        --zone us-central1-a
        """)


class InstanceGroupsManagedInstancesConfigsListRegionalTest(
    InstanceGroupsManagedInstancesConfigsListTestBase):

  def SetUp(self):
    super(InstanceGroupsManagedInstancesConfigsListRegionalTest, self).SetUp()
    self.make_requests.side_effect = iter([
        [
            self.messages.InstanceGroupManagersListPerInstanceConfigsResp(
                items=self._MakeInstanceConfigsInManagedInstanceGroupRegional(),
            )
        ],
    ])

  def _MakeInstanceConfigsInManagedInstanceGroupRegional(self):
    prefix = '{0}/projects/my-project/'.format(self.compute_uri)
    return [
        self.MakePerInstanceConfig(
            prefix + 'zones/us-central1-a/instances/inst-0001', [
                {
                    'device_name': 'my-disk-1',
                    'source': prefix + 'zones/us-central1-a/disks/inst-0001-1',
                    'mode': 'READ_WRITE'
                },
                {
                    'device_name': 'my-disk-2',
                    'source': prefix + 'zones/us-central1-a/disks/inst-0001-2',
                    'mode': 'READ_ONLY'
                },
            ], [
                {
                    'key': 'key-BAR',
                    'value': 'value BAR'
                },
                {
                    'key': 'key-foo',
                    'value': 'value foo'
                },
            ], 'AUTO_GENERATED'),
        self.MakePerInstanceConfig(
            prefix + 'zones/us-central1-b/instances/inst-0002', [
                {
                    'device_name': 'my-disk-1',
                    'source': prefix + 'zones/us-central1-b/disks/inst-0002-1',
                    'mode': 'READ_WRITE'
                },
                {
                    'device_name': 'my-disk-2',
                    'source': prefix + 'zones/us-central1-b/disks/inst-0002-2',
                    'mode': 'READ_ONLY'
                },
            ], [], 'AUTO_GENERATED'),
        self.MakePerInstanceConfig(
            prefix + 'zones/us-central1-b/instances/custom-inst-0003', [
                {
                    'device_name':
                        'my-custom-disk-1',
                    'source':
                        prefix + 'zones/us-central1-b/disks/custom-disk-1',
                    'mode':
                        'READ_ONLY'
                },
            ], [], 'USER_PROVIDED'),
    ]

  def testListInstanceConfigs(self):
    self.Run("""
        compute instance-groups managed instance-configs list
        group-a --region us-central1
        """)
    request = (
        self.messages.
        ComputeRegionInstanceGroupManagersListPerInstanceConfigsRequest(
            instanceGroupManager='group-a',
            project='my-project',
            region='us-central1'))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers,
                         'ListPerInstanceConfigs', request)])

    self.AssertOutputMatches("""\
        ---
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0001
        name: inst-0001
        override:
          disks:
          - deviceName: my-disk-1
            mode: READ_WRITE
            source: {compute_uri}/projects/my-project/zones/us-central1-a/disks/inst-0001-1
          - deviceName: my-disk-2
            mode: READ_ONLY
            source: {compute_uri}/projects/my-project/zones/us-central1-a/disks/inst-0001-2
          metadata:
          - key: key-BAR
            value: value BAR
          - key: key-foo
            value: value foo
          origin: AUTO_GENERATED
        preservedState:
          disks:
            my-disk-1:
              autoDelete: NEVER
              mode: READ_WRITE
              source: https://www.googleapis.com/compute/alpha/projects/my-project/zones/us-central1-a/disks/inst-0001-1
            my-disk-2:
              autoDelete: NEVER
              mode: READ_ONLY
              source: https://www.googleapis.com/compute/alpha/projects/my-project/zones/us-central1-a/disks/inst-0001-2
          metadata:
            key-BAR: value BAR
            key-foo: value foo
        .*
        instance: {compute_uri}/projects/my-project/zones/us-central1-b/instances/inst-0002
        .*
        instance: {compute_uri}/projects/my-project/zones/us-central1-b/instances/custom-inst-0003
        .*
        """.format(compute_uri=self.compute_uri), normalize_space=True)

  def testListInstanceConfigsWithLimit(self):
    self.Run("""
        compute instance-groups managed instance-configs list
        group-a --region us-central1 --limit 1
        """)
    request = (
        self.messages.
        ComputeRegionInstanceGroupManagersListPerInstanceConfigsRequest(
            instanceGroupManager='group-a',
            project='my-project',
            region='us-central1'))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers,
                         'ListPerInstanceConfigs', request)])

    self.AssertOutputContains("""\
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0001
        name: inst-0001
        """.format(compute_uri=self.compute_uri), normalize_space=True)
    self.AssertOutputNotContains("""\
        instance: {compute_uri}/projects/my-project/zones/us-central1-b/instances/inst-0002
        """.format(compute_uri=self.compute_uri), normalize_space=True)
    self.AssertOutputNotContains("""\
        instance: {compute_uri}/projects/my-project/zones/us-central1-b/instances/custom-inst-0003
        """.format(compute_uri=self.compute_uri), normalize_space=True)

  def testListInstanceConfigsUriOutput(self):
    self.Run("""
        compute instance-groups managed instance-configs list
        group-a --region us-central1 --uri
        """)
    request = (
        self.messages.
        ComputeRegionInstanceGroupManagersListPerInstanceConfigsRequest(
            instanceGroupManager='group-a',
            project='my-project',
            region='us-central1'))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers,
                         'ListPerInstanceConfigs', request)])

    self.AssertOutputEquals("""\
        {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0001
        {compute_uri}/projects/my-project/zones/us-central1-b/instances/inst-0002
        {compute_uri}/projects/my-project/zones/us-central1-b/instances/custom-inst-0003
        """.format(compute_uri=self.compute_uri), normalize_space=True)

  def testListInstanceConfigsSortedOutput(self):
    self.Run("""
        compute instance-groups managed instance-configs list
        group-a --region us-central1 --sort-by ~instance
        """)
    request = (
        self.messages.
        ComputeRegionInstanceGroupManagersListPerInstanceConfigsRequest(
            instanceGroupManager='group-a',
            project='my-project',
            region='us-central1'))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers,
                         'ListPerInstanceConfigs', request)])

    self.AssertOutputMatches("""\
        .*
        instance: {compute_uri}/projects/my-project/zones/us-central1-b/instances/inst-0002
        .*
        instance: {compute_uri}/projects/my-project/zones/us-central1-b/instances/custom-inst-0003
        .*
        instance: {compute_uri}/projects/my-project/zones/us-central1-a/instances/inst-0001
        .*
        """.format(compute_uri=self.compute_uri), normalize_space=True)

  def testListInstanceConfigsWithFilter(self):
    self.Run("""
        compute instance-groups managed instance-configs list
        group-a --region us-central1 --filter "override.origin = USER_PROVIDED"
        """)
    request = (
        self.messages.
        ComputeRegionInstanceGroupManagersListPerInstanceConfigsRequest(
            instanceGroupManager='group-a',
            project='my-project',
            region='us-central1'))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers,
                         'ListPerInstanceConfigs', request)])

    self.AssertOutputMatches("""\
        ---
        instance: {compute_uri}/projects/my-project/zones/us-central1-b/instances/custom-inst-0003
        .*
        origin: USER_PROVIDED
        """.format(compute_uri=self.compute_uri), normalize_space=True)
    self.AssertOutputNotContains('origin: AUTO_GENERATED', normalize_space=True)


if __name__ == '__main__':
  test_case.main()
