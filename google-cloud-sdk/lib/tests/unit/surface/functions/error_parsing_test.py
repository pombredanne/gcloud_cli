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

"""Tests for functions error_parsing."""

from googlecloudsdk.api_lib.functions import util
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.functions import util as testutil


class ErrorParsingTest(sdk_test_base.SdkBase):

  def testErrorWithoutJson(self):
    error = testutil.CreateTestHttpError(10, 'reason', 'invalid json')
    result = util.GetHttpErrorMessage(error)
    self.assertEqual(
        result,
        'ResponseError: status=[10], code=[reason], message=[invalid json]')

  def testErrorInvalidJsonWithError(self):
    # Test that 'error' word doesn't break our functions.
    error = testutil.CreateTestHttpError(10, 'reason', 'json error')
    result = util.GetHttpErrorMessage(error)
    self.assertEqual(
        result,
        'ResponseError: status=[10], code=[reason], message=[json error]')

  def testErrorWithoutError(self):
    content = '{}'
    error = testutil.CreateTestHttpError(10, 'reason', content)
    result = util.GetHttpErrorMessage(error)
    self.assertEqual(
        result,
        'ResponseError: status=[10], code=[reason], message=[]')

  def testErrorWithStringError(self):
    content = '{"error": "message"}'
    error = testutil.CreateTestHttpError(10, 'reason', content)
    result = util.GetHttpErrorMessage(error)
    expected = 'ResponseError: status=[{0}], code=[{1}], message=[{2}]'.format(
        10, 'reason', '{"error": "message"}')
    self.assertEqual(result, expected)

  def testErrorWithMessage(self):
    content = '{"error": {"message": "message"}}'
    error = testutil.CreateTestHttpError(10, 'reason', content)
    result = util.GetHttpErrorMessage(error)
    self.assertEqual(
        result,
        'ResponseError: status=[10], code=[reason], message=[message]')

  def testErrorWithStringDetails(self):
    content = '{"error": {"details": "field"}}'
    error = testutil.CreateTestHttpError(10, 'reason', content)
    result = util.GetHttpErrorMessage(error)
    self.assertEqual(
        result,
        'ResponseError: status=[10], code=[reason], message=[]')

  def testErrorWithDetailsWithoutInnerDictionary(self):
    content = '{"error": {"details": {"field": "value"}}}'
    error = testutil.CreateTestHttpError(10, 'reason', content)
    result = util.GetHttpErrorMessage(error)
    self.assertEqual(
        result,
        'ResponseError: status=[10], code=[reason], message=[]')

  def testErrorWithStringViolations(self):
    content = """{"error": {"details":
    [{"field": "value", "fieldViolations": "value"}]}}"""
    error = testutil.CreateTestHttpError(10, 'reason', content)
    result = util.GetHttpErrorMessage(error)
    self.assertEqual(
        result,
        'ResponseError: status=[10], code=[reason], message=[]')

  def testErrorWithViolationsWithoutList(self):
    content = """{"error": {"details":
    [{"field": "value", "fieldViolations": {"description": "value"}}]}}"""
    error = testutil.CreateTestHttpError(10, 'reason', content)
    result = util.GetHttpErrorMessage(error)
    self.assertEqual(
        result,
        'ResponseError: status=[10], code=[reason], message=[]')

  def testErrorWithViolationsWithoutDescription(self):
    content = """{"error": {"details":
    [{"field": "value", "fieldViolations": [{"key": "value"}]}]}}"""
    error = testutil.CreateTestHttpError(10, 'reason', content)
    result = util.GetHttpErrorMessage(error)
    self.assertEqual(
        result,
        'ResponseError: status=[10], code=[reason], message=[]')

  def testErrorSuccessful(self):
    content = """{"error": {"details":
    [{"field": "value", "fieldViolations": [
    {"description": "value 1"}, {"description": "value 2"}]},
    {"field": "my value", "fieldViolations":
    [{"field": "key", "description": "value 3"}]}]}}"""
    error = testutil.CreateTestHttpError(10, 'reason', content)
    result = util.GetHttpErrorMessage(error)
    self.assertEqual(
        result,
        '\n'.join(['ResponseError: status=[10], code=[reason], message=[',
                   'Problems:', 'value 1', 'value 2', 'value 3', ']']))

if __name__ == '__main__':
  test_case.main()