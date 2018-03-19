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

"""Tests for the concepts module."""

import re

from googlecloudsdk.api_lib.util import resource as resource_util
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base
from tests.lib.calliope.concepts import util


class ConceptsTest(concepts_test_base.ConceptsTestBase):

  def testCreateResourceSpecFromCollection(self):
    """Tests creating resource from the collection with no config overrides."""
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        api_version='v1')

    # Check that attributes have correct defaults, and name and anchor are
    # stored correctly.
    self.assertEqual([concepts.Attribute(name='projectsId',
                                         help_text=None,
                                         required=True),
                      concepts.Attribute(name='shelvesId',
                                         help_text=None,
                                         required=True),
                      concepts.Attribute(name='name',
                                         help_text=concepts.ANCHOR_HELP,
                                         required=True)],
                     resource_spec.attributes)
    self.assertEqual('book', resource_spec.name)
    self.assertEqual(
        concepts.Attribute(
            name='name',
            help_text=concepts.ANCHOR_HELP,
            required=True),
        resource_spec.anchor)
    # Check that the param names for each attribute are stored correctly.
    self.assertEqual('projectsId', resource_spec.ParamName('projectsId'))
    self.assertEqual('shelvesId', resource_spec.ParamName('shelvesId'))
    self.assertEqual('booksId', resource_spec.ParamName('name'))

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
        'unknown attribute(s): [junk]'):
      concepts.ResourceSpec(
          'example.projects.shelves.books',
          resource_name='book',
          api_version='v1',
          junk=concepts.ResourceParameterAttributeConfig())

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
                               help_text=concepts.ANCHOR_HELP,
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
                               help_text=concepts.ANCHOR_HELP,
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
    deps_object = deps.Deps(
        {'book': [deps.ArgFallthrough('--book', 'example')],
         'shelf': [deps.ArgFallthrough('--book-shelf', 'exampleshelf')],
         'project': [
             deps.ArgFallthrough('--book-project', 'exampleproject')]})
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **self._MakeAttributeConfigs())

    registry_resource = resource_spec.Initialize(deps_object)

    self.assertEqual(
        'projects/exampleproject/shelves/exampleshelf/books/example',
        registry_resource.RelativeName())

  def testInitializeWithPropertyFallthroughs(self):
    """Tests that a resource is initialized correctly with property fallthrough.
    """
    deps_object = deps.Deps(
        {'book': [deps.ArgFallthrough('--book', 'example')],
         'shelf': [deps.ArgFallthrough('--book-shelf', 'exampleshelf')],
         'project': [
             deps.ArgFallthrough('--book-project', None),
             deps.PropertyFallthrough(properties.VALUES.core.project)]})
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **self._MakeAttributeConfigs())

    registry_resource = resource_spec.Initialize(deps_object)

    self.assertEqual(
        'projects/{}/shelves/exampleshelf/books/example'.format(
            self.Project()),
        registry_resource.RelativeName())

  def testInitializeWithRelativeName(self):
    """Tests Initialize when a fully specified name is given to the anchor.
    """
    deps_object = deps.Deps(
        {'book': [
            deps.ArgFallthrough(
                '--book',
                'projects/exampleproject/shelves/exampleshelf/books/example')],
         'shelf': [deps.ArgFallthrough('--book-shelf', 'anothershelf')],
         'project': [
             deps.PropertyFallthrough(properties.VALUES.core.project)]})
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **self._MakeAttributeConfigs())

    registry_resource = resource_spec.Initialize(deps_object)

    self.assertEqual(
        'projects/exampleproject/shelves/exampleshelf/books/example',
        registry_resource.RelativeName())

  def testInitializeFails(self):
    """Tests Initialize raises a useful error message when attribute not found.
    """
    self.UnsetProject()
    deps_object = deps.Deps(
        {'book': [deps.ArgFallthrough('--book', 'example')],
         'shelf': [deps.ArgFallthrough('--book-shelf', 'exampleshelf')],
         'project': [
             deps.ArgFallthrough('--book-project', None),
             deps.PropertyFallthrough(properties.VALUES.core.project)]})
    resource_spec = concepts.ResourceSpec(
        'example.projects.shelves.books',
        resource_name='book',
        **self._MakeAttributeConfigs())

    msg = re.escape(
        'The [book] resource is not properly specified.\n'
        'Failed to find attribute [project]. The attribute can be set in the '
        'following ways: \n'
        '- Provide the flag [--book-project] on the command line\n'
        '- Set the property [core/project] or provide the flag [--project] on '
        'the command line')
    with self.assertRaisesRegexp(concepts.InitializationError, msg):
      resource_spec.Initialize(deps_object)


if __name__ == '__main__':
  test_case.main()