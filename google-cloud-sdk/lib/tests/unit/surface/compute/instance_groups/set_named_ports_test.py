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
"""Tests for the instance-groups get-named-ports subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InstanceGroupsSetNamedPortsCommonTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.make_requests.side_effect = iter([
        iter([self.messages.InstanceGroup(name='group-1', fingerprint=b'123')]),
        []
    ])

  def testSetSinglePortForGroup(self):
    self.Run("""
        compute instance-groups set-named-ports group-1
          --named-ports serv-1:1111
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Get',
          self.messages.ComputeInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='central2-a'))],
        [(self.compute.instanceGroups,
          'SetNamedPorts',
          self.messages.ComputeInstanceGroupsSetNamedPortsRequest(
              instanceGroup='group-1',
              instanceGroupsSetNamedPortsRequest=(
                  self.messages.InstanceGroupsSetNamedPortsRequest(
                      fingerprint=b'123',
                      namedPorts=[
                          self.messages.NamedPort(name='serv-1', port=1111)])),
              project='my-project',
              zone='central2-a'))],
    )

  def testSetMultiplePortsForGroup(self):
    self.Run("""
        compute instance-groups set-named-ports group-1
          --named-ports serv-1:1111,serv-2:2222,serv-3:3333
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Get',
          self.messages.ComputeInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='central2-a'))],
        [(self.compute.instanceGroups,
          'SetNamedPorts',
          self.messages.ComputeInstanceGroupsSetNamedPortsRequest(
              instanceGroup='group-1',
              instanceGroupsSetNamedPortsRequest=(
                  self.messages.InstanceGroupsSetNamedPortsRequest(
                      fingerprint=b'123',
                      namedPorts=[
                          self.messages.NamedPort(name='serv-1', port=1111),
                          self.messages.NamedPort(name='serv-2', port=2222),
                          self.messages.NamedPort(name='serv-3', port=3333)])),
              project='my-project',
              zone='central2-a'))],
    )

  def testClearPortsForGroup(self):
    self.Run("""
        compute instance-groups set-named-ports group-1
          --named-ports ''
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Get',
          self.messages.ComputeInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='central2-a'))],
        [(self.compute.instanceGroups,
          'SetNamedPorts',
          self.messages.ComputeInstanceGroupsSetNamedPortsRequest(
              instanceGroup='group-1',
              instanceGroupsSetNamedPortsRequest=(
                  self.messages.InstanceGroupsSetNamedPortsRequest(
                      fingerprint=b'123',
                      namedPorts=[])),
              project='my-project',
              zone='central2-a'))],
    )

  def testSetPortsbyUri(self):
    self.Run("""
        compute instance-groups set-named-ports
          {0}/projects/my-project/zones/central2-a/instanceGroups/group-1
          --named-ports serv-1:1111
          --zone central2-a
        """.format(self.compute_uri))

    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Get',
          self.messages.ComputeInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='central2-a'))],
        [(self.compute.instanceGroups,
          'SetNamedPorts',
          self.messages.ComputeInstanceGroupsSetNamedPortsRequest(
              instanceGroup='group-1',
              instanceGroupsSetNamedPortsRequest=(
                  self.messages.InstanceGroupsSetNamedPortsRequest(
                      fingerprint=b'123',
                      namedPorts=[
                          self.messages.NamedPort(name='serv-1', port=1111)])),
              project='my-project',
              zone='central2-a'))],
    )

  def testSetPortsWithMultiscopePrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='central1'),
            self.messages.Region(name='central2'),
        ],
        [
            self.messages.Zone(name='central1-a'),
            self.messages.Zone(name='central1-b'),
            self.messages.Zone(name='central2-a'),
        ],
        iter([self.messages.InstanceGroup(name='group-1', fingerprint=b'123')]),
        []
    ])
    self.WriteInput('2\n')
    self.Run("""
        compute instance-groups set-named-ports group-1
          --named-ports serv-1:1111
        """)

    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.regionInstanceGroups,
          'Get',
          self.messages.ComputeRegionInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              region='central2'))],
        [(self.compute.regionInstanceGroups,
          'SetNamedPorts',
          self.messages.ComputeRegionInstanceGroupsSetNamedPortsRequest(
              instanceGroup='group-1',
              regionInstanceGroupsSetNamedPortsRequest=(
                  self.messages.RegionInstanceGroupsSetNamedPortsRequest(
                      fingerprint=b'123',
                      namedPorts=[
                          self.messages.NamedPort(name='serv-1', port=1111)])),
              project='my-project',
              region='central2'))],
    )


if __name__ == '__main__':
  test_case.main()
