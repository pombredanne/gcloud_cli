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
"""Tests for the instances remove-iam-policy-binding subcommand."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


@parameterized.parameters(
    (calliope_base.ReleaseTrack.ALPHA, 'alpha'),
    (calliope_base.ReleaseTrack.BETA, 'beta'))
class RemoveIamPolicyBindingTest(test_base.BaseTest,
                                 test_case.WithOutputCapture,
                                 parameterized.TestCase):

  def _SetUp(self, track, api_version):
    self.SelectApi(api_version)
    self.track = track

  def testRemoveOwnerFromInstance(self, track, api_version):
    self._SetUp(track, api_version)
    self.make_requests.side_effect = iter([
        iter([test_resources.IamPolicyWithOneBinding(self.messages)]),
        iter([test_resources.EmptyIamPolicy(self.messages)]),
    ])

    self.Run("""
        compute instances remove-iam-policy-binding resource --zone zone-1
        --member user:testuser@google.com --role owner
        """)

    policy = test_resources.EmptyIamPolicy(self.messages)
    self.CheckRequests(
        [(self.compute.instances,
          'GetIamPolicy',
          self.messages.ComputeInstancesGetIamPolicyRequest(
              resource='resource',
              project='my-project',
              zone='zone-1')),],
        [(self.compute.instances,
          'SetIamPolicy',
          self.messages.ComputeInstancesSetIamPolicyRequest(
              resource='resource',
              project='my-project',
              zone='zone-1',
              zoneSetPolicyRequest=self.messages.ZoneSetPolicyRequest(
                  policy=policy))),
        ]
    )

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            etag: dGVzdA==
            """))


if __name__ == '__main__':
  test_case.main()
