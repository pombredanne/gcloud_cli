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
"""Tests for `gcloud access-context-manager levels delete`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager
from six import text_type


class LevelsDeleteTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)

  def _ExpectDelete(self, level, policy):
    level_name = 'accessPolicies/{}/accessLevels/{}'.format(policy, level)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsDeleteRequest
    self.client.accessPolicies_accessLevels.Delete.Expect(
        request_type(name=level_name),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')

  def testDelete_MissingRequired(self):
    self.SetUpForTrack(self.track)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager levels delete --policy 123')

  def testDelete_Prompt(self):
    self.SetUpForTrack(self.track)
    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run('access-context-manager levels delete my_level --policy 123')

  def testDelete(self):
    self.SetUpForTrack(self.track)
    self._ExpectDelete('my_level', '123')

    self.Run('access-context-manager levels delete my_level --policy 123 '
             '    --quiet')

    self.AssertOutputEquals('')

  def testDelete_PolicyFromProperty(self):
    self.SetUpForTrack(self.track)
    policy = '456'
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectDelete('my_level', policy)

    self.Run('access-context-manager levels delete my_level --quiet')

    self.AssertOutputEquals('')

  def testDelete_InvalidPolicyArg(self):
    self.SetUpForTrack(self.track)
    with self.assertRaises(properties.InvalidValueError) as ex:
      # Common error is to specify --policy arg as 'accessPolicies/<num>'
      self.Run('access-context-manager levels delete my_level --quiet'
               ' --policy accessPolicy/123')
    self.assertIn('set to the policy number', text_type(ex.exception))


class LevelsDeleteTestBeta(LevelsDeleteTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class LevelsDeleteTestAlpha(LevelsDeleteTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
