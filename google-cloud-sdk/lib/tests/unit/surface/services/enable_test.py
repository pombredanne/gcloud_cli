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

"""Unit tests for service-management enable command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class EnableTest(unit_test_base.SUUnitTestBase):
  """Unit tests for services enable command."""
  OPERATION_NAME = 'operations/abc.0000000000'

  def testEnable(self, track):
    self.track = track
    self.ExpectEnableApiCall(self.OPERATION_NAME)
    self.ExpectOperation(self.OPERATION_NAME, 3)

    self.Run('services enable %s' % self.DEFAULT_SERVICE)
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('finished successfully')

  def testBatchEnable(self, track):
    self.track = track
    self.ExpectBatchEnableApiCall(self.OPERATION_NAME)
    self.ExpectOperation(self.OPERATION_NAME, 3)

    self.Run('services enable %s %s' %
             (self.DEFAULT_SERVICE, self.DEFAULT_SERVICE_2))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('finished successfully')

  def testEnableAsync(self, track):
    self.track = track
    self.ExpectEnableApiCall(self.OPERATION_NAME)

    self.Run('services enable %s --async' % self.DEFAULT_SERVICE)
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('operation is in progress')

  def testEnablePermissionDenied(self, track):
    self.track = track
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectEnableApiCall(None, error=server_error)

    with self.assertRaisesRegex(
        exceptions.EnableServicePermissionDeniedException, r'Error.'):
      self.Run('services enable %s' % self.DEFAULT_SERVICE)


if __name__ == '__main__':
  test_case.main()
