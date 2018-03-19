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
"""Tests for the instances detach-disk subcommand."""
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class InstancesDetachDiskTest(test_base.BaseTest):

  def SetUp(self):
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='my-instance',
            disks=[
                messages.AttachedDisk(
                    deviceName='device-1',
                    source=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-1')),
                messages.AttachedDisk(
                    deviceName='device-2',
                    source=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-2')),
            ])],

        [],
    ])

  def testWithDeviceThatExists(self):
    self.Run("""
        compute instances detach-disk my-instance
          --device-name device-2
          --zone us-central1-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'DetachDisk',
          messages.ComputeInstancesDetachDiskRequest(
              deviceName='device-2',
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],
    )

  def testWithDeviceThatDoesNotExist(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'No disk with device name \[device-3\] is attached to instance '
        r'\[my-instance\] in zone \[us-central1-a\].'):
      self.Run("""
          compute instances detach-disk my-instance
            --device-name device-3
            --zone us-central1-a
          """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],
    )

  def testWithDiskThatExists(self):
    self.Run("""
        compute instances detach-disk my-instance
          --disk disk-2
          --zone us-central1-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'DetachDisk',
          messages.ComputeInstancesDetachDiskRequest(
              deviceName='device-2',
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],
    )

  def testWithDiskThatDoesNotExist(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Disk \[disk-3\] is not attached to instance \[my-instance\] in zone '
        r'\[us-central1-a\].'):
      self.Run("""
          compute instances detach-disk my-instance
            --disk disk-3
            --zone us-central1-a
          """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],
    )

  def testUriSupport(self):
    self.Run("""
        compute instances detach-disk
          https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instances/my-instance
          --disk https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/disks/disk-2
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'DetachDisk',
          messages.ComputeInstancesDetachDiskRequest(
              deviceName='device-2',
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],
    )

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Instance(name='my-instance', zone='us-central1-a'),
            messages.Instance(name='my-instance', zone='us-central1-b'),
            messages.Instance(name='my-instance', zone='us-central2-a'),
        ],

        [messages.Instance(
            name='my-instance',
            disks=[
                messages.AttachedDisk(
                    deviceName='device-1',
                    source=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-1')),
                messages.AttachedDisk(
                    deviceName='device-2',
                    source=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-2')),
            ])],

        [],
    ])
    self.WriteInput('1\n')

    self.Run("""
        compute instances detach-disk my-instance
          --disk disk-2
        """)

    self.AssertErrContains('my-instance')
    self.AssertErrContains('us-central1-a')
    self.AssertErrContains('us-central1-b')
    self.AssertErrContains('us-central2-a')
    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('my-instance'),

        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'DetachDisk',
          messages.ComputeInstancesDetachDiskRequest(
              deviceName='device-2',
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],
    )

  def testModificationFailure(self):
    def MakeRequests(requests, *_, **kwargs):
      _, method, _ = requests[0]

      if method == 'Get':
        yield messages.Instance(
            name='my-instance',
            disks=[
                messages.AttachedDisk(
                    deviceName='device-1',
                    source=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-1')),
                messages.AttachedDisk(
                    deviceName='device-2',
                    source=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-2')),
            ])

      elif method == 'DetachDisk':
        kwargs['errors'].append((500, 'Server Error'))

      else:
        self.fail('Did not expect a call on method [{0}].'.format(method))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not fetch resource:
         - Server Error
        """)):
      self.Run("""
          compute instances detach-disk my-instance
            --device-name device-2
            --zone us-central1-a
          """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'DetachDisk',
          messages.ComputeInstancesDetachDiskRequest(
              deviceName='device-2',
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],
    )


if __name__ == '__main__':
  test_case.main()