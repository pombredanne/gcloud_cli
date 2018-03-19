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

from apitools.base.py import encoding
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.surface.ml.vision import base as vision_base

import httplib2


@parameterized.named_parameters(
    ('Alpha', base.ReleaseTrack.ALPHA),
    ('Beta', base.ReleaseTrack.BETA),
    ('GA', base.ReleaseTrack.GA))
class DetectDocumentTest(vision_base.MlVisionTestBase):

  def _ExpectDetectDocumentRequest(self, image_path, text=None,
                                   error_message=None, contents=None,
                                   language_hints=None):
    """Build expected calls to the API for detect-document.

    Args:
      image_path: str, the image path given to command.
      text: str, the text to return in a successful result (if any).
      error_message: str, the error message expected from the API (if any).
      contents: the content field of the Image message to be expected (if any).
          Alternative to image_path.
      language_hints: [str], the list of language hints in the context to be
          expected (if any).
    """
    ftype = self.messages.Feature.TypeValueValuesEnum.DOCUMENT_TEXT_DETECTION
    image = self.messages.Image()
    if image_path:
      image.source = self.messages.ImageSource(imageUri=image_path)
    if contents:
      image.content = contents
    request = self.messages.BatchAnnotateImagesRequest(
        requests=[self.messages.AnnotateImageRequest(
            features=[self.messages.Feature(type=ftype)],
            image=image)])
    if language_hints:
      request.requests[0].imageContext = self.messages.ImageContext(
          languageHints=language_hints)
    responses = []
    if text:
      responses.append(
          self.messages.AnnotateImageResponse(
              fullTextAnnotation=(
                  self.messages.TextAnnotation(
                      pages=[self.messages.Page()],
                      text=text))))
    if error_message:
      response = encoding.PyValueToMessage(
          self.messages.AnnotateImageResponse,
          {'error': {'code': 400,
                     'details': [],
                     'message': error_message}})
      responses.append(response)
    response = self.messages.BatchAnnotateImagesResponse(responses=responses)
    self.client.images.Annotate.Expect(request,
                                       response=response)

  def testDetectDocument_Success(self, track):
    """Test `gcloud ml vision detect-document` with a remote path."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectDetectDocumentRequest(path_to_image, text='Detected text.')
    self.Run('ml vision detect-document {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "fullTextAnnotation": {
                "pages": [
                  {}
                ],
                "text": "Detected text."
              }
            }
          ]
        }
    """))

  def testDetectDocument_LocalPath(self, track):
    """Test `gcloud ml vision detect-document` with a local path."""
    self.track = track
    tempdir = self.CreateTempDir()
    path_to_image = self.Touch(tempdir, name='imagefile', contents='image')
    self._ExpectDetectDocumentRequest(None, text='Detected text.',
                                      contents=bytes('image'))
    self.Run('ml vision detect-document {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "fullTextAnnotation": {
                "pages": [
                  {}
                ],
                "text": "Detected text."
              }
            }
          ]
        }
    """))

  def testDetectDocument_LanguageHints(self, track):
    """Test `gcloud ml vision detect-document` when language hints are given."""
    self.track = track
    path_to_image = 'gs://bucket/object'
    self._ExpectDetectDocumentRequest(path_to_image, text='Detected text.',
                                      language_hints=['ja', 'ko'])
    self.Run('ml vision detect-document {path} --language-hints ja,ko'.format(
        path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "fullTextAnnotation": {
                "pages": [
                  {}
                ],
                "text": "Detected text."
              }
            }
          ]
        }
    """))

  def testDetectDocument_Error(self, track):
    """Test `gcloud ml vision detect-document` when an error is returned."""
    self.track = track
    path_to_image = 'https://example.com/fake-file'
    self._ExpectDetectDocumentRequest(path_to_image,
                                      error_message='Not found.')
    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'Code: [400] Message: [Not found.]'):
      self.Run('ml vision detect-document {path}'.format(path=path_to_image))


class QuotaHeaderTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                      parameterized.TestCase):

  def SetUp(self):
    properties.VALUES.core.project.Set('foo')
    self.request_mock = self.StartObjectPatch(
        httplib2.Http, 'request',
        return_value=(httplib2.Response({'status': 200}), ''))

  @parameterized.parameters(
      (None, 'alpha', 'foo'),
      (None, 'beta', 'foo'),
      (properties.VALUES.billing.LEGACY, 'alpha', None),
      (properties.VALUES.billing.LEGACY, 'beta', None),
      (properties.VALUES.billing.CURRENT_PROJECT, 'alpha', 'foo'),
      (properties.VALUES.billing.CURRENT_PROJECT, 'beta', 'foo'),
      ('bar', 'alpha', 'bar'),
      ('bar', 'beta', 'bar'),
  )
  def testQuotaHeader(self, prop_value, track, header_value):
    properties.VALUES.billing.quota_project.Set(prop_value)
    self.Run(track + ' ml vision detect-document --project=foo {path}'
             .format(path='gs://fake-bucket/fake-file'))
    header = self.request_mock.call_args[0][3].get('X-Goog-User-Project', None)
    self.assertEquals(header, header_value)


if __name__ == '__main__':
  cli_test_base.main()