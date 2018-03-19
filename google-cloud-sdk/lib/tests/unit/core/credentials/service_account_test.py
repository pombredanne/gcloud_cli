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

"""Tests for googlecloudsdk.core.credentials.service_account."""

import json
import os

from tests.lib import sdk_test_base
from tests.lib import test_case
from oauth2client.contrib import multistore_file


class StoreTests(sdk_test_base.SdkBase):

  def SetUp(self):
    self.maxDiff = None

  def _GetTestDataPathFor(self, filename):
    return self.Resource(
        'tests', 'unit', 'core', 'credentials', 'testdata', filename)

  def testLoads(self):
    # Credential store does not like symlinks.
    multistore_store_file = os.path.realpath(self._GetTestDataPathFor(
        'service_account_multistore_legacy.json'))
    all_keys = multistore_file.get_all_credential_keys(
        filename=multistore_store_file)
    key_dict = {
        'account': 'inactive@developer.gserviceaccount.com',
        'type': 'google-cloud-sdk',
    }
    self.assertEquals([key_dict], all_keys)

    storage = multistore_file.get_credential_storage_custom_key(
        filename=multistore_store_file,
        key_dict=key_dict)

    creds_from_old = storage.get()

    single_store_file = self._GetTestDataPathFor(
        'service_account_singlestore.json')

    # Check that now it serializes to new format.
    with open(single_store_file) as f:
      self.assertEquals(json.load(f),
                        json.loads(creds_from_old.to_json()))


if __name__ == '__main__':
  test_case.main()