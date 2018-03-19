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
"""Test of the 'describe' command."""

from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.bigtable import base


class DescribeCommandTest(base.BigtableV2TestBase,
                          sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.svc = self.client.projects_instances_clusters.Get
    self.msg = self.msgs.BigtableadminProjectsInstancesClustersGetRequest(
        name='projects/{0}/instances/theinstance/clusters/thecluster'.format(
            self.Project()))

  def _RunSuccessTest(self, cmd):
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.Cluster(
            name=
            'projects/theprojects/instances/theinstance/clusters/thecluster',
            serveNodes=6,
            defaultStorageType=(
                self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD)))
    self.RunBT(cmd)
    self.AssertOutputContains('thecluster')
    self.AssertOutputContains('6')
    self.AssertOutputContains('SSD')

  def testDescribe(self):
    self._RunSuccessTest('clusters describe thecluster --instance=theinstance')

  def testDescribeByUri(self):
    cmd = ('clusters describe https://bigtableadmin.googleapis.com/v2/'
           'projects/{0}/instances/theinstance/clusters/thecluster'.format(
               self.Project()))
    self._RunSuccessTest(cmd)

  def testErrorResponse(self):
    with self.AssertHttpResponseError(self.svc, self.msg):
      self.RunBT('clusters describe thecluster --instance=theinstance')


if __name__ == '__main__':
  test_case.main()