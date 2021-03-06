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

"""Tests for the arg_marshalling module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util.apis import arg_marshalling
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.apis import resource_arg_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib.calliope import util as calliope_util
from tests.lib.command_lib.util.apis import base

import mock
import six


def CheckArgs(args):
  parser = calliope_util.ArgumentParser()
  expanded_args = {}

  def _AddArgs(arguments, top=False):
    for arg in arguments:
      if top:
        arg.AddToParser(parser)
      if isinstance(arg, concept_parsers.ConceptParser):
        for spec in arg._specs.values():
          expanded_args.update(
              {a.name: a for a in arg.GetInfo(spec.name).GetAttributeArgs()})
      elif isinstance(arg, calliope_base.ArgumentGroup):
        _AddArgs(arg.arguments)
      else:
        expanded_args[arg.name] = arg

  _AddArgs(args, top=True)

  # Just to make testing easier, since this flag is not actually generated by
  # commands because it exists at the global level.
  parser.add_argument('--project', help='Auxilio aliis.')

  return parser, expanded_args


def MakeResource(collection='foo.projects.instances', attributes=None,
                 is_positional=None, removed_flags=None, arg_name=None):
  attributes = attributes if attributes is not None else ['instance']
  return resource_arg_schema.YAMLResourceArgument(
      {'name': attributes[-1] if attributes else 'UNKNOWN',
       'collection': collection,
       'request_id_field': 'instance.name',
       'attributes': [
           {
               'parameter_name': a + 'sId',
               'attribute_name': a,
               'help': 'h'} for a in attributes]
      },
      'gh',
      is_positional=is_positional,
      removed_flags=removed_flags,
      arg_name=arg_name
  )


def Fallthrough():
  return '!'


class DeclarativeTests(base.Base, parameterized.TestCase):
  """Tests the declarative arg generator.

  This entire class is parameterized to test both atomic and 'flat' APIs. Atomic
  means they use atomic names in their request paths (like /v1/{+name}) whereas
  flat means they declare all the parameters (like /projects/{project}).
  """

  @parameterized.parameters(True, False)
  def testResourceArgRemoved(self, is_atomic):
    self.MockCRUDMethods(('foo.projects.instances', False))
    method = registry.GetMethod('foo.projects.instances', 'get')
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource(removed_flags=['instance']))
    (_, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual([], sorted(args.keys()))

  @parameterized.parameters(True, False)
  def testGenerateGet(self, is_atomic):
    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', 'get')
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource())
    (_, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['instance'], sorted(args.keys()))
    self.assertEqual(
        args['instance'].kwargs['help'],
        'ID of the instance or fully qualified identifier for the instance.')

    # Make sure positional override works.
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource(is_positional=False))
    parser, args = CheckArgs(gen.GenerateArgs())
    six.assertCountEqual(self, ('--instance',), args)
    self.assertEqual(
        args['--instance'].kwargs['help'],
        'ID of the instance or fully qualified identifier for the instance.')

    namespace = parser.parse_args(['--instance=i'])
    properties.VALUES.core.project.Set('p')
    req = gen.CreateRequest(namespace)
    if is_atomic:
      self.assertEqual('projects/p/instances/i', req.name)
    else:
      self.assertEqual('p', req.projectsId)
      self.assertEqual('i', req.instancesId)

  @parameterized.parameters(True, False)
  def testGenerateGetWithArgNameOverride(self, is_atomic):
    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', 'get')
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource(arg_name='new_instance'))
    (_, args) = CheckArgs(gen.GenerateArgs())
    six.assertCountEqual(self, ('new_instance',), args)
    self.assertEqual(
        args['new_instance'].kwargs['help'],
        'ID of the new_instance or fully qualified identifier for the '
        'new_instance.')

    # Make sure positional override works.
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource(is_positional=False))
    (parser, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['--instance'], sorted(args.keys()))
    self.assertEqual(
        args['--instance'].kwargs['help'],
        'ID of the instance or fully qualified identifier for the instance.')

    namespace = parser.parse_args(['--instance=i'])
    properties.VALUES.core.project.Set('p')
    req = gen.CreateRequest(namespace)
    if is_atomic:
      self.assertEqual('projects/p/instances/i', req.name)
    else:
      self.assertEqual('p', req.projectsId)
      self.assertEqual('i', req.instancesId)

  @parameterized.parameters(True, False)
  def testGenerateCreate(self, is_atomic):
    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', 'create')

    instance_type = self.CreateRequestType(['name'])

    request_type = method.GetRequestType()
    method._service.GetRequestType.return_value = self.CreateRequestType(
        [f.name for f in request_type.all_fields()] + ['instance'])
    request_type = method.GetRequestType()
    request_type.field_by_name['instance'].type = instance_type

    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource())
    (parser, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['instance'], sorted(args.keys()))
    self.assertEqual(
        args['instance'].kwargs['help'],
        'ID of the instance or fully qualified identifier for the instance.')

    namespace = parser.parse_args(['i'])
    properties.VALUES.core.project.Set('p')
    req = gen.CreateRequest(namespace)
    if is_atomic:
      self.assertEqual('projects/p', req.parent)
      self.assertEqual('i', req.instance.name)
    else:
      self.assertEqual('p', req.projectsId)
      self.assertEqual('i', req.instance.name)

  @parameterized.parameters(True, False)
  def testGenerateList(self, is_atomic):
    self.MockCRUDMethods(('foo.locations.instances', is_atomic))
    method = registry.GetMethod('foo.locations.instances', 'list')
    # Make sure positional override works.
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource(collection='foo.locations',
                                 attributes=['location'],
                                 is_positional=True))
    (_, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['location'], sorted(args.keys()))
    self.assertEqual(args['location'].name, 'location')

    # Make sure list commands are non-positional by default.
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource(collection='foo.locations',
                                 attributes=['location']))
    (parser, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['--location'], sorted(args.keys()))
    self.assertEqual(args['--location'].name, '--location')
    self.assertEqual(
        args['--location'].kwargs['help'],
        'ID of the location or fully qualified identifier for the location.')
    self.assertEqual(args['--location'].kwargs['required'], True)

    namespace = parser.parse_args(['--location=l'])
    req = gen.CreateRequest(namespace)
    if is_atomic:
      self.assertEqual('locations/l', req.parent)
    else:
      self.assertEqual('l', req.locationsId)

  @parameterized.parameters(True, False)
  def testGenerateListWithTopLevelDefault(self, is_atomic):
    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', 'list')
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource(collection='foo.projects', attributes=[]))
    (parser, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual({}, args)

    namespace = parser.parse_args([])
    properties.VALUES.core.project.Set('p')
    req = gen.CreateRequest(namespace)
    if is_atomic:
      self.assertEqual('projects/p', req.parent)
    else:
      self.assertEqual('p', req.projectsId)

  @parameterized.parameters(True, False)
  def testResponseRef(self, is_atomic):
    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', 'list')
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource(collection='foo.projects', attributes=[]))
    (parser, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual([], sorted(args.keys()))
    # Test parsing the response reference.
    properties.VALUES.core.project.Set('p')
    namespace = parser.parse_args([])
    ref = gen.GetResponseResourceRef('foo', namespace)
    self.assertEqual(ref.instancesId, 'foo')
    self.assertEqual(ref.projectsId, 'p')
    self.assertEqual(ref.Collection(), 'foo.projects.instances')

  @parameterized.parameters(True, False)
  def testGenerateFields(self, is_atomic):
    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', 'list')
    arg_info = [yaml_command_schema.Argument('pageSize', 'page-size', 'ph'),
                yaml_command_schema.Argument(None, 'just-a-flag', 'help!')]
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, arg_info,
        MakeResource(collection='foo.projects', attributes=[]))
    (parser, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['--just-a-flag', '--page-size'], sorted(args.keys()))
    self.assertEqual(args['--page-size'].kwargs['help'], 'ph')
    self.assertEqual(args['--just-a-flag'].kwargs['help'], 'help!')

    namespace = parser.parse_args(['--page-size', '1'])
    properties.VALUES.core.project.Set('p')
    req = gen.CreateRequest(namespace)
    self.assertEqual('1', req.pageSize)
    if is_atomic:
      self.assertEqual('projects/p', req.parent)
    else:
      self.assertEqual('p', req.projectsId)

  @parameterized.parameters(itertools.product([True, False], [True, False]))
  def testGenerateGroups(self, is_atomic, is_required):
    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', 'list')
    group_args = [
        yaml_command_schema.Argument('pageSize', 'page-size', 'ph'),
        yaml_command_schema.Argument('pageToken', 'page-token', 'th')]
    group = yaml_command_schema.ArgumentGroup(
        arguments=group_args, mutex=True, required=is_required)
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [group],
        MakeResource(collection='foo.projects', attributes=[]))
    (_, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(2, len(args))
    self.assertEqual(['--page-size', '--page-token'], sorted(args))

  @parameterized.parameters(True, False)
  def testCreateRequestWithParamOverride(self, is_atomic):
    self.MockCRUDMethods(('foo.instances', is_atomic))
    method = registry.GetMethod('foo.instances', 'get')
    method.params = ['foo']
    mock_field = mock.MagicMock()
    mock_field.name = 'foo'
    mock_field.repeated = False
    method.GetRequestType().all_fields.return_value = [mock_field]
    message = method.GetRequestType()()
    message.field_by_name = mock.Mock(return_value=mock_field)

    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource(collection='foo.instances'))
    (parser, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['instance'], sorted(args.keys()))
    self.assertEqual(
        args['instance'].kwargs['help'],
        'ID of the instance or fully qualified identifier for the instance.')

    namespace = parser.parse_args(['i'])
    properties.VALUES.core.project.Set('p')
    req = gen.CreateRequest(namespace,
                            resource_method_params={'foo': 'instancesId'})
    self.assertEqual('i', req.foo)

  @parameterized.parameters(True, False)
  def testCreateRequestWithStaticFields(self, is_atomic):
    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', 'list')
    arg_info = [yaml_command_schema.Argument('pageSize', 'page-size', 'ph')]
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, arg_info,
        MakeResource(collection='foo.projects', attributes=[]))
    (_, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['--page-size'], sorted(args.keys()))
    self.assertEqual(args['--page-size'].kwargs['help'], 'ph')

    req = gen.CreateRequest(mock.MagicMock(project='p', page_size=None),
                            static_fields={'pageSize': 1})
    self.assertEqual(1, req.pageSize)
    req = gen.CreateRequest(mock.MagicMock(project='p', page_size=2),
                            static_fields={'pageSize': 1})
    self.assertEqual(2, req.pageSize)

  @parameterized.parameters(True, False)
  def testFieldProcessing(self, is_atomic):
    def P(value):
      return '!' + value

    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', 'list')
    arg_info = [yaml_command_schema.Argument('pageSize', 'page-size', 'ph',
                                             processor=P)]
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, arg_info,
        MakeResource(collection='foo.projects', attributes=[]))
    req = gen.CreateRequest(mock.MagicMock(project='p', page_size='a'))
    self.assertEqual('!a', req.pageSize)

  @parameterized.parameters(True, False)
  def testFieldFallback(self, is_atomic):
    def Fallback():
      return '!'

    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', 'list')
    arg_info = [yaml_command_schema.Argument('pageSize', 'page-size', 'ph',
                                             fallback=Fallback)]
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, arg_info,
        MakeResource(collection='foo.projects', attributes=[]))
    (parser, _) = CheckArgs(gen.GenerateArgs())
    properties.VALUES.core.project.Set('p')
    namespace = parser.parse_args([])
    req = gen.CreateRequest(namespace)
    self.assertEqual('!', req.pageSize)

  @parameterized.parameters(True, False)
  def testFieldFallbackResourceArg(self, is_atomic):
    self.MockCRUDMethods(('foo.projects.parents.instances', is_atomic))
    method = registry.GetMethod('foo.projects.parents.instances', 'get')
    resource_arg = MakeResource(collection='foo.projects.parents.instances',
                                attributes=['parent', 'instance'])
    resource_arg._attribute_data[0]['fallthroughs'] = [
        {
            'hook': DeclarativeTests.__module__ + ':Fallthrough',
            'hint': 'If the fallthrough works'
        }
    ]
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], resource_arg)
    (parser, _) = CheckArgs(gen.GenerateArgs())
    properties.VALUES.core.project.Set('p')
    namespace = parser.parse_args(['i'])
    req = gen.CreateRequest(namespace)
    if is_atomic:
      self.assertEqual('projects/p/parents/!/instances/i', req.name)
    else:
      self.assertEqual('i', req.instancesId)
      self.assertEqual('!', req.parentsId)

    # Make sure fallback doesn't get called if the information is provided in
    # the resource name
    (parser, _) = CheckArgs(gen.GenerateArgs())
    namespace = parser.parse_args(['projects/p/parents/parent/instances/i'])
    req = gen.CreateRequest(namespace)
    if is_atomic:
      self.assertEqual('projects/p/parents/parent/instances/i', req.name)
    else:
      self.assertEqual('i', req.instancesId)
      self.assertEqual('parent', req.parentsId)

  @parameterized.parameters(True, False)
  def testCommandFallbackResourceArg(self, is_atomic):
    self.MockCRUDMethods(('foo.projects.parents.instances', is_atomic))
    method = registry.GetMethod('foo.projects.parents.instances', 'get')
    resource_arg = MakeResource(collection='foo.projects.parents.instances',
                                attributes=['parent', 'instance'])
    resource_arg.command_level_fallthroughs = {'parent': ['--just-a-flag']}
    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [yaml_command_schema.Argument(None, 'just-a-flag', 'help!')],
        resource_arg)
    (parser, _) = CheckArgs(gen.GenerateArgs())
    properties.VALUES.core.project.Set('p')
    namespace = parser.parse_args(['i', '--just-a-flag', '!'])
    req = gen.CreateRequest(namespace)
    if is_atomic:
      self.assertEqual('projects/p/parents/!/instances/i', req.name)
    else:
      self.assertEqual('i', req.instancesId)
      self.assertEqual('!', req.parentsId)

    # Make sure fallback doesn't get called if the information is provided in
    # the resource name
    (parser, _) = CheckArgs(gen.GenerateArgs())
    namespace = parser.parse_args(['projects/p/parents/parent/instances/i',
                                   '--just-a-flag', '!'])
    req = gen.CreateRequest(namespace)
    if is_atomic:
      self.assertEqual('projects/p/parents/parent/instances/i', req.name)
    else:
      self.assertEqual('i', req.instancesId)
      self.assertEqual('parent', req.parentsId)

  def testCreateRequestIgnoreResource(self):
    self.MockCRUDMethods(('foo.instances', True))
    method = registry.GetMethod('foo.instances', 'get')

    gen = arg_marshalling.DeclarativeArgumentGenerator(
        method, [], MakeResource(collection='foo.instances'))
    (parser, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['instance'], sorted(args.keys()))
    self.assertEqual(
        args['instance'].kwargs['help'],
        'ID of the instance or fully qualified identifier for the instance.')

    namespace = parser.parse_args(['i'])
    properties.VALUES.core.project.Set('p')
    req = gen.CreateRequest(namespace, parse_resource_into_request=False)
    self.assertIsNone(req.name)

  @parameterized.parameters(True, False)
  def testCreateRequestForUpdate(self, is_atomic):
    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', 'patch')
    arg_info = [
        yaml_command_schema.Argument('description', 'display-name', 'dn')
    ]

    gen = arg_marshalling.DeclarativeArgumentGenerator(method, arg_info,
                                                       MakeResource())
    (parser, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['--display-name', 'instance'], sorted(args.keys()))
    self.assertEqual(
        args['instance'].kwargs['help'],
        'ID of the instance or fully qualified identifier for the instance.')
    self.assertEqual(args['--display-name'].kwargs['help'], 'dn')

    namespace = parser.parse_args(['i', '--display-name', 'dis'])
    properties.VALUES.core.project.Set('p')
    req = gen.CreateRequest(namespace)
    self.assertEqual('dis', req.description)

    if is_atomic:
      self.assertEqual('projects/p/instances/i', req.name)
    else:
      self.assertEqual('p', req.projectsId)
      self.assertEqual('i', req.instancesId)

  def testCreateRequestExistingMessage(self):
    self.MockCRUDMethods(('foo.projects.instances', True))
    method = registry.GetMethod('foo.projects.instances', 'patch')
    arg_info = [
        yaml_command_schema.Argument('description', 'display-name', 'dn')
    ]
    gen = arg_marshalling.DeclarativeArgumentGenerator(method, arg_info,
                                                       MakeResource())
    (parser, _) = CheckArgs(gen.GenerateArgs())
    namespace = parser.parse_args(['i', '--display-name', 'dis'])
    properties.VALUES.core.project.Set('p')
    original_message = list(method.GetRequestType().all_fields.return_value)
    mock_field = mock.MagicMock()
    mock_field.name = 'foo'
    mock_field.repeated = False
    existing_message = original_message.append(mock_field)

    req = gen.CreateRequest(namespace, existing_message=existing_message)
    self.assertEqual('projects/p/instances/i', req.name)
    self.assertEqual('dis', req.description)
    self.assertIsNotNone(req.foo)


class AutoTests(base.Base, parameterized.TestCase):
  """Tests for the automatic argument generator.

  The automatic generator has both a raw mode and a normal mode. The raw mode
  only affects the list methods because it doesn't generate fields for things
  that we have global list flags for. For each, there are tests for both atomic
  and flat APIs (see above class for description).
  """

  @parameterized.parameters(True, False)
  def testGenerateFlatGet(self, raw):
    self.MockCRUDMethods(('foo.projects.instances', False))
    method = registry.GetMethod('foo.projects.instances', 'get')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=raw)
    (_, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['--instancesId', '--projectsId', 'resource'],
                     sorted(args.keys()))
    self.assertEqual(
        args['--instancesId'].kwargs['help'],
        'For substitution into: projects/{projectsId}/instances/{instancesId}')
    self.assertEqual(
        args['--projectsId'].kwargs['help'],
        'For substitution into: projects/{projectsId}/instances/{instancesId}')
    self.assertEqual(
        args['resource'].kwargs['help'],
        'The GRI for the resource being operated on.')

  @parameterized.parameters(itertools.product(
      [True, False],
      [(None, 'p', None, 'i'),
       (None, None, 'p', 'i'),
       ('projects/p/instances/i', None, None, None),
       ('projects/p/instances/i', 'q', None, None),
       ('projects/p/instances/i', None, 'q', None),
       ('projects/p/instances/i', None, None, 'j')]))
  def testCreateFlatGet(self, raw, data):
    resource, projects_id, prop, instances_id = data
    properties.VALUES.core.project.Set(prop)
    self.MockCRUDMethods(('foo.projects.instances', False))
    method = registry.GetMethod('foo.projects.instances', 'get')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=raw)
    mock_request_type = method.GetRequestType()
    gen.CreateRequest(
        mock.MagicMock(resource=resource, projectsId=projects_id,
                       instancesId=instances_id))
    mock_request_type.assert_called_once_with(instancesId='i', projectsId='p')

  @parameterized.parameters(True, False)
  def testGenerateAtomicGet(self, raw):
    self.MockCRUDMethods(('foo.projects.instances', True))
    method = registry.GetMethod('foo.projects.instances', 'get')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=raw)
    (_, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['--instancesId', '--name', '--projectsId', 'resource'],
                     sorted(args.keys()))
    self.assertEqual(
        args['--instancesId'].kwargs['help'],
        'For substitution into: projects/{projectsId}/instances/{instancesId}')
    self.assertEqual(
        args['--projectsId'].kwargs['help'],
        'For substitution into: projects/{projectsId}/instances/{instancesId}')
    self.assertEqual(args['--name'].kwargs['help'],
                     'API doc needs help for field [name].')
    self.assertEqual(
        args['resource'].kwargs['help'],
        'The GRI for the resource being operated on.')

  @parameterized.parameters(itertools.product(
      [True, False],
      [(None, 'p', None, 'i', None),
       (None, None, 'p', 'i', None),
       ('projects/p/instances/i', None, None, None, None),
       ('projects/p/instances/i', 'q', None, None, None),
       ('projects/p/instances/i', None, 'q', None, None),
       ('projects/p/instances/i', None, None, 'j', None),
       (None, None, None, None, 'projects/p/instances/i')]))
  def testCreateAtomicGet(self, raw, data):
    resource, projects_id, prop, instances_id, name = data
    properties.VALUES.core.project.Set(prop)
    self.MockCRUDMethods(('foo.projects.instances', True))
    method = registry.GetMethod('foo.projects.instances', 'get')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=raw)
    mock_request_type = method.GetRequestType()
    m = mock.MagicMock(resource=resource, projectsId=projects_id,
                       instancesId=instances_id)
    m.name = name
    gen.CreateRequest(m)
    mock_request_type.assert_called_once_with(name='projects/p/instances/i')

  def testGenerateFlatListRaw(self):
    self.MockCRUDMethods(('foo.projects.instances', False))
    method = registry.GetMethod('foo.projects.instances', 'list')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=True)
    (_, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['--pageSize', '--pageToken', '--projectsId',
                      'resource'], sorted(args.keys()))

  @parameterized.parameters(
      (None, 'p', None, None, None, {'projectsId': 'p'}),
      ('p', None, None, None, None, {'projectsId': 'p'}),
      ('p', None, 'p', None, None, {'projectsId': 'p'}),
      (None, 'p', None, 'xyz', 1,
       {'projectsId': 'p', 'pageToken': 'xyz', 'pageSize': 1}),
  )
  def testCreateFlatListRaw(self, resource, projects_id, prop, page_token,
                            page_size, result):
    properties.VALUES.core.project.Set(prop)
    self.MockCRUDMethods(('foo.projects.instances', False))
    method = registry.GetMethod('foo.projects.instances', 'list')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=True)
    mock_request_type = method.GetRequestType()
    gen.CreateRequest(mock.MagicMock(resource=resource, projectsId=projects_id,
                                     pageToken=page_token, pageSize=page_size))
    mock_request_type.assert_called_once_with(**result)

  def testGenerateAtomicListRaw(self):
    self.MockCRUDMethods(('foo.projects.instances', True))
    method = registry.GetMethod('foo.projects.instances', 'list')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=True)
    (_, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['--pageSize', '--pageToken', '--parent', '--projectsId',
                      'resource'], sorted(args.keys()))

  @parameterized.parameters(
      (None, None, 'p', None, None, None, {'parent': 'projects/p'}),
      ('p', None, None, None, None, None, {'parent': 'projects/p'}),
      (None, None, None, 'p', None, None, {'parent': 'projects/p'}),
      (None, 'projects/p', None, None, None, None, {'parent': 'projects/p'}),
      (None, None, 'p', None, 'xyz', 1,
       {'parent': 'projects/p', 'pageToken': 'xyz', 'pageSize': 1}),
  )
  def testCreateAtomicListRaw(self, resource, parent, projects_id, prop,
                              page_token, page_size, result):
    properties.VALUES.core.project.Set(prop)
    self.MockCRUDMethods(('foo.projects.instances', True))
    method = registry.GetMethod('foo.projects.instances', 'list')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=True)
    mock_request_type = method.GetRequestType()
    m = mock.MagicMock(resource=resource, projectsId=projects_id,
                       pageToken=page_token, pageSize=page_size)
    m.parent = parent
    gen.CreateRequest(m)
    mock_request_type.assert_called_once_with(**result)

  def testGenerateFlatList(self):
    self.MockCRUDMethods(('foo.projects.instances', False))
    method = registry.GetMethod('foo.projects.instances', 'list')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=False)
    (_, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['--filter', '--limit', '--page-size', '--projectsId',
                      '--sort-by', 'resource'], sorted(args.keys()))

  @parameterized.parameters(
      (None, 'p', None, None, None, {'projectsId': 'p'}),
      ('p', None, None, None, None, {'projectsId': 'p'}),
      (None, None, 'p', None, None, {'projectsId': 'p'}),
      # Filter and sort don't get parsed directly into the message.
      (None, 'p', None, 'filter', 'sort', {'projectsId': 'p',}),
  )
  def testCreateFlatList(self, resource, projects_id, prop, filter_arg, sort_by,
                         result):
    properties.VALUES.core.project.Set(prop)
    self.MockCRUDMethods(('foo.projects.instances', False))
    method = registry.GetMethod('foo.projects.instances', 'list')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=False)
    mock_request_type = method.GetRequestType()
    gen.CreateRequest(mock.MagicMock(resource=resource, projectsId=projects_id,
                                     filter=filter_arg, sort_by=sort_by))
    mock_request_type.assert_called_once_with(**result)

  def testGenerateAtomicList(self):
    self.MockCRUDMethods(('foo.projects.instances', True))
    method = registry.GetMethod('foo.projects.instances', 'list')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=False)
    (_, args) = CheckArgs(gen.GenerateArgs())
    self.assertEqual(['--filter', '--limit', '--page-size', '--parent',
                      '--projectsId', '--sort-by', 'resource'],
                     sorted(args.keys()))

  @parameterized.parameters(
      (None, None, 'p', None, None, None, {'parent': 'projects/p'}),
      ('p', None, None, None, None, None, {'parent': 'projects/p'}),
      (None, None, None, 'p', None, None, {'parent': 'projects/p'}),
      (None, 'projects/p', None, None, None, None, {'parent': 'projects/p'}),
      (None, None, 'p', None, 'filter', 'sort_by', {'parent': 'projects/p'}),
  )
  def testCreateAtomicList(self, resource, parent, projects_id, prop,
                           filter_arg, sort_by, result):
    properties.VALUES.core.project.Set(prop)
    self.MockCRUDMethods(('foo.projects.instances', True))
    method = registry.GetMethod('foo.projects.instances', 'list')
    gen = arg_marshalling.AutoArgumentGenerator(method, raw=False)
    mock_request_type = method.GetRequestType()
    m = mock.MagicMock(resource=resource, projectsId=projects_id,
                       filter=filter_arg, sort_by=sort_by)
    m.parent = parent
    gen.CreateRequest(m)
    mock_request_type.assert_called_once_with(**result)


if __name__ == '__main__':
  base.main()
