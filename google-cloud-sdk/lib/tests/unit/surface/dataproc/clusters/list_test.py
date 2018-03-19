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

"""Test of the 'clusters list' command."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base


class ClustersListUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for dataproc clusters list."""

  def SetUp(self):
    self.clusters = [
        self.MakeRunningCluster(clusterName=name, labels={'k1': 'v1'})
        for name in self.CLUSTER_NAMES]

  def ExpectListClusters(
      self, clusters=None, list_filter=None, region=None, exception=None):
    response = None
    if not exception:
      response = self.messages.ListClustersResponse(clusters=clusters)
    self.mock_client.projects_regions_clusters.List.Expect(
        self.messages.DataprocProjectsRegionsClustersListRequest(
            pageSize=100,
            region=region or self.REGION,
            filter=list_filter,
            projectId=self.Project()),
        response=response,
        exception=exception)

  def testListClusters(self):
    self.ExpectListClusters(self.clusters)
    result = self.RunDataproc('clusters list')
    self.AssertMessagesEqual(self.clusters, list(result))

  def testListClustersOutput(self):
    clusters = [self.MakeRunningCluster(clusterName=name)
                for name in self.CLUSTER_NAMES]
    self.ExpectListClusters(clusters)
    self.RunDataproc('clusters list', output_format='')
    self.AssertOutputContains(
        'NAME WORKER_COUNT STATUS ZONE', normalize_space=True)
    self.AssertOutputContains(
        'test-cluster-1 2 RUNNING us-central1-a', normalize_space=True)

  def testListClustersFilter(self):
    self.ExpectListClusters(self.clusters, list_filter='labels.k1:v1')
    result = self.RunDataproc('clusters list --filter="labels.k1:v1"')
    self.AssertMessagesEqual(self.clusters, list(result))

  def testListClustersPermissionsError(self):
    self.ExpectListClusters(
        exception=self.MakeHttpError(403))
    with self.AssertRaisesHttpErrorMatchesAsHttpException(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('clusters list').next()

  def testListClustersPagination(self):
    self.mock_client.projects_regions_clusters.List.Expect(
        self.messages.DataprocProjectsRegionsClustersListRequest(
            region=self.REGION,
            projectId=self.Project(),
            pageSize=2),
        response=self.messages.ListClustersResponse(
            clusters=self.clusters[:1],
            nextPageToken='test-token'))
    self.mock_client.projects_regions_clusters.List.Expect(
        self.messages.DataprocProjectsRegionsClustersListRequest(
            region=self.REGION,
            projectId=self.Project(),
            pageSize=2,
            pageToken='test-token'),
        response=self.messages.ListClustersResponse(
            clusters=self.clusters[1:]))

    result = self.RunDataproc('clusters list --page-size=2 --limit=3')
    self.AssertMessagesEqual(self.clusters, self.FilterOutPageMarkers(result))

  def testListClustersNonDefaultRegion(self):
    self.ExpectListClusters(self.clusters, region='us-central1')
    self.RunDataproc(
        'clusters list --region="us-central1"').next()

  def testListClustersNonDefaultRegionProperty(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self.ExpectListClusters(self.clusters, region='us-central1')
    self.RunDataproc('clusters list').next()


class ClustersListUnitTestBeta(ClustersListUnitTest, base.DataprocTestBaseBeta):
  """Tests for dataproc clusters list."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)


if __name__ == '__main__':
  sdk_test_base.main()