# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for `gcloud access-context-manager zones delete`."""
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class ZonesDeleteTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)

  def _ExpectDelete(self, zone, policy):
    zone_name = 'accessPolicies/{}/accessZones/{}'.format(policy, zone)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessZonesDeleteRequest
    self.client.accessPolicies_accessZones.Delete.Expect(
        request_type(
            name=zone_name
        ),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')

  def testDelete_MissingRequired(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager zones delete --policy my_policy')

  def testDelete_Prompt(self, track):
    self.SetUpForTrack(track)
    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run(
          'access-context-manager zones delete my_zone --policy my_policy')

  def testDelete(self, track):
    self.SetUpForTrack(track)
    self._ExpectDelete('my_zone', 'my_policy')

    self.Run('access-context-manager zones delete my_zone --policy my_policy '
             '    --quiet')

    self.AssertOutputEquals('')

  def testDelete_PolicyFromProperty(self, track):
    self.SetUpForTrack(track)
    policy = 'my_acm_policy'
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectDelete('my_zone', policy)

    self.Run('access-context-manager zones delete my_zone --quiet')

    self.AssertOutputEquals('')

if __name__ == '__main__':
  test_case.main()