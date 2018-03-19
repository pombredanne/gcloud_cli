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
"""Tests for the network peering create command."""

from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class PeeringsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.mock_get_global_resources = self.StartObjectPatch(
        lister,
        'GetGlobalResources',
        autospec=True,
        return_value=test_resources.NETWORK_PEERINGS_V1)
    self.track = calliope_base.ReleaseTrack.GA

  def testCreatePeeringSameProject(self):
    self.Run('compute networks peerings create peering-1 --network '
             'network-1 --peer-network network-2 --auto-create-routes')

    self.CheckRequests(
        [(self.compute.networks, 'AddPeering',
          self.messages.ComputeNetworksAddPeeringRequest(
              network='network-1',
              networksAddPeeringRequest=self.messages.NetworksAddPeeringRequest(
                  autoCreateRoutes=True,
                  name='peering-1',
                  peerNetwork='projects/my-project/global/networks/network-2'),
              project='my-project'))],)

  def testCreatePeeringDifferentProject(self):
    self.Run('compute networks peerings create peering-1 --network '
             'network-1 --peer-project my-project-2 --peer-network '
             'network-2 --auto-create-routes')

    self.CheckRequests(
        [(self.compute.networks, 'AddPeering',
          self.messages.ComputeNetworksAddPeeringRequest(
              network='network-1',
              networksAddPeeringRequest=self.messages.NetworksAddPeeringRequest(
                  autoCreateRoutes=True,
                  name='peering-1',
                  peerNetwork='projects/my-project-2/global/networks/'
                  'network-2'),
              project='my-project'))],)

  def testCreatePeeringNoAutoCreateRoutes(self):
    self.Run('compute networks peerings create peering-1 --network '
             'network-1 --peer-project my-project-2 --peer-network '
             'network-2')

    self.CheckRequests(
        [(self.compute.networks, 'AddPeering',
          self.messages.ComputeNetworksAddPeeringRequest(
              network='network-1',
              networksAddPeeringRequest=self.messages.NetworksAddPeeringRequest(
                  autoCreateRoutes=False,
                  name='peering-1',
                  peerNetwork='projects/my-project-2/global/networks/'
                  'network-2'),
              project='my-project'))],)

  def testCreatePeeringNoArgumentsError(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument NAME --network --peer-network: Must be specified.'):
      self.Run('compute networks peerings create')

  def testCreatePeeringNoNetworkError(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --network: Must be specified.'):
      self.Run('compute networks peerings create peering-1 '
               '--peer-network network-2')

  def testCreatePeeringNoPeerNetworkError(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --peer-network: Must be specified.'):
      self.Run('compute networks peerings create peering-1 --network '
               'network-1')

if __name__ == '__main__':
  test_case.main()