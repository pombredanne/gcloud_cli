# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for the health-checks create udp subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HealthChecksCreateUdpTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    self._health_check_api = self.compute_alpha.healthChecks

  def RunCreate(self, command):
    self.Run('compute health-checks create udp --global ' + command)

  def testDefaultOptions(self):
    self.make_requests.side_effect = [[
        self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP)
    ]]

    self.RunCreate('my-health-check --request sync --response ack')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

    self.AssertOutputEquals("""\
      NAME             PROTOCOL
      my-health-check  UDP
      """, normalize_space=True)

  def testUnspecifiedRequestResponse(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --request --response: Must be specified.'
        ):
      self.RunCreate('my-health-check')
    self.CheckRequests()

  def testUnspecifiedResponse(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --response: Must be specified.'):
      self.RunCreate('my-health-check --request sync')
    self.CheckRequests()

  def testUnspecifiedRequest(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --request: Must be specified.'):
      self.RunCreate('my-health-check --response ack')
    self.CheckRequests()

  def testEmptyRequestResponse(self):
    with self.AssertRaisesToolExceptionRegexp(
        '"request" field for UDP can not be empty.'):
      self.RunCreate("""
          my-health-check --request '' --response ack
      """)
    self.CheckRequests()

    with self.AssertRaisesToolExceptionRegexp(
        '"response" field for UDP can not be empty.'):
      self.RunCreate('my-health-check --request sync --response ""')
    self.CheckRequests()

  def testUriSupport(self):
    self.Run("""
        compute health-checks create udp
          https://compute.googleapis.com/compute/alpha/projects/my-project/global/healthChecks/my-health-check
          --request sync
          --response ack
        """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testPortOption(self):
    self.RunCreate('my-health-check --port 8888 --request sync --response ack')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      port=8888, request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testPortNameOption(self):
    self.RunCreate("""
        my-health-check
          --port-name magic-port
          --request sync
          --response ack
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      portName='magic-port', request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testCheckIntervalOption(self):
    self.RunCreate("""
        my-health-check
          --check-interval 34s
          --request sync
          --response ack
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=34,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testTimeoutSecOption(self):
    self.RunCreate("""
        my-health-check
          --timeout 2m
          --request sync
          --response ack
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testHealthyThresholdOption(self):
    self.RunCreate("""
        my-health-check
          --healthy-threshold 7
          --request sync
          --response ack
     """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testUnhealthyThresholdOption(self):
    self.RunCreate("""
        my-health-check
          --unhealthy-threshold 8
          --request sync
          --response ack
        """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=8),
              project='my-project'))],)

  def testDescriptionOption(self):
    self.RunCreate("""
        my-health-check
          --description "Circulation, Airway, Breathing"
          --request sync
          --response ack
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  description='Circulation, Airway, Breathing',
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)


class HealthChecksCreateUdpUnicodeTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    self._health_check_api = self.compute_alpha.healthChecks

  def RunCreate(self, command):
    self.Run('compute health-checks create udp --global ' + command)

  def testRequestOptionUnicode(self):
    self.RunCreate('my-health-check --request Ṳᾔḯ¢◎ⅾℯ --response ack')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='Ṳᾔḯ¢◎ⅾℯ', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testResponseOptionUnicode(self):
    self.RunCreate("""
        my-health-check
          --request sync
          --response Ṳᾔḯ¢◎ⅾℯ
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='Ṳᾔḯ¢◎ⅾℯ'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)


class RegionHealthChecksCreateUdpTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    self._health_check_api = self.compute_alpha.regionHealthChecks

  def RunCreate(self, command):
    self.Run('compute health-checks create udp --region us-west-1 ' + command)

  def testDefaultOptions(self):
    self.make_requests.side_effect = [[
        self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP)
    ]]

    self.RunCreate('my-health-check --request sync --response ack')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

    self.AssertOutputEquals(
        """\
      NAME             PROTOCOL
      my-health-check  UDP
      """,
        normalize_space=True)

  def testUnspecifiedRequestResponse(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --request --response: Must be specified.'):
      self.RunCreate('my-health-check')
    self.CheckRequests()

  def testUnspecifiedResponse(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --response: Must be specified.'):
      self.RunCreate('my-health-check --request sync')
    self.CheckRequests()

  def testUnspecifiedRequest(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --request: Must be specified.'):
      self.RunCreate('my-health-check --response ack')
    self.CheckRequests()

  def testEmptyRequestResponse(self):
    with self.AssertRaisesToolExceptionRegexp(
        '"request" field for UDP can not be empty.'):
      self.RunCreate("""
          my-health-check --request '' --response ack
      """)
    self.CheckRequests()

    with self.AssertRaisesToolExceptionRegexp(
        '"response" field for UDP can not be empty.'):
      self.RunCreate('my-health-check --request sync --response ""')
    self.CheckRequests()

  def testUriSupport(self):
    self.Run("""
        compute health-checks create udp
          https://compute.googleapis.com/compute/alpha/projects/my-project/regions/us-west-1/healthChecks/my-health-check
          --request sync
          --response ack
        """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testPortOption(self):
    self.RunCreate('my-health-check --port 8888 --request sync --response ack')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      port=8888, request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testPortNameOption(self):
    self.RunCreate("""
        my-health-check
          --port-name magic-port
          --request sync
          --response ack
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      portName='magic-port', request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testCheckIntervalOption(self):
    self.RunCreate("""
        my-health-check
          --check-interval 34s
          --request sync
          --response ack
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=34,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testTimeoutSecOption(self):
    self.RunCreate("""
        my-health-check
          --timeout 2m
          --request sync
          --response ack
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testHealthyThresholdOption(self):
    self.RunCreate("""
        my-health-check
          --healthy-threshold 7
          --request sync
          --response ack
     """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testUnhealthyThresholdOption(self):
    self.RunCreate("""
        my-health-check
          --unhealthy-threshold 8
          --request sync
          --response ack
        """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=8),
              project='my-project',
              region='us-west-1'))],)

  def testDescriptionOption(self):
    self.RunCreate("""
        my-health-check
          --description "Circulation, Airway, Breathing"
          --request sync
          --response ack
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  description='Circulation, Airway, Breathing',
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testRequestOptionUnicode(self):
    self.RunCreate('my-health-check --request Ṳᾔḯ¢◎ⅾℯ --response ack')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='Ṳᾔḯ¢◎ⅾℯ', response='ack'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testResponseOptionUnicode(self):
    self.RunCreate("""
        my-health-check
          --request sync
          --response Ṳᾔḯ¢◎ⅾℯ
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='sync', response='Ṳᾔḯ¢◎ⅾℯ'),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)


if __name__ == '__main__':
  test_case.main()
