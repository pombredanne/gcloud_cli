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

"""Tests that exercise describing Android locales in the device catalog."""

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core.console import console_attr
from tests.lib import test_case
from tests.lib.surface.firebase.test import commands
from tests.lib.surface.firebase.test import fake_catalogs
from tests.lib.surface.firebase.test import unit_base


class TestLocalesDescribeTest(unit_base.TestMockClientTest):

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def TearDown(self):
    console_attr.ResetConsoleAttr()

  def testLocalesDescribe_LocaleNotFound(self):
    self.ExpectCatalogGet(fake_catalogs.FakeAndroidCatalog())

    with self.assertRaises(exceptions.LocaleNotFoundError):
      self.Run(commands.ANDROID_LOCALES_DESCRIBE + 'bad-locale')

    self.AssertErrContains("'bad-locale' is not a valid locale")

  def testLocalesDescribe_LocaleFound(self):
    self.ExpectCatalogGet(fake_catalogs.FakeAndroidCatalog())
    self.Run(commands.ANDROID_LOCALES_DESCRIBE + 'ro')

    self.AssertOutputContains('id: ro')
    self.AssertOutputContains('name: Romulan')
    self.AssertOutputContains('region: Romulus')
    self.AssertOutputContains('tags:\n- cunning')

  def testLocalesDescribe_ApiThrowsHttpError(self):
    err = unit_base.MakeHttpError('ErrorXYZ', 'Environment catalog failure.')
    self.ExpectCatalogGetError(err)

    with self.assertRaises(calliope_exceptions.HttpException):
      self.Run(commands.ANDROID_LOCALES_DESCRIBE + 'a-locale')

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*.test.android.locales.describe)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()