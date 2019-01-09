# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests that exercise IAM-related `binauthz attestors` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class AttestorsGetIamTest(base.BinauthzMockedBetaPolicyClientUnitTest):

  def SetUp(self):
    self.proj = self.Project()
    self.name = 'my_attestor'
    self.resource = 'projects/{}/attestors/{}'.format(
        self.proj, self.name)

  def testGet(self):
    self.client.projects_policy.GetIamPolicy.Expect(
        self.messages.
        BinaryauthorizationProjectsPolicyGetIamPolicyRequest(
            resource=self.resource),
        self.messages.IamPolicy(etag=b'foo'))

    self.RunBinauthz('attestors get-iam-policy {}'.format(self.name))
    self.AssertOutputContains('etag: Zm9v')  # "foo" in b64

  def testListCommandFilter(self):
    self.client.projects_policy.GetIamPolicy.Expect(
        self.messages.BinaryauthorizationProjectsPolicyGetIamPolicyRequest(
            resource=self.resource),
        self.messages.IamPolicy(etag=b'foo'))

    self.RunBinauthz(
        'attestors get-iam-policy {} '
        '    --filter=etag:Zm9v'
        '    --format=table[no-heading](etag:sort=1)'.format(self.name))
    self.AssertOutputEquals('Zm9v\n')


class AttestorsModifyIamTest(sdk_test_base.WithTempCWD,
                             base.BinauthzMockedBetaPolicyClientUnitTest):

  def SetUp(self):
    self.proj = self.Project()
    self.name = 'my_attestor'
    self.resource = 'projects/{}/attestors/{}'.format(
        self.proj, self.name)

  def testSetBindings(self):
    policy = self.messages.IamPolicy(
        etag=b'foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ])
    policy_filename = self.Touch(
        name='foo.json',
        directory=self.cwd_path,
        contents=textwrap.dedent("""
        {
          "etag": "Zm9v",
          "bindings": [ { "members": ["people"], "role": "roles/owner" } ]
        }
        """))

    self.client.projects_policy.SetIamPolicy.Expect(
        self.messages.BinaryauthorizationProjectsPolicySetIamPolicyRequest(
            resource=self.resource,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy)),
        response=policy)

    self.RunBinauthz(
        'attestors set-iam-policy {} {}'.format(self.name, policy_filename))
    self.AssertOutputContains(textwrap.dedent("""
        bindings:
        - members:
          - people
          role: roles/owner
        etag: Zm9v
    """).lstrip())
    self.AssertErrContains('Updated IAM policy for attestor [my_attestor].')


if __name__ == '__main__':
  test_case.main()