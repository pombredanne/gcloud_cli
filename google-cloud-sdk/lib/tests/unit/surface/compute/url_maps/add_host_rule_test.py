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
"""Tests for the url-maps add-host-rule subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


_V1_URI_PREFIX = 'https://www.googleapis.com/compute/v1/projects/my-project/'
_BACKEND_SERVICES_URI_PREFIX = _V1_URI_PREFIX + 'global/backendServices/'


URL_MAP = messages.UrlMap(
    name='url-map-1',
    defaultService=_BACKEND_SERVICES_URI_PREFIX + 'default-service',
    hostRules=[
        messages.HostRule(
            hosts=['*.google.com', 'google.com'],
            pathMatcher='www'),
        messages.HostRule(
            hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
            pathMatcher='youtube'),
    ],
    pathMatchers=[
        messages.PathMatcher(
            name='www',
            defaultService=_BACKEND_SERVICES_URI_PREFIX + 'www-default',
            pathRules=[
                messages.PathRule(
                    paths=['/search', '/search/*'],
                    service=_BACKEND_SERVICES_URI_PREFIX + 'search'),
                messages.PathRule(
                    paths=['/search/ads', '/search/ads/*'],
                    service=_BACKEND_SERVICES_URI_PREFIX + 'ads'),
                messages.PathRule(
                    paths=['/images'],
                    service=_BACKEND_SERVICES_URI_PREFIX + 'images'),
            ]),
        messages.PathMatcher(
            name='youtube',
            defaultService=_BACKEND_SERVICES_URI_PREFIX + 'youtube-default',
            pathRules=[
                messages.PathRule(
                    paths=['/search', '/search/*'],
                    service=(_BACKEND_SERVICES_URI_PREFIX +
                             'youtube-search')),
                messages.PathRule(
                    paths=['/watch', '/view', '/preview'],
                    service=_BACKEND_SERVICES_URI_PREFIX + 'youtube-watch'),
            ]),
    ],
    tests=[
        messages.UrlMapTest(
            host='www.google.com',
            path='/search/ads/inline?q=flowers',
            service=_BACKEND_SERVICES_URI_PREFIX + 'ads'),
        messages.UrlMapTest(
            host='youtube.com',
            path='/watch/this',
            service=_BACKEND_SERVICES_URI_PREFIX + 'youtube-default'),
    ])


class UrlMapsAddHostRuleTest(test_base.BaseTest):

  def testAddHostRule(self):
    self.make_requests.side_effect = iter([
        [URL_MAP],
        [],
    ])

    self.Run("""
        compute url-maps add-host-rule url-map-1
          --description new
          --hosts a.b.com,c.d.com
          --path-matcher-name youtube
        """)

    expected_url_map = messages.UrlMap(
        name='url-map-1',
        defaultService=_BACKEND_SERVICES_URI_PREFIX + 'default-service',
        hostRules=[
            messages.HostRule(
                hosts=['*.google.com', 'google.com'],
                pathMatcher='www'),
            messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
            messages.HostRule(
                description='new',
                hosts=['a.b.com', 'c.d.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            messages.PathMatcher(
                name='www',
                defaultService=_BACKEND_SERVICES_URI_PREFIX + 'www-default',
                pathRules=[
                    messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=_BACKEND_SERVICES_URI_PREFIX + 'search'),
                    messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=_BACKEND_SERVICES_URI_PREFIX + 'ads'),
                    messages.PathRule(
                        paths=['/images'],
                        service=_BACKEND_SERVICES_URI_PREFIX + 'images'),
                ]),
            messages.PathMatcher(
                name='youtube',
                defaultService=_BACKEND_SERVICES_URI_PREFIX + 'youtube-default',
                pathRules=[
                    messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(_BACKEND_SERVICES_URI_PREFIX +
                                 'youtube-search')),
                    messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=_BACKEND_SERVICES_URI_PREFIX + 'youtube-watch'),
                ]),
        ],
        tests=[
            messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=_BACKEND_SERVICES_URI_PREFIX + 'ads'),
            messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=_BACKEND_SERVICES_URI_PREFIX + 'youtube-default'),
        ])

    self.CheckRequests(
        [(self.compute_v1.urlMaps,
          'Get',
          messages.ComputeUrlMapsGetRequest(
              urlMap='url-map-1',
              project='my-project'))],
        [(self.compute_v1.urlMaps,
          'Update',
          messages.ComputeUrlMapsUpdateRequest(
              urlMap='url-map-1',
              project='my-project',
              urlMapResource=expected_url_map))])

  def testUriSupport(self):
    self.make_requests.side_effect = iter([
        [URL_MAP],
        [],
    ])

    self.Run("""
        compute url-maps add-host-rule
          https://www.googleapis.com/compute/v1/projects/my-project/global/urlMaps/url-map-1
          --hosts a.b.com,c.d.com
          --path-matcher-name youtube
        """)

    expected_url_map = messages.UrlMap(
        name='url-map-1',
        defaultService=_BACKEND_SERVICES_URI_PREFIX + 'default-service',
        hostRules=[
            messages.HostRule(
                hosts=['*.google.com', 'google.com'],
                pathMatcher='www'),
            messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
            messages.HostRule(
                hosts=['a.b.com', 'c.d.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            messages.PathMatcher(
                name='www',
                defaultService=_BACKEND_SERVICES_URI_PREFIX + 'www-default',
                pathRules=[
                    messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=_BACKEND_SERVICES_URI_PREFIX + 'search'),
                    messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=_BACKEND_SERVICES_URI_PREFIX + 'ads'),
                    messages.PathRule(
                        paths=['/images'],
                        service=_BACKEND_SERVICES_URI_PREFIX + 'images'),
                ]),
            messages.PathMatcher(
                name='youtube',
                defaultService=_BACKEND_SERVICES_URI_PREFIX + 'youtube-default',
                pathRules=[
                    messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(_BACKEND_SERVICES_URI_PREFIX +
                                 'youtube-search')),
                    messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=_BACKEND_SERVICES_URI_PREFIX + 'youtube-watch'),
                ]),
        ],
        tests=[
            messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=_BACKEND_SERVICES_URI_PREFIX + 'ads'),
            messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=_BACKEND_SERVICES_URI_PREFIX + 'youtube-default'),
        ])

    self.CheckRequests(
        [(self.compute_v1.urlMaps,
          'Get',
          messages.ComputeUrlMapsGetRequest(
              urlMap='url-map-1',
              project='my-project'))],
        [(self.compute_v1.urlMaps,
          'Update',
          messages.ComputeUrlMapsUpdateRequest(
              urlMap='url-map-1',
              project='my-project',
              urlMapResource=expected_url_map))])

  def testHostsRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --hosts: Must be specified.'):
      self.Run("""
          compute url-maps add-host-rule url-map-1
            --description new
            --path-matcher-name youtube
          """)

    self.CheckRequests()

  def testPathMatcherRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --path-matcher-name: Must be specified.'):
      self.Run("""
          compute url-maps add-host-rule url-map-1
            --description new
            --hosts a.b.com,c.d.com
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
