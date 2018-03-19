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
"""Tests for the security policy rules describe subcommand."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import textwrap

from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class SecurityPoliciyRulesDescribeTestBeta(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.MakeSecurityPolicyRule(self.messages)],
    ])
    self.Run("""
        compute security-policies rules describe 1000
        --security-policy my-policy
        """)

    self.CheckRequests([
        (self.compute.securityPolicies, 'GetRule',
         self.messages.ComputeSecurityPoliciesGetRuleRequest(
             project='my-project', priority=1000, securityPolicy='my-policy'))
    ],)
    self.assertMultiLineEqual(
        textwrap.dedent("""\
            ---
            action: allow
            description: my rule
            match:
              config:
                srcIpRanges:
                - 1.1.1.1
              versionedExpr: SRC_IPS_V1
            preview: false
            priority: 1000
            """), self.GetOutput())
    self.AssertErrEquals('')


class SecurityPoliciyRulesDescribeTestAlpha(
    SecurityPoliciyRulesDescribeTestBeta):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)


if __name__ == '__main__':
  test_case.main()