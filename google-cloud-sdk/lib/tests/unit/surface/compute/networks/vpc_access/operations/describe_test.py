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
"""Tests of 'gcloud compute networks vpc-access operations describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.networks.vpc_access import base


class OperationsDescribeTestGa(base.VpcAccessUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def _SetExpected(self):
    self.expected_operation = self.messages.Operation(
        name=self.operation_relative_name)
    self.operations_client.Get.Expect(
        request=self.messages.VpcaccessProjectsLocationsOperationsGetRequest(
            name=self.expected_operation.name),
        response=self.expected_operation)

  def testOperationsDescribe(self):
    self._SetExpected()
    actual_operation = self.Run(
        'compute networks vpc-access operations describe {} --region={}'.format(
            self.operation_id, self.region_id))
    self.assertEqual(actual_operation, self.expected_operation)

  def testOpertionsDescribe_UsingRelativeOperationName(self):
    self._SetExpected()
    actual_operation = self.Run(
        'compute networks vpc-access operations describe {}'.format(
            self.operation_relative_name))
    self.assertEqual(actual_operation, self.expected_operation)


class OperationsDescribeTestBeta(OperationsDescribeTestGa):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'v1beta1'


class OperationsDescribeTestAlpha(OperationsDescribeTestGa):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'v1alpha1'


if __name__ == '__main__':
  test_case.main()
