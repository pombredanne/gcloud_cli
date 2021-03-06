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
"""Test of the 'delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import app_profiles
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.bigtable import base


class AppProfileDeleteTestsGA(base.BigtableV2TestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.app_profile_delete_mock = self.StartObjectPatch(
        app_profiles, 'Delete', return_value=self.msgs.Empty())
    self.app_profile_ref = util.GetAppProfileRef('my-instance',
                                                 'my-app-profile')

  def testDelete(self):
    self.WriteInput('y\n')
    self.Run('bigtable app-profiles delete my-app-profile '
             '--instance my-instance')
    self.app_profile_delete_mock.assert_called_once_with(
        self.app_profile_ref, force=False)
    self.AssertLogContains('Deleted app profile [my-app-profile]')


class AppProfileDeleteTestsBeta(AppProfileDeleteTestsGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class AppProfileDeleteTestsAlpha(AppProfileDeleteTestsBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
