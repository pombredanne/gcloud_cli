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

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.auth import exceptions as auth_exceptions
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class PrintAccessTokenTest(sdk_test_base.WithFakeAuth,
                           cli_test_base.CliTestBase):

  def testPrint(self):
    # pylint: disable=unused-argument, Has to match real signature.
    def FakeRefresh(cred, http=None):
      if cred:
        cred.access_token = 'FakeAccessToken'

    self.StartObjectPatch(store, 'Refresh', side_effect=FakeRefresh)
    self.Run('auth print-access-token')
    self.AssertOutputEquals('FakeAccessToken\n')

  def testBadCred(self):
    # pylint: disable=unused-argument, Has to match real signature.
    def FakeRefresh(cred, http=None):
      if cred:
        cred.access_token = None

    self.StartObjectPatch(store, 'Refresh', side_effect=FakeRefresh)
    with self.assertRaisesRegex(auth_exceptions.InvalidCredentialsError,
                                'No access token could be obtained'):
      self.Run('auth print-access-token')


if __name__ == '__main__':
  test_case.main()
