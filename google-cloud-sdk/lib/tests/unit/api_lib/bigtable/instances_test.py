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
"""Tests for Bigtable snapshots library."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.bigtable import instances
from googlecloudsdk.core import resources
from tests.lib.surface.bigtable import base


class InstancesClientTest(base.BigtableV2TestBase):

  def SetUp(self):
    instance_id = 'my-instance'

    self.instance_ref = resources.REGISTRY.Parse(
        instance_id,
        params={'projectsId': self.Project()},
        collection='bigtableadmin.projects.instances')

  def ExpectInstanceUpdateRequest(self, response):
    self.client.projects_instances.PartialUpdateInstance.Expect(
        request=self.msgs.
        BigtableadminProjectsInstancesPartialUpdateInstanceRequest(
            instance=self.msgs.Instance(
                type=self.msgs.Instance.TypeValueValuesEnum.PRODUCTION),
            name=self.instance_ref.RelativeName(),
            updateMask='type'),
        response=response)

  def testUpgrade(self):
    response = self.msgs.Operation()
    self.ExpectInstanceUpdateRequest(response)
    self.assertEqual(instances.Upgrade('my-instance'), response)
