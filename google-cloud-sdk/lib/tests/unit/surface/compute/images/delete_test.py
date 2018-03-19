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
"""Tests for the images delete subcommand."""
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class ImagesDeleteTest(test_base.BaseTest):

  def testWithSingleImage(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute images delete image-1
        """)

    self.CheckRequests(
        [(self.compute_v1.images,
          'Delete',
          messages.ComputeImagesDeleteRequest(
              image='image-1',
              project='my-project'))],
    )

  def testWithManyImages(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute images delete image-1 image-2 image-3
        """)

    self.CheckRequests(
        [(self.compute_v1.images,
          'Delete',
          messages.ComputeImagesDeleteRequest(
              image='image-1',
              project='my-project')),

         (self.compute_v1.images,
          'Delete',
          messages.ComputeImagesDeleteRequest(
              image='image-2',
              project='my-project')),

         (self.compute_v1.images,
          'Delete',
          messages.ComputeImagesDeleteRequest(
              image='image-3',
              project='my-project'))],
    )

  def testUriSupport(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute images delete
          https://www.googleapis.com/compute/v1/projects/my-project/global/images/image-1
          image-2
        """)
    self.CheckRequests(
        [(self.compute_v1.images,
          'Delete',
          messages.ComputeImagesDeleteRequest(
              image='image-1',
              project='my-project')),

         (self.compute_v1.images,
          'Delete',
          messages.ComputeImagesDeleteRequest(
              image='image-2',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute images delete image-1 image-2 image-3
        """)

    self.CheckRequests(
        [(self.compute_v1.images,
          'Delete',
          messages.ComputeImagesDeleteRequest(
              image='image-1',
              project='my-project')),

         (self.compute_v1.images,
          'Delete',
          messages.ComputeImagesDeleteRequest(
              image='image-2',
              project='my-project')),

         (self.compute_v1.images,
          'Delete',
          messages.ComputeImagesDeleteRequest(
              image='image-3',
              project='my-project'))],
    )
    self.AssertErrContains(textwrap.dedent("""\
        The following images will be deleted:
         - [image-1]
         - [image-2]
         - [image-3]


        Do you want to continue (Y/n)? """))

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute images delete image-1 image-2 image-3
          """)

    self.CheckRequests()
    self.AssertErrContains(textwrap.dedent("""\
        The following images will be deleted:
         - [image-1]
         - [image-2]
         - [image-3]


        Do you want to continue (Y/n)? """))


if __name__ == '__main__':
  test_case.main()