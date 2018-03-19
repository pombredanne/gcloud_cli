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
"""gcloud ml speech recognize unit tests."""

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.ml.speech import exceptions as speech_exceptions
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.ml.speech import base as speech_base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA))
class RecognizeTest(speech_base.MlSpeechTestBase):
  """Class to test `gcloud ml speech recognize`."""

  def SetUp(self):
    self.short_file = self.Resource('tests', 'unit', 'api_lib', 'ml', 'speech',
                                    'testdata', 'sample.flac')

  def testBasicOutput(self, track):
    """Test recognize command basic output with default flag values."""
    self.track = track
    self._ExpectRecognizeRequest(uri='gs://bucket/object', language='en-US',
                                 sample_rate=None, max_alternatives=1,
                                 results=['Transcribed text'])
    expected = self.messages.RecognizeResponse(
        results=[self.messages.SpeechRecognitionResult(
            alternatives=[
                self.messages.SpeechRecognitionAlternative(
                    confidence=0.8, transcript='Transcribed text')])])
    actual = self.Run(
        'ml speech recognize gs://bucket/object --language-code en-US')
    self.assertEqual(expected, actual)
    self.assertEqual(json.loads(self.GetOutput()),
                     encoding.MessageToPyValue(expected))

  def testWithNoDefaults(self, track):
    """Test recognize command with no default flag values."""
    self.track = track
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object', language='es-ES', sample_rate=22000,
        max_alternatives=2, hints=['Bueno'], results=['Bueno', 'Buena'],
        encoding='OGG_OPUS', enable_word_time_offsets=True)
    expected = self.messages.RecognizeResponse(
        results=[self.messages.SpeechRecognitionResult(
            alternatives=[
                self.messages.SpeechRecognitionAlternative(
                    confidence=0.8, transcript='Bueno'),
                self.messages.SpeechRecognitionAlternative(
                    confidence=0.8, transcript='Buena')])])
    actual = self.Run(
        'ml speech recognize gs://bucket/object --language-code es-ES '
        '--sample-rate 22000 --max-alternatives 2 --hints Bueno --encoding '
        'OGG_OPUS --include-word-time-offsets')
    self.assertEqual(expected, actual)

  def testWithLocalFile(self, track):
    """Test recognize command with local content."""
    self.track = track
    with open(self.short_file, 'rb') as audio_file:
      contents = audio_file.read()
    self._ExpectRecognizeRequest(content=contents, language='en-US',
                                 sample_rate=None, max_alternatives=1,
                                 results=['Transcribed text'])
    expected = self.messages.RecognizeResponse(
        results=[self.messages.SpeechRecognitionResult(
            alternatives=[
                self.messages.SpeechRecognitionAlternative(
                    confidence=0.8, transcript='Transcribed text')])])
    actual = self.Run(
        'ml speech recognize {} --language-code en-US'.format(self.short_file))
    self.assertEqual(expected, actual)

  def testRaisesError(self, track):
    """Test recognize command raises HttpException."""
    self.track = track
    error = http_error.MakeDetailedHttpError(code=400, message='Error message',
                                             details=self.sample_error_details)
    self._ExpectRecognizeRequest(uri='gs://bucket/object', language='en-US',
                                 sample_rate=None, max_alternatives=1,
                                 error=error)
    with self.assertRaisesRegexp(exceptions.HttpException,
                                 r'Error message'):
      self.Run('ml speech recognize gs://bucket/object --language-code en-US')

  def testMissingRequiredAudioFilePositional(self, track):
    self.track = track
    with self.AssertRaisesArgumentErrorMatches(
        'argument AUDIO: Must be specified.'):
      self.Run('ml speech recognize --language-code en-US')

  def testMissingRequiredLanguageFlag(self, track):
    self.track = track
    with self.AssertRaisesArgumentErrorMatches(
        '--language-code must be specified'):
      self.Run('ml speech recognize gs://bucket/object')

  def testInvalidFlagValues(self, track):
    """Test recognize command raises with invalid flag values."""
    self.track = track
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize gs://bucket/object --language-code en-US '
               '--max-alternatives notanumber')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize gs://bucket/object --language-code en-US '
               '--sample-rate notanumber')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize gs://bucket/object --language-code en-US '
               '--filter-profanity invalidvalue')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000 '
               '--encoding NOT_AN_ENCODING')

  def testAudioError(self, track):
    """Test recognize command raises AudioException with invalid audio."""
    self.track = track
    audio_path = self.short_file + 'x'
    with self.AssertRaisesExceptionMatches(speech_exceptions.AudioException,
                                           '[{}]'.format(audio_path)):
      self.Run(
          'ml speech recognize {} --language-code en-US'.format(audio_path))


if __name__ == '__main__':
  test_case.main()