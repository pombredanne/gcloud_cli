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

"""Tests for container_command_util.py utils."""

import argparse

from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.command_lib.container import container_command_util
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


class GetZoneTest(sdk_test_base.SdkBase):

  def testZone(self):
    args = argparse.Namespace(zone='test-zone-2')
    result = container_command_util.GetZone(args)
    self.assertEqual(result, 'test-zone-2')

  def testProperty(self):
    properties.VALUES.compute.zone.Set('test-zone-1')
    args = argparse.Namespace()
    result = container_command_util.GetZone(args)
    self.assertEqual(result, 'test-zone-1')

  def testRequired(self):
    properties.VALUES.compute.zone.Set(None)
    args = argparse.Namespace()
    with self.assertRaises(exceptions.MinimumArgumentException):
      container_command_util.GetZone(args, required=True)

  def testNotRequired(self):
    properties.VALUES.compute.zone.Set(None)
    args = argparse.Namespace()
    output = container_command_util.GetZone(args, required=False)
    self.assertIsNone(output)

  def testIgnoreProperty(self):
    properties.VALUES.compute.zone.Set('test-zone-1')
    args = argparse.Namespace()
    with self.assertRaises(exceptions.MinimumArgumentException):
      # Although property is set, it's not used so function raises exception.
      container_command_util.GetZone(args, ignore_property=True)


class GetZoneOrRegionTest(sdk_test_base.SdkBase):

  def testZone(self):
    args = argparse.Namespace(zone='test-zone-2')
    result = container_command_util.GetZoneOrRegion(args)
    self.assertEqual(result, 'test-zone-2')

  def testRegion(self):
    args = argparse.Namespace(region='region-1')
    result = container_command_util.GetZoneOrRegion(args)
    self.assertEqual(result, 'region-1')

  def testProperty(self):
    properties.VALUES.compute.zone.Set('test-zone-1')
    args = argparse.Namespace()
    result = container_command_util.GetZoneOrRegion(args)
    self.assertEqual(result, 'test-zone-1')

  def testRequired(self):
    properties.VALUES.compute.zone.Set(None)
    args = argparse.Namespace()
    with self.assertRaises(exceptions.MinimumArgumentException):
      container_command_util.GetZoneOrRegion(args, required=True)

  def testNotRequired(self):
    properties.VALUES.compute.zone.Set(None)
    args = argparse.Namespace()
    output = container_command_util.GetZoneOrRegion(args, required=False)
    self.assertIsNone(output)

  def testIgnoreProperty(self):
    properties.VALUES.compute.zone.Set('test-zone-1')
    args = argparse.Namespace()
    with self.assertRaises(exceptions.MinimumArgumentException):
      # Although property is set, it's not used so function raises exception.
      container_command_util.GetZoneOrRegion(args, ignore_property=True)

  def testBothRegionAndZone(self):
    args = argparse.Namespace(zone='us-central1-a', region='us-central1')
    with self.assertRaises(exceptions.ConflictingArgumentsException):
      container_command_util.GetZoneOrRegion(args)


class GetUseV1APIPropertyTest(
    parameterized.TestCase, cli_test_base.CliTestBase):

  @parameterized.parameters(
      (None, None, True),
      (True, None, True),
      (False, None, False),
      (None, True, True),
      (True, True, True),
      (None, False, False),
      (False, False, False),
  )
  def testGetUseV1APIProperty(self, use_v1_api, use_v1_api_client, expected):
    self._testGetUseV1APIProperty(use_v1_api, use_v1_api_client, expected)

  @parameterized.parameters(
      (False, True),
      (True, False),
  )
  def testGetUseV1APIPropertyConflict(self, use_v1_api, use_v1_api_client):
    with self.AssertRaisesExceptionMatches(
        util.Error,
        constants.CANNOT_SET_BOTH_USE_V1_API_PROPERTIES_WITH_DIFF_VALUES):
      self._testGetUseV1APIProperty(use_v1_api, use_v1_api_client, None)

  def _testGetUseV1APIProperty(self, use_v1_api, use_v1_api_client, expected):
    properties.VALUES.container.use_v1_api.Set(use_v1_api)
    properties.VALUES.container.use_v1_api_client.Set(use_v1_api_client)
    actual = container_command_util.GetUseV1APIProperty()
    self.assertEquals(expected, actual)


if __name__ == '__main__':
  test_case.main()