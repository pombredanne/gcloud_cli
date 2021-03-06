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
"""Tests for target VPN gateways update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import target_vpn_gateways_labels_test_base


class UpdateLabelsTestBeta(
    target_vpn_gateways_labels_test_base.TargetVpnGatewaysLabelsTestBase):

  def SetUp(self):
    super(target_vpn_gateways_labels_test_base.TargetVpnGatewaysLabelsTestBase,
          self).SetUp()
    self.target_vpn_gateway_ref = self._GetTargetVpnGatewayRef(
        'gw-1', region='us-central1')

  def testUpdateMissingNameOrLabels(self):
    with self.assertRaisesRegex(exceptions.RequiredArgumentException,
                                'At least one of --update-labels or '
                                '--remove-labels must be specified.'):
      self.Run('compute target-vpn-gateways update {0} --region {1}'.format(
          self.target_vpn_gateway_ref.Name(),
          self.target_vpn_gateway_ref.region))

  def testUpdateAndRemoveLabels(self):
    target_vpn_gateway_labels = (('key1', 'value1'), ('key2', 'value2'),
                                 ('key3', 'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (('key2', 'update2'), ('key3', 'value3'), ('key4',
                                                               'value4'))

    target_vpn_gateway = self._MakeTargetVpnGatewayProto(
        labels=target_vpn_gateway_labels, fingerprint=b'fingerprint-42')
    updated_target_vpn_gateway = self._MakeTargetVpnGatewayProto(
        labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1', 'us-central1')
    operation = self._MakeOperationMessage(operation_ref,
                                           self.target_vpn_gateway_ref)

    self._ExpectGetRequest(self.target_vpn_gateway_ref, target_vpn_gateway)
    self._ExpectLabelsSetRequest(self.target_vpn_gateway_ref, edited_labels,
                                 b'fingerprint-42', operation)
    self._ExpectOperationPollingRequest(operation_ref, operation)
    self._ExpectGetRequest(self.target_vpn_gateway_ref,
                           updated_target_vpn_gateway)

    response = self.Run(
        'compute target-vpn-gateways update {0} --update-labels {1} '
        '--remove-labels key1,key0'.format(
            self.target_vpn_gateway_ref.SelfLink(), ','.join(
                '{0}={1}'.format(pair[0], pair[1]) for pair in update_labels)))
    self.assertEqual(response, updated_target_vpn_gateway)

  def testUpdateClearLabels(self):
    target_vpn_gateway_labels = (('key1', 'value1'), ('key2', 'value2'),
                                 ('key3', 'value3'))
    edited_labels = ()

    target_vpn_gateway = self._MakeTargetVpnGatewayProto(
        labels=target_vpn_gateway_labels, fingerprint=b'fingerprint-42')
    updated_target_vpn_gateway = self._MakeTargetVpnGatewayProto(
        labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1', 'us-central1')
    operation = self._MakeOperationMessage(operation_ref,
                                           self.target_vpn_gateway_ref)

    self._ExpectGetRequest(self.target_vpn_gateway_ref, target_vpn_gateway)
    self._ExpectLabelsSetRequest(self.target_vpn_gateway_ref, edited_labels,
                                 b'fingerprint-42', operation)
    self._ExpectOperationPollingRequest(operation_ref, operation)
    self._ExpectGetRequest(self.target_vpn_gateway_ref,
                           updated_target_vpn_gateway)

    response = self.Run(
        'compute target-vpn-gateways update {0} --clear-labels'.format(
            self.target_vpn_gateway_ref.SelfLink()))
    self.assertEqual(response, updated_target_vpn_gateway)

  def testUpdateWithNoLabels(self):
    update_labels = (('key2', 'update2'), ('key4', 'value4'))

    target_vpn_gateway = self._MakeTargetVpnGatewayProto(
        labels=(), fingerprint=b'fingerprint-42')
    updated_target_vpn_gateway = self._MakeTargetVpnGatewayProto(
        labels=update_labels)
    operation_ref = self._GetOperationRef('operation-1', 'us-central1')
    operation = self._MakeOperationMessage(operation_ref,
                                           self.target_vpn_gateway_ref)

    self._ExpectGetRequest(self.target_vpn_gateway_ref, target_vpn_gateway)
    self._ExpectLabelsSetRequest(self.target_vpn_gateway_ref, update_labels,
                                 b'fingerprint-42', operation)
    self._ExpectOperationPollingRequest(operation_ref, operation)
    self._ExpectGetRequest(self.target_vpn_gateway_ref,
                           updated_target_vpn_gateway)

    response = self.Run(
        'compute target-vpn-gateways update {0} --update-labels {1} '.format(
            self.target_vpn_gateway_ref.SelfLink(), ','.join(
                '{0}={1}'.format(pair[0], pair[1]) for pair in update_labels)))
    self.assertEqual(response, updated_target_vpn_gateway)

  def testRemoveWithNoLabelsOnTargetVpnGateway(self):
    target_vpn_gateway = self._MakeTargetVpnGatewayProto(
        labels={}, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(self.target_vpn_gateway_ref, target_vpn_gateway)

    response = self.Run(
        'compute target-vpn-gateways update {0} --remove-labels DoesNotExist'
        .format(self.target_vpn_gateway_ref.SelfLink()))
    self.assertEqual(response, target_vpn_gateway)

  def testNoNetUpdate(self):
    target_vpn_gateway_labels = (('key1', 'value1'), ('key2', 'value2'),
                                 ('key3', 'value3'))
    update_labels = copy.deepcopy(target_vpn_gateway_labels)

    target_vpn_gateway = self._MakeTargetVpnGatewayProto(
        labels=target_vpn_gateway_labels, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(self.target_vpn_gateway_ref, target_vpn_gateway)

    response = self.Run(
        'compute target-vpn-gateways update {0} --update-labels {1} '
        '--remove-labels key4'.format(
            self.target_vpn_gateway_ref.SelfLink(), ','.join(
                '{0}={1}'.format(pair[0], pair[1]) for pair in update_labels)))
    self.assertEqual(response, target_vpn_gateway)

  def testScopePrompt(self):
    target_vpn_gateway = self._MakeTargetVpnGatewayProto(labels=[])
    self._ExpectGetRequest(self.target_vpn_gateway_ref, target_vpn_gateway)

    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.regions.service.List',
        return_value=[
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2')
        ],)
    self.WriteInput('1\n')
    self.Run('compute target-vpn-gateways update gw-1 --remove-labels key0')
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains('"choices": ["us-central1", "us-central2"]')


if __name__ == '__main__':
  test_case.main()
