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
"""Test of the 'pubsub subscriptions get-iam-policy' command."""
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class SubscriptionsGetIamPolicyTest(base.CloudPubsubTestBase):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.GetIamPolicy

  def testGetIamPolicy(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    self.svc.Expect(
        self.msgs.PubsubProjectsSubscriptionsGetIamPolicyRequest(
            resource=sub_ref.RelativeName()),
        self.policy)

    result = self.Run(
        'pubsub subscriptions get-iam-policy subs1')

    self.assertEqual(result, self.policy)

  def testGetIamPolicy_Filter(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    self.svc.Expect(
        self.msgs.PubsubProjectsSubscriptionsGetIamPolicyRequest(
            resource=sub_ref.RelativeName()),
        self.policy)

    self.Run(
        'pubsub subscriptions get-iam-policy subs1 '
        '--flatten=bindings[].members '
        '--filter=bindings.role:roles/owner '
        '--format=value(bindings.members)')

    self.AssertOutputEquals('user:test-user@gmail.com\n')


if __name__ == '__main__':
  test_case.main()