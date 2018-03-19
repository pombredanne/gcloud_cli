# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Tests for orgnaizations get-iam-policy."""

from tests.lib import test_case
from tests.lib.surface.organizations import testbase


class OrganizationsGetIamPolicyTest(testbase.OrganizationsUnitTestBase):

  def testGetIamPolicyOrganization(self):
    self.mock_client.organizations.GetIamPolicy.Expect(self.ExpectedRequest(),
                                                       self._GetTestIamPolicy())
    self.assertEqual(self.DoRequest(), self._GetTestIamPolicy())

  def testListCommandFilter(self):
    self.mock_client.organizations.GetIamPolicy.Expect(self.ExpectedRequest(),
                                                       self._GetTestIamPolicy())
    args = [
        '--flatten=bindings[].members',
        '--filter=bindings.role:roles/resourcemanager.organizationAdmin',
        '--format=value(bindings.members)',
    ]
    self.DoRequest(args)
    self.AssertOutputEquals('user:admin@foo.com\n')

  def testGetIamPolicyOrganization_raisesOrganizationsNotFoundError(self):
    self.SetupGetIamPolicyFailure(self.HTTP_404_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'Organization [BAD_ID] not found: Resource not found.'):
      self.DoRequest()

  def testGetIamPolicyOrganization_raisesOrganizationsAccessError(self):
    self.SetupGetIamPolicyFailure(self.HTTP_403_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'User [{}] does not have permission to access organization [SECRET_ID] '
        '(or it may not exist): Permission denied.'.format(
            self.FakeAuthAccount())):
      self.DoRequest()

  def ExpectedRequest(self):
    return self.messages.CloudresourcemanagerOrganizationsGetIamPolicyRequest(
        organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):],
        getIamPolicyRequest=self.messages.GetIamPolicyRequest())

  def SetupGetIamPolicyFailure(self, exception):
    self.mock_client.organizations.GetIamPolicy.Expect(self.ExpectedRequest(),
                                                       exception=exception)

  def DoRequest(self, args=None):
    command = [
        'get-iam-policy',
        self.TEST_ORGANIZATION.name[len('organizations/'):],
    ]
    if args:
      command += args
    return self.RunOrganizations(*command)


if __name__ == '__main__':
  test_case.main()