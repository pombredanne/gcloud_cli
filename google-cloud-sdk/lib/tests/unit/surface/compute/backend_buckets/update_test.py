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
"""Tests for the backend buckets update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.backend_buckets import test_resources


class BackendBucketUpdateGaTest(test_base.BaseTest):

  def _GetApiName(self, release_track):
    """Returns the API name for the specified release track."""
    if release_track == calliope_base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif release_track == calliope_base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  def _SetUp(self, release_track):
    """Setup common test components.

    Args:
      release_track: Release track the test is targeting.
    """
    self.SelectApi(self._GetApiName(release_track))
    self.track = release_track

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)
    self._backend_buckets = test_resources.BACKEND_BUCKETS

  def RunUpdate(self, command):
    """Runs the compute backend-buckets update command with the arguments."""
    self.Run('compute backend-buckets update ' + command)

  def CheckRequestMadeWithCdnPolicy(self, expected_cdn_policy):
    """Verifies the request was made with the expected CDN policy."""
    messages = self.messages
    self.CheckRequests([(self.compute.backendBuckets, 'Get',
                         messages.ComputeBackendBucketsGetRequest(
                             backendBucket='backend-bucket-2-enable-cdn-true',
                             project='my-project'))],
                       [(self.compute.backendBuckets, 'Patch',
                         messages.ComputeBackendBucketsPatchRequest(
                             backendBucket='backend-bucket-2-enable-cdn-true',
                             backendBucketResource=messages.BackendBucket(
                                 bucketName='gcs-bucket-2',
                                 cdnPolicy=expected_cdn_policy,
                                 description='my other backend bucket',
                                 enableCdn=True,
                                 name='backend-bucket-2-enable-cdn-true',
                                 selfLink=(self.compute_uri + '/projects/'
                                           'my-project/global/backendBuckets/'
                                           'backend-bucket-2-enable-cdn-true')),
                             project='my-project'))])

  def testWithNoFlags(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.RunUpdate("""
          backend-bucket-1-enable-cdn-false
          """)

    self.CheckRequests()

  def testWithNewDescription(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_buckets[0]],
        [],
    ])

    self.RunUpdate("""
        backend-bucket-1-enable-cdn-false
          --description "my new description"
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Get',
          messages.ComputeBackendBucketsGetRequest(
              backendBucket='backend-bucket-1-enable-cdn-false',
              project='my-project'))],
        [(self.compute.backendBuckets,
          'Patch',
          messages.ComputeBackendBucketsPatchRequest(
              backendBucket='backend-bucket-1-enable-cdn-false',
              backendBucketResource=messages.BackendBucket(
                  bucketName='gcs-bucket-1',
                  description='my new description',
                  enableCdn=False,
                  name='backend-bucket-1-enable-cdn-false',
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendBuckets/'
                            'backend-bucket-1-enable-cdn-false')),
              project='my-project'))])

  def testWithDescriptionRemoval(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_buckets[0]],
        [],
    ])

    self.RunUpdate("""
        backend-bucket-1-enable-cdn-false
          --description ""
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Get',
          messages.ComputeBackendBucketsGetRequest(
              backendBucket='backend-bucket-1-enable-cdn-false',
              project='my-project'))],
        [(self.compute.backendBuckets,
          'Patch',
          messages.ComputeBackendBucketsPatchRequest(
              backendBucket='backend-bucket-1-enable-cdn-false',
              backendBucketResource=messages.BackendBucket(
                  bucketName='gcs-bucket-1',
                  description='',
                  enableCdn=False,
                  name='backend-bucket-1-enable-cdn-false',
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendBuckets/'
                            'backend-bucket-1-enable-cdn-false')),
              project='my-project'))])

  def testWithBucketName(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_buckets[0]],

        [],
    ])

    self.RunUpdate("""
        backend-bucket-1-enable-cdn-false
          --gcs-bucket-name new-gcs-bucket
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Get',
          messages.ComputeBackendBucketsGetRequest(
              backendBucket='backend-bucket-1-enable-cdn-false',
              project='my-project'))],
        [(self.compute.backendBuckets,
          'Patch',
          messages.ComputeBackendBucketsPatchRequest(
              backendBucket='backend-bucket-1-enable-cdn-false',
              backendBucketResource=messages.BackendBucket(
                  bucketName='new-gcs-bucket',
                  description='my backend bucket',
                  enableCdn=False,
                  name='backend-bucket-1-enable-cdn-false',
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendBuckets/'
                            'backend-bucket-1-enable-cdn-false')),
              project='my-project'))])

  def testWithEmptyBucketNameMakesNoChanges(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_buckets[0]],
        [],
    ])

    self.RunUpdate("""
        backend-bucket-1-enable-cdn-false
          --gcs-bucket-name ''
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Get',
          messages.ComputeBackendBucketsGetRequest(
              backendBucket='backend-bucket-1-enable-cdn-false',
              project='my-project'))])

  def testWithEnableCdnTrue(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_buckets[0]],
        [],
    ])

    self.RunUpdate("""
        backend-bucket-1-enable-cdn-false
          --enable-cdn
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Get',
          messages.ComputeBackendBucketsGetRequest(
              backendBucket='backend-bucket-1-enable-cdn-false',
              project='my-project'))],
        [(self.compute.backendBuckets,
          'Patch',
          messages.ComputeBackendBucketsPatchRequest(
              backendBucket='backend-bucket-1-enable-cdn-false',
              backendBucketResource=messages.BackendBucket(
                  bucketName='gcs-bucket-1',
                  description='my backend bucket',
                  enableCdn=True,
                  name='backend-bucket-1-enable-cdn-false',
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendBuckets/'
                            'backend-bucket-1-enable-cdn-false')),
              project='my-project'))])

  def testWithEnableCdnFalse(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_buckets[1]],
        [],
    ])

    self.RunUpdate("""
        backend-bucket-2-enable-cdn-true
          --no-enable-cdn
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Get',
          messages.ComputeBackendBucketsGetRequest(
              backendBucket='backend-bucket-2-enable-cdn-true',
              project='my-project'))],
        [(self.compute.backendBuckets,
          'Patch',
          messages.ComputeBackendBucketsPatchRequest(
              backendBucket='backend-bucket-2-enable-cdn-true',
              backendBucketResource=messages.BackendBucket(
                  bucketName='gcs-bucket-2',
                  description='my other backend bucket',
                  enableCdn=False,
                  name='backend-bucket-2-enable-cdn-true',
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendBuckets/'
                            'backend-bucket-2-enable-cdn-true')),
              project='my-project'))])

  def testSetValidCacheMaxAge(self):
    """Tests updating backend bucket with a valid cache max age."""
    self.make_requests.side_effect = iter([
        [self._backend_buckets[1]],
        [],
    ])
    self.RunUpdate(
        'backend-bucket-2-enable-cdn-true --signed-url-cache-max-age 456789')
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendBucketCdnPolicy(signedUrlCacheMaxAgeSec=456789))

  def testUpdateWithCacheMaxAgeZero(self):
    """Tests updating backend bucket with a cache max age of 0."""
    self.make_requests.side_effect = iter([
        [self._backend_buckets[1]],
        [],
    ])
    self.RunUpdate(
        'backend-bucket-2-enable-cdn-true --signed-url-cache-max-age 0')
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendBucketCdnPolicy(signedUrlCacheMaxAgeSec=0))

  def testUpdateWithCacheMaxAgeSeconds(self):
    """Tests updating backend bucket with a cache max age in seconds."""
    self.make_requests.side_effect = iter([
        [self._backend_buckets[1]],
        [],
    ])
    self.RunUpdate(
        'backend-bucket-2-enable-cdn-true --signed-url-cache-max-age 7890s')
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendBucketCdnPolicy(signedUrlCacheMaxAgeSec=7890))

  def testUpdateWithCacheMaxAgeMinutes(self):
    """Tests updating backend bucket with a cache max age in minutes."""
    self.make_requests.side_effect = iter([
        [self._backend_buckets[1]],
        [],
    ])
    self.RunUpdate(
        'backend-bucket-2-enable-cdn-true --signed-url-cache-max-age 234m')
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendBucketCdnPolicy(signedUrlCacheMaxAgeSec=234 * 60))

  def testUpdateWithCacheMaxAgeHours(self):
    """Tests updating backend bucket with a cache max age in hours."""
    self.make_requests.side_effect = iter([
        [self._backend_buckets[1]],
        [],
    ])
    self.RunUpdate(
        'backend-bucket-2-enable-cdn-true --signed-url-cache-max-age 38h')
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendBucketCdnPolicy(
            signedUrlCacheMaxAgeSec=38 * 60 * 60))

  def testUpdateWithCacheMaxAgeDays(self):
    """Tests updating backend bucket with a cache max age in days."""
    self.make_requests.side_effect = iter([
        [self._backend_buckets[1]],
        [],
    ])
    self.RunUpdate(
        'backend-bucket-2-enable-cdn-true --signed-url-cache-max-age 99d')
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendBucketCdnPolicy(
            signedUrlCacheMaxAgeSec=99 * 24 * 60 * 60))

  def testSetInvalidCacheMaxAge(self):
    """Tests updating backend bucket with an invalid cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        "argument --signed-url-cache-max-age: Failed to parse duration: "
        "Duration unit 'invalid-value' must be preceded by a number"):
      self.RunUpdate(
          'backend-bucket-2-enable-cdn-true --signed-url-cache-max-age '
          'invalid-value')

  def testSetCacheMaxAgeNegative(self):
    """Tests updating backend bucket with a negative cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        'argument --signed-url-cache-max-age: value must be greater than or '
        'equal to 0; received: -1'):
      self.RunUpdate(
          'backend-bucket-2-enable-cdn-true --signed-url-cache-max-age -1')


class BackendBucketUpdateBetaTest(BackendBucketUpdateGaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)
    self._backend_buckets = test_resources.BACKEND_BUCKETS_BETA


class BackendBucketUpdateAlphaTest(BackendBucketUpdateBetaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)
    self._backend_buckets = test_resources.BACKEND_BUCKETS_ALPHA


if __name__ == '__main__':
  test_case.main()
