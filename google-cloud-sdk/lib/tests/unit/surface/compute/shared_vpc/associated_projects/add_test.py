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
"""Tests for `gcloud compute shared-vpc associated-projects add`."""
from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.compute import xpn_test_base


class AddTest(xpn_test_base.XpnTestBase):

  def testAdd_NoProject(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument PROJECT_ID --host-project: Must be specified.'):
      self.Run('compute shared-vpc associated-projects add')
    self.xpn_client.EnableXpnAssociatedProject.assert_not_called()

  def testAdd(self):
    self._testAdd('shared-vpc')

  def testAdd_xpn(self):
    self._testAdd('xpn')

  def _testAdd(self, module_name):
    self.Run('compute {} associated-projects add --host-project xpn-host '
             'xpn-user'.format(module_name))
    self.xpn_client.EnableXpnAssociatedProject.assert_called_once_with(
        'xpn-host', 'xpn-user')


if __name__ == '__main__':
  test_case.main()
