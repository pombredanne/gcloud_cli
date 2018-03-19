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
"""Test of the 'delete' command."""

from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.bigtable import base


class DeleteCommandTest(base.BigtableV2TestBase,
                        sdk_test_base.WithOutputCapture,
                        test_case.WithInput):

  def SetUp(self):
    self.cmd = 'instances delete theinstance'
    self.svc = self.client.projects_instances.Delete
    self.msg = self.msgs.BigtableadminProjectsInstancesDeleteRequest(
        name='projects/{0}/instances/theinstance'.format(self.Project()))
    self.other_msg = self.msgs.BigtableadminProjectsInstancesDeleteRequest(
        name='projects/{0}/instances/theotherinstance'.format(self.Project()))

  def _RunSuccessTest(self):
    self.svc.Expect(request=self.msg, response=self.msgs.Empty())
    self.RunBT(self.cmd)

  def testDelete(self):
    self._RunSuccessTest()

  def testDeleteByUri(self):
    self.cmd = ('instances delete https://bigtableadmin.googleapis.com/v2/'
                'projects/{0}/instances/theinstance'.format(self.Project()))
    self._RunSuccessTest()

  def testDeleteWarning(self):
    self.cmd = 'instances delete theinstance theotherinstance'
    # Confirm the deletion of both instances.
    self.WriteInput('y\n')
    self.WriteInput('y\n')
    self.svc.Expect(request=self.msg, response=self.msgs.Empty())
    self.svc.Expect(request=self.other_msg, response=self.msgs.Empty())
    self.RunBT(self.cmd)

  def testDeleteNoConfirmation(self):
    self.cmd = 'instances delete theinstance'
    # Reject the deletion of the instance.
    self.WriteInput('n\n')
    self.RunBT(self.cmd)

  def testErrorResponse(self):
    with self.AssertHttpResponseError(self.svc, self.msg):
      self.RunBT(self.cmd)


if __name__ == '__main__':
  test_case.main()