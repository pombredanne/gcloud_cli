# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Tests that exercise the 'gcloud beta dns policies create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util_beta


class CreateTest(base.DnsMockBetaTest):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def testCreateWithOptionalArgs(self):
    test_networks = [
        util_beta.GetNetworkURI('default', self.Project()),
        util_beta.GetNetworkURI('network1', self.Project())
    ]
    test_nameservers = ['1.0.1.1', '1.0.1.2']
    expected_output = util_beta.GetPolicies(
        networks=test_networks,
        forwarding=True,
        logging=True,
        name_server_config=util_beta.GetAltNameServerConfig(
            target_servers=test_nameservers),
        num=1).pop()
    create_req = self.messages.DnsPoliciesCreateRequest(
        project=self.Project(), policy=expected_output)
    self.client.policies.Create.Expect(
        request=create_req, response=expected_output)
    actual_output = self.Run('dns policies create mypolicy0 --description '
                             '"My policy 0" --networks default,network1 '
                             '--alternative-name-servers 1.0.1.1,1.0.1.2 '
                             '--enable-inbound-forwarding '
                             '--enable-logging ')
    self.assertEqual(expected_output, actual_output)

  def testCreateWithBothAlternativeNameServers(self):
    test_networks = [
        util_beta.GetNetworkURI('default', self.Project()),
        util_beta.GetNetworkURI('network1', self.Project())
    ]
    test_nameservers = ['1.0.1.1', '1.0.1.2']
    private_nameservers = ['8.8.8.8']
    expected_output = util_beta.GetPolicies(
        networks=test_networks,
        forwarding=True,
        logging=True,
        name_server_config=util_beta.GetAltNameServerConfig(
            target_servers=test_nameservers,
            private_target_servers=private_nameservers),
        num=1).pop()
    create_req = self.messages.DnsPoliciesCreateRequest(
        project=self.Project(), policy=expected_output)
    self.client.policies.Create.Expect(
        request=create_req, response=expected_output)
    actual_output = self.Run('dns policies create mypolicy0 --description '
                             '"My policy 0" --networks default,network1 '
                             '--alternative-name-servers 1.0.1.1,1.0.1.2 '
                             '--private-alternative-name-servers 8.8.8.8 '
                             '--enable-inbound-forwarding '
                             '--enable-logging ')
    self.assertEqual(expected_output, actual_output)

  def testCreateWithOnlyPrivateAlternativeNameServers(self):
    test_networks = [
        util_beta.GetNetworkURI('default', self.Project()),
        util_beta.GetNetworkURI('network1', self.Project())
    ]
    private_nameservers = ['8.8.8.8']
    expected_output = util_beta.GetPolicies(
        networks=test_networks,
        forwarding=True,
        logging=True,
        name_server_config=util_beta.GetAltNameServerConfig(
            target_servers=[], private_target_servers=private_nameservers),
        num=1).pop()
    create_req = self.messages.DnsPoliciesCreateRequest(
        project=self.Project(), policy=expected_output)
    self.client.policies.Create.Expect(
        request=create_req, response=expected_output)
    actual_output = self.Run('dns policies create mypolicy0 --description '
                             '"My policy 0" --networks default,network1 '
                             '--private-alternative-name-servers 8.8.8.8 '
                             '--enable-inbound-forwarding '
                             '--enable-logging ')
    self.assertEqual(expected_output, actual_output)


if __name__ == '__main__':
  test_case.main()
