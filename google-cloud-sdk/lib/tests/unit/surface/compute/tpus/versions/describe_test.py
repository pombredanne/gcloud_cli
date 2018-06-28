# Copyright 2018 Google Inc. All Rights Reserved.
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
"""tpus versions describe tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.tpus import base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class DescribeTest(base.TpuUnitTestBase):

  def SetUp(self):
    self.zone = 'us-central1-c'
    properties.VALUES.compute.zone.Set(self.zone)

  def testDescribe(self, track):
    self._SetTrack(track)
    location_ref = resources.REGISTRY.Parse(
        self.zone,
        params={'projectsId': self.Project()},
        collection='tpu.projects.locations')
    tf = self.GetTestTFVersion(version='1.7')
    self.mock_client.projects_locations_tensorflowVersions.Get.Expect(
        self.messages.TpuProjectsLocationsTensorflowVersionsGetRequest(
            name='{}/tensorflowVersions/{}'.format(
                location_ref.RelativeName(), '1.7')),
        tf)

    self.assertEqual(
        self.Run('compute tpus versions describe 1.7'),
        tf)


if __name__ == '__main__':
  test_case.main()