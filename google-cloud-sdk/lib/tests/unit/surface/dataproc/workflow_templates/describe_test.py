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
"""Test of the 'workflow template describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk import calliope

from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplateDescribeUnitTest(unit_base.DataprocUnitTestBase,
                                       compute_base.BaseComputeUnitTest):
  """Tests for workflow template describe."""

  def testDescribeWorkflowTemplates(self):
    """Tests the describe command."""
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectGetWorkflowTemplate(
        name=workflow_template.name,
        version=workflow_template.version,
        response=workflow_template)
    result = self.RunDataproc(
        'workflow-templates describe {0}'.format(self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(workflow_template, result)

  def testCreateWorkflowTemplatesWithVersion(self):
    workflow_template = self.MakeWorkflowTemplate(version=2)
    self.ExpectGetWorkflowTemplate(
        name=workflow_template.name,
        version=workflow_template.version,
        response=workflow_template)
    result = self.RunDataproc('workflow-templates describe {0} --version 2'.
                              format(self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(workflow_template, result)


class WorkflowTemplateDescribeUnitTestBeta(WorkflowTemplateDescribeUnitTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA


class WorkflowTemplateDescribeUnitTestAlpha(
    WorkflowTemplateDescribeUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  sdk_test_base.main()
