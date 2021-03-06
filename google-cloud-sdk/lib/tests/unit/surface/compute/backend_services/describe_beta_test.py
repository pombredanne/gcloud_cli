# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Tests for the beta backend-services describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.backend_services import test_resources


class BackendServicesDescribeTest(test_base.BaseTest,
                                  test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi('beta')
    self._backend_services = test_resources.BACKEND_SERVICES_BETA

  def testSimpleCase(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
    ])

    self.Run("""
        beta compute backend-services describe my-backend-service
        --region alaska
        """)

    self.CheckRequests(
        [(self.compute.regionBackendServices,
          'Get',
          messages.ComputeRegionBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project',
              region='alaska'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            description: my backend service
            healthChecks:
            - {uri}/projects/my-project/global/httpHealthChecks/my-health-check
            name: backend-service-1
            portName: http
            protocol: HTTP
            selfLink: {uri}/projects/my-project/global/backendServices/backend-service-1
            timeoutSec: 30
            """.format(uri=self.compute_uri)))

  def testScopeWarning(self):
    self.make_requests.side_effect = iter([[self._backend_services[0]],])

    self.Run("""
        beta compute backend-services describe my-backend-service
        --region alaska
        """)

    self.AssertErrNotContains('WARNING:')


class BackendServicesDescribeCompletionTest(test_base.BaseTest,
                                            completer_test_base.CompleterBase):

  def testDescribeCompletion(self):
    # Autocompletion uses default API, instead of assigned track API.
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(regional=True),
        result=resource_projector.MakeSerializable(
            test_resources.BACKEND_SERVICES_V1))
    self.ExpectListerInvoke(
        scope_set=self.MakeGlobalScope(),
        result=resource_projector.MakeSerializable(
            test_resources.BACKEND_SERVICES_V1))
    self.RunCompletion(
        'beta compute backend-services describe b',
        [
            'backend-service-1',
            'backend-service-tcp',
            'backend-service-2',
        ])


if __name__ == '__main__':
  test_case.main()
