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
"""ml-engine versions update tests."""

from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA),
)
class UpdateSurfaceTest(base.MlGaPlatformTestBase, parameterized.TestCase):

  def _MakeVersion(self, name=None, labels=None, description=None):
    if labels is not None:
      labels_cls = self.short_msgs.Version.LabelsValue
      labels = labels_cls(additionalProperties=[
          labels_cls.AdditionalProperty(key=key, value=value) for key, value in
          sorted(labels.items())
      ])
    return self.short_msgs.Version(
        name=name,
        labels=labels,
        description=description
    )

  def _ExpectPoll(self):
    self.client.projects_operations.Get.Expect(
        request=self.msgs.MlProjectsOperationsGetRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        response=self.msgs.GoogleLongrunningOperation(
            name='opName', done=True))

  def _ExpectGet(self, model='myModel', name='myVersion', **kwargs):
    version = self._MakeVersion(name=name, **kwargs)
    self.client.projects_models_versions.Get.Expect(
        self.msgs.MlProjectsModelsVersionsGetRequest(
            name='projects/{}/models/{}/versions/{}'.format(self.Project(),
                                                            model, name),
        ),
        version)

  def _ExpectPatch(self, update_mask, **kwargs):
    version = self._MakeVersion(**kwargs)
    self.client.projects_models_versions.Patch.Expect(
        self.msgs.MlProjectsModelsVersionsPatchRequest(
            name='projects/{}/models/myModel/versions/myVersion'.format(
                self.Project()),
            googleCloudMlV1Version=version,
            updateMask=update_mask
        ),
        self.msgs.GoogleLongrunningOperation(name='opId'))

  def testUpdateNoUpdateRequested(self, track):
    self.track = track

    with self.assertRaises(versions_api.NoFieldsSpecifiedError):
      self.Run('ml-engine versions update myVersion --model myModel')

  def testUpdateNewLabelsNoOp(self, track):
    self.track = track

    self._ExpectGet(labels={'key': 'value'})
    self.Run('ml-engine versions update myVersion --model myModel '
             '--update-labels key=value')

  def testUpdateNewLabels(self, track):
    self.track = track

    self._ExpectGet()
    self._ExpectPatch('labels', labels={'key': 'value'})
    self._ExpectPoll()
    self.Run('ml-engine versions update myVersion --model myModel '
             '--update-labels key=value')

  def testUpdateClearLabels(self, track):
    self.track = track

    self._ExpectGet(labels={'key': 'value'})
    self._ExpectPatch('labels', labels={})
    self._ExpectPoll()
    self.Run('ml-engine versions update myVersion --model myModel '
             '--clear-labels')

  def testUpdateRemoveLabels(self, track):
    self.track = track

    self._ExpectGet(labels={'a': '1', 'b': '2'})
    self._ExpectPatch('labels', labels={'a': '1'})
    self._ExpectPoll()
    self.Run('ml-engine versions update myVersion --model myModel '
             '--remove-labels b')

  def testUpdateAll(self, track):
    self.track = track

    self._ExpectGet()
    self._ExpectPatch('labels,description',
                      labels={'key': 'value'}, description='Foo')
    self._ExpectPoll()
    self.Run('ml-engine versions update myVersion --model myModel '
             '--update-labels key=value --description Foo')

if __name__ == '__main__':
  test_case.main()