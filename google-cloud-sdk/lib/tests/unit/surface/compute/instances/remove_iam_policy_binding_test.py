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


import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'alpha')


class RemoveIamPolicyBindingTest(test_base.BaseTest,
                                 test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testRemoveOwnerFromInstance(self):
    self.make_requests.side_effect = iter([
        iter([test_resources.AlphaIamPolicyWithOneBinding()]),
        iter([test_resources.EmptyAlphaIamPolicy()]),
    ])

    self.Run("""
        compute instances remove-iam-policy-binding resource --zone zone-1
        --member user:testuser@google.com --role owner
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'GetIamPolicy',
          messages.ComputeInstancesGetIamPolicyRequest(
              resource='resource',
              project='my-project',
              zone='zone-1')),],
        [(self.compute.instances,
          'SetIamPolicy',
          messages.ComputeInstancesSetIamPolicyRequest(
              resource='resource',
              project='my-project',
              zone='zone-1',
              policy=test_resources.EmptyAlphaIamPolicy())),
        ]
    )

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            etag: dGVzdA==
            """))


if __name__ == '__main__':
  test_case.main()