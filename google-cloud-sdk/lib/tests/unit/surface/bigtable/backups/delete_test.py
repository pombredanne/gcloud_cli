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
"""Tests of the 'delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base
from tests.lib.command_lib.util.concepts import resource_completer_test_base
from tests.lib.surface.bigtable import base


class DeleteCommandTestGA(base.BigtableV2TestBase,
                          resource_completer_test_base.ResourceCompleterBase,
                          concepts_test_base.ConceptsTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.svc = self.client.projects_instances_clusters_backups.Delete
    self.msg = self.msgs.BigtableadminProjectsInstancesClustersBackupsDeleteRequest(
        name='projects/{0}/instances/{1}/clusters/{2}/backups/{3}'.format(
            self.Project(), 'theinstance', 'thecluster', 'thebackup'))

  def testDelete(self):
    self.svc.Expect(request=self.msg, response=self.msgs.Empty())
    self.WriteInput('y\n')
    self.Run('bigtable backups delete thebackup --instance theinstance '
             '--cluster thecluster')
    self.AssertLogContains('Deleted backup [thebackup]')


class DeleteCommandTestBeta(DeleteCommandTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class DeleteCommandTestAlpha(DeleteCommandTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
