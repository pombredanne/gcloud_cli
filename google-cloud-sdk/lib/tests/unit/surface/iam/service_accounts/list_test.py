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
"""Tests that ensure deserialization of server responses work properly."""

from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class ListTest(unit_test_base.BaseTest):

  def testEmptyResponse(self):
    self.client.projects_serviceAccounts.List.Expect(
        request=self.msgs.IamProjectsServiceAccountsListRequest(
            name=u'projects/test-project',
            pageSize=100),
        response=self.msgs.ListServiceAccountsResponse(accounts=[]))

    self.Run('iam service-accounts list')

  def testPopulatedResponse(self):
    self.client.projects_serviceAccounts.List.Expect(
        request=self.msgs.IamProjectsServiceAccountsListRequest(
            name=u'projects/test-project',
            pageSize=100),
        response=self.msgs.ListServiceAccountsResponse(accounts=[
            self.msgs.ServiceAccount(
                displayName='Test Account',
                email='test@test-project.iam.gserviceaccount.com',
                uniqueId='000000001',
                projectId=self.Project()),
            self.msgs.ServiceAccount(
                displayName='Example Account',
                email='example@test-project.iam.gserviceaccount.com',
                uniqueId='000000002',
                projectId=self.Project()),
        ]))

    self.Run('iam service-accounts list')

    self.AssertOutputContains('Test Account')
    self.AssertOutputContains('test@test-project.iam.gserviceaccount.com')

    self.AssertOutputContains('Example Account')
    self.AssertOutputContains('example@test-project.iam.gserviceaccount.com')

  def testLimitedResponse(self):
    self.client.projects_serviceAccounts.List.Expect(
        request=self.msgs.IamProjectsServiceAccountsListRequest(
            name=u'projects/test-project',
            pageSize=1),
        response=self.msgs.ListServiceAccountsResponse(accounts=[
            self.msgs.ServiceAccount(
                displayName='Test Account',
                email='test@test-project.iam.gserviceaccount.com'),
            self.msgs.ServiceAccount(
                displayName='Example Account',
                email='example@test-project.iam.gserviceaccount.com'),
        ]))

    self.Run('iam service-accounts list --limit 1')

    self.AssertOutputContains('Test Account')
    self.AssertOutputContains('test@test-project.iam.gserviceaccount.com')

    self.AssertOutputNotContains('Example Account')
    self.AssertOutputNotContains('example@test-project.iam.gserviceaccount.com')

  def testFilteredResponse(self):
    self.client.projects_serviceAccounts.List.Expect(
        request=self.msgs.IamProjectsServiceAccountsListRequest(
            name=u'projects/test-project',
            pageSize=100),
        response=self.msgs.ListServiceAccountsResponse(accounts=[
            self.msgs.ServiceAccount(
                displayName='Test Account',
                email='test@test-project.iam.gserviceaccount.com'),
            self.msgs.ServiceAccount(
                displayName='Example Account',
                email='example@test-project.iam.gserviceaccount.com'),
        ]))

    self.Run('beta iam service-accounts list --filter=email:example@*')

    self.AssertOutputNotContains('Test Account')
    self.AssertOutputNotContains('test@test-project.iam.gserviceaccount.com')

    self.AssertOutputContains('Example Account')
    self.AssertOutputContains('example@test-project.iam.gserviceaccount.com')

  def testBadLength(self):
    with self.AssertRaisesArgumentError():
      self.Run('iam service-accounts list --limit 0')
    with self.AssertRaisesArgumentError():
      self.Run('iam service-accounts list --limit -1')


if __name__ == '__main__':
  test_case.main()