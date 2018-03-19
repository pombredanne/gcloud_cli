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
"""Test of the 'update' command."""

from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.bigtable import base


class UpdateCommandTest(base.BigtableV2TestBase,
                        sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.cmd = 'instances update theinstance --display-name newdisplayname'
    self.svc = self.client.projects_instances.Get
    self.msg = self.msgs.BigtableadminProjectsInstancesGetRequest(
        name='projects/{0}/instances/theinstance'.format(self.Project()))

  def _RunSuccessTest(self):
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.Instance(
            name='projects/theprojects/instances/theinstance',
            displayName='thedisplayname'))
    updated = self.msgs.Instance(
        name='projects/theprojects/instances/theinstance',
        displayName='newdisplayname')
    self.client.projects_instances.Update.Expect(
        request=updated, response=updated)
    self.RunBT(self.cmd)
    self.AssertErrContains(
        'Updated instance [projects/theprojects/instances/theinstance].\n')

  def testUpdate(self):
    self._RunSuccessTest()

  # TODO(b/73365914) Remove after deprecation period
  def testUpdateDescription(self):
    self.cmd = 'instances update theinstance --description newdisplayname'
    self._RunSuccessTest()
    self.AssertErrContains('WARNING: Flag --description is deprecated.')

  # TODO(b/38428550) Remove after deprecation period
  def testUpdateDevInstance(self):
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.Instance(
            name='projects/theprojects/instances/theinstance',
            displayName='thedisplayname',
            type=self.msgs.Instance.TypeValueValuesEnum.DEVELOPMENT))
    updated = self.msgs.Instance(
        name='projects/theprojects/instances/theinstance',
        displayName='thedisplayname',
        type=self.msgs.Instance.TypeValueValuesEnum.PRODUCTION)
    self.client.projects_instances.Update.Expect(
        request=updated, response=updated)
    self.cmd = 'instances update theinstance --instance-type production'
    self.RunBT(self.cmd)
    self.AssertErrContains(
        'Updated instance [projects/theprojects/instances/theinstance].\n')
    self.AssertErrContains(
        'WARNING: Upgrading development instances with --instance-type '
        'is deprecated.')

  def testUpdateByUri(self):
    self.cmd = (
        'instances update https://bigtableadmin.googleapis.com/v2/'
        'projects/{0}/instances/theinstance --description newdisplayname'
        .format(self.Project()))
    self._RunSuccessTest()

  def testErrorResponse(self):
    with self.AssertHttpResponseError(self.svc, self.msg):
      self.RunBT(self.cmd)


if __name__ == '__main__':
  test_case.main()