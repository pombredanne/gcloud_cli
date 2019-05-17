# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.unit.surface.compute.os_config.patch_jobs.describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.os_config import test_base


class DescribeTestAlpha(test_base.OsConfigBaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SetUpMockApis(self.track)

  def testDescribeNoPatchJobArg(self):
    with self.AssertRaisesArgumentError():
      self.Run("""compute os-config patch-jobs describe""")

    self.AssertErrContains('argument PATCH_JOB: Must be specified.')

  def testDescribeWithPatchJobName(self):
    expected_response = self.CreatePatchJob('my-project', 'my-patch-job')
    self.mock_osconfig_client.projects_patchJobs.Get.Expect(
        request=self.messages.OsconfigProjectsPatchJobsGetRequest(
            name='projects/my-project/patchJobs/my-patch-job'),
        response=expected_response)

    response = self.Run("""
        compute os-config patch-jobs describe my-patch-job
        """)

    self.assertEqual(expected_response, response)

  def testDescribeWithRelativePatchJobPath(self):
    expected_response = self.CreatePatchJob('my-project', 'my-patch-job')
    self.mock_osconfig_client.projects_patchJobs.Get.Expect(
        request=self.messages.OsconfigProjectsPatchJobsGetRequest(
            name='projects/my-project/patchJobs/my-patch-job'),
        response=expected_response)

    response = self.Run("""
        compute os-config patch-jobs describe
        projects/my-project/patchJobs/my-patch-job
        """)

    self.assertEqual(expected_response, response)

  def testDescribeWithPatchJobUri(self):
    expected_response = self.CreatePatchJob('my-project', 'my-patch-job')
    self.mock_osconfig_client.projects_patchJobs.Get.Expect(
        request=self.messages.OsconfigProjectsPatchJobsGetRequest(
            name='projects/my-project/patchJobs/my-patch-job'),
        response=expected_response)

    response = self.Run("""
        compute os-config patch-jobs describe
        https://osconfig.googleapis.com/v1alpha1/projects/my-project/patchJobs/my-patch-job
        """)

    self.assertEqual(expected_response, response)


if __name__ == '__main__':
  test_case.main()