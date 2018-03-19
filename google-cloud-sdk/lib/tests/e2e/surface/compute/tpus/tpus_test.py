
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
"""e2e tests for compute tpus command group."""
import contextlib
import random

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case

NETWORK = 'tpus-test-do-not-delete'  # auto mode network
_DELETE_MESSAGE = 'Deleted [{tpu_name}].'
_TPU_DESCRIPTION = 'Test TF Node {tpu_name}'


def _GetRandomCidr():
  # This gets us 256*32 possible ranges, which should be enough to prevent
  # issues running in parallel
  components = [
      '10',
      '240',
      str(random.choice(range(256))),
      str(random.choice((range(0, 256, 8)))),
  ]
  return '.'.join(components) + '/29'


class TpusTests(e2e_base.WithServiceAuth):
  """E2E tests for ml compute tpus command group."""

  def _GetTpuName(self):
    generator = e2e_utils.GetResourceNameGenerator(
        prefix='cloud-tpu-test', sequence_start=0, delimiter='-')
    return generator.next()

  @contextlib.contextmanager
  def _CreateTPU(self):
    """Creates Test TPU and deletes on exit."""
    tpu_id = self._GetTpuName()
    cidr = _GetRandomCidr()
    command = ("compute tpus create {name} --zone {zone} "
               "--network {network} "
               "--range '{cidr}' --accelerator-type 'tpu-v2' "
               "--description 'Test TF Node {name}' "
               "--version '1.6'".format(zone=self.zone, name=tpu_id, cidr=cidr,
                                        network=NETWORK))
    try:
      self.Run(command)
      yield tpu_id
    finally:
      delete_retryer = retry.Retryer(max_retrials=10, max_wait_ms=240000,
                                     exponential_sleep_multiplier=2)
      delete_retryer.RetryOnException(
          self.Run, ['compute tpus delete {} --quiet'.format(tpu_id)])

  def SetUp(self):
    self.zone = 'us-central1-c'
    self.track = calliope_base.ReleaseTrack.ALPHA
    properties.VALUES.compute.zone.Set(self.zone)

  def testEmptyListResult(self):
    """Basic Test of client connectivity."""
    result = self.Run('compute tpus list --zone {}'.format(self.zone))
    self.assertIsNotNone(result)
    self.assertEqual(len(list(result)), 0)

  @test_case.Filters.skip('Failing', 'b/74062611')
  def testWorkflow(self):
    """Test of Basic TPU CRUD Workflow."""
    with self._CreateTPU() as tpu_name:
      self.Run('compute tpus list')
      self.AssertOutputContains(tpu_name)
      result = self.Run('compute tpus describe {}'.format(tpu_name))
      self.assertIsNotNone(result)
      self.assertEqual(result.description,
                       _TPU_DESCRIPTION.format(tpu_name=tpu_name))
    self.AssertErrContains(_DELETE_MESSAGE.format(tpu_name=tpu_name))


if __name__ == '__main__':
  test_case.main()