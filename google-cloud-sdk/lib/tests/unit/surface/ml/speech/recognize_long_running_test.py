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
"""gcloud ml speech recognize-long-running unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.ml.speech import util
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.ml.speech import base as speech_base


LONG_RUNNING_RESPONSE = ('type.googleapis.com/google.cloud.speech.{version}.'
                         'LongRunningRecognizeResponse')


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA))
class RecognizeLongRunningTest(speech_base.MlSpeechTestBase):
  """Class to test `gcloud ml speech recognize-long-running`."""

  _VERSIONS_FOR_RELEASE_TRACKS = {
      calliope_base.ReleaseTrack.ALPHA: 'v1p1beta1',
      calliope_base.ReleaseTrack.BETA: 'v1p1beta1',
      calliope_base.ReleaseTrack.GA: 'v1'
  }

  def SetUp(self):
    self.long_file = self.Resource('tests', 'unit', 'command_lib', 'ml',
                                   'speech', 'testdata', 'sample.raw')

  def testBasicOutput_Async(self, track):
    """Test recognize-long-running command basic output with --async flag."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        encoding=None
    )
    expected = self.messages.Operation(name='12345')
    actual = self.Run(
        'ml speech recognize-long-running gs://bucket/object --language-code '
        'en-US --sample-rate 16000 --async'
    )
    self.assertEqual(expected, actual)
    self.assertEqual(json.loads(self.GetOutput()),
                     encoding.MessageToPyValue(expected))

  def testWithNoDefaults_Async(self, track):
    """Test recognize-long-running command with all flags set."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='es-ES',
        sample_rate=22000,
        max_alternatives=2,
        result='12345',
        hints=['Hola'],
        encoding='FLAC',
        enable_word_time_offsets=True,
    )
    expected = self.messages.Operation(name='12345')
    actual = self.Run(
        'ml speech recognize-long-running gs://bucket/object --language-code '
        'es-ES --sample-rate 22000 --max-alternatives 2 --hints Hola --async '
        '--encoding FLAC --include-word-time-offsets'
    )
    self.assertEqual(expected, actual)

  def testWithLocalFile_Async(self, track):
    """Test recognize-long-running command with local content."""
    self.SetUpForTrack(track)
    with open(self.long_file, 'rb') as audio_file:
      contents = audio_file.read()
    self._ExpectLongRunningRecognizeRequest(
        content=contents,
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        encoding=None
    )
    expected = self.messages.Operation(name='12345')
    actual = self.Run(
        'ml speech recognize-long-running {} --language-code en-US '
        '--sample-rate 16000 --async'.format(self.long_file))
    self.assertEqual(expected, actual)

  def testResults_Sync(self, track):
    """Test recognize-long-running command waits for operation results."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        hints=[],
        encoding=None
    )
    self._ExpectPollOperationRequests('12345', 3, results=['Hello world.'])
    expected = {
        '@type': LONG_RUNNING_RESPONSE.format(version=self.version),
        'results': [{'alternatives': [{'confidence': 0.8,
                                       'transcript': 'Hello world.'}]}]}
    self.Run('ml speech recognize-long-running gs://bucket/object '
             '--language-code en-US --sample-rate 16000')
    self.assertEqual(json.loads(self.GetOutput()), expected)

  def testWithNoDefaults_Sync(self, track):
    """Test recognize-long-running command with all flags set except --async."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='es-ES',
        sample_rate=22000,
        max_alternatives=2,
        result='12345',
        hints=['Hola.'],
        encoding=None,
        enable_word_time_offsets=True
    )
    self._ExpectPollOperationRequests('12345', 3, results=['Hola.'])
    expected = {
        '@type': LONG_RUNNING_RESPONSE.format(version=self.version),
        'results': [{'alternatives': [{'confidence': 0.8,
                                       'transcript': 'Hola.'}]}]}
    self.Run('ml speech recognize-long-running gs://bucket/object '
             '--language-code es-ES --sample-rate 22000 --hints Hola. '
             '--max-alternatives 2 --include-word-time-offsets')
    self.assertEqual(json.loads(self.GetOutput()), expected)

  def testWithLocalFile_Sync(self, track):
    """Test recognize-long-running command with local source (synchronous)."""
    self.SetUpForTrack(track)
    with open(self.long_file, 'rb') as audio_file:
      contents = audio_file.read()
    self._ExpectLongRunningRecognizeRequest(
        content=contents,
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        hints=[],
        encoding=None
    )
    self._ExpectPollOperationRequests('12345', 3, results=['Hello world.'])
    expected = {
        '@type': LONG_RUNNING_RESPONSE.format(version=self.version),
        'results': [{'alternatives': [{'confidence': 0.8,
                                       'transcript': 'Hello world.'}]}]}
    self.Run('ml speech recognize-long-running {} --language-code en-US '
             '--sample-rate 16000'.format(self.long_file))
    self.assertEqual(json.loads(self.GetOutput()), expected)

  def testRaisesError(self, track):
    """Test recognize-long-running command raises HttpException on error."""
    self.SetUpForTrack(track)
    error = http_error.MakeDetailedHttpError(code=400, message='Error message',
                                             details=self.sample_error_details)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        hints=[],
        encoding=None,
        error=error
    )
    with self.assertRaisesRegex(exceptions.HttpException, r'Error message'):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000')

  def testRaisesOperationError(self, track):
    """Test recognize-long-running command if operation contains error."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        hints=[],
        encoding=None,
        result='12345'
    )
    self._ExpectPollOperationRequests(
        '12345', 3, error_json={'code': 400, 'message': 'Message.'})
    with self.assertRaisesRegex(waiter.OperationError,
                                r'Message.'):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000')

  def testMissingRequiredAudioFilePositional(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesArgumentErrorMatches(
        'argument AUDIO: Must be specified.'):
      self.Run('ml speech recognize-long-running --language-code en-US '
               '--sample-rate 16000')

  def testMissingRequiredLanguageFlag(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesArgumentErrorMatches(
        '--language-code must be specified'):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--sample-rate 16000')

  def testInvalidFlagValues(self, track):
    """Test recognize-long-running command exits if invalid flag value given."""
    self.SetUpForTrack(track)
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000 '
               '--max-alternatives notanumber')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate notanumber')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000 '
               '--filter-profanity invalidvalue')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000 '
               '--encoding NOT_AN_ENCODING')

  def testAudioError(self, track):
    """Test recognize-long-running raises AudioException with invalid audio."""
    self.SetUpForTrack(track)
    audio_path = self.long_file + 'x'
    with self.AssertRaisesExceptionMatches(util.AudioException,
                                           '[{}]'.format(audio_path)):
      self.Run('ml speech recognize-long-running {} --language-code en-US '
               '--sample-rate 16000'.format(self.long_file + 'x'))


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA))
class RecognizeLongRunningSpecificTrackTest(speech_base.MlSpeechTestBase,
                                            parameterized.TestCase):
  """Class to test `gcloud ml speech recognize-long-running`."""

  _VERSIONS_FOR_RELEASE_TRACKS = {
      calliope_base.ReleaseTrack.ALPHA: 'v1p1beta1',
      calliope_base.ReleaseTrack.BETA: 'v1p1beta1',
      calliope_base.ReleaseTrack.GA: 'v1'
  }

  def testIncludeWordConfidence_Async(self, track):
    """Test recognize-long-running command that requests word confidence."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        encoding=None,
        enable_word_confidence=True
    )

    actual = self.Run(
        'ml speech recognize-long-running gs://bucket/object '
        '    --language-code en-US '
        '    --sample-rate 16000 '
        '    --async '
        '    --include-word-confidence'
    )

    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)
    self.assertEqual(json.loads(self.GetOutput()),
                     encoding.MessageToPyValue(expected))

  def testSpeakerDiarizationRequest_Async(self, track):
    """Test diarization flag values mapped in request."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        max_alternatives=1,
        result='12345',
        encoding=None,
        enable_speaker_diarization=True,
        speaker_count=7)

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --async '
                      '    --diarization-speaker-count 7 '
                      '    --enable-speaker-diarization')

    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)
    self.assertEqual(
        json.loads(self.GetOutput()), encoding.MessageToPyValue(expected))

  def testInvalidSpeakerDiarizationRequest_Async(self, track):
    """Test invalid diarization flag values."""
    self.SetUpForTrack(track)
    with self.AssertRaisesArgumentErrorRegexp(
        'enable-speaker-diarization must be specified.'):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '    --language-code en-US '
               '    --diarization-speaker-count 8')

    with self.AssertRaisesArgumentErrorRegexp(
        "invalid int value: 'catsanddogs'"):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '    --language-code en-US '
               '    --enable-speaker-diarization '
               '    --diarization-speaker-count catsanddogs')

  def testAdditionalLanguages_Async(self, track):
    """Test additional_language_codes flag."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        encoding=None,
        additional_language_codes=['en-TZ', 'en-CA'])

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --sample-rate 16000 '
                      '    --async '
                      '    --additional-language-codes en-TZ,en-CA')

    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)
    self.assertEqual(
        json.loads(self.GetOutput()), encoding.MessageToPyValue(expected))


class RecognizeAlpha(speech_base.MlSpeechTestBase,
                     parameterized.TestCase):

  _VERSIONS_FOR_RELEASE_TRACKS = {
      calliope_base.ReleaseTrack.ALPHA: 'v1p1beta1',
  }

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

    self.SetUpForTrack(self.track)

  @parameterized.parameters(
      ('discussion', 'DISCUSSION'),
      ('phone-call', 'PHONE_CALL'),
      ('voicemail', 'VOICEMAIL'),
      ('professionally-produced', 'PROFESSIONALLY_PRODUCED'),
      ('voice-search', 'VOICE_SEARCH'),
      ('voice-command', 'VOICE_COMMAND'),
      ('dictation', 'DICTATION'),
  )
  def testRecognizeMetadataInteractionType(self, choice, value):
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        interaction_type=value
    )

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --sample-rate 16000 '
                      '    --async '
                      '    --interaction-type {} '.format(choice))
    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)

  def testRecognizePunctuation(self):
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        max_alternatives=1,
        result='12345',
        sample_rate=16000,
        enable_punctuation=True)

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --sample-rate 16000 '
                      '    --async '
                      '    --enable-automatic-punctuation ')
    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)

  def testRecognizeNaics(self):
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        max_alternatives=1,
        result='12345',
        sample_rate=16000,
        naics_code=123456)

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --sample-rate 16000 '
                      '    --async '
                      '    --naics-code 123456')
    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)

  @parameterized.parameters(
      ('nearfield', 'NEARFIELD'),
      ('midfield', 'MIDFIELD'),
      ('farfield', 'FARFIELD')
  )
  def testRecognizeMicrophoneDistance(self, choice, value):
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        microphone_distance=value)

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --sample-rate 16000 '
                      '    --async '
                      '    --microphone-distance {}'.format(choice))
    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)

  @parameterized.parameters(
      ('audio', 'AUDIO'),
      ('video', 'VIDEO')
  )
  def testRecognizeMediaType(self, choice, value):
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        media_type=value)

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --sample-rate 16000 '
                      '    --async '
                      '    --original-media-type {}'.format(choice))
    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)

  @parameterized.parameters(
      ('smartphone', 'SMARTPHONE'),
      ('pc', 'PC'),
      ('phone-line', 'PHONE_LINE'),
      ('vehicle', 'VEHICLE'),
      ('outdoor', 'OTHER_OUTDOOR_DEVICE'),
      ('indoor', 'OTHER_INDOOR_DEVICE'),
  )
  def testRecognizeDeviceType(self, choice, value):
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        device_type=value)

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --sample-rate 16000 '
                      '    --async '
                      '    --recording-device-type {}'.format(choice))
    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)

  def testRecordingDeviceName(self):
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        device_name='Nexus 5X')

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --sample-rate 16000 '
                      '    --async '
                      '    --recording-device-name "Nexus 5X"')
    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)

  def testRecordingMimeType(self):
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        mime_type='audio/mp3')

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --sample-rate 16000 '
                      '    --async '
                      '    --original-mime-type "audio/mp3"')
    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)

  def testRecordingAudioTopic(self):
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        audio_topic='Recordings of federal supreme court')

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --sample-rate 16000 '
                      '    --async '
                      '    --audio-topic '
                      '"Recordings of federal supreme court"')
    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)

  def testSeparateChannelRecognition(self):
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        audio_channel_count=3,
        enable_separate_recognition=True
    )

    actual = self.Run('ml speech recognize-long-running gs://bucket/object '
                      '    --language-code en-US '
                      '    --sample-rate 16000 '
                      '    --async '
                      '    --audio-channel-count 3 '
                      '    --separate-channel-recognition ')
    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)

  def testInvalidSeparateRecognitionRequest(self):
    """Test invalid separate recognition flag values."""
    with self.AssertRaisesArgumentErrorRegexp(
        '--separate-channel-recognition: Must be specified.'):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '    --language-code en-US '
               '    --sample-rate 16000 '
               '    --async '
               '    --audio-channel-count 3')

  def testInvalidAudioChannelCountRequest(self):
    """Test invalid separate recognition flag values."""
    with self.AssertRaisesArgumentErrorRegexp(
        '-audio-channel-count: Must be specified.'):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '    --language-code en-US '
               '    --sample-rate 16000 '
               '    --async '
               '    --separate-channel-recognition ')


if __name__ == '__main__':
  test_case.main()
