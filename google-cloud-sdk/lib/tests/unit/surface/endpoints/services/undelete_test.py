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
"""Unit tests for endpoints services undelete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base


class EndpointsUndeleteTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints services undelete command."""

  def testServicesUndelete(self):
    operation_name = 'operation-12345-67890'
    self.mocked_client.services.Undelete.Expect(
        request=self.services_messages.ServicemanagementServicesUndeleteRequest(
            serviceName=self.DEFAULT_SERVICE_NAME),
        response=self.services_messages.Operation(
            name=operation_name,
            done=True,))

    self.MockOperationWait(operation_name)

    self.WriteInput('y\n')
    self.Run('endpoints services undelete ' + self.DEFAULT_SERVICE_NAME)
    self.AssertErrContains(operation_name)
    self.AssertErrContains('Operation finished successfully.')

  def testServicesUndeleteAsync(self):
    operation_name = 'operation-12345-67890'
    self.mocked_client.services.Undelete.Expect(
        request=self.services_messages.ServicemanagementServicesUndeleteRequest(
            serviceName=self.DEFAULT_SERVICE_NAME),
        response=self.services_messages.Operation(
            name=operation_name,
            done=False,))

    self.WriteInput('y\n')
    self.Run('endpoints services undelete --async {0}'.format(
        self.DEFAULT_SERVICE_NAME))
    self.AssertErrContains(operation_name)
    self.AssertErrContains('Asynchronous operation is in progress')


if __name__ == '__main__':
  test_case.main()
