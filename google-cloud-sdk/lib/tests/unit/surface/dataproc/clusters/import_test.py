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
"""Test of the 'clusters import' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

import os

from googlecloudsdk import calliope

from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class ClustersImportUnitTest(unit_base.DataprocUnitTestBase,
                             compute_base.BaseComputeUnitTest):
  """Tests for clusters import."""

  def ExpectCreateCluster(self,
                          cluster=None,
                          response=None,
                          region=None,
                          project_id=None,
                          exception=None):
    if not region:
      region = self.REGION
    if not project_id:
      project_id = self.Project()
    if not cluster:
      cluster = self.MakeCluster()
    if not (response or exception):
      response = self.MakeOperation()
    self.mock_client.projects_regions_clusters.Create.Expect(
        self.messages.DataprocProjectsRegionsClustersCreateRequest(
            cluster=cluster,
            region=region,
            projectId=project_id,
            requestId=self.REQUEST_ID),
        response=response,
        exception=exception)

  def ExpectCreateCalls(self,
                        request_cluster=None,
                        response_cluster=None,
                        region=None,
                        error=None):
    if not request_cluster:
      request_cluster = self.MakeCluster()
    # Create request_cluster returns operation pending
    self.ExpectCreateCluster(cluster=request_cluster, region=region)
    # Initial get operation returns pending
    self.ExpectGetOperation()
    # Second get operation returns done
    self.ExpectGetOperation(operation=self.MakeCompletedOperation(error=error))
    if not error:
      # Get the request_cluster to display it.
      self.ExpectGetCluster(cluster=response_cluster, region=region)


class ClustersImportUnitTestGA(ClustersImportUnitTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.GA

  def _testImportClustersFromStdIn(self, region=None, region_flag=''):
    # Cluster with only configuration-related information.
    provided_cluster = self.messages.Cluster()

    # The cluster name and project id are populated before
    # we make the create request.
    expected_request = copy.deepcopy(provided_cluster)
    expected_request.clusterName = self.CLUSTER_NAME
    expected_request.projectId = self.Project()

    # The response has a lot more fields populated.
    response_cluster = self.MakeRunningCluster()

    self.WriteInput(export_util.Export(provided_cluster))
    self.ExpectCreateCalls(expected_request, response_cluster, region=region)
    result = self.RunDataproc('clusters import {0} {1}'.format(
        self.CLUSTER_NAME, region_flag))
    self.AssertMessagesEqual(response_cluster, result)

  def testImportClustersFromStdIn(self):
    self._testImportClustersFromStdIn()

  def testImportClustersRegionProperty(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self._testImportClustersFromStdIn(region='us-central1')

  def testImportClustersRegionFlag(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self._testImportClustersFromStdIn(
        region='us-east1', region_flag='--region=us-east1')

  def testImportClustersNoRegionFlag(self):
    provided_cluster = self.messages.Cluster()

    # The cluster name and project id are populated before
    # we make the create request.
    expected_request = copy.deepcopy(provided_cluster)
    expected_request.clusterName = self.CLUSTER_NAME
    expected_request.projectId = self.Project()

    self.WriteInput(export_util.Export(provided_cluster))

    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc(
          'clusters import {0}'.format(self.CLUSTER_NAME), set_region=False)

  def testImportClustersInvalid(self):
    expected_request = self.messages.Cluster(
        projectId=self.Project(), clusterName=self.CLUSTER_NAME)
    self.WriteInput('foo: bar')
    self.ExpectCreateCluster(
        cluster=expected_request, exception=self.MakeHttpError(status_code=400))
    # Ignores the invalid properties and passes the request for server-side
    # validation.
    with self.AssertRaisesHttpExceptionMatches('Invalid request'):
      self.RunDataproc('clusters import {0}'.format(self.CLUSTER_NAME))

  def testImportClustersHttpError(self):
    # Cluster with only configuration-related information.
    provided_cluster = self.messages.Cluster()

    # The cluster name and project id are populated before
    # we make the create request.
    expected_request = copy.deepcopy(provided_cluster)
    expected_request.clusterName = self.CLUSTER_NAME
    expected_request.projectId = self.Project()

    self.WriteInput(export_util.Export(provided_cluster))
    self.ExpectCreateCluster(
        cluster=expected_request, exception=self.MakeHttpError(status_code=403))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('clusters import {0}'.format(self.CLUSTER_NAME))

  def testImportClustersFromFile(self):
    # Cluster with only configuration-related information.
    provided_cluster = self.messages.Cluster()

    # The cluster name and project id are populated before
    # we make the create request.
    expected_request = copy.deepcopy(provided_cluster)
    expected_request.clusterName = self.CLUSTER_NAME
    expected_request.projectId = self.Project()

    # The response has a lot more fields populated.
    response_cluster = self.MakeRunningCluster()

    # Write test template to file.
    file_name = os.path.join(self.temp_path, 'cluster.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=provided_cluster, stream=stream)

    self.ExpectCreateCalls(expected_request, response_cluster)
    result = self.RunDataproc('clusters import {0} --source {1}'.format(
        self.CLUSTER_NAME, file_name))
    self.AssertMessagesEqual(response_cluster, result)

  def testImportClustersWithRegionNoZone(self):
    # Set region property.
    properties.VALUES.dataproc.region.Set('us-test1')

    # Cluster with no zone specified.
    provided_cluster = self.messages.Cluster()

    # The cluster name and project id are populated before
    # we make the create request.
    expected_request = copy.deepcopy(provided_cluster)
    expected_request.clusterName = self.CLUSTER_NAME
    expected_request.projectId = self.Project()

    # The response has a lot more fields populated.
    response_cluster = self.MakeRunningCluster()

    self.WriteInput(export_util.Export(provided_cluster))
    self.ExpectCreateCalls(
        expected_request, response_cluster, region='us-test1')
    result = self.RunDataproc('clusters import {0}'.format(self.CLUSTER_NAME))
    self.AssertMessagesEqual(response_cluster, result)


class ClustersImportUnitTestBeta(ClustersImportUnitTestGA):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA


class ClustersImportUnitTestAlpha(ClustersImportUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
