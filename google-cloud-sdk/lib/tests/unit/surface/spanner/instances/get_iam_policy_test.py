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
"""Tests for Spanner instances get-iam-policy command."""

from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class GetIamPolicyTest(base.SpannerTestBase):

  def SetUp(self):
    self.instance_ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')

  def testGetIamPolicy(self):
    test_iam_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role=u'roles/spanner.databaseAdmin',
                members=[u'domain:foo.com']), self.msgs.Binding(
                    role=u'roles/spanner.viewer',
                    members=[u'user:admin@foo.com'])
        ],
        etag='someUniqueEtag',
        version=1)
    self.client.projects_instances.GetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesGetIamPolicyRequest(
            resource=self.instance_ref.RelativeName()),
        response=test_iam_policy)
    get_policy_request = self.Run(
        'spanner instances get-iam-policy insId')
    self.assertEqual(get_policy_request, test_iam_policy)

  def testListCommandFilter(self):
    test_iam_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role=u'roles/spanner.databaseAdmin',
                members=[u'domain:foo.com']), self.msgs.Binding(
                    role=u'roles/spanner.viewer',
                    members=[u'user:admin@foo.com'])
        ],
        etag='someUniqueEtag',
        version=1)
    self.client.projects_instances.GetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesGetIamPolicyRequest(
            resource=self.instance_ref.RelativeName()),
        response=test_iam_policy)
    self.Run("""
        spanner instances get-iam-policy insId
        --flatten=bindings[].members
        --filter=bindings.role:roles/spanner.viewer
        --format=table[no-heading](bindings.members:sort=1)
        """)
    self.AssertOutputEquals('user:admin@foo.com\n')