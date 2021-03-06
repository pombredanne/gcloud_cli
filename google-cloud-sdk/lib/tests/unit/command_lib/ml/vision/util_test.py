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

"""Tests for the ML vision command_lib utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ml.vision import util
from tests.lib import sdk_test_base
from tests.lib import test_case


class VisionUtilTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self.messages = apis.GetMessagesModule(
        util.VISION_API, util.VISION_API_VERSION)

  def testGetImageGCS(self):
    """Test util.GetAnnotateRequest creates correct request."""
    self.assertEqual(
        util.GetImageFromPath('gs://bucket/file'),
        self.messages.Image(
            source=self.messages.ImageSource(imageUri='gs://bucket/file')))

  def testGetImageLocalFile(self):
    """Same as above, using a local file."""
    source_file = self.Resource('tests', 'unit', 'command_lib', 'ml', 'vision',
                                'testdata', 'face-input.png')
    with open(source_file, 'rb') as source:
      contents = source.read()
    self.assertEqual(
        util.GetImageFromPath(source_file),
        self.messages.Image(content=contents))

  def testGetImageValidateErrors(self):
    """Test that image paths are validated."""
    # Non-existent local paths should raise.
    bad_file = self.Resource('tests', 'unit', 'command_lib', 'ml', 'vision',
                             'testdata', 'not-exists.png')
    with self.assertRaises(util.ImagePathError):
      util.GetImageFromPath(bad_file)
    # Malformatted URLs should raise.
    with self.assertRaises(util.ImagePathError):
      util.GetImageFromPath('not-https://www.example.com/mypicture')
    with self.assertRaises(util.ImagePathError):
      util.GetImageFromPath('gs:/bucket/image')


if __name__ == '__main__':
  test_case.main()
