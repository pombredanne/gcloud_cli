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
"""Test of the 'workflow template remove-job' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk import calliope
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import jobs_unit_base


class WorkflowTemplateRemoveJobUnitTest(jobs_unit_base.JobsUnitTestBase,
                                        compute_base.BaseComputeUnitTest):
  """Tests for dataproc workflow template remove job."""

  def _testRemoveJob(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION
    workflow_template = self.MakeWorkflowTemplate(region=region)
    labels = {'some_label_key': 'some_label_value'}
    ordered_job_1 = self.MakeOrderedJob(
        step_id='001',
        start_after=['ABC'],
        hadoopJob=self.HADOOP_JOB,
        labels=labels)
    ordered_job_2 = self.MakeOrderedJob(
        step_id='ABC', hadoopJob=self.HADOOP_JOB, labels=labels)
    workflow_template.jobs = [ordered_job_1, ordered_job_2]
    self.WriteInput('y\n')
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template,
        ordered_jobs=[ordered_job_2])
    result = self.RunDataproc('workflow-templates remove-job {0} '
                              '--step-id 001 {1}'.format(
                                  self.WORKFLOW_TEMPLATE, region_flag))
    self.AssertMessagesEqual(expected, result)

  def testRemoveJob(self):
    self._testRemoveJob()

  def testRemoveJob_regionProperty(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testRemoveJob(region='global')

  def testRemoveJob_regionFlag(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testRemoveJob(
        region='us-central1', region_flag='--region=us-central1')

  def testRemoveJob_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc(
          'workflow-templates remove-job foo --step-id=step', set_region=False)

  def testRemoveJobNoJobWithStepId(self):
    workflow_template = self.MakeWorkflowTemplate()
    labels = {'some_label_key': 'some_label_value'}
    ordered_job = self.MakeOrderedJob(
        step_id='001',
        start_after=['002'],
        hadoopJob=self.HADOOP_JOB,
        labels=labels)
    workflow_template.jobs = [ordered_job]
    self.ExpectGetWorkflowTemplate(
        name=workflow_template.name,
        version=workflow_template.version,
        response=workflow_template)
    result = self.RunDataproc('workflow-templates remove-job {0} '
                              '--step-id 12'.format(self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(None, result)
    err_msg = 'Step id [{0}] is not found in workflow template [{1}].'.format(
        12, workflow_template.id)
    self.AssertErrContains(err_msg)


class WorkflowTemplateRemoveJobUnitTestBeta(WorkflowTemplateRemoveJobUnitTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA


class WorkflowTemplateRemoveJobUnitTestAlpha(
    WorkflowTemplateRemoveJobUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
