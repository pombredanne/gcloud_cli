# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Unit tests for the `run revisions list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.run import base
from six.moves import range


class RevisionsListTestBeta(base.ServerlessSurfaceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.revisions = [
        revision.Revision.New(
            self.mock_serverless_client, 'us-central1.fake-project')
        for _ in range(2)]
    for i, r in enumerate(self.revisions):
      r.name = 'revision{}'.format(i)
      r.metadata.creationTimestamp = '2018/01/01 00:{}0:00Z'.format(i)
      r.metadata.selfLink = '/apis/serving.knative.dev/v1alpha1/namespaces/{}/revisions/{}'.format(
          self.namespace.Name(), r.name)
      r.labels['serving.knative.dev/service'] = 'foo'
      r.labels['serving.knative.dev/configuration'] = 'foo'
      r.annotations[revision.AUTHOR_ANNOTATION] = 'some{}@google.com'.format(i)
      r.status.conditions = [
          self.serverless_messages.RevisionCondition(
              type='Ready',
              status='Unknown' if i%2 else 'True'),
          self.serverless_messages.RevisionCondition(
              type='Active',
              status='Unknown' if i%2 else 'True')
      ]

    self.operations.ListRevisions.return_value = self.revisions
    self._MockConnectionContext()

  def testNoArg(self):
    """Two revisions are listable using the Serverless API format."""
    out = self.Run('run revisions list')

    self.operations.ListRevisions.assert_called_once_with(self.namespace,
                                                          None)
    self.assertEqual(out, self.revisions)
    self.AssertOutputEquals(
        """REVISION ACTIVE SERVICE DEPLOYED DEPLOYED BY
        + revision0 yes foo 2018-01-01 00:00:00 UTC some0@google.com
        . revision1 foo 2018-01-01 00:10:00 UTC some1@google.com
        """, normalize_space=True)

  def testServiceArg(self):
    """Two revisions are listable using the Serverless API format."""
    out = self.Run('run revisions list --service foo')

    self.operations.ListRevisions.assert_called_once_with(self.namespace,
                                                          'foo')
    self.assertEqual(out, self.revisions)
    self.AssertOutputEquals(
        """REVISION ACTIVE SERVICE DEPLOYED DEPLOYED BY
        + revision0 yes foo 2018-01-01 00:00:00 UTC some0@google.com
        . revision1 foo 2018-01-01 00:10:00 UTC some1@google.com
        """, normalize_space=True)

  def testNoArgUri(self):
    """Two routes are listable using the Serverless API format."""
    self.Run('run revisions list --uri')

    self.operations.ListRevisions.assert_called_once_with(self.namespace,
                                                          None)
    self.AssertOutputEquals(
        """https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/revisions/revision0
        https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/revisions/revision1
        """,
        normalize_space=True)


class RevisionsListTestAlpha(RevisionsListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
