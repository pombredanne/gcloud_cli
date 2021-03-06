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

"""beta ml vision tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml.vision import base as vision_base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA, 'builtin/stable'),
    ('Beta', calliope_base.ReleaseTrack.BETA, 'builtin/stable'),
    ('GA', calliope_base.ReleaseTrack.GA, None))
class DetectLabelsCommonTest(vision_base.MlVisionTestBase):

  def testDetectLabels_Success(self, track, model):
    """Test `gcloud ml vision detect-labels` runs and outputs correctly."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectEntityAnnotationRequest(
        path_to_image,
        self.messages.Feature.TypeValueValuesEnum.LABEL_DETECTION,
        'labelAnnotations',
        results=['cat', 'dog'],
        model=model)
    self.Run('ml vision detect-labels {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "labelAnnotations": [
                {
                  "confidence": 0.5,
                  "description": "cat"
                },
                {
                  "confidence": 0.5,
                  "description": "dog"
                }
              ]
            }
          ]
        }
    """))

  def testDetectLabels_LocalPath(self, track, model):
    """Test `gcloud ml vision detect-labels` with a local image path."""
    self.track = track
    tempdir = self.CreateTempDir()
    path_to_image = self.Touch(tempdir, name='imagefile', contents='image')
    self._ExpectEntityAnnotationRequest(
        None,
        self.messages.Feature.TypeValueValuesEnum.LABEL_DETECTION,
        'labelAnnotations',
        results=['cat', 'dog'],
        contents=b'image',
        model=model)
    self.Run('ml vision detect-labels {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "labelAnnotations": [
                {
                  "confidence": 0.5,
                  "description": "cat"
                },
                {
                  "confidence": 0.5,
                  "description": "dog"
                }
              ]
            }
          ]
        }
    """))

  def testDetectLabels_MaxResults(self, track, model):
    """Test `gcloud ml vision detect-labels` with --max-results specified."""
    self.track = track
    path_to_image = 'https://fake-bucket/fake-file'
    self._ExpectEntityAnnotationRequest(
        path_to_image,
        self.messages.Feature.TypeValueValuesEnum.LABEL_DETECTION,
        'labelAnnotations',
        max_results=3,
        results=['cat', 'dog'],
        model=model)
    self.Run('ml vision detect-labels {path} '
             '--max-results 3'.format(path=path_to_image))

  def testDetectLabels_Error(self, track, model):
    """Test `gcloud ml vision detect-labels` with an error response."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectEntityAnnotationRequest(
        path_to_image,
        self.messages.Feature.TypeValueValuesEnum.LABEL_DETECTION,
        'labelAnnotations',
        error_message='Not found.',
        model=model)
    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'Code: [400] Message: [Not found.]'):
      self.Run('ml vision detect-labels {path}'.format(path=path_to_image))


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA))
class DetectLabelsAlphaBetaTest(vision_base.MlVisionTestBase):

  def testDetectLabels_ModelVersion(self, track):
    self.track = track
    path_to_image = 'https://fake-bucket/fake-file'
    self._ExpectEntityAnnotationRequest(
        path_to_image,
        self.messages.Feature.TypeValueValuesEnum.LABEL_DETECTION,
        'labelAnnotations',
        results=['cat', 'dog'],
        model='builtin/latest')
    self.Run('ml vision detect-labels {path} '
             '--model-version builtin/latest'.format(path=path_to_image))


if __name__ == '__main__':
  test_case.main()
