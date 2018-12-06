# -*- coding: utf-8 -*- #
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
"""Tests for the target-https-proxies list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute.target_https_proxies import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


class TargetHttpsProxiesListTest(test_base.BaseTest,
                                 completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(
            test_resources.TARGET_HTTPS_PROXIES_V1))

  def testSimpleCase(self):
    self.Run("""
        compute target-https-proxies list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.targetHttpsProxies,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME                 SSL_CERTIFICATES URL_MAP
        target-https-proxy-1 ssl-cert-1       url-map-1
        target-https-proxy-2 ssl-cert-2       url-map-2
        target-https-proxy-3 ssl-cert-3       url-map-3
        """), normalize_space=True)

  def testTargetHttpsProxiesCompleter(self):
    self.RunCompleter(
        flags.TargetHttpsProxiesCompleter,
        expected_command=[
            'compute',
            'target-https-proxies',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'target-https-proxy-1',
            'target-https-proxy-2',
            'target-https-proxy-3',
        ],
        cli=self.cli,
    )
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.targetHttpsProxies,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])


class TargetHttpsProxiesListAlphaTest(test_base.BaseTest,
                                      completer_test_base.CompleterBase):
  URI_PREFIX = 'https://www.googleapis.com/compute/alpha/projects/my-project/'

  def SetUp(self):
    self.SelectApi('alpha')
    self._compute_api = self.compute_alpha

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

    self.target_https_proxies = [
        self.messages.TargetHttpsProxy(
            name='target-https-proxy-1',
            sslCertificates=([
                self.URI_PREFIX + 'global/sslCertificates/ssl-cert-1'
            ]),
            urlMap=self.URI_PREFIX + 'global/urlMaps/url-map-1',
            selfLink=(self.URI_PREFIX +
                      'global/targetHttpsProxies/target-https-proxy-1')),
        self.messages.TargetHttpsProxy(
            name='target-https-proxy-2',
            sslCertificates=([
                self.URI_PREFIX + 'global/sslCertificates/ssl-cert-2'
            ]),
            urlMap=self.URI_PREFIX + 'global/urlMaps/url-map-2',
            selfLink=(self.URI_PREFIX +
                      'global/targetHttpsProxies/target-https-proxy-2')),
    ]
    self.region_target_https_proxies = [
        self.messages.TargetHttpsProxy(
            name='target-https-proxy-3',
            sslCertificates=([
                self.URI_PREFIX + 'regions/region-1/sslCertificates/ssl-cert-3'
            ]),
            urlMap=self.URI_PREFIX + 'regions/region-1/urlMaps/url-map-3',
            selfLink=(self.URI_PREFIX + 'regions/region-1/'
                      'targetHttpsProxies/target-https-proxy-3'),
            region='region-1'),
        self.messages.TargetHttpsProxy(
            name='target-https-proxy-4',
            sslCertificates=([
                self.URI_PREFIX + 'regions/region-2/sslCertificates/ssl-cert-4'
            ]),
            urlMap=self.URI_PREFIX + 'regions/region-2/urlMaps/url-map-4',
            selfLink=(self.URI_PREFIX + 'regions/region-2/'
                      'targetHttpsProxies/target-https-proxy-4'),
            region='region-2'),
    ]

  def testGlobalOption(self):
    command = 'alpha compute target-https-proxies list --uri --global'
    output = ("""\
        https://www.googleapis.com/compute/alpha/projects/my-project/global/targetHttpsProxies/target-https-proxy-1
        https://www.googleapis.com/compute/alpha/projects/my-project/global/targetHttpsProxies/target-https-proxy-2
    """)

    self.RequestOnlyGlobal(command, self.target_https_proxies, output)

  def testOneRegion(self):
    command = 'alpha compute target-https-proxies list --uri --regions region-1'
    output = ("""\
        https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-1/targetHttpsProxies/target-https-proxy-3
        """)

    self.RequestOneRegion(command, self.region_target_https_proxies, output)

  def testTwoRegions(self):
    command = """
      alpha compute target-https-proxies list --uri --regions region-1,region-2
    """
    output = ("""\
        https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-1/targetHttpsProxies/target-https-proxy-3
        https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-2/targetHttpsProxies/target-https-proxy-4
        """)

    self.RequestTwoRegions(command, self.region_target_https_proxies, output)

  def testPositionalArgsWithSimpleNames(self):
    command = 'alpha compute target-https-proxies list'
    return_value = self.target_https_proxies + self.region_target_https_proxies
    output = ("""\
        NAME                  SSL_CERTIFICATES   URL_MAP
        target-https-proxy-1  ssl-cert-1         url-map-1
        target-https-proxy-2  ssl-cert-2         url-map-2
        target-https-proxy-3  ssl-cert-3         url-map-3
        target-https-proxy-4  ssl-cert-4         url-map-4
    """)

    self.RequestAggregate(command, return_value, output)

  def RequestOnlyGlobal(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.targetHttpsProxies, 'List',
                   self.messages.ComputeTargetHttpsProxiesListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestAggregate(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)

    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.targetHttpsProxies, 'AggregatedList',
                   self.messages.ComputeTargetHttpsProxiesAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestOneRegion(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.regionTargetHttpsProxies, 'List',
                   self.messages.ComputeRegionTargetHttpsProxiesListRequest(
                       project='my-project', region='region-1'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestTwoRegions(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.regionTargetHttpsProxies, 'List',
                   self.messages.ComputeRegionTargetHttpsProxiesListRequest(
                       project='my-project', region='region-1')),
                  (self._compute_api.regionTargetHttpsProxies, 'List',
                   self.messages.ComputeRegionTargetHttpsProxiesListRequest(
                       project='my-project', region='region-2'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)


if __name__ == '__main__':
  test_case.main()
