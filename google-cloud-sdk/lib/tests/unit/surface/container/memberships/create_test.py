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
"""Tests for 'memberships create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.container.memberships import base


class CreateTestBeta(base.MembershipsTestBase):
  """gcloud Beta track using GKE Hub v1 API."""

  # TODO(b/116715821): add more negative tests.
  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectCreateCalls(self, membership, asynchronous=False):
    operation = self._MakeOperation()
    self.ExpectCreateMembership(membership, operation)
    if asynchronous:
      return
    self.ExpectGetOperation(operation)  # Second time succeed.
    response = encoding.PyValueToMessage(
        self.messages.Operation.ResponseValue, {
            '@type': ('type.googleapis.com/google.cloud.gkehub.{}.LongRunning'
                      'Membership').format(self.API_VERSION),
            'results': [encoding.MessageToPyValue(membership)]
        })
    operation = self._MakeOperation(done=True, response=response)
    self.ExpectGetOperation(operation)
    self.ExpectGetMembership(membership)

  def testCreateDefaults(self):
    self.WriteInput('y')
    membership = self._MakeMembership(description=self.MEMBERSHIP_DESCRIPTION)
    self._ExpectCreateCalls(membership)
    self._RunMembershipCommand([
        'create', self.MEMBERSHIP_NAME, '--description',
        self.MEMBERSHIP_DESCRIPTION
    ])

  def testCreateMissingResource(self):
    with self.AssertRaisesArgumentErrorMatches('MEMBERSHIP'):
      self._RunMembershipCommand(
          ['create', '--description', self.MEMBERSHIP_DESCRIPTION])

  def testCreateMissingDescription(self):
    with self.AssertRaisesArgumentErrorMatches('--description'):
      self._RunMembershipCommand(['create', self.MEMBERSHIP_NAME])

  def testCreateWithGKEClusterSelfLink(self):
    self.WriteInput('y')
    membership = self._MakeMembership(
        description=self.MEMBERSHIP_DESCRIPTION,
        gke_cluster_self_link=self.MEMBERSHIP_SELF_LINK)
    self._ExpectCreateCalls(membership)
    self._RunMembershipCommand([
        'create',
        self.MEMBERSHIP_NAME,
        '--description',
        self.MEMBERSHIP_DESCRIPTION,
        '--gke-cluster-self-link',
        self.MEMBERSHIP_SELF_LINK])

  def testCreateWithLabels(self):
    self.WriteInput('y')
    membership = self._MakeMembership(
        description=self.MEMBERSHIP_DESCRIPTION,
        labels_dict={
            'foo': 'bar',
            'baz': 'bar',
        })
    self._ExpectCreateCalls(membership)
    self._RunMembershipCommand([
        'create',
        self.MEMBERSHIP_NAME,
        '--description',
        self.MEMBERSHIP_DESCRIPTION,
        '--labels',
        'foo=bar,baz=bar'])

  def testCreateWithAllFields(self):
    self.WriteInput('y')
    membership = self._MakeMembership(
        description=self.MEMBERSHIP_DESCRIPTION,
        gke_cluster_self_link=self.MEMBERSHIP_SELF_LINK,
        labels_dict={
            'foo': 'bar',
            'baz': 'bar',
        })
    self._ExpectCreateCalls(membership)
    self._RunMembershipCommand([
        'create',
        self.MEMBERSHIP_NAME,
        '--description',
        self.MEMBERSHIP_DESCRIPTION,
        '--gke-cluster-self-link',
        self.MEMBERSHIP_SELF_LINK,
        '--labels',
        'foo=bar,baz=bar',
    ])


class CreateTestAlpha(CreateTestBeta):
  """gcloud Alpha track using GKE Hub v1 API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
