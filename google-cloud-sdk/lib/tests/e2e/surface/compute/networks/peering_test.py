# -*- coding: utf-8 -*- #
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
"""Integration tests for manipulating network peerings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base
from six.moves import range  # pylint: disable=redefined-builtin
from six.moves import zip  # pylint: disable=redefined-builtin


class NetworkPeeringTestBase(e2e_test_base.BaseTest):

  SUBNET_RANGES = ['10.1.0.0/16', '10.2.0.0/16']

  def SetUpCommon(self, track):
    self.track = track
    self.network_names = []
    self.subnetwork_names = []
    self.peering_names = []

    for _ in range(2):
      # Prefix limited in size to avoid conflict in firewall names based on
      # first 43 characters of network names.
      self.network_names.append(
          next(
              e2e_utils.GetResourceNameGenerator(prefix='compute-peering-net')))
      self.subnetwork_names.append(
          next(
              e2e_utils.GetResourceNameGenerator(prefix='compute-peering-sub')))
      self.peering_names.append(
          next(
              e2e_utils.GetResourceNameGenerator(
                  prefix='compute-peering-peer')))

    # Create two networks with non-overlapping custom subnets
    for (network_name, subnetwork_name, subnet_range) in zip(
        self.network_names, self.subnetwork_names, self.SUBNET_RANGES):
      self.Run('compute networks create {0} --subnet-mode custom'.format(
          network_name))
      self.AssertNewOutputContains(network_name)
      self.Run('compute networks subnets create {0} --network {1} '
               '--region {2} --range {3}'.format(subnetwork_name, network_name,
                                                 self.region, subnet_range))
      self.AssertNewOutputContains(subnetwork_name)

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for subnetwork_name in self.subnetwork_names:
      self.CleanUpResource(
          subnetwork_name, 'networks subnets', scope=e2e_test_base.REGIONAL)
    for network_name in self.network_names:
      self.CleanUpResource(network_name, 'networks', scope=e2e_test_base.GLOBAL)


class NetworkPeeringTestGa(NetworkPeeringTestBase):

  def SetUp(self):
    self.SetUpCommon(calliope_base.ReleaseTrack.GA)

  def testNetworkPeering(self):
    # Create a peering in network 0 to network 1
    self.Run('compute networks peerings create {0} --network {1} '
             '--peer-network {2} --auto-create-routes'.format(
                 self.peering_names[0], self.network_names[0],
                 self.network_names[1]))
    # Peering is inactive
    self.AssertNewOutputContains('state: INACTIVE')

    # Create a matching peering in network 1 to 0.
    self.Run('compute networks peerings create {0} --network {1} '
             '--peer-network {2} --auto-create-routes'.format(
                 self.peering_names[1], self.network_names[1],
                 self.network_names[0]))
    # Peering is now active
    self.AssertNewOutputContains('state: ACTIVE')

    # Delete the first peering created.
    self.Run('compute networks peerings delete {0} --network {1}'.format(
        self.peering_names[0], self.network_names[0]))

    # List peering in second peering to check that it is now inactive.
    self.Run('compute networks peerings list --network {0}'.format(
        self.network_names[1]))
    self.AssertNewOutputContains('INACTIVE')

    self.Run('compute networks peerings delete {0} --network {1}'.format(
        self.peering_names[1], self.network_names[1]))

    for subnetwork_name in self.subnetwork_names:
      self.Run('compute networks subnets delete {0} --region {1}'.format(
          subnetwork_name, self.region))

    for network_name in self.network_names:
      self.Run('compute networks delete {0}'.format(network_name))


class NetworkPeeringTestAlpha(NetworkPeeringTestBase):

  def SetUp(self):
    self.SetUpCommon(calliope_base.ReleaseTrack.ALPHA)

  def testPeeringWithRoutePolicy(self):
    # Create a peering in network 0 to network 1 which imports routes.
    self.Run('compute networks peerings create {0} --network {1} '
             '--peer-network {2} --auto-create-routes '
             '--no-export-custom-routes --import-custom-routes'.format(
                 self.peering_names[0], self.network_names[0],
                 self.network_names[1]))
    # Create a matching peering in network 1 to 0 which exports routes.
    self.Run('compute networks peerings create {0} --network {1} '
             '--peer-network {2} --auto-create-routes '
             '--export-custom-routes --no-import-custom-routes'.format(
                 self.peering_names[1], self.network_names[1],
                 self.network_names[0]))
    # Verify route policies.
    self.Run('compute networks describe {0}'.format(self.network_names[0]))
    self.AssertNewOutputContainsAll('state: ACTIVE',
                                    'exportCustomRoutes: false',
                                    'importCustomRoutes: true')
    self.Run('compute networks describe {0}'.format(self.network_names[1]))
    self.AssertNewOutputContainsAll('state: ACTIVE', 'exportCustomRoutes: true',
                                    'importCustomRoutes: false')
    # Update the peering in network 0.
    self.Run('compute networks peerings update {0} --network {1} '
             '--export-custom-routes --no-import-custom-routes'.format(
                 self.peering_names[0], self.network_names[0]))
    self.Run('compute networks peerings update {0} --network {1} '
             '--no-export-custom-routes --import-custom-routes'.format(
                 self.peering_names[1], self.network_names[1]))
    # Verify route policies.
    self.Run('compute networks describe {0}'.format(self.network_names[0]))
    self.AssertNewOutputContainsAll('state: ACTIVE', 'exportCustomRoutes: true',
                                    'importCustomRoutes: false')
    self.Run('compute networks describe {0}'.format(self.network_names[1]))
    self.AssertNewOutputContainsAll('state: ACTIVE',
                                    'exportCustomRoutes: false',
                                    'importCustomRoutes: true')


if __name__ == '__main__':
  e2e_test_base.main()
