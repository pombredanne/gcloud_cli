# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud ml-engine locations list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib.surface.ml_engine import base


@parameterized.parameters('ml-engine', 'ai-platform')
class LocationsListTest(base.MlAlphaPlatformTestBase):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    m = self.short_msgs
    # Capability Types
    training = m.Capability.TypeValueValuesEnum.TRAINING
    batch = m.Capability.TypeValueValuesEnum.BATCH_PREDICTION
    # Accelerator Types
    k80 = (m.Capability.AvailableAcceleratorsValueListEntryValuesEnum
           .NVIDIA_TESLA_K80)
    p100 = (m.Capability.AvailableAcceleratorsValueListEntryValuesEnum
            .NVIDIA_TESLA_P100)
    cap1 = m.Capability(type=training, availableAccelerators=[k80, p100])
    cap2 = m.Capability(type=batch)
    cap3 = m.Capability(type=training, availableAccelerators=[k80])
    self.loc1 = m.Location(name='loc1', capabilities=[cap1])
    self.loc2 = m.Location(name='loc2', capabilities=[cap3, cap2])

  def _ExpectList(self, project_id=None):
    m = self.short_msgs
    if not project_id:
      project_id = self.Project()
    parent_project = 'projects/{}'.format(project_id)
    request = self.msgs.MlProjectsLocationsListRequest(parent=parent_project)
    response = m.ListLocationsResponse(locations=[self.loc1, self.loc2])
    self.client.projects_locations.List.Expect(request, response)

  def testList(self, module_name):
    self._ExpectList()
    results = self.Run('{} locations list'.format(module_name))
    self.assertEqual([self.loc1, self.loc2], results)

  def testListWithProjectOverride(self, module_name):
    self._ExpectList(project_id='p1')
    results = self.Run('{} locations list --project p1'.format(module_name))
    self.assertEqual([self.loc1, self.loc2], results)

  def testListFormat(self, module_name):
    properties.VALUES.core.user_output_enabled.Set(True)
    self._ExpectList()
    self.Run('{} locations list'.format(module_name))
    self.AssertOutputMatches(
        # pylint: disable=line-too-long
        r"""NAME TYPE AVAILABLE_ACCELERATORS
        loc1  \[u?'TRAINING'\]  \[u?'NVIDIA_TESLA_K80', u?'NVIDIA_TESLA_P100'\]
        loc2 \[u?'TRAINING', u?'BATCH_PREDICTION'\] \[u?'NVIDIA_TESLA_K80'\],None""",
        normalize_space=True)
