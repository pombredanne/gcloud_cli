# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for `gcloud access-context-manager zones create`."""
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class ZonesCreateTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectCreate(self, zone, policy):
    policy_name = 'accessPolicies/{}'.format(policy)
    m = self.messages
    req_type = m.AccesscontextmanagerAccessPoliciesAccessZonesCreateRequest
    self.client.accessPolicies_accessZones.Create.Expect(
        req_type(
            parent=policy_name,
            accessZone=zone
        ),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')
    get_req_type = m.AccesscontextmanagerAccessPoliciesAccessZonesGetRequest
    self.client.accessPolicies_accessZones.Get.Expect(
        get_req_type(name=zone.name), zone)

  def testCreate_MissingRequired(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Must be specified'):
      self.Run(
          'access-context-manager zones create my_zone --policy MY_POLICY '
          '    --title "My Title"')

  def testCreate(self, track):
    self.SetUpForTrack(track)
    zone = self._MakeZone('MY_ZONE', title='My Zone Title', description=None,
                          restricted_services=[], unrestricted_services=[],
                          access_levels=[], type_='ZONE_TYPE_REGULAR')
    self._ExpectCreate(zone, 'MY_POLICY')

    result = self.Run(
        'access-context-manager zones create MY_ZONE --policy MY_POLICY '
        '    --title "My Zone Title" --resources projects/12345,projects/67890')

    self.assertEqual(result, zone)

  def testCreate_PolicyFromProperty(self, track):
    self.SetUpForTrack(track)
    policy = 'my_acm_policy'
    properties.VALUES.access_context_manager.policy.Set(policy)
    zone = self._MakeZone('MY_ZONE', title='My Zone Title', description=None,
                          restricted_services=[], unrestricted_services=[],
                          access_levels=[], type_='ZONE_TYPE_REGULAR')
    zone.name = 'accessPolicies/{}/accessZones/MY_ZONE'.format(policy)
    self._ExpectCreate(zone, policy)

    result = self.Run(
        'access-context-manager zones create MY_ZONE --title "My Zone Title" '
        '    --resources projects/12345,projects/67890')

    self.assertEqual(result, zone)

  def testCreate_AllParamsRestrictedServices(self, track):
    self.SetUpForTrack(track)
    zone = self._MakeZone('MY_ZONE', title='My Zone Title', description=None,
                          restricted_services=['foo.googleapis.com',
                                               'bar.googleapis.com'],
                          unrestricted_services=['*'],
                          access_levels=['MY_LEVEL', 'MY_LEVEL_2'],
                          type_='ZONE_TYPE_BRIDGE')
    self._ExpectCreate(zone, 'MY_POLICY')

    result = self.Run(
        'access-context-manager zones create MY_ZONE --policy MY_POLICY '
        '    --access-levels MY_LEVEL,MY_LEVEL_2 --zone-type bridge '
        '    --restricted-services foo.googleapis.com,bar.googleapis.com'
        '    --title "My Zone Title" --resources projects/12345,projects/67890')

    self.assertEqual(result, zone)

  def testCreate_AllParamsUnrestrictedServices(self, track):
    self.SetUpForTrack(track)
    zone = self._MakeZone('MY_ZONE', title='My Zone Title', description=None,
                          restricted_services=['*'],
                          unrestricted_services=['foo.googleapis.com',
                                                 'bar.googleapis.com'],
                          access_levels=['MY_LEVEL', 'MY_LEVEL_2'],
                          type_='ZONE_TYPE_BRIDGE')
    self._ExpectCreate(zone, 'MY_POLICY')

    result = self.Run(
        'access-context-manager zones create MY_ZONE --policy MY_POLICY '
        '    --access-levels MY_LEVEL,MY_LEVEL_2 --zone-type bridge '
        '    --unrestricted-services foo.googleapis.com,bar.googleapis.com'
        '    --title "My Zone Title" --resources projects/12345,projects/67890')

    self.assertEqual(result, zone)

if __name__ == '__main__':
  test_case.main()