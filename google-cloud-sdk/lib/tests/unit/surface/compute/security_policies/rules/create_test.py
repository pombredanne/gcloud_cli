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
"""Tests for the security policy rules create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class SecurityPolicyRulesCreateTest(test_base.BaseTest, parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')
    self.my_policy_ref = self.resources.Create(
        'compute.securityPolicies',
        securityPolicy='my-policy',
        project='my-project')

  def CheckSecurityPolicyRuleRequest(self, rule):
    self.CheckRequests([(self.compute.securityPolicies, 'AddRule',
                         self.messages.ComputeSecurityPoliciesAddRuleRequest(
                             project='my-project',
                             securityPolicyRule=rule,
                             securityPolicy='my-policy'))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testWithSrcIpRange(self):
    messages = self.messages
    expected_rule = messages.SecurityPolicyRule(
        description='my rule',
        priority=1000,
        match=messages.SecurityPolicyRuleMatcher(
            versionedExpr=messages.SecurityPolicyRuleMatcher
            .VersionedExprValueValuesEnum('SRC_IPS_V1'),
            config=messages.SecurityPolicyRuleMatcherConfig(
                srcIpRanges=['1.1.1.1'])),
        action='allow',
        preview=True)

    self.Run("""
        compute security-policies rules create 1000
        --security-policy my-policy
        --description "my rule"
        --src-ip-ranges 1.1.1.1
        --action allow
        --preview
        """)
    self.CheckSecurityPolicyRuleRequest(expected_rule)

  @parameterized.named_parameters(('Allow', 'allow', 'allow'),
                                  ('Deny-403', 'deny-403', 'deny(403)'),
                                  ('Deny-404', 'deny-404', 'deny(404)'),
                                  ('Deny-502', 'deny-502', 'deny(502)'))
  def testValidActions(self, action, expected_action):
    messages = self.messages
    expected_rule = messages.SecurityPolicyRule(
        description='my rule',
        priority=1000,
        match=messages.SecurityPolicyRuleMatcher(
            versionedExpr=messages.SecurityPolicyRuleMatcher
            .VersionedExprValueValuesEnum('SRC_IPS_V1'),
            config=messages.SecurityPolicyRuleMatcherConfig(
                srcIpRanges=['1.1.1.1'])),
        action=expected_action,
        preview=False)

    self.Run("""
        compute security-policies rules create 1000
        --security-policy my-policy
        --description "my rule"
        --src-ip-ranges 1.1.1.1
        --action {0}
        --no-preview
        """.format(action))
    self.CheckSecurityPolicyRuleRequest(expected_rule)

  def testUriSupport(self):
    rule = self.resources.Create(
        'compute.securityPolicyRules',
        securityPolicy='my-policy',
        securityPolicyRule='1000',
        project='my-project')
    messages = self.messages
    expected_rule = messages.SecurityPolicyRule(
        description='my rule',
        priority=1000,
        match=messages.SecurityPolicyRuleMatcher(
            versionedExpr=messages.SecurityPolicyRuleMatcher
            .VersionedExprValueValuesEnum('SRC_IPS_V1'),
            config=messages.SecurityPolicyRuleMatcherConfig(
                srcIpRanges=['1.1.1.1'])),
        action='allow',
        preview=False)

    self.Run("""
        compute security-policies rules create {0}
        --description "my rule"
        --src-ip-ranges 1.1.1.1
        --action allow
        --no-preview
        """.format(rule.SelfLink()))
    self.CheckSecurityPolicyRuleRequest(expected_rule)

  @parameterized.named_parameters(('NonInt', 'invalid'),
                                  ('NegativeInt', '-1000'))
  def testInvalidPriority(self, invalid_priority):
    with self.AssertRaisesToolExceptionRegexp(
        '^Invalid value for \\[priority\\]: priority must be a valid'
        ' non-negative integer.'):
      self.Run("""
        compute security-policies rules create {0}
        --security-policy my-policy
        --description "my rule"
        --src-ip-ranges 1.1.1.1
        --action allow
        """.format(invalid_priority))


class SecurityPolicyRulesCreateTestBeta(SecurityPolicyRulesCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')
    self.my_policy_ref = self.resources.Create(
        'compute.securityPolicies',
        securityPolicy='my-policy',
        project='my-project')


class SecurityPolicyRulesCreateTestAlpha(SecurityPolicyRulesCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.my_policy_ref = self.resources.Create(
        'compute.securityPolicies',
        securityPolicy='my-policy',
        project='my-project')

  def testWithExpression(self):
    messages = self.messages
    expected_rule = messages.SecurityPolicyRule(
        description='my rule',
        priority=1000,
        match=messages.SecurityPolicyRuleMatcher(
            expr=messages.Expr(expression='origin.ip == 1.1.1.1')),
        action='allow',
        preview=True)

    self.Run("""
        compute security-policies rules create 1000
        --security-policy my-policy
        --description "my rule"
        --expression "origin.ip == 1.1.1.1"
        --action allow
        --preview
        """)
    self.CheckSecurityPolicyRuleRequest(expected_rule)


if __name__ == '__main__':
  test_case.main()
