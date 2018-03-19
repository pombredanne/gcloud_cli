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

from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class CreateTest(unit_test_base.BaseTest):

  def _SetUpCreateKeyExpectations(self, service_account):
    key_type = iam_util.KeyTypeFromString('json')

    self.client.projects_serviceAccounts_keys.Create.Expect(
        request=self.msgs.IamProjectsServiceAccountsKeysCreateRequest(
            name='projects/-/serviceAccounts/' + service_account,
            createServiceAccountKeyRequest=
            self.msgs.CreateServiceAccountKeyRequest(
                privateKeyType=iam_util.KeyTypeToCreateKeyType(key_type))),
        response=self.msgs.ServiceAccountKey(
            name=('projects/test-project/serviceAccounts/%s/keys/0'
                  % service_account),
            privateKeyType=key_type,
            privateKeyData='key data goes here'))

  def testCreateServiceAccountKey(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    self._SetUpCreateKeyExpectations(service_account)

    tmp_file = self.MockFileWrite('key data goes here')
    self.Run('iam service-accounts keys create --key-file-type json '
             '--iam-account {0} {1}'.format(service_account, tmp_file))

    self.AssertErrContains(
        ('created key [0] of type [json] as [{0}] for '
         '[test@test-project.iam.gserviceaccount.com]').format(tmp_file))

  def testCreateServiceAccountKeyInvalidAccount(self):
    with self.assertRaisesRegexp(
        cli_test_base.MockArgumentError,
        r'Not a valid service account identifier. It should be either a '
        r'numeric string representing the unique_id or an email of the form: '
        r'my-iam-account@somedomain.com or '
        r'my-iam-account@PROJECT_ID.iam.gserviceaccount.com'):
      self.Run('iam service-accounts keys create --key-file-type json '
               '--iam-account testfoo outfile')

  def testCreateServiceAccountKeyValidUniqueId(self):
    service_account = self.sample_unique_id
    self._SetUpCreateKeyExpectations(service_account)

    tmp_file = self.MockFileWrite('key data goes here')
    try:
      self.Run('iam service-accounts keys create --key-file-type json '
               '--iam-account {0} {1}'.format(service_account, tmp_file))
    except cli_test_base.MockArgumentError:
      self.fail('create should accept unique ids for service accounts.')

if __name__ == '__main__':
  test_case.main()