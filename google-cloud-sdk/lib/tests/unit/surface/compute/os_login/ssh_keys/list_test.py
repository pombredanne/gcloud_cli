# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for the ssh-keys list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.oslogin import test_base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA),
)
class ListTest(test_base.OsloginBaseTest):

  def _RunSetUp(self, track):
    self.track = track
    self.SetUpMockApis(self.track)
    self.profiles = self.GetProfiles(self.messages)

  def testSimpleCase(self, track):
    self._RunSetUp(track)
    properties.VALUES.core.user_output_enabled.Set(False)

    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_keys'])

    response = self.Run("""
        compute os-login ssh-keys list
        """)

    profile = self.profiles['profile_with_keys']
    self.assertEqual(response, profile.sshPublicKeys.additionalProperties)

  def testImpersonateServiceAccount(self, track):
    self._RunSetUp(track)
    properties.VALUES.core.user_output_enabled.Set(False)

    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/service_account_user@google.com'),
        response=self.profiles['profile_with_keys'])

    response = self.Run("""
        compute os-login ssh-keys list
            --impersonate-service-account service_account_user@google.com
        """)

    profile = self.profiles['profile_with_keys']
    self.assertEqual(response, profile.sshPublicKeys.additionalProperties)


if __name__ == '__main__':
  test_case.main()
