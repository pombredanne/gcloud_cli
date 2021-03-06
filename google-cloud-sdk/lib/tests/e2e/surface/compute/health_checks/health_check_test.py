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
"""Integration tests for health checks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class HealthChecksTest(e2e_test_base.BaseTest):

  def UniqueName(self, name):
    return next(
        e2e_utils.GetResourceNameGenerator(prefix='compute-health-check-test-' +
                                           name))

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    properties.VALUES.core.user_output_enabled.Set(False)
    self.health_check_names = []

  def TearDown(self):
    for name in self.health_check_names:
      self.CleanUpResource(
          name,
          'health-checks',
          scope=e2e_test_base.EXPLICIT_GLOBAL
          if self.track == calliope_base.ReleaseTrack.ALPHA else
          e2e_test_base.GLOBAL)

  def GetProtocolAgnosticDefaultParams(self):
    return {
        'timeoutSec': 5,
        'checkIntervalSec': 5,
        'healthyThreshold': 2,
        'unhealthyThreshold': 2,
    }

  def CreateHealthCheck(self, protocol):
    name = self.UniqueName('{0}-hc'.format(protocol))
    global_flag = (' --global'
                   if self.track == calliope_base.ReleaseTrack.ALPHA else '')
    result = self.Run('compute health-checks create {0} {1} {2}'.format(
        protocol, name, global_flag))

    result_list = list(result)
    self.assertEqual(1, len(result_list))
    self.assertEqual(name, result_list[0].name)
    self.health_check_names.append(name)
    return name, result_list[0]

  def UpdateHealthCheck(self, protocol, hc_name, updated_protocol_params):
    # Update parameters common to all protocols.
    updated_default = """
      --timeout 1s
      --check-interval 3s
      --healthy-threshold 3
      --unhealthy-threshold 4
      --description "Health check test."
      --global
    """
    expected = {
        'timeoutSec': 1,
        'checkIntervalSec': 3,
        'healthyThreshold': 3,
        'unhealthyThreshold': 4,
        'description': 'Health check test.',
    }

    result = self.Run('compute health-checks update {0} {1} {2} {3}'.format(
        protocol, hc_name, updated_default, updated_protocol_params))

    self.assertEqual(1, len(result))
    self.assertEqual(hc_name, result[0].name)
    self.assertDictContainsSubset(expected, encoding.MessageToDict(result[0]))
    return result[0]

  def ListHealthCheck(self, name):
    result = self.Run('compute health-checks list --global {0}'.format(name))
    result_list = list(result)
    self.assertEqual(1, len(result_list))
    return result_list[0]

  def DeleteHealthCheck(self, hc_name):
    result = self.Run(
        'compute health-checks delete --global {0}'.format(hc_name))
    result_list = list(result)
    self.assertEqual(0, len(result_list))

  def testHTTPHealthCheck(self):
    protocol = 'http'
    # Test the create operation.
    hc_name, hc = self.CreateHealthCheck(protocol)
    expected = self.GetProtocolAgnosticDefaultParams()
    # Add HTTP specific parameters.
    expected.update({
        'type': 'HTTP',
        'httpHealthCheck': {
            'port': 80,
            'portSpecification': 'USE_FIXED_PORT',
            'proxyHeader': 'NONE',
            'requestPath': '/',
        }
    })
    self.assertDictContainsSubset(expected, encoding.MessageToDict(hc))

    # Now update and test that the parameters have changed.
    updated_http_params = """
      --port 8080
      --proxy-header PROXY_V1
      --request-path /healthz/hc
    """
    hc = self.UpdateHealthCheck(protocol, hc_name, updated_http_params)
    expect_updated_params = {
        'httpHealthCheck': {
            'port': 8080,
            'portSpecification': 'USE_FIXED_PORT',
            'proxyHeader': 'PROXY_V1',
            'requestPath': '/healthz/hc',
        }
    }
    self.assertDictContainsSubset(expect_updated_params,
                                  encoding.MessageToDict(hc))

    # Test the list operation.
    hc = self.ListHealthCheck(hc_name)
    self.assertEqual(protocol.upper(), hc['type'])

    # Test the delete operation.
    self.DeleteHealthCheck(hc_name)

  def testHTTPSHealthCheck(self):
    protocol = 'https'
    # Test the create operation.
    hc_name, hc = self.CreateHealthCheck(protocol)
    expected = self.GetProtocolAgnosticDefaultParams()
    # Add HTTPS specific parameters.
    expected.update({
        'type': 'HTTPS',
        'httpsHealthCheck': {
            'port': 80,
            'portSpecification': 'USE_FIXED_PORT',
            'proxyHeader': 'NONE',
            'requestPath': '/'
        }
    })
    self.assertDictContainsSubset(expected, encoding.MessageToDict(hc))

    # Now update and test that the parameters have changed.
    updated_https_params = """
      --port 8080
      --proxy-header PROXY_V1
      --request-path /healthz/hc
    """
    hc = self.UpdateHealthCheck(protocol, hc_name, updated_https_params)
    expect_updated_params = {
        'httpsHealthCheck': {
            'port': 8080,
            'portSpecification': 'USE_FIXED_PORT',
            'proxyHeader': 'PROXY_V1',
            'requestPath': '/healthz/hc'
        }
    }
    self.assertDictContainsSubset(expect_updated_params,
                                  encoding.MessageToDict(hc))

    # Test the list operation.
    hc = self.ListHealthCheck(hc_name)
    self.assertEqual(protocol.upper(), hc['type'])

    # Test the delete operation.
    self.DeleteHealthCheck(hc_name)

  def testTCPHealthCheck(self):
    protocol = 'tcp'
    # Test the create operation.
    hc_name, hc = self.CreateHealthCheck(protocol)
    expected = self.GetProtocolAgnosticDefaultParams()
    # Add TCP specific parameters.
    expected.update({
        'type': 'TCP',
        'tcpHealthCheck': {
            'port': 80,
            'portSpecification': 'USE_FIXED_PORT',
            'proxyHeader': 'NONE',
        }
    })
    self.assertDictContainsSubset(expected, encoding.MessageToDict(hc))

    # Now update and test that the parameters have changed.
    updated_tcp_params = """
      --port 8080
      --proxy-header PROXY_V1
      --request HelloWorld
      --response Hello
    """
    hc = self.UpdateHealthCheck(protocol, hc_name, updated_tcp_params)
    expect_updated_params = {
        'tcpHealthCheck': {
            'port': 8080,
            'portSpecification': 'USE_FIXED_PORT',
            'request': 'HelloWorld',
            'response': 'Hello',
            'proxyHeader': 'PROXY_V1',
        }
    }
    self.assertDictContainsSubset(expect_updated_params,
                                  encoding.MessageToDict(hc))

    # Test the list operation.
    hc = self.ListHealthCheck(hc_name)
    self.assertEqual(protocol.upper(), hc['type'])

    # Test the delete operation.
    self.DeleteHealthCheck(hc_name)

  def testSSLHealthCheck(self):
    protocol = 'ssl'
    # Test the create operation.
    hc_name, hc = self.CreateHealthCheck(protocol)
    expected = self.GetProtocolAgnosticDefaultParams()
    # Add SSL specific parameters.
    expected.update({
        'type': 'SSL',
        'sslHealthCheck': {
            'port': 80,
            'portSpecification': 'USE_FIXED_PORT',
            'proxyHeader': 'NONE',
        }
    })
    self.assertDictContainsSubset(expected, encoding.MessageToDict(hc))

    # Now update and test that the parameters have changed.
    updated_ssl_params = """
      --port 8080
      --request HelloWorld
      --response Hello
      --proxy-header PROXY_V1
    """
    hc = self.UpdateHealthCheck(protocol, hc_name, updated_ssl_params)
    expect_updated_params = {
        'sslHealthCheck': {
            'port': 8080,
            'portSpecification': 'USE_FIXED_PORT',
            'request': 'HelloWorld',
            'response': 'Hello',
            'proxyHeader': 'PROXY_V1',
        }
    }
    self.assertDictContainsSubset(expect_updated_params,
                                  encoding.MessageToDict(hc))

    # Test the list operation.
    hc = self.ListHealthCheck(hc_name)
    self.assertEqual(protocol.upper(), hc['type'])

    # Test the delete operation.
    self.DeleteHealthCheck(hc_name)


if __name__ == '__main__':
  e2e_test_base.main()
