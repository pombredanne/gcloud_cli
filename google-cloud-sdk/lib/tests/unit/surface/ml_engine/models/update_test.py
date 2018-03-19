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
"""ml-engine models update tests."""

from googlecloudsdk.api_lib.ml_engine import models
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

  def _MakeModel(self, name=None, regions=(), online_prediction_logging=None,
                 labels=None, description=None):
    if labels is not None:
      labels_cls = self.short_msgs.Model.LabelsValue
      labels = labels_cls(additionalProperties=[
          labels_cls.AdditionalProperty(key=key, value=value) for key, value in
          sorted(labels.items())
      ])

    return self.short_msgs.Model(
        name=name,
        regions=regions,
        onlinePredictionLogging=online_prediction_logging,
        labels=labels,
        description=description
    )

  def _ExpectPoll(self):
    self.client.projects_operations.Get.Expect(
        request=self.msgs.MlProjectsOperationsGetRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        response=self.msgs.GoogleLongrunningOperation(
            name='opName', done=True))

  def _ExpectGet(self, name='myModel', **kwargs):
    model = self._MakeModel(name=name, **kwargs)
    self.client.projects_models.Get.Expect(
        self.msgs.MlProjectsModelsGetRequest(
            name='projects/{}/models/{}'.format(self.Project(), name),
        ),
        model)

  def _ExpectPatch(self, update_mask, **kwargs):
    model = self._MakeModel(**kwargs)
    self.client.projects_models.Patch.Expect(
        self.msgs.MlProjectsModelsPatchRequest(
            name='projects/{}/models/myModel'.format(self.Project()),
            googleCloudMlV1Model=model,
            updateMask=update_mask
        ),
        self.msgs.GoogleLongrunningOperation(name='opId'))

  def testUpdateNoUpdateRequested(self, track):
    self.track = track

    with self.assertRaises(models.NoFieldsSpecifiedError):
      self.Run('ml-engine models update myModel')

  def testUpdateNewLabelsNoOp(self, track):
    self.track = track

    self._ExpectGet(labels={'key': 'value'})
    self.Run('ml-engine models update myModel --update-labels key=value')

  def testUpdateNewLabels(self, track):
    self.track = track

    self._ExpectGet()
    self._ExpectPatch('labels', labels={'key': 'value'})
    self._ExpectPoll()
    self.Run('ml-engine models update myModel --update-labels key=value')

  def testUpdateClearLabels(self, track):
    self.track = track

    self._ExpectGet(labels={'key': 'value'})
    self._ExpectPatch('labels', labels={})
    self._ExpectPoll()
    self.Run('ml-engine models update myModel --clear-labels')

  def testUpdateRemoveLabels(self, track):
    self.track = track

    self._ExpectGet(labels={'a': '1', 'b': '2', 'c': '3'})
    self._ExpectPatch('labels', labels={'a': '1', 'c': '3'})
    self._ExpectPoll()
    self.Run('ml-engine models update myModel --remove-labels b')

  def testUpdateDescription(self, track):
    self.track = track

    self._ExpectPatch('description', description='New Description')
    self._ExpectPoll()
    self.Run('ml-engine models update myModel --description "New Description"')

  def testUpdateAll(self, track):
    self.track = track

    self._ExpectGet()
    self._ExpectPatch('labels,description',
                      labels={'key': 'value'}, description='New Description')
    self._ExpectPoll()
    self.Run('ml-engine models update myModel --update-labels key=value '
             '--description "New Description"')


if __name__ == '__main__':
  test_case.main()