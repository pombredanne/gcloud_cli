# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Test of the 'workflow template list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import jobs_unit_base


class WorkflowTemplatesListUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc workflow template list."""

  def ExpectListWorkflowTemplates(
      self, templates=None, exception=None, region=None):
    if region is None:
      region = self.REGION
    response = None
    if not exception:
      response = self.messages.ListWorkflowTemplatesResponse(
          templates=templates)
    self.mock_client.projects_regions_workflowTemplates.List.Expect(
        self.messages.DataprocProjectsRegionsWorkflowTemplatesListRequest(
            pageSize=100,
            parent=self.WorkflowTemplateParentName(region=region)),
        response=response,
        exception=exception)

  def SetUp(self):
    ordered_job = self.MakeOrderedJob(
        step_id='001', start_after=['ABC'], hadoopJob=self.HADOOP_JOB)
    self.workflow_templates_list = [
        self.MakeWorkflowTemplate(
            template_id=template_id,
            version=1,
            create_time='2017-08-14T23:49:50.654Z',
            update_time='2017-08-14T23:49:50.654Z',
            jobs=[ordered_job]) for template_id in self.WORKFLOW_TEMPLATE_IDS
    ]

  def testListWorkflorTemplatesPagination(self):
    self.mock_client.projects_regions_workflowTemplates.List.Expect(
        self.messages.DataprocProjectsRegionsWorkflowTemplatesListRequest(
            parent=self.WorkflowTemplateParentName(), pageSize=2),
        response=self.messages.ListWorkflowTemplatesResponse(
            templates=self.workflow_templates_list[:1],
            nextPageToken='test-token'))
    self.mock_client.projects_regions_workflowTemplates.List.Expect(
        self.messages.DataprocProjectsRegionsWorkflowTemplatesListRequest(
            parent=self.WorkflowTemplateParentName(),
            pageSize=2,
            pageToken='test-token'),
        response=self.messages.ListWorkflowTemplatesResponse(
            templates=self.workflow_templates_list[1:]))

    result = self.RunDataproc('workflow-templates list --page-size=2')
    self.AssertMessagesEqual(self.workflow_templates_list,
                             self.FilterOutPageMarkers(result))

  def _testListWorkflorTemplates(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION
    self.ExpectListWorkflowTemplates(
        self.workflow_templates_list, region=region)
    result = self.RunDataproc('workflow-templates list {0}'.format(region_flag))
    self.AssertMessagesEqual(self.workflow_templates_list, list(result))

  def testListWorkflorTemplates(self):
    self._testListWorkflorTemplates()

  def testListWorkflorTemplates_regionProperty(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testListWorkflorTemplates(region='global')

  def testListWorkflorTemplates_regionFlag(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testListWorkflorTemplates(
        region='us-central1', region_flag='--region=us-central1')

  def testListWorkflorTemplates_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'The required property \[region\] is not currently set'
    with self.assertRaisesRegex(properties.RequiredPropertyError, regex):
      self.RunDataproc('workflow-templates list', set_region=False)

  def testListWorkflowTemplatesOutput(self):
    self.ExpectListWorkflowTemplates(self.workflow_templates_list)
    self.RunDataproc('workflow-templates list', output_format='')

    self.AssertOutputEquals(
        textwrap.dedent("""\
ID                        JOBS  UPDATE_TIME               VERSION
test-workflow-template-0  1     2017-08-14T23:49:50.654Z  1
test-workflow-template-1  1     2017-08-14T23:49:50.654Z  1
test-workflow-template-2  1     2017-08-14T23:49:50.654Z  1
"""))


class WorkflowTemplatesListUnitTestBeta(WorkflowTemplatesListUnitTest):
  """Tests for dataproc workflow templates list."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    ordered_job = self.MakeOrderedJob(
        step_id='001', start_after=['ABC'], hadoopJob=self.HADOOP_JOB)
    self.workflow_templates_list = [
        self.MakeWorkflowTemplate(
            template_id=template_id,
            version=1,
            create_time='2017-08-14T23:49:50.654Z',
            update_time='2017-08-14T23:49:50.654Z',
            jobs=[ordered_job]) for template_id in self.WORKFLOW_TEMPLATE_IDS
    ]


class WorkflowTemplatesListUnitTestAlpha(WorkflowTemplatesListUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  sdk_test_base.main()
