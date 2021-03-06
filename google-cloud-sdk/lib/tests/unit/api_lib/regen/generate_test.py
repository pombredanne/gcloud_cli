# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Tests for the generator.py script."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.api_lib.regen import api_def
from googlecloudsdk.api_lib.regen import generate
from googlecloudsdk.api_lib.util import apis_internal as core_apis
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from tests.lib import test_case
from googlecloudsdk.third_party.apis import apis_map
import six


class ApiMapGeneratorTest(test_case.Base):

  def testGetAPIsMap(self):
    config = yaml.load(
        textwrap.dedent("""\
        orange:
          v1:
            discovery: organge_v1.json
            default: true
          v2:
            discovery: organge_v2.json
        banana:
          v2beta:
            discovery: banana_v2beta.json
          v2_staging:
            version: v2
            discovery: banana_v2_staging.json
            default: true
        pear:
          v7_test:
            discovery: pear_v7_test.json
    """))
    expected_map = {
        'orange': {
            'v1': api_def.APIDef(
                'fruits.orange.v1',
                'orange_v1_client.OrangeV1',
                'orange_v1_messages', True),
            'v2': api_def.APIDef(
                'fruits.orange.v2',
                'orange_v2_client.OrangeV2',
                'orange_v2_messages')
        },
        'banana': {
            'v2beta': api_def.APIDef(
                'fruits.banana.v2beta',
                'banana_v2beta_client.BananaV2beta',
                'banana_v2beta_messages'),
            'v2_staging': api_def.APIDef(
                'fruits.banana.v2_staging',
                'banana_v2_client.BananaV2',
                'banana_v2_messages', True)
        },
        'pear': {
            'v7_test': api_def.APIDef(
                'fruits.pear.v7_test',
                'pear_v7_test_client.PearV7Test',
                'pear_v7_test_messages', True)
        }
    }
    actual_map = generate._MakeApiMap('fruits', config)
    self.assertEqual(expected_map, actual_map)

  def testGetAPIsMapMultipleDefaultsClientsForAPI(self):
    config = yaml.load(
        textwrap.dedent("""\
        orange:
          v1:
            discovery: organge_v1.json
            default: true
          v2:
            discovery: organge_v2.json
            default: true
    """))

    with self.assertRaises(Exception) as ctx:
      generate._MakeApiMap('fruits', config)

    msg = str(ctx.exception)
    self.assertEqual(msg,
                     'Multiple default client versions found for [orange]!')

  def testGetAPIsMapNoDefaultsClientsForAPIs(self):
    config = yaml.load(textwrap.dedent("""\
        orange:
          v1:
            discovery: organge_v1.json
          v2:
            discovery: organge_v2.json
    """))

    with self.assertRaises(Exception) as ctx:
      generate._MakeApiMap('fruits', config)

    msg = str(ctx.exception)
    self.assertEqual(msg, 'No default client versions found for [orange]!')

  def testCreateAPIsMapFile(self):
    config = yaml.load(
        textwrap.dedent("""\
        orange:
          v1:
            discovery: organge_v1.json
            default: true
          v2:
            discovery: organge_v2.json
        banana:
          v2beta:
            discovery: banana_v2beta.json
          v2_staging:
            version: v2
            discovery: banana_v2_staging.json
            default: true
        pear:
          v7_test:
            discovery: pear_v7_test.json
    """))

    with files.TemporaryDirectory() as tmp_dir:
      dir_path = os.path.join(tmp_dir, 'fruits')
      os.makedirs(dir_path)
      generate.GenerateApiMap(tmp_dir, 'fruits', config)
      content = files.ReadFileContents(os.path.join(dir_path, 'apis_map.py'))

    self.maxDiff = None  # pylint: disable=invalid-name
    self.assertMultiLineEqual(
        files.ReadFileContents(os.path.join(os.path.dirname(__file__),
                                            'testdata', 'api_map_sample.txt')),
        content)

  def testSanityOfGeneratedApisMap(self):
    for api_name, ver_map in six.iteritems(apis_map.MAP):
      for ver, api_definition in six.iteritems(ver_map):
        self.assertEqual(api_definition, core_apis._GetApiDef(api_name, ver))


class ApiMapGeneratorTestWithMTLS(test_case.Base):

  def testGetAPIsMap(self):
    config = yaml.load(
        textwrap.dedent("""\
        orange:
          v1:
            discovery: organge_v1.json
            enable_mtls: false
            default: true
          v2:
            discovery: organge_v2.json
            enable_mtls: true
        banana:
          v2beta:
            discovery: banana_v2beta.json
            enable_mtls: true
            mtls_endpoint_override: 'https://banana.mtls.googleapis.com/banana/v2beta/'
          v2_staging:
            version: v2
            discovery: banana_v2_staging.json
            default: true
        pear:
          v7_test:
            discovery: pear_v7_test.json
    """))
    expected_map = {
        'orange': {
            'v1':
                api_def.APIDef('fruits.orange.v1', 'orange_v1_client.OrangeV1',
                               'orange_v1_messages', True),
            'v2':
                api_def.APIDef('fruits.orange.v2', 'orange_v2_client.OrangeV2',
                               'orange_v2_messages', False, True, '')
        },
        'banana': {
            'v2beta':
                api_def.APIDef(
                    'fruits.banana.v2beta', 'banana_v2beta_client.BananaV2beta',
                    'banana_v2beta_messages', False, True,
                    'https://banana.mtls.googleapis.com/banana/v2beta/'),
            'v2_staging':
                api_def.APIDef('fruits.banana.v2_staging',
                               'banana_v2_client.BananaV2',
                               'banana_v2_messages', True)
        },
        'pear': {
            'v7_test':
                api_def.APIDef('fruits.pear.v7_test',
                               'pear_v7_test_client.PearV7Test',
                               'pear_v7_test_messages', True)
        }
    }
    actual_map = generate._MakeApiMap('fruits', config)
    self.assertEqual(expected_map, actual_map)

  def testCreateAPIsMapFile(self):
    config = yaml.load(
        textwrap.dedent("""\
        orange:
          v1:
            discovery: organge_v1.json
            enable_mtls: false
            default: true
          v2:
            discovery: organge_v2.json
            enable_mtls: true
        banana:
          v2beta:
            discovery: banana_v2beta.json
            enable_mtls: true
            mtls_endpoint_override: 'https://banana.mtls.googleapis.com/banana/v2beta/'
          v2_staging:
            version: v2
            discovery: banana_v2_staging.json
            default: true
        pear:
          v7_test:
            discovery: pear_v7_test.json
    """))

    with files.TemporaryDirectory() as tmp_dir:
      dir_path = os.path.join(tmp_dir, 'fruits')
      os.makedirs(dir_path)
      generate.GenerateApiMap(tmp_dir, 'fruits', config)
      content = files.ReadFileContents(os.path.join(dir_path, 'apis_map.py'))

    self.maxDiff = None  # pylint: disable=invalid-name
    self.assertMultiLineEqual(
        files.ReadFileContents(
            os.path.join(
                os.path.dirname(__file__), 'testdata',
                'api_map_sample_mtls.txt')), content)


if __name__ == '__main__':
  test_case.main()
