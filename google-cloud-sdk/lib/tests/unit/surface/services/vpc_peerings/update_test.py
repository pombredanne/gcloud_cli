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
"""Unit tests for service-management enable command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base
import mock


class UpdateTest(unit_test_base.SNUnitTestBase):
  """Unit tests for services vpc-peerings update command."""
  OPERATION_NAME = 'operations/abc.0000000000'
  NETWORK = 'hello'
  RANGES = ['google1', 'google2']
  RANGE_ARG = ','.join(RANGES)

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetProjectNumber(self):
    mock_get = self.StartObjectPatch(projects_api, 'Get')
    p = mock.Mock()
    p.projectNumber = self.PROJECT_NUMBER
    mock_get.return_value = p

  def testUpdate(self):
    self.ExpectUpdateConnection(self.NETWORK, self.RANGES, self.OPERATION_NAME,
                                False)
    self.ExpectOperation(self.OPERATION_NAME, 3)
    self.SetProjectNumber()

    self.Run('services vpc-peerings update --service={0} --network={1} '
             '--ranges={2}'.format(self.service, self.NETWORK, self.RANGE_ARG))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('finished successfully')

  def testUpdateForce(self):
    self.ExpectUpdateConnection(self.NETWORK, self.RANGES, self.OPERATION_NAME,
                                True)
    self.ExpectOperation(self.OPERATION_NAME, 3)
    self.SetProjectNumber()

    self.Run('services vpc-peerings update --service={0} --network={1} '
             '--ranges={2} --force'.format(self.service, self.NETWORK,
                                           self.RANGE_ARG))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('finished successfully')

  def testConnectAsync(self):
    self.ExpectUpdateConnection(self.NETWORK, self.RANGES, self.OPERATION_NAME,
                                False)
    self.SetProjectNumber()

    self.Run('services vpc-peerings update --service={0} --network={1} '
             '--ranges={2} --async'.format(self.service, self.NETWORK,
                                           self.RANGE_ARG))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('operation is in progress')

  def testConnectAsyncWithDefaultService(self):
    self.service = 'servicenetworking.googleapis.com'
    self.ExpectUpdateConnection(self.NETWORK, self.RANGES, self.OPERATION_NAME,
                                False)
    self.SetProjectNumber()

    self.Run('services vpc-peerings update --network={0} '
             '--ranges={1} --async'.format(self.NETWORK, self.RANGE_ARG))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('operation is in progress')

  def testConnectPermissionDenied(self):
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectUpdateConnection(
        self.NETWORK, self.RANGES, None, False, error=server_error)
    self.SetProjectNumber()

    with self.assertRaisesRegex(
        exceptions.CreateConnectionsPermissionDeniedException, r'Error.'):
      self.Run('services vpc-peerings update --service={0} --network={1} '
               '--ranges={2}'.format(self.service, self.NETWORK,
                                     self.RANGE_ARG))


class UpdateAlphaTest(UpdateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class UpdateBetaTest(UpdateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
