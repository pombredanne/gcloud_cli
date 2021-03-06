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
"""Tests for `gcloud access-context-manager perimeters describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager
from six import text_type


class PerimetersDescribeTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectGet(self, perimeter):
    m = self.messages
    request_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersGetRequest)
    self.client.accessPolicies_servicePerimeters.Get.Expect(
        request_type(name=perimeter.name), perimeter)

  def testDescribe_MissingRequired(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager perimeters describe --policy 123')

  def testDescribe(self):
    self.SetUpForAPI(self.api_version)
    perimeter = self._MakePerimeter('my_perimeter')
    self._ExpectGet(perimeter)

    result = self.Run('access-context-manager perimeters describe my_perimeter '
                      '--policy 123')

    self.assertEqual(result, perimeter)

  def testDescribe_PolicyFromProperty(self):
    self.SetUpForAPI(self.api_version)
    perimeter = self._MakePerimeter('my_perimeter')
    policy = '456'
    perimeter.name = ('accessPolicies/456/servicePerimeters/my_perimeter')
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectGet(perimeter)

    result = self.Run('access-context-manager perimeters describe my_perimeter')

    self.assertEqual(result, perimeter)

  def testDescribe_InvalidPolicyArg(self):
    with self.assertRaises(properties.InvalidValueError) as ex:
      # Common error is to specify --policy arg as 'accessPolicies/<num>'
      self.Run('access-context-manager perimeters describe MY_PERIMETER '
               '    --policy accessPolicies/123')
    self.assertIn('set to the policy number', text_type(ex.exception))


class PerimetersDescribeTestBeta(PerimetersDescribeTestGA):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA


class PerimetersDescribeTestAlpha(PerimetersDescribeTestGA):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
