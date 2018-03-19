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

"""Tests for organizations remove-iam-policy-binding."""

import copy

from tests.lib import test_case
from tests.lib.surface.organizations import testbase


class OrganizationsRemoveIamPolicyBindingTest(
    testbase.OrganizationsUnitTestBase):

  messages = testbase.OrganizationsUnitTestBase.messages

  REMOVE_USER = 'user:admin@foo.com'
  REMOVE_ROLE = 'roles/resourcemanager.organizationAdmin'
  START_POLICY = messages.Policy(bindings=[
      messages.Binding(role=u'roles/resourcemanager.projectCreator',
                       members=[u'domain:foo.com']), messages.Binding(
                           role=u'roles/resourcemanager.organizationAdmin',
                           members=[u'user:admin@foo.com'])
  ],
                                 etag='someUniqueEtag',
                                 version=1)
  NEW_POLICY = messages.Policy(bindings=[
      messages.Binding(role=u'roles/resourcemanager.projectCreator',
                       members=[u'domain:foo.com'])
  ],
                               etag='someUniqueEtag',
                               version=1)

  def testRemoveIamPolicyBinding(self):
    """Test the standard use case."""
    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(), copy.deepcopy(self.START_POLICY))
    self.mock_client.organizations.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
            organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):],
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=self.NEW_POLICY)),
        self.NEW_POLICY)

    self.assertEqual(self.DoRequest(), self.NEW_POLICY)

  def testRemoveIamPolicyBindingOrganization_raisesOrganizationsNotFoundError(
      self):
    self.SetupGetIamPolicyFailure(self.HTTP_404_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'Organization [BAD_ID] not found: Resource not found.'):
      self.DoRequest()

  def testRemoveIamPolicyBindingOrganization_raisesOrganizationsAccessError(
      self):
    self.SetupGetIamPolicyFailure(self.HTTP_403_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'User [{}] does not have permission to access organization [SECRET_ID] '
        '(or it may not exist): Permission denied.'.format(
            self.FakeAuthAccount())):
      self.DoRequest()

  def ExpectedGetRequest(self):
    return self.messages.CloudresourcemanagerOrganizationsGetIamPolicyRequest(
        organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):],
        getIamPolicyRequest=self.messages.GetIamPolicyRequest())

  def SetupGetIamPolicyFailure(self, exception):
    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(),
        exception=exception)

  def DoRequest(self):
    return self.RunOrganizations(
        'remove-iam-policy-binding',
        self.TEST_ORGANIZATION.name[len('organizations/'):],
        '--role={0}'.format(self.REMOVE_ROLE),
        '--member={0}'.format(self.REMOVE_USER))


if __name__ == '__main__':
  test_case.main()