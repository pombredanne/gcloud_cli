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
"""Tests for the url-maps delete subcommand."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

MESSAGES = apis.GetMessagesModule('compute', 'v1')


class UrlMapsDeleteTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def testWithSingleUrlMap(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute url-maps delete map-1
        """)

    self.CheckRequests(
        [(self.compute_v1.urlMaps,
          'Delete',
          MESSAGES.ComputeUrlMapsDeleteRequest(
              urlMap='map-1',
              project='my-project'))],
    )

  def testWithManyUrlMaps(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute url-maps delete map-1 map-2 map-3
        """)

    self.CheckRequests(
        [(self.compute_v1.urlMaps,
          'Delete',
          MESSAGES.ComputeUrlMapsDeleteRequest(
              urlMap='map-1',
              project='my-project')),

         (self.compute_v1.urlMaps,
          'Delete',
          MESSAGES.ComputeUrlMapsDeleteRequest(
              urlMap='map-2',
              project='my-project')),

         (self.compute_v1.urlMaps,
          'Delete',
          MESSAGES.ComputeUrlMapsDeleteRequest(
              urlMap='map-3',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute url-maps delete map-1 map-2 map-3
        """)

    self.CheckRequests(
        [(self.compute_v1.urlMaps,
          'Delete',
          MESSAGES.ComputeUrlMapsDeleteRequest(
              urlMap='map-1',
              project='my-project')),

         (self.compute_v1.urlMaps,
          'Delete',
          MESSAGES.ComputeUrlMapsDeleteRequest(
              urlMap='map-2',
              project='my-project')),

         (self.compute_v1.urlMaps,
          'Delete',
          MESSAGES.ComputeUrlMapsDeleteRequest(
              urlMap='map-3',
              project='my-project'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute url-maps delete map-1 map-2 map-3
          """)

    self.CheckRequests()

  def testDeleteCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.URL_MAPS)
    self.RunCompletion(
        'compute url-maps delete ',
        [
            'url-map-3',
            'url-map-4',
            'url-map-1',
            'url-map-2',
        ])

if __name__ == '__main__':
  test_case.main()