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
"""Test of the 'operations cancel' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import operations
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.firestore import base


class CancelTestGA(base.FirestoreCommandUnitTest):
  """Tests the GA firestore operations cancel command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testCancelRelativeResourcePath(self):
    operation_name_relative = 'doomed'
    operation_name_full =\
      'projects/my-test-project/databases/(default)/operations/doomed'

    request = self._GetMockCancelRequest(operation_name_full)
    response = operations.GetMessages().Empty()

    self.mock_firestore_v1.projects_databases_operations.Cancel.Expect(
        request, response=response)

    self.RunFirestoreTest(
        'operations cancel {}'.format(operation_name_relative))

  def testCancelAbsoluteResourcePath(self):
    operation_name_full =\
      'projects/my-test-project/databases/(default)/operations/doomed'

    request = self._GetMockCancelRequest(operation_name_full)
    response = operations.GetMessages().Empty()

    self.mock_firestore_v1.projects_databases_operations.Cancel.Expect(
        request, response=response)

    self.RunFirestoreTest('operations cancel {}'.format(operation_name_full))

  def _GetMockCancelRequest(self, name):
    messages = operations.GetMessages()
    request = messages.FirestoreProjectsDatabasesOperationsCancelRequest()
    request.name = name
    return request


class CancelTestBeta(CancelTestGA):
  """Tests the beta firestore operations cancel command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CancelTestAlpha(CancelTestBeta):
  """Tests the alpha firestore operations cancel command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
