# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests for the concepts module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.util import resource as resource_util
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base
from tests.lib.calliope.concepts import util

import six


class ConceptsTest(concepts_test_base.ConceptsTestBase,
                   parameterized.TestCase):

  def testCreateResourceSpecFromCollection(self):
    """Tests creating resource from the collection with no config overrides."""
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        api_version='v1')

    # Check that attributes have correct defaults, and name and anchor are
    # stored correctly.
    self.assertEqual([concepts.Attribute(name='projects_id',
                                         help_text=None,
                                         required=True),
                      concepts.Attribute(name='shelves_id',
                                         help_text=None,
                                         required=True),
                      concepts.Attribute(name='name',
                                         help_text=None,
                                         required=True)],
                     resource_spec.attributes)
    self.assertEqual(
        concepts.Attribute(
            name='name',
            help_text=None,
            required=True),
        resource_spec.anchor)
    # Check that the param names for each attribute are stored correctly.
    self.assertEqual('projectsId', resource_spec.ParamName('projects_id'))
    self.assertEqual('shelvesId', resource_spec.ParamName('shelves_id'))
    self.assertEqual('booksId', resource_spec.ParamName('name'))

  @parameterized.named_parameters(
      ('Name', {'resource_name': 'book'}, 'book'),
      ('NoName', {}, 'resource'))
  def testResourceSpecName(self, kwargs, expected_name):
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        **kwargs)
    self.assertEqual(resource_spec.name, expected_name)

  def testResourceSpecInvalidAttributeName(self):
    """Raises ValueError if attribute name has a capital letter."""
    with self.AssertRaisesExceptionMatches(ValueError, '[projectName]'):
      concepts.ResourceSpec(
          'example.projects.shelves.books',
          resource_name='book',
          projectsId=concepts.ResourceParameterAttributeConfig(
              name='projectName',
              help_text='help'))

  def testNoParamsCollectionRaises(self):
    """Tests creating resource from the collection with no config overrides."""
    empty_collection = resource_util.CollectionInfo(
        'example', 'v1', '', '', 'books',
        '',
        {'': ''},
        [])
    self.StartObjectPatch(resources.Registry, 'GetCollectionInfo',
                          return_value=empty_collection)
    with self.AssertRaisesExceptionMatches(
        concepts.ResourceConfigurationError,
        'Resource [book] has no parameters'):
      concepts.ResourceSpec(
          'books',
          resource_name='book',
          api_version='v1')

  def testNonexistentAttributeRaises(self):
    """Tests creating resource from the collection with no config overrides."""
    with self.AssertRaisesExceptionMatches(
        concepts.ResourceConfigurationError,
        'unknown attribute(s): Expected [projectsId, shelvesId, booksId], '
        'Found [junk]'):
      concepts.ResourceSpec(
          'example.projects.shelves.books',
          resource_name='book',
          api_version='v1',
          junk=concepts.ResourceParameterAttributeConfig())

  def testResourceParameterAttributeConfigDefaultValueType(self):
    """Tests ResourceParameterAttributeConfig default value_type."""
    config = concepts.ResourceParameterAttributeConfig(
        name='number',
        help_text='The number.',
    )
    self.assertEqual(six.text_type, config.value_type)

  def testResourceParameterAttributeConfigExplicitValueType(self):
    """Tests ResourceParameterAttributeConfig handles value_type=..."""
    value_type = int
    config = concepts.ResourceParameterAttributeConfig(
        name='number',
        help_text='The number.',
        value_type=value_type,
    )
    self.assertEqual(value_type, config.value_type)

  def testCreateResourceSpecWithAttributeConfigs(self):
    """Tests using ResourceParameterAttributeConfig to configure resources.
    """
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **self._MakeAttributeConfigs(with_completers=True))
    self.assertEqual(
        [
            concepts.Attribute(name='project',
                               help_text=('The Cloud Project of the '
                                          '{resource}.'),
                               required=True,
                               fallthroughs=[deps.PropertyFallthrough(
                                   properties.VALUES.core.project)],
                               completer=util.MockProjectCompleter),
            concepts.Attribute(name='shelf',
                               help_text=('The shelf of the {resource}. Shelves'
                                          ' hold books.'),
                               required=True,
                               completer=util.MockShelfCompleter),
            concepts.Attribute(name='book',
                               help_text='The book of the {resource}.',
                               required=True,
                               completer=util.MockBookCompleter)],
        resource_spec.attributes)
    self.assertEqual('projectsId', resource_spec.ParamName('project'))
    self.assertEqual('shelvesId', resource_spec.ParamName('shelf'))
    self.assertEqual('booksId', resource_spec.ParamName('book'))

  def testCreateResourceSpecWithCompletionConfigured(self):
    """Tests using ResourceParameterAttributeConfig to configure resources.
    """
    attributes = self._MakeAttributeConfigs()
    attributes['booksId'].completion_id_field = 'id'
    attributes['booksId'].completion_request_params = {'fieldMask': 'id'}
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **attributes
        )
    self.assertEqual(
        [
            concepts.Attribute(name='project',
                               help_text=('The Cloud Project of the '
                                          '{resource}.'),
                               required=True,
                               fallthroughs=[deps.PropertyFallthrough(
                                   properties.VALUES.core.project)]),
            concepts.Attribute(name='shelf',
                               help_text=('The shelf of the {resource}. Shelves'
                                          ' hold books.'),
                               required=True),
            concepts.Attribute(name='book',
                               help_text='The book of the {resource}.',
                               required=True,
                               completion_id_field='id',
                               completion_request_params={'fieldMask': 'id'})],
        resource_spec.attributes)
    self.assertEqual('projectsId', resource_spec.ParamName('project'))
    self.assertEqual('shelvesId', resource_spec.ParamName('shelf'))
    self.assertEqual('booksId', resource_spec.ParamName('book'))

  def testResourceSpecParamName(self):
    """Tests using ResourceParameterAttributeConfig to configure resources.
    """
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **self._MakeAttributeConfigs(with_completers=True))
    self.assertEqual('projectsId', resource_spec.ParamName('project'))
    self.assertEqual('shelvesId', resource_spec.ParamName('shelf'))
    self.assertEqual('booksId', resource_spec.ParamName('book'))
    with self.assertRaisesRegex(
        ValueError,
        re.escape('[book, project, shelf]')):
      resource_spec.ParamName('junk')

  def testResourceSpecAttributeName(self):
    """Tests using ResourceParameterAttributeConfig to configure resources.
    """
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **self._MakeAttributeConfigs(with_completers=True))
    self.assertEqual('project', resource_spec.AttributeName('projectsId'))
    self.assertEqual('shelf', resource_spec.AttributeName('shelvesId'))
    self.assertEqual('book', resource_spec.AttributeName('booksId'))

  def testInitialize(self):
    """Tests that a resource is initialized correctly using a deps object."""
    fallthroughs_map = {
        'book': [deps.ArgFallthrough('--book')],
        'shelf': [deps.ArgFallthrough('--book-shelf')],
        'project': [deps.ArgFallthrough('--book-project')]}
    parsed_args = self._GetMockNamespace(
        book='example', book_shelf='exampleshelf',
        book_project='exampleproject')
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **self._MakeAttributeConfigs())

    registry_resource = resource_spec.Initialize(fallthroughs_map,
                                                 parsed_args=parsed_args)

    self.assertEqual(
        'projects/exampleproject/shelves/exampleshelf/books/example',
        registry_resource.RelativeName())

  def testInitializeWithPropertyFallthroughs(self):
    """Tests that a resource is initialized correctly with property fallthrough.
    """
    fallthroughs_map = {
        'book': [deps.ArgFallthrough('--book')],
        'shelf': [deps.ArgFallthrough('--book-shelf')],
        'project': [
            deps.ArgFallthrough('--book-project'),
            deps.PropertyFallthrough(properties.VALUES.core.project)]}
    parsed_args = self._GetMockNamespace(
        book='example', book_shelf='exampleshelf',
        book_project=None)
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **self._MakeAttributeConfigs())

    registry_resource = resource_spec.Initialize(fallthroughs_map,
                                                 parsed_args=parsed_args)

    self.assertEqual(
        'projects/{}/shelves/exampleshelf/books/example'.format(
            self.Project()),
        registry_resource.RelativeName())

  def testInitializeWithRelativeName(self):
    """Tests Initialize when a fully specified name is given to the anchor.
    """
    fallthroughs_map = {
        'book': [deps.ArgFallthrough('--book')],
        'shelf': [deps.ArgFallthrough('--book-shelf')],
        'project': [
            deps.PropertyFallthrough(properties.VALUES.core.project)]}
    parsed_args = self._GetMockNamespace(
        book='projects/exampleproject/shelves/exampleshelf/books/example',
        book_shelf='anothershelf',
        book_project=None)
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **self._MakeAttributeConfigs())

    registry_resource = resource_spec.Initialize(fallthroughs_map,
                                                 parsed_args=parsed_args)

    self.assertEqual(
        'projects/exampleproject/shelves/exampleshelf/books/example',
        registry_resource.RelativeName())

  def testInitializeFails(self):
    """Tests Initialize raises a useful error message when attribute not found.
    """
    self.UnsetProject()
    fallthroughs_map = {
        'book': [deps.ArgFallthrough('--book')],
        'shelf': [deps.ArgFallthrough('--book-shelf')],
        'project': [
            deps.ArgFallthrough('--book-project'),
            deps.ArgFallthrough('--project'),
            deps.PropertyFallthrough(properties.VALUES.core.project)]}
    parsed_args = self._GetMockNamespace(
        book='example',
        book_shelf='exampleshelf',
        book_project=None)
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **self._MakeAttributeConfigs())

    msg = re.escape(
        'The [book] resource is not properly specified.\n'
        'Failed to find attribute [project]. The attribute can be set in the '
        'following ways: \n'
        '- provide the argument [--book-project] on the command line\n'
        '- provide the argument [--project] on the command line\n'
        '- set the property [core/project]')
    with self.assertRaisesRegex(concepts.InitializationError, msg):
      resource_spec.Initialize(fallthroughs_map, parsed_args=parsed_args)

  @parameterized.named_parameters(
      ('Flag', '--book', 'book'),
      ('Positional', 'BOOK', 'BOOK'))
  def testParse(self, name, namespace_name):
    """Tests Parse method correctly parses with different anchor names."""
    attribute_to_args_map = {
        'book': name, 'shelf': '--shelf', 'project': '--book-project'}
    args_dict = {namespace_name: 'examplebook',
                 'shelf': 'exampleshelf',
                 'book_project': 'exampleproject'}
    parsed_args = self._GetMockNamespace(**args_dict)

    parsed = self.resource_spec.Parse(
        attribute_to_args_map,
        base_fallthroughs_map={
            'project':
            [deps.PropertyFallthrough(properties.VALUES.core.project)]},
        parsed_args=parsed_args,
        allow_empty=False)

    self.assertEqual(
        'projects/exampleproject/shelves/exampleshelf/books/examplebook',
        parsed.RelativeName())

  @parameterized.named_parameters(
      ('MissingProject',
       {'book': 'examplebook', 'shelf': 'exampleshelf'}, '[project]'),
      ('MissingShelf',
       {'book': 'examplebook', 'book_project': 'exampleproject'}, '[shelf]'))
  def testParseError(self, args_dict, error_msg):
    """Tests that Parse method raises InitializationError when necessary."""
    self.UnsetProject()
    attribute_to_args_map = {
        'book': '--book', 'shelf': '--shelf', 'project': '--book-project'}
    parsed_args = self._GetMockNamespace(**args_dict)

    base_fallthroughs_map = {
        'project': [
            deps.PropertyFallthrough(properties.VALUES.core.project)]}

    with self.assertRaisesRegex(concepts.InitializationError,
                                re.escape(error_msg)):
      self.resource_spec.Parse(attribute_to_args_map,
                               base_fallthroughs_map,
                               parsed_args=parsed_args,
                               allow_empty=False)

  def testCreateAttributeConfigFromData(self):
    attribute_config = concepts.ResourceParameterAttributeConfig.FromData(
        {
            'parameter_name': 'projectsId',
            'attribute_name': 'project',
            'help': 'help1',
            'prop': 'core/project',
            'completion_id_field': 'id',
            'completion_request_params': [{
                'fieldName': 'fieldMask',
                'value': 'name'}]})
    self.assertEqual('project', attribute_config.attribute_name)
    self.assertEqual(None, attribute_config.completer)
    self.assertEqual('id', attribute_config.completion_id_field)
    self.assertEqual({'fieldMask': 'name'},
                     attribute_config.completion_request_params)
    self.assertEqual('projectsId', attribute_config.parameter_name)
    self.assertEqual(
        [
            deps.ArgFallthrough('--project'),
            deps.PropertyFallthrough(properties.VALUES.core.project)],
        attribute_config.fallthroughs)

  def testCreateResourceSpecFromYaml(self):
    yaml = {
        'disable_auto_completers':
            False,
        'name':
            'device',
        'request_id_field':
            'device.id',
        'attributes': [{
            'attribute_name': 'region',
            'help': 'The name of the Cloud IoT region.',
            'parameter_name': 'locationsId'
        },
                       {
                           'attribute_name': 'registry',
                           'help': 'The name of the Cloud IoT registry.',
                           'parameter_name': 'registriesId'
                       },
                       {
                           'attribute_name':
                               'device',
                           'help':
                               'The name of the Cloud IoT device.,',
                           'completion_request_params': [{
                               'value': 'name',
                               'fieldName': 'fieldMask'
                           }],
                           'completion_id_field':
                               'id',
                           'parameter_name':
                               'devicesId'
                       }],
        'collection':
            'cloudiot.projects.locations.registries.devices'
    }
    spec = concepts.ResourceSpec.FromYaml(yaml)
    self.assertEqual(None, spec.plural_name)
    self.assertEqual('cloudiot.projects.locations.registries.devices',
                     spec.collection)
    self.assertEqual(4, len(spec.attributes))
    self.assertEqual('device', spec.name)
    self.assertEqual(spec.attributes[3], spec.anchor)

  def testParseAttributesFromData(self):
    data = [
        {
            'attribute_name': 'region',
            'help': 'The name of the Cloud IoT region.',
            'parameter_name': 'locationsId'
        },
        {
            'attribute_name': 'registry',
            'help': 'The name of the Cloud IoT registry.',
            'parameter_name': 'registriesId'
        },
    ]
    parsed_attributes = concepts.ParseAttributesFromData(
        data, ['projectsId', 'locationsId', 'registriesId'])
    self.assertEqual(3, len(parsed_attributes))
    self.assertEqual('project', parsed_attributes[0].attribute_name)
    self.assertEqual('projectsId', parsed_attributes[0].parameter_name)
    self.assertEqual('region', parsed_attributes[1].attribute_name)
    self.assertEqual('locationsId', parsed_attributes[1].parameter_name)
    self.assertEqual('registry', parsed_attributes[2].attribute_name)
    self.assertEqual('registriesId', parsed_attributes[2].parameter_name)

  def testParseAttributesFromDataInvalid(self):
    with self.assertRaisesRegex(
        concepts.InvalidResourceArgumentLists,
        r'Invalid resource arguments: Expected \[\[projectsId\], instancesId\],'
        r' Found \[\]'):
      concepts.ParseAttributesFromData([], ['projectsId', 'instancesId'])

    with self.assertRaisesRegex(
        concepts.InvalidResourceArgumentLists,
        r'Invalid resource arguments: Expected \[\[projectsId\], instancesId\],'
        r' Found \[junk\]'):
      concepts.ParseAttributesFromData(
          [{
              'parameter_name': 'junk',
              'attribute_name': 'junk',
              'help': 'h'
          }],
          ['projectsId', 'instancesId'],
      )

    with self.assertRaisesRegex(
        concepts.InvalidResourceArgumentLists,
        r'Invalid resource arguments: Expected \[\[projectsId\], instancesId\],'
        r' Found \[instancesId, extraId\]'):
      concepts.ParseAttributesFromData([{
          'parameter_name': 'instancesId',
          'attribute_name': 'instance',
          'help': 'h'
      }, {
          'parameter_name': 'extraId',
          'attribute_name': 'extra',
          'help': 'h'
      }], ['projectsId', 'instancesId'])


if __name__ == '__main__':
  test_case.main()
