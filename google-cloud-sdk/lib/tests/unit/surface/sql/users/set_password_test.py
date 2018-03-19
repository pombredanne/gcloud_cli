# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests that exercise user password changes."""

import getpass

from googlecloudsdk.api_lib.util import apis
from tests.lib import test_case
from tests.lib.surface.sql import base


class UsersSetPasswordTest(base.SqlMockTestBeta):

  def testSetPassword(self):
    msgs = apis.GetMessagesModule('sqladmin', 'v1beta4')
    self.mocked_client.users.Update.Expect(
        msgs.SqlUsersUpdateRequest(
            project=self.Project(),
            instance='my_instance',
            name='my_username',
            host='my_host',
            user=msgs.User(
                project=self.Project(),
                instance='my_instance',
                name='my_username',
                host='my_host',
                password='my_password')),
        msgs.Operation(name='op_name'))
    self.mocked_client.operations.Get.Expect(
        msgs.SqlOperationsGetRequest(
            operation='op_name', project=self.Project()),
        msgs.Operation(name='op_name', status='DONE'))
    self.Run('sql users set-password --instance my_instance my_username '
             'my_host --password my_password')
    self.AssertErrContains('Updating Cloud SQL user')

  def testSetPasswordAsync(self):
    msgs = apis.GetMessagesModule('sqladmin', 'v1beta4')
    self.mocked_client.users.Update.Expect(
        msgs.SqlUsersUpdateRequest(
            project=self.Project(),
            instance='my_instance',
            name='my_username',
            host='my_host',
            user=msgs.User(
                project=self.Project(),
                instance='my_instance',
                name='my_username',
                host='my_host',
                password='my_password')),
        msgs.Operation(name='op_name'))
    self.mocked_client.operations.Get.Expect(
        msgs.SqlOperationsGetRequest(
            operation='op_name', project=self.Project()),
        msgs.Operation(name='op_name'))

    result = self.Run('sql users set-password --instance my_instance '
                      'my_username my_host --password my_password --async')
    self.assertEquals(result.name, 'op_name')
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testSetPasswordPrompt(self):
    self.StartObjectPatch(getpass, 'getpass', return_value='my_password')
    msgs = apis.GetMessagesModule('sqladmin', 'v1beta4')
    self.mocked_client.users.Update.Expect(
        msgs.SqlUsersUpdateRequest(
            project=self.Project(),
            instance='my_instance',
            name='my_username',
            host='my_host',
            user=msgs.User(
                project=self.Project(),
                instance='my_instance',
                name='my_username',
                host='my_host',
                password='my_password')),
        msgs.Operation(name='op_name'))
    self.mocked_client.operations.Get.Expect(
        msgs.SqlOperationsGetRequest(
            operation='op_name', project=self.Project()),
        msgs.Operation(name='op_name', status='DONE'))
    self.Run('sql users set-password --instance my_instance my_username '
             'my_host --prompt-for-password')
    self.AssertErrContains('Updating Cloud SQL user')


if __name__ == '__main__':
  test_case.main()