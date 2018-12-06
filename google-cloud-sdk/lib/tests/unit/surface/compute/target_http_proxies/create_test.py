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
"""Tests for the target-http-proxies create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetHTTPProxiesCreateTest(test_base.BaseTest):

  def SetUp(self):
    self._api = 'v1'
    self.SelectApi(self._api)
    self._target_http_proxies_api = self.compute.targetHttpProxies

  def RunCreate(self, command):
    self.Run('compute target-http-proxies create ' + command)

  def testSimpleCase(self):
    self.make_requests.side_effect = [[
        self.messages.TargetHttpProxy(
            name='my-proxy',
            urlMap=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/global/urlMaps/my-map'.format(self._api)))
    ]]

    self.RunCreate("""
        my-proxy
          --description "My target HTTP proxy"
          --url-map my-map
        """)

    self.CheckRequests(
        [(self._target_http_proxies_api, 'Insert',
          self.messages.ComputeTargetHttpProxiesInsertRequest(
              project='my-project',
              targetHttpProxy=self.messages.TargetHttpProxy(
                  description='My target HTTP proxy',
                  name='my-proxy',
                  urlMap=('https://www.googleapis.com/compute/{0}/projects/'
                          'my-project/global/urlMaps/my-map'.format(
                              self._api)))))],)

    self.AssertOutputEquals("""\
      NAME      URL_MAP
      my-proxy  my-map
      """, normalize_space=True)

  def testUriSupport(self):
    self.RunCreate("""
          https://www.googleapis.com/compute/{0}/projects/my-project/global/targetHttpProxies/my-proxy
          --url-map https://www.googleapis.com/compute/{0}/projects/my-project/global/urlMaps/my-map
        """.format(self._api))

    self.CheckRequests(
        [(self._target_http_proxies_api, 'Insert',
          self.messages.ComputeTargetHttpProxiesInsertRequest(
              project='my-project',
              targetHttpProxy=self.messages.TargetHttpProxy(
                  name='my-proxy',
                  urlMap=('https://www.googleapis.com/compute/{0}/projects/'
                          'my-project/global/urlMaps/my-map'.format(
                              self._api)))))],)

  def testWithoutURLMap(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --url-map: Must be specified.'):
      self.RunCreate('my-proxy')

    self.CheckRequests()


class TargetHTTPProxiesCreateAlphaTest(TargetHTTPProxiesCreateTest):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_http_proxies_api = self.compute_alpha.targetHttpProxies

  def RunCreate(self, command):
    self.Run('alpha compute target-http-proxies create --global ' + command)


class RegionTargetHTTPProxiesCreateTest(test_base.BaseTest):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_http_proxies_api = self.compute_alpha.regionTargetHttpProxies

  def RunCreate(self, command):
    self.Run('alpha compute target-http-proxies create --region us-west-1 ' +
             command)

  def testSimpleCase(self):
    self.make_requests.side_effect = [[
        self.messages.TargetHttpProxy(
            name='my-proxy',
            urlMap=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/regions/us-west-1/urlMaps/my-map'.format(
                        self._api)))
    ]]

    self.RunCreate("""
        my-proxy
          --description "My target HTTP proxy"
          --url-map my-map
        """)

    self.CheckRequests(
        [(self._target_http_proxies_api, 'Insert',
          self.messages.ComputeRegionTargetHttpProxiesInsertRequest(
              project='my-project',
              region='us-west-1',
              targetHttpProxy=self.messages.TargetHttpProxy(
                  description='My target HTTP proxy',
                  name='my-proxy',
                  urlMap=('https://www.googleapis.com/compute/%(api)s/projects/'
                          'my-project/regions/us-west-1/urlMaps/my-map' % {
                              'api': self._api
                          }))))],)

    self.AssertOutputEquals(
        """\
      NAME      URL_MAP
      my-proxy  my-map
      """,
        normalize_space=True)

  def testUriSupport(self):
    self.RunCreate("""
          https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/targetHttpProxies/my-proxy
          --url-map https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/urlMaps/my-map
        """ % {'api': self._api})

    self.CheckRequests(
        [(self._target_http_proxies_api, 'Insert',
          self.messages.ComputeRegionTargetHttpProxiesInsertRequest(
              project='my-project',
              region='us-west-1',
              targetHttpProxy=self.messages.TargetHttpProxy(
                  name='my-proxy',
                  urlMap=('https://www.googleapis.com/compute/%(api)s/projects/'
                          'my-project/regions/us-west-1/urlMaps/my-map' % {
                              'api': self._api
                          }))))],)

  def testWithoutURLMap(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --url-map: Must be specified.'):
      self.RunCreate('my-proxy')

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
