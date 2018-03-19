# Copyright 2016 Google Inc. All Rights Reserved.
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
"""ml-engine jobs cancel tests."""

from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class CancelTestBase(object):

  def testCancel(self):
    self.client.projects_jobs.Cancel.Expect(
        self.msgs.MlProjectsJobsCancelRequest(
            name='projects/{}/jobs/opId'.format(self.Project())),
        self.msgs.GoogleProtobufEmpty()
    )

    self.Run('ml-engine jobs cancel opId')

    self.AssertOutputEquals('')


class CancelGaTest(CancelTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(CancelGaTest, self).SetUp()


class CancelBetaTest(CancelTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(CancelBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()