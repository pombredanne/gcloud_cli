# Copyright 2017 Google Inc. All Rights Reserved.
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

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml.vision import base as vision_base


@parameterized.named_parameters(
    ('Alpha', base.ReleaseTrack.ALPHA),
    ('Beta', base.ReleaseTrack.BETA),
    ('GA', base.ReleaseTrack.GA))
class DetectLogosTest(vision_base.MlVisionTestBase):

  def testDetectLogos_Success(self, track):
    """Test `gcloud vision detect-logos` runs & displays correctly."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectEntityAnnotationRequest(
        path_to_image,
        self.messages.Feature.TypeValueValuesEnum.LOGO_DETECTION,
        'logoAnnotations',
        results=['Google', 'Alphabet'])
    self.Run('ml vision detect-logos {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "logoAnnotations": [
                {
                  "confidence": 0.5,
                  "description": "Google"
                },
                {
                  "confidence": 0.5,
                  "description": "Alphabet"
                }
              ]
            }
          ]
        }
    """))

  def testDetectLogos_LocalPath(self, track):
    """Test `gcloud vision detect-landmarks` with a local image path."""
    self.track = track
    tempdir = self.CreateTempDir()
    path_to_image = self.Touch(tempdir, name='imagefile', contents='image')
    self._ExpectEntityAnnotationRequest(
        None,
        self.messages.Feature.TypeValueValuesEnum.LOGO_DETECTION,
        'logoAnnotations',
        results=['Google', 'Alphabet'],
        contents=bytes('image')
    )
    self.Run('ml vision detect-logos {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "logoAnnotations": [
                {
                  "confidence": 0.5,
                  "description": "Google"
                },
                {
                  "confidence": 0.5,
                  "description": "Alphabet"
                }
              ]
            }
          ]
        }
    """))

  def testDetectLandmarks_MaxResults(self, track):
    """Test `gcloud vision detect-landmarks` with --max-results flag."""
    self.track = track
    path_to_image = 'https://example.com/fake-file'
    self._ExpectEntityAnnotationRequest(
        path_to_image,
        self.messages.Feature.TypeValueValuesEnum.LOGO_DETECTION,
        'logoAnnotations',
        max_results=4,
        results=['Google', 'Alphabet'])
    self.Run('ml vision detect-logos {path} '
             '--max-results 4'.format(path=path_to_image))

  def testDetectLogos_Error(self, track):
    """Test `gcloud vision detect-landmarks` when result contains an error."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectEntityAnnotationRequest(
        path_to_image,
        self.messages.Feature.TypeValueValuesEnum.LOGO_DETECTION,
        'logoAnnotations',
        error_message='Not found.')
    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'Code: [400] Message: [Not found.]'):
      self.Run('ml vision detect-logos {path}'.format(path=path_to_image))


if __name__ == '__main__':
  test_case.main()