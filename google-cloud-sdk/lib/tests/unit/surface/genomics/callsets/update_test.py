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

"""Tests for genomics callsets update command."""

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class UpdateTest(base.GenomicsUnitTest):
  """Unit tests for genomics callsets update command."""

  def testCallsetsUpdate(self):
    self.mocked_client.callsets.Patch.Expect(
        request=
        self.messages.GenomicsCallsetsPatchRequest(
            callSet=self.messages.CallSet(
                id='1000',
                name='callset-name-new',
                # This is the dummy response inserted by update.py.
                # See b/22818510.
                variantSetIds=['123'],),
            callSetId='1000',),
        response=self.messages.CallSet(id='1000',
                                       name='callset-name-new',))
    self.RunGenomics(['callsets', 'update', '1000',
                      '--name', 'callset-name-new'])
    self.AssertOutputEquals('')
    self.AssertErrEquals('Updated call set [callset-name-new, id: 1000].\n')

  def testCallsetsUpdateNotExists(self):
    self.mocked_client.callsets.Patch.Expect(
        request=
        self.messages.GenomicsCallsetsPatchRequest(
            callSet=self.messages.CallSet(
                id='1000',
                name='callset-name-new',
                # This is the dummy response inserted by update.py.
                # See b/22818510.
                variantSetIds=['123'],),
            callSetId='1000',),
        exception=self.MakeHttpError(404, 'Callset not found: 1000'))
    with self.assertRaisesRegexp(exceptions.HttpException,
                                 'Callset not found: 1000'):
      self.RunGenomics(['callsets', 'update', '1000',
                        '--name', 'callset-name-new'])

if __name__ == '__main__':
  test_case.main()