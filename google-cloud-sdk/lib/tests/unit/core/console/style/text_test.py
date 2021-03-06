# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.console.style import text
from tests.lib import test_case


class LogResourceChangeTest(test_case.TestCase):

  def testTextAdd(self):
    left = text.TypedText(['Left'])
    self.assertEqual((left + 'Right').texts, [left, 'Right'])

  def testTextRightAdd(self):
    right = text.TypedText(['Right'])
    self.assertEqual(('Left' + right).texts, ['Left', right])

  def testTexLength(self):
    nested_text = text.TypedText(
        ['asdf',
         text.TypedText(['fdsa'], text_type=text.TextTypes.RESOURCE_NAME)])
    self.assertEqual(len(nested_text), 8)


if __name__ == '__main__':
  test_case.main()
