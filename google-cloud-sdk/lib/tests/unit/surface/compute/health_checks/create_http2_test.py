# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the health-checks create http2 subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HealthChecksCreateHttp2Test(test_base.BaseTest, parameterized.TestCase):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testDefaultOptions(self):
    self.make_requests.side_effect = [[
        self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2)
    ]]

    self.Run("""
        compute health-checks create http2 my-health-check
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                  http2HealthCheck=self.messages.HTTP2HealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTP2HealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

    self.AssertOutputEquals("""\
      NAME             PROTOCOL
      my-health-check  HTTP2
      """, normalize_space=True)

  def testUriSupport(self):
    self.Run("""
        compute health-checks create http2
          https://www.googleapis.com/compute/alpha/projects/my-project/global/healthChecks/my-health-check
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                  http2HealthCheck=self.messages.HTTP2HealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTP2HealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testHostOption(self):
    self.Run("""
        compute health-checks create http2 my-health-check
          --host www.example.com
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                  http2HealthCheck=self.messages.HTTP2HealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTP2HealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testPortOption(self):
    self.Run("""
        compute health-checks create http2 my-health-check
          --port 8888
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                  http2HealthCheck=self.messages.HTTP2HealthCheck(
                      port=8888,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTP2HealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testPortNameOption(self):
    self.Run("""
        compute health-checks create http2 my-health-check
          --port-name magic-port
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                  http2HealthCheck=self.messages.HTTP2HealthCheck(
                      port=80,
                      portName='magic-port',
                      requestPath='/',
                      proxyHeader=(self.messages.HTTP2HealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testRequestPathOption(self):
    self.Run("""
        compute health-checks create http2 my-health-check
          --request-path /testpath
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                  http2HealthCheck=self.messages.HTTP2HealthCheck(
                      port=80,
                      requestPath='/testpath',
                      proxyHeader=(self.messages.HTTP2HealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testCheckIntervalOption(self):
    self.Run("""
        compute health-checks create http2 my-health-check
          --check-interval 34s
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                  http2HealthCheck=self.messages.HTTP2HealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTP2HealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=34,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testTimeoutSecOption(self):
    self.Run("""
        compute health-checks create http2 my-health-check
          --timeout 2m
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                  http2HealthCheck=self.messages.HTTP2HealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTP2HealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testHealthyThresholdOption(self):
    self.Run("""
        compute health-checks create http2 my-health-check
          --healthy-threshold 7
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                  http2HealthCheck=self.messages.HTTP2HealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTP2HealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testUnhealthyThresholdOption(self):
    self.Run("""
        compute health-checks create http2 my-health-check
          --unhealthy-threshold 8
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                  http2HealthCheck=self.messages.HTTP2HealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTP2HealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=8),
              project='my-project'))],
    )

  def testDescriptionOption(self):
    self.Run("""
        compute health-checks create http2 my-health-check
           --description "Circulation, Airway, Breathing"
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                  description='Circulation, Airway, Breathing',
                  http2HealthCheck=self.messages.HTTP2HealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTP2HealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testProxyHeaderOption(self):
    self.Run("""
        compute health-checks create http2 my-health-check
          --proxy-header PROXY_V1
        """)

    self.CheckRequests([(
        self.compute.healthChecks, 'Insert',
        self.messages.ComputeHealthChecksInsertRequest(
            healthCheck=self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                http2HealthCheck=self.messages.HTTP2HealthCheck(
                    proxyHeader=(self.messages.HTTP2HealthCheck
                                 .ProxyHeaderValueValuesEnum.PROXY_V1),
                    port=80,
                    requestPath='/'),
                checkIntervalSec=5,
                timeoutSec=5,
                healthyThreshold=2,
                unhealthyThreshold=2),
            project='my-project'))],)

  def testResponseOption(self):
    self.Run("""
        compute health-checks create http2 my-health-check
          --response "Ok Google"
        """)

    self.CheckRequests([(
        self.compute.healthChecks, 'Insert',
        self.messages.ComputeHealthChecksInsertRequest(
            healthCheck=self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                http2HealthCheck=self.messages.HTTP2HealthCheck(
                    port=80,
                    requestPath='/',
                    response='Ok Google',
                    proxyHeader=(self.messages.HTTP2HealthCheck
                                 .ProxyHeaderValueValuesEnum.NONE)),
                checkIntervalSec=5,
                timeoutSec=5,
                healthyThreshold=2,
                unhealthyThreshold=2),
            project='my-project'))],)

  @parameterized.parameters(
      ('USE_FIXED_PORT', '--port 80', 80, None),
      ('USE_NAMED_PORT', '--port-name my-port', None, 'my-port'),
      ('USE_SERVING_PORT', '', None, None))
  def testPortSpecificationOption(self, enum_value, additional_flags, port,
                                  port_name):
    self.Run("""
        compute health-checks create http2 my-health-check
          --port-specification {0} {1}
        """.format(enum_value, additional_flags))

    self.CheckRequests([(
        self.compute.healthChecks, 'Insert',
        self.messages.ComputeHealthChecksInsertRequest(
            healthCheck=self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                http2HealthCheck=self.messages.HTTP2HealthCheck(
                    port=port,
                    portName=port_name,
                    portSpecification=(self.messages.HTTP2HealthCheck
                                       .PortSpecificationValueValuesEnum(
                                           enum_value)),
                    requestPath='/',
                    proxyHeader=(self.messages.HTTP2HealthCheck
                                 .ProxyHeaderValueValuesEnum.NONE)),
                checkIntervalSec=5,
                timeoutSec=5,
                healthyThreshold=2,
                unhealthyThreshold=2),
            project='my-project'))],)

  @parameterized.parameters('USE_NAMED_PORT', 'USE_SERVING_PORT')
  def testPortSpecificationOptionPortOverride(self, enum_value):
    self.Run("""
        compute health-checks create http2 my-health-check
          --port-specification {}
        """.format(enum_value))

    self.CheckRequests([(
        self.compute.healthChecks, 'Insert',
        self.messages.ComputeHealthChecksInsertRequest(
            healthCheck=self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
                http2HealthCheck=self.messages.HTTP2HealthCheck(
                    portSpecification=(self.messages.HTTP2HealthCheck
                                       .PortSpecificationValueValuesEnum(
                                           enum_value)),
                    requestPath='/',
                    proxyHeader=(self.messages.HTTP2HealthCheck
                                 .ProxyHeaderValueValuesEnum.NONE)),
                checkIntervalSec=5,
                timeoutSec=5,
                healthyThreshold=2,
                unhealthyThreshold=2),
            project='my-project'))],)

  @parameterized.parameters(
      ('USE_FIXED_PORT', '--port-name', 'my-port'),
      ('USE_NAMED_PORT', '--port', 80),
      ('USE_SERVING_PORT', '--port-name', 'my-port'),
      ('USE_SERVING_PORT', '--port', 80))
  def testPortSpecificationOptionErrors(self, enum_value, flag, flag_value):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--port-specification]: {0} cannot be specified '
        'when using: {1}'.format(flag, enum_value)):
      self.Run("""
          compute health-checks create http2 my-health-check
            --port-specification {0} {1} {2}
          """.format(enum_value, flag, flag_value))


if __name__ == '__main__':
  test_case.main()
