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
"""Tests for environment patch command utility functions."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.command_lib.composer import environment_patch_util as patch_util
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.composer import base


class EnvironmentPatchUtilTest(base.EnvironmentsUnitTest):

  def SetUp(self):
    self.field_mask = 'testfieldmask'
    self.patch_environment = self.messages.Environment(name='patch')
    self.env_resource = resources.REGISTRY.Parse(
        self.TEST_ENVIRONMENT_ID,
        params={
            'projectsId': self.TEST_PROJECT,
            'locationsId': self.TEST_LOCATION
        },
        collection='composer.projects.locations.environments')

    self.running_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=False)
    self.successful_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True)

  def testPatch_Synchronous(self):
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self.patch_environment,
        update_mask=self.field_mask,
        response=self.running_op)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=self.successful_op)

    retval = patch_util.Patch(self.env_resource, self.field_mask,
                              self.patch_environment, False)
    self.assertIsNone(retval)
    self.AssertErrMatches(
        r'^<START PROGRESS TRACKER>Waiting for \[{}] to be updated with \[{}]'
        .format(self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testPatch_Asynchronous(self):
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self.patch_environment,
        update_mask=self.field_mask,
        response=self.running_op)

    retval = patch_util.Patch(self.env_resource, self.field_mask,
                              self.patch_environment, True)
    self.assertEqual(self.running_op, retval)
    self.AssertErrMatches(
        r'^Update in progress for environment \[{}] with operation \[{}]'.
        format(self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))


if __name__ == '__main__':
  test_case.main()