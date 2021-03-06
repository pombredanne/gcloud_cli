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

"""Tests for gcloud ml language analyze-sentiments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.ml.language import util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.ml.language import base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA))
class AnalyzeSentimentTest(base.MlLanguageTestBase):
  """Tests for gcloud ml language analyze-sentiment."""

  def _CreateResponse(self, sentences, language):
    sentence_responses = []
    for s in sentences:
      sentence_responses.append(
          {
              'sentiment': {
                  'magnitude': 0.8,
                  'score': 0.8
              },
              'text': {
                  'beginOffset': 0,
                  'content': s
              }
          }
      )
    sentiment = {
        'documentSentiment': {
            'magnitude': 0.8,
            'score': 0.8
        },
        'sentences': sentence_responses,
        'language': language
    }
    return sentiment

  def _ExpectAnalyzeSentimentRequest(self, gcs_content_uri=None, content=None,
                                     encoding_type=None, content_type=None,
                                     request_language=None,
                                     response_language='eng', sentences=None,
                                     error=None):
    """Build expected requests and responses for the Language client.

    Args:
      gcs_content_uri: str, the expected URI for the document in the request,
          if any.
      content: bytes, the expected content of the document in the request,
          if any.
      encoding_type: str, the expected encoding type of the request.
      content_type: str, the expected document type in the request.
      request_language: str, the expected language of the document in the
          request.
      response_language: str, the expected language of the response.
      sentences: [str], list of sentences in expected response.
      error: HttpError to be expected from the client, if any.
    """
    if sentences:
      response = self._CreateResponse(sentences, response_language)
    else:
      response = None
    annotate_request = self.messages.AnalyzeSentimentRequest(
        document=self.messages.Document(
            gcsContentUri=gcs_content_uri,
            content=content,
            type=content_type,
            language=request_language),
        encodingType=encoding_type)
    if response:
      response = encoding.PyValueToMessage(
          self.messages.AnalyzeSentimentResponse,
          response
      )
      self.client.documents.AnalyzeSentiment.Expect(annotate_request, response)
    if error:
      self.client.documents.AnalyzeSentiment.Expect(annotate_request,
                                                    exception=error)

  def testBasicResult(self, track):
    """Test that results return correctly."""
    self.SetTrack(track)
    self._ExpectAnalyzeSentimentRequest(
        content='I love puppies.',
        sentences=['I love puppies.'],
        encoding_type=self.sentiment_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT
    )
    expected = self.messages.AnalyzeSentimentResponse(
        documentSentiment=self.messages.Sentiment(
            magnitude=0.8,
            score=0.8),
        language='eng',
        sentences=[self.messages.Sentence(
            sentiment=self.messages.Sentiment(
                magnitude=0.8,
                score=0.8),
            text=self.messages.TextSpan(
                beginOffset=0,
                content='I love puppies.')
        )])
    result = self.Run('ml language analyze-sentiment --content '
                      '"I love puppies."')
    self.assertEqual(expected, result)

  def testBasicOutput(self, track):
    """Test that results print as expected."""
    self.SetTrack(track)
    self._ExpectAnalyzeSentimentRequest(
        content='I love puppies.',
        sentences=['I love puppies.'],
        encoding_type=self.sentiment_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT
    )
    self.Run('ml language analyze-sentiment --content "I love puppies."')
    self.AssertOutputEquals(textwrap.dedent("""\
    {
      "documentSentiment": {
        "magnitude": 0.8,
        "score": 0.8
      },
      "language": "eng",
      "sentences": [
        {
          "sentiment": {
            "magnitude": 0.8,
            "score": 0.8
          },
          "text": {
            "beginOffset": 0,
            "content": "I love puppies."
          }
        }
      ]
    }
    """))

  def testWithContentFile(self, track):
    """Test result when a content file is given."""
    self.SetTrack(track)
    self._ExpectAnalyzeSentimentRequest(
        content='Hello world',
        sentences=['Hello world'],
        encoding_type=self.sentiment_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT
    )
    self.Run(
        'ml language analyze-sentiment --content-file {}'.format(
            self.test_file))

  def testWithGCSContentFile(self, track):
    """Test that a GCS URL is sent to the service."""
    self.SetTrack(track)
    self._ExpectAnalyzeSentimentRequest(
        gcs_content_uri='gs://bucket/file',
        sentences=['I love puppies.'],
        encoding_type=self.sentiment_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT
    )
    self.Run('ml language analyze-sentiment --content-file gs://bucket/file')

  def testWithContentType(self, track):
    """Test result with --content-type flag."""
    self.SetTrack(track)
    self._ExpectAnalyzeSentimentRequest(
        content='<p>I love puppies.</p>',
        sentences=['I love puppies.'],
        encoding_type=self.sentiment_encoding_enum.UTF8,
        content_type=self.content_enum.HTML
    )
    self.Run(
        'ml language analyze-sentiment --content "<p>I love puppies.</p>" '
        '--content-type HTML')

  def testWithEncodingType(self, track):
    """Test result with --encoding-type flag."""
    self.SetTrack(track)
    self._ExpectAnalyzeSentimentRequest(
        content='I love puppies.',
        sentences=['I love puppies.'],
        encoding_type=self.sentiment_encoding_enum.UTF32,
        content_type=self.content_enum.PLAIN_TEXT
    )
    self.Run(
        'ml language analyze-sentiment --content "I love puppies." '
        '--encoding-type UTF32')

  def testWithLanguage(self, track):
    """Test result with --language flag."""
    self.SetTrack(track)
    self._ExpectAnalyzeSentimentRequest(
        content='I love puppies.',
        sentences=['I love puppies.'],
        encoding_type=self.sentiment_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT,
        request_language='en',
        response_language='en'
    )
    self.Run(
        'ml language analyze-sentiment --content "I love puppies." '
        '--language en')

  def testWithAllFlags(self, track):
    """Test result with --language, --content-type, --encoding-type flags."""
    self.SetTrack(track)
    self._ExpectAnalyzeSentimentRequest(
        content='<p>I love puppies.</p>',
        sentences=['I love puppies.'],
        encoding_type=self.sentiment_encoding_enum.UTF32,
        content_type=self.content_enum.HTML,
        request_language='en',
        response_language='en'
    )
    self.Run(
        'ml language analyze-sentiment --content "<p>I love puppies.</p>" '
        '--language en --content-type HTML --encoding-type UTF32')

  def testWithNonGCSUrl(self, track):
    """Assert ContentFileError for a non-GCS URL in --content-file."""
    self.SetTrack(track)
    non_gcs_url = 'https://bucket/file'
    with self.assertRaises(util.ContentFileError):
      self.Run('ml language analyze-sentiment --content-file {}'.format(
          non_gcs_url))
    self.AssertErrContains(
        'Could not find --content-file [https://bucket/file]. Content file '
        'must be a path to a local file or a Google Cloud Storage URL '
        '(format: `gs://bucket_name/object_name`)')

  def testWithEmptyContent(self, track):
    """Assert ContentError is raised if empty --content is given."""
    self.SetTrack(track)
    with self.assertRaises(util.ContentError):
      self.Run('ml language analyze-sentiment --content ""')
    self.AssertErrContains('The content provided is empty. Please provide '
                           'language content to analyze.')

  def testWithNonExistentFile(self, track):
    """Assert ContentFileError is raised for non-existent local file."""
    self.SetTrack(track)
    with self.assertRaises(util.ContentFileError):
      self.Run('ml language analyze-sentiment --content-file {}'.format(
          self.test_file + '-no-exist'))
    self.AssertErrContains(
        'Could not find --content-file [{}]. Content file '
        'must be a path to a local file or a Google Cloud Storage URL '
        '(format: `gs://bucket_name/object_name`)'.format(
            self.test_file + '-no-exist'))

  def testWithHttpError(self, track):
    """Assert HttpException is raised when API returns an error."""
    self.SetTrack(track)
    # These details do not show up in the error format string.
    details = [
        {'@type': 'type.googleapis.com/google.rpc.BadRequest',
         'fieldViolations': [
             {
                 'field': 'document.gcs_content_uri',
                 'description': 'Description of violation'
             }
         ]
        },
        {'@type': 'type.googleapis.com/google.rpc.DebugInfo',
         'detail': '[ORIGINAL ERROR] original error message'}
    ]
    error = http_error.MakeDetailedHttpError(details=details,
                                             message='The file does not exist.')
    self._ExpectAnalyzeSentimentRequest(
        gcs_content_uri='gs://fake/fake',
        encoding_type=self.sentiment_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT,
        error=error
    )
    with self.assertRaises(exceptions.HttpException):
      self.Run('ml language analyze-sentiment --content-file gs://fake/fake')
    self.AssertErrContains('The file does not exist.')


if __name__ == '__main__':
  test_case.main()
