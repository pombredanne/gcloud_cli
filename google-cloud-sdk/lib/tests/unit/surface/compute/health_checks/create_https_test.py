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
"""Tests for the health-checks create https subcommand."""
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HealthChecksCreateHttpsTest(test_base.BaseTest):

  def testDefaultOptions(self):
    self.Run("""
        compute health-checks create https my-health-check
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testUriSupport(self):
    self.Run("""
        compute health-checks create https
          https://www.googleapis.com/compute/v1/projects/my-project/global/healthChecks/my-health-check
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testHostOption(self):
    self.Run("""
        compute health-checks create https my-health-check
          --host www.example.com
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testPortOption(self):
    self.Run("""
        compute health-checks create https my-health-check
          --port 8888
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=8888,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testPortNameOption(self):
    self.Run("""
        compute health-checks create https my-health-check
          --port-name magic-port
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      portName='magic-port',
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testRequestPathOption(self):
    self.Run("""
        compute health-checks create https my-health-check
          --request-path /testpath
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      requestPath='/testpath',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testCheckIntervalOption(self):
    self.Run("""
        compute health-checks create https my-health-check
          --check-interval 34s
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=34,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testTimeoutSecOption(self):
    self.Run("""
        compute health-checks create https my-health-check
          --timeout 2m
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testHealthyThresholdOption(self):
    self.Run("""
        compute health-checks create https my-health-check
          --healthy-threshold 7
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testUnhealthyThresholdOption(self):
    self.Run("""
        compute health-checks create https my-health-check
          --unhealthy-threshold 8
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=8),
              project='my-project'))],
    )

  def testDescriptionOption(self):
    self.Run("""
        compute health-checks create https my-health-check
           --description "Circulation, Airway, Breathing"
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  description='Circulation, Airway, Breathing',
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testProxyHeaderOption(self):
    self.Run("""
        compute health-checks create https my-health-check
          --proxy-header PROXY_V1
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.PROXY_V1)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )


class HealthChecksCreateHttpsAlphaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testResponseOption(self):
    self.Run("""
        compute health-checks create https my-health-check
          --response new-response
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      requestPath='/',
                      response='new-response',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

if __name__ == '__main__':
  test_case.main()