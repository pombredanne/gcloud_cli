# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class SignBlobTest(unit_test_base.BaseTest):

  def testSignBlobServiceAccount(self):
    test_key = '1234'
    self.client.projects_serviceAccounts.SignBlob.Expect(
        request=self.msgs.IamProjectsServiceAccountsSignBlobRequest(
            name=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com'),
            signBlobRequest=self.msgs.SignBlobRequest(
                bytesToSign=b'blob to sign')),
        response=self.msgs.SignBlobResponse(keyId=test_key,
                                            signature=b'signed blob'))

    in_file = self.Touch(self.temp_path, contents=b'blob to sign')
    out_file = self.Touch(self.temp_path)
    self.Run('iam service-accounts sign-blob '
             '--iam-account test@test-project.iam.gserviceaccount.com '
             '{0} {1}'.format(in_file, out_file))

    self.AssertErrContains(('signed blob [{0}] as [{1}] for '
                            '[test@test-project.iam.gserviceaccount.com] '
                            'using key [{2}]').format(in_file, out_file,
                                                      test_key))
    self.AssertBinaryFileEquals(b'signed blob', out_file)

  def testMissingInputFile(self):
    with self.assertRaises(files.Error):
      self.Run('iam service-accounts sign-blob '
               '--iam-account=test@test-project.iam.gserviceaccount.com '
               '/file-does-not-exist /tmp/key')


if __name__ == '__main__':
  test_case.main()
