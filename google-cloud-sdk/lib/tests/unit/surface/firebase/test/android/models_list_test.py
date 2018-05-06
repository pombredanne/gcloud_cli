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

"""Tests that exercise listing of Android models in the device catalog."""

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_attr
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.android import commands
from tests.lib.surface.firebase.test.android import fake_catalogs
from tests.lib.surface.firebase.test.android import unit_base


class TestModelsListTest(unit_base.AndroidMockClientTest):

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def TearDown(self):
    console_attr.ResetConsoleAttr()

  def testModelsList_NoModelsFound(self):
    self.ExpectCatalogGet(fake_catalogs.EmptyAndroidCatalog())
    self.Run(commands.ANDROID_MODELS_LIST)
    self.AssertErrContains('Listed 0 items.')

  def testModelsList_ModelsFound(self):
    self.ExpectCatalogGet(fake_catalogs.FakeAndroidCatalog())
    self.Run(commands.ANDROID_MODELS_LIST)
    self.AssertOutputContains(
        """\
        | Nexus2099 | MegaCorp | Nexus 2099 | VIRTUAL | 800 x 600 | v98,v99 | |
        | Universe3 | Sungsam | Universe T3 | PHYSICAL | 2000 x 1000 | C,F \
        | youreit, default |""",
        normalize_space=True)

  def testModelsList_DeprecationWarningShown(self):
    self.ExpectCatalogGet(fake_catalogs.FakeAndroidCatalog())
    self.Run(commands.ANDROID_MODELS_LIST)
    self.AssertOutputContains(
        """\
        | EsperiaXYZ | Genuine Panaphonics | Esperia XYZ | PHYSICAL | 7 x 10 \
        | 0,1,2 | deprecated=1,2 |""",
        normalize_space=True)
    self.AssertErrContains('Some devices are deprecated. Learn more')

  def testModelsList_ApiThrowsHttpError(self):
    err = test_utils.MakeHttpError('ErrorXYZ', 'Environment catalog failure.')
    self.ExpectCatalogGetError(err)

    with self.assertRaises(exceptions.HttpException):
      self.Run(commands.ANDROID_MODELS_LIST)

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*.test.android.models.list)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()
