# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Test of the workflow template set-cluster-selector command."""

import copy

from googlecloudsdk import calliope

from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplateSetClusterSelectorUnitTest(
    unit_base.DataprocUnitTestBase, compute_base.BaseComputeUnitTest):
  """Tests for dataproc workflow template set-cluster-selector."""

  def MakeClusterSelector(self, cluster_labels, zone):
    labels = labels_util.Diff(additions=cluster_labels).Apply(
        self.messages.ClusterSelector.ClusterLabelsValue).GetOrNone()
    return self.messages.ClusterSelector(clusterLabels=labels, zone=zone)

  def ExpectSetClusterSelector(self,
                               workflow_template=None,
                               response=None,
                               exception=None):
    if not (response or exception):
      response = copy.deepcopy(workflow_template)
    self.mock_client.projects_regions_workflowTemplates.Update.Expect(
        workflow_template, response=response, exception=exception)

  def ExpectCallSetClusterSelector(self,
                                   workflow_template=None,
                                   cluster_selector=None,
                                   response=None,
                                   exception=None):
    if not workflow_template:
      workflow_template = self.MakeWorkflowTemplate()
    self.ExpectGetWorkflowTemplate(workflow_template=workflow_template)
    if not cluster_selector:
      cluster_selector = self.messages.ClusterSelector()
    workflow_template.placement = self.messages.WorkflowTemplatePlacement(
        clusterSelector=cluster_selector)
    if not (response or exception):
      response = copy.deepcopy(workflow_template)
    self.ExpectSetClusterSelector(
        workflow_template, response=response, exception=exception)


class WorkflowTemplateSetClusterSelectorUnitTestBeta(
    WorkflowTemplateSetClusterSelectorUnitTest):

  def SetUp(self):
    self.SetupForReleaseTrack(calliope.base.ReleaseTrack.BETA)

  def testSetClusterSelector(self):
    workflow_template = self.MakeWorkflowTemplate()
    cluster_labels = {'k1': 'v1'}
    cluster_selector = self.MakeClusterSelector(cluster_labels, 'us-west1-a')
    self.ExpectCallSetClusterSelector(
        workflow_template=workflow_template, cluster_selector=cluster_selector)
    result = self.RunDataproc('workflow-templates set-cluster-selector {0} '
                              '--zone us-west1-a --cluster-labels=k1=v1'.format(
                                  self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(workflow_template, result)

  def testSetClusterSelectorNoZone(self):
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectGetWorkflowTemplate(workflow_template=workflow_template)
    try:
      self.RunDataproc('workflow-templates set-cluster-selector {0} '
                       '--cluster-labels=k1=v1'.format(self.WORKFLOW_TEMPLATE))
      self.fail('Expected exception has not been raised')
    except properties.RequiredPropertyError:
      self.AssertErrContains('required property [zone] is not currently set')

  def testSetClusterSelectorNoClusterLabels(self):
    workflow_template = self.MakeWorkflowTemplate()
    cluster_selector = self.MakeClusterSelector(None, 'us-west1-a')
    self.ExpectCallSetClusterSelector(
        workflow_template=workflow_template, cluster_selector=cluster_selector)
    result = self.RunDataproc(
        'workflow-templates set-cluster-selector {0} '
        '--zone us-west1-a'.format(self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(workflow_template, result)

  def testSetClusterSelectorClusterLabelsLength(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --cluster-labels: expected one argument'):
      self.RunDataproc('workflow-templates set-cluster-selector {0} '
                       '--zone us-central1-a --cluster-labels'.format(
                           self.WORKFLOW_TEMPLATE))