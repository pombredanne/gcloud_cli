# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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


"""Defines the different types of scenario event handlers."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
from collections import OrderedDict
import json
import os

import enum

from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import http_encoding
from tests.lib.scenario import assertions
from tests.lib.scenario import updates
import httplib2
import six
from six.moves import urllib


class Error(Exception):
  """General exception for the module."""
  pass


class UnknownFieldError(Error):
  """Exception for when a referenced field does not exist in the data."""
  pass


class Event(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for all events."""

  def __init__(self, update_context):
    self._update_context = update_context

  @classmethod
  def EventType(cls):
    return None

  def UpdateContext(self):
    return self._update_context

  @abc.abstractmethod
  def Handle(self, *args, **kwargs):
    return []

  def Summary(self):
    return []

  def __str__(self):
    return '{}: [{}]'.format(self.EventType(), self._update_context.Location())


class _SingleValueEvent(six.with_metaclass(abc.ABCMeta, Event)):
  """Base class for all event types that just check a single value."""

  @classmethod
  def _Build(cls, backing_data, field, default=None, was_missing=False,
             location=None):
    value = backing_data.get(field, default)
    if value is None:
      value = ''
    update_context = updates.Context(
        backing_data, field, cls.EventType().UpdateMode(),
        was_missing=was_missing, location=location)
    return cls(update_context, assertions.Assertion.ForComplex(value))

  def __init__(self, update_context, assertion):
    super(_SingleValueEvent, self).__init__(update_context)
    self._assertion = assertion

  def Handle(self, value):
    return self._assertion.Check(self._update_context, value)

  def Summary(self):
    return [{str(self.EventType()): self._assertion.ValueRepr()}]


class StdoutEvent(_SingleValueEvent):
  """Checks that the captured stdout matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.STDOUT

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_stdout')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(
        OrderedDict(), 'expect_stdout', was_missing=True, location=location)


class StderrEvent(_SingleValueEvent):
  """Checks that the captured stderr matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.STDERR

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_stderr')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(
        OrderedDict(), 'expect_stderr', was_missing=True, location=location)


class ExitEvent(Event):
  """Checks that the command exit code matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.EXIT

  @classmethod
  def FromData(cls, backing_data):
    exit_data = backing_data['expect_exit']
    code = exit_data.get('code')
    has_message = 'message' in exit_data
    message = exit_data.get('message')
    return cls(
        updates.Context(
            backing_data, 'expect_exit', cls.EventType().UpdateMode()),
        code,
        assertions.EqualsAssertion(code),
        assertions.Assertion.ForComplex(message) if has_message else None
    )

  @classmethod
  def ForMissing(cls, location):
    update_context = updates.Context(
        {'expect_exit': OrderedDict()}, 'expect_exit',
        cls.EventType().UpdateMode(), was_missing=True, location=location)
    return cls(update_context,
               0,
               assertions.EqualsAssertion(None),
               assertions.EqualsAssertion(None))

  def __init__(self, update_context, code, code_assertion, message_assertion):
    super(ExitEvent, self).__init__(update_context)
    self._code = code
    self._code_assertion = code_assertion
    self._message_assertion = message_assertion

  def Handle(self, exc):
    code = getattr(exc, 'exit_code', 1) if exc else 0
    message = six.text_type(exc) if exc else None
    return self.HandleReturnCode(code, message)

  def HandleReturnCode(self, return_code, message=None):
    failures = []
    failures.extend(
        self._code_assertion.Check(
            self._update_context.ForKey('code'), return_code))
    if self._message_assertion or (failures and message):
      msg_assertion = self._message_assertion or assertions.EqualsAssertion('')
      failures.extend(
          msg_assertion.Check(self._update_context.ForKey('message'), message))
    return failures

  def Summary(self):
    if self._code == 0:
      return []
    return [{'error': '{}: {}'.format(
        self._code,
        self._message_assertion.ValueRepr() if self._message_assertion
        else None)}]


class UserInputEvent(Event):
  """Provides user input to a prompt."""

  @classmethod
  def EventType(cls):
    return EventType.USER_INPUT

  @classmethod
  def FromData(cls, backing_data):
    return cls(
        updates.Context(
            backing_data, 'user_input', cls.EventType().UpdateMode()),
        backing_data.get('user_input') or [])

  @classmethod
  def ForMissing(cls, location):
    update_context = updates.Context(
        OrderedDict(), 'user_input', cls.EventType().UpdateMode(),
        was_missing=True, location=location)
    return cls(update_context, [])

  def __init__(self, update_context, lines):
    super(UserInputEvent, self).__init__(update_context)
    self._lines = lines

  def Lines(self):
    return self._lines

  def Handle(self):
    """Handle the event.

    A user input event is a little different from the others because it is not
    an assertion. Basically, if there are lines registered, there is no failure
    because it provides the input and execution moves on. If there are no lines,
    then the prompt cannot be answered and it is an error.

    Returns:
      [Failure], The failures or []
    """
    if self._lines:
      return []
    return [assertions.Failure.ForGeneric(
        self._update_context, title='Missing user input event')]

  def Summary(self):
    return [{'input': self._lines}]


class FileWrittenEvent(Event):
  """Checks that a given file was written with the given contents."""

  @classmethod
  def EventType(cls):
    return EventType.FILE_WRITTEN

  @classmethod
  def FromData(cls, backing_data):
    file_data = backing_data['expect_file_written']
    update_context = updates.Context(
        backing_data, 'expect_file_written', cls.EventType().UpdateMode())

    path_assertion = assertions.EqualsAssertion(file_data.get('path'))
    contents_assertion = assertions.Assertion.ForComplex(
        file_data.get('contents'))
    binary_contents = file_data.get('binary_contents')
    if (binary_contents is not None and
        isinstance(binary_contents, six.text_type)):
      binary_contents = binary_contents.encode('utf8')
    binary_contents_assertion = assertions.Assertion.ForComplex(binary_contents)
    is_private_assertion = assertions.EqualsAssertion(
        file_data.get('is_private') or False)

    return cls(update_context, path_assertion, contents_assertion,
               binary_contents_assertion, is_private_assertion)

  @classmethod
  def ForMissing(cls, location):
    update_context = updates.Context(
        {'expect_file_written': OrderedDict()}, 'expect_file_written',
        cls.EventType().UpdateMode(), was_missing=True, location=location)
    return cls(update_context,
               assertions.EqualsAssertion(None),
               assertions.EqualsAssertion(None),
               assertions.EqualsAssertion(None),
               assertions.EqualsAssertion(False))

  def __init__(self, update_context, path_assertion, contents_assertion,
               binary_contents_assertion, is_private_assertion):
    super(FileWrittenEvent, self).__init__(update_context)
    self._path_assertion = path_assertion
    self._contents_assertion = contents_assertion
    self._binary_contents_assertion = binary_contents_assertion
    self._is_private_assertion = is_private_assertion

  def Handle(self, path, contents, private):
    # Normalize slashes so the schema in the yaml file can stay the same.
    path = path.replace('\\', '/')

    failures = []
    failures.extend(
        self._path_assertion.Check(self._update_context.ForKey('path'), path))
    if isinstance(contents, six.text_type):
      binary_contents = None
    else:
      binary_contents = contents
      contents = None

    failures.extend(
        self._contents_assertion.Check(
            self._update_context.ForKey('contents'), contents))
    failures.extend(
        self._binary_contents_assertion.Check(
            self._update_context.ForKey('binary_contents'), binary_contents))
    failures.extend(
        self._is_private_assertion.Check(
            self._update_context.ForKey('is_private'), private))
    return failures

  def Summary(self):
    return [{'write_file': self._path_assertion.ValueRepr()}]


class ApiCallEvent(Event):
  """Checks that the API request matches an expected request."""

  @classmethod
  def EventType(cls):
    return EventType.API_CALL

  @classmethod
  def FromData(cls, backing_data):
    """Builds a request event handler from yaml data."""
    call_data = backing_data['api_call']
    update_context = updates.Context(
        backing_data, 'api_call', cls.EventType().UpdateMode())

    poll_operation = call_data.get('poll_operation', None)
    is_repeatable = call_data.get('repeatable', None)
    is_optional = call_data.get('optional', False)
    request_assertion = HTTPAssertion.ForRequest(call_data['expect_request'])
    response_assertion = HTTPAssertion.ForResponse(
        call_data.get('expect_response'))

    response_payload_data = call_data.get('return_response') or OrderedDict()
    response_payload = HTTPResponsePayload(
        headers=response_payload_data.get('headers', {'status': '200'}),
        payload=response_payload_data.get('body', ''),
        omit_fields=response_payload_data.get('omit_fields'))

    return cls(update_context, poll_operation, is_repeatable,
               is_optional, request_assertion, response_assertion,
               response_payload)

  @classmethod
  def ForMissing(cls, location):
    backing_data = {
        'api_call': OrderedDict([
            ('expect_request',
             OrderedDict([('uri', ''),
                          ('method', ''),
                          ('headers', {}),
                          ('body', {'text': None, 'json': {}})])),
            ('return_response',
             OrderedDict([('headers', {'status': '200'}),
                          ('body', None)]))
        ])
    }
    update_context = updates.Context(
        backing_data, 'api_call', cls.EventType().UpdateMode(),
        was_missing=True, location=location)
    response = backing_data['api_call']['return_response']

    return cls(
        update_context,
        None,
        None,
        False,
        HTTPAssertion(
            'expect_request',
            assertions.EqualsAssertion(assertions.MISSING_VALUE),
            assertions.EqualsAssertion(assertions.MISSING_VALUE),
            assertions.DictAssertion(),
            assertions.JsonAssertion().Matches('', assertions.MISSING_VALUE),
            assertions.EqualsAssertion(assertions.MISSING_VALUE),
            False,
            {}),
        None,
        HTTPResponsePayload(headers=response['headers'],
                            payload=response['body'],
                            omit_fields=None))

  def __init__(self, update_context, poll_operation, is_repeatable,
               is_optional, request_assertion, response_assertion,
               response_payload):
    super(ApiCallEvent, self).__init__(update_context)
    self._poll_operation = poll_operation
    self._is_repeatable = is_repeatable
    self._is_optional = is_optional
    self._was_repeated = False
    self._request_assertion = request_assertion
    self._response_assertion = response_assertion
    self._response_payload = response_payload
    self._call_data = None
    self._generated_op = None

  def IsOptional(self):
    return self._is_optional

  def CanBeRepeated(self):
    # pylint: disable=g-explicit-bool-comparison, We will try to repeat events
    # if necessary unless this is explicitly set to False.
    return self._is_repeatable != False

  def MarkRepeated(self):
    self._was_repeated = True

  def MarkCalledWith(self, uri, method, body, response):
    response_body = self._ParseResponse(response[1]) if response else None
    self._call_data = (uri, method, body, response_body)

  def MatchesPreviousCall(self, uri, method, body, response):
    response_body = self._ParseResponse(response[1]) if response else None
    new_call = (uri, method, body, response_body)
    return self._call_data == new_call

  def _ParseResponse(self, response):
    try:
      return json.loads(response)
    except (ValueError, TypeError):
      # Not a json object.
      return response

  def GetMatchingOperationForRequest(self, uri, method):
    if (self._generated_op and
        self._generated_op.MatchesPollingRequest(uri, method)):
      return self._generated_op
    return None

  def CheckRepeatable(self):
    return assertions.EqualsAssertion(self._is_repeatable).Check(
        self._update_context.ForKey('repeatable'), self._was_repeated)

  def Handle(self, uri, method, headers, body, dry_run=False):
    return self._request_assertion.Check(
        self._update_context, uri, method, headers, body, dry_run=dry_run)

  def HandleResponse(self, headers, body, resource_ref_resolver, dry_run=False,
                     generate_extras=False):
    if not isinstance(body, six.text_type):
      # For regular requests, this gets called before the wrapped request
      # decodes the response so this call is necessary. However, when this
      # function gets called during a batch request process, the response
      # has already gone through the entire wrapped request and the body
      # is already decoded.
      body = body.decode('utf8')

    failures = []
    if generate_extras:
      failures.extend(
          self._GenerateOperationPolling(resource_ref_resolver, headers, body))
    elif self._poll_operation and not dry_run:
      op = Operation.FromResponse(headers, body,
                                  force_operation=self._poll_operation)
      self._ExtractOperationPollingName(resource_ref_resolver, op)

    if self._response_assertion:
      if not dry_run:
        self._response_assertion.ExtractReferences(resource_ref_resolver, body)
      failures.extend(self._response_assertion.Check(
          self._update_context, None, None, headers, body, dry_run=dry_run))
    elif generate_extras and self._poll_operation is False:
      # Legacy operation detection.
      failures.extend(
          self._GenerateOperationsExtras(resource_ref_resolver, body))
    return failures

  def _GenerateOperationPolling(self, resource_ref_resolver, headers,
                                response_body):
    if self._poll_operation is False:
      # If explicitly disabled, don't treat this as an operation no matter what.
      return []

    op = Operation.FromResponse(headers, response_body,
                                force_operation=self._poll_operation)
    if not op or resource_ref_resolver.IsExtractedIdCurrent('operation',
                                                            op.name):
      # Not an operation response at all.
      if self._poll_operation is None:
        return []
      return assertions.EqualsAssertion(self._poll_operation).Check(
          self._update_context.ForKey('poll_operation'), False)

    # We've identified the response as an operation, make sure polling is turned
    # on.
    self._ExtractOperationPollingName(resource_ref_resolver, op)
    failures = assertions.EqualsAssertion(self._poll_operation).Check(
        self._update_context.ForKey('poll_operation'), True)
    return failures

  def _ExtractOperationPollingName(self, resource_ref_resolver, op):
    self._generated_op = op
    resource_ref_resolver.SetExtractedId('operation', op.name)
    resource_ref_resolver.SetExtractedId('operation-basename',
                                         os.path.basename(op.name))

  def _GenerateOperationsExtras(self, resource_ref_resolver, response_body):
    """Generates extra data if this response looks like an operation.

    If the body has a kind attribute that indicates an operation, this will
    update the scenario spec to include a default extract_references block
    to pull out the operation id. This should only be called if an
    expect_response block is not already present. If this is a polling operation
    it will be marked as optional.

    Args:
      resource_ref_resolver: ResourceReferenceResolver, The resolver to track
        the extracted references.
      response_body: str, The body of the response from the server.

    Returns:
      [Failure], The failures to update the spec and inject the new block or [].
    """
    op = Operation.FromResponse(None, response_body,
                                force_operation=self._poll_operation)
    if not op:
      # Not an operation response at all.
      return []
    if resource_ref_resolver.IsExtractedIdCurrent('operation', op.name):
      # This is an op, but the id has already been extracted in a previous
      # event. This means that this is not the call that generated the op, but
      # rather the polling of the op. No need to generate the ref extraction,
      # but we do want to mark polling steps as optional and repeated calls.
      self.MarkRepeated()
      failures = self.CheckRepeatable()
      if op.status:
        # In order for optional to work, we need to also generate an assertion
        # against the status in the response.
        failures = assertions.EqualsAssertion(self._is_optional).Check(
            self._update_context.ForKey('optional'), True)
        failures.append(
            assertions.Failure.ForGeneric(
                self._update_context.ForKey('expect_response'),
                'Adding operation response assertion for optional polling',
                OrderedDict([('body', {'json': {'status': op.status}})]))
        )
      return failures

    # This is a call that resulted in an operation being created. Extract its
    # id for future polling calls.
    resource_ref_resolver.SetExtractedId('operation', op.name)
    return [assertions.Failure.ForGeneric(
        self._update_context.ForKey('expect_response'),
        'Adding reference extraction for Operations response',
        OrderedDict([
            ('extract_references',
             [OrderedDict([('field', 'name'), ('reference', 'operation')])]),
            ('body', {'json': {}})])
    )]

  def GetResponsePayload(self):
    return self._response_payload.Respond()

  def UpdateResponsePayload(self, headers, body):
    return self._response_payload.Update(self._update_context, headers, body)

  def __str__(self):
    # pylint: disable=protected-access
    return super(ApiCallEvent, self).__str__() + ' [{}]'.format(
        self._request_assertion._uri_assertion)


class Operation(object):
  """Holds information about an operation that got returned an can be polled."""

  _NEXT_STATE = {
      'PENDING': 'RUNNING',
      'RUNNING': 'DONE',
      'DONE': 'DONE',
      None: 'DONE',
  }

  @classmethod
  def FromResponse(cls, headers, body, force_operation=False):
    """Construct an Operation from an API response."""
    try:
      json_data = json.loads(body)
    except (ValueError, TypeError):
      # Not a json object.
      return None

    name = json_data.get('name')
    if not name:
      return None

    if (json_data.get('kind', '').endswith('#operation') or
        'operationType' in json_data):
      return _OldOperation(name, headers, json_data)

    t = (json_data.get('metadata') or {}).get('@type') or ''
    if force_operation or 'done' in json_data or 'operation' in t.lower():
      return _NewOperation(name, headers, json_data)

    return None

  def __init__(self, name, headers, parsed_response_body):
    self._name = name
    self._headers = headers
    self._parsed_response_body = parsed_response_body

  @property
  def name(self):
    return self._name

  def MatchesPollingRequest(self, uri, method):
    return method == 'GET' and ('/' + self.name) in uri

  def Respond(self):
    self.status = Operation._NEXT_STATE[self.status]
    response = HTTPResponsePayload(
        self._headers, self._parsed_response_body, None)
    return response.Respond()


class _NewOperation(Operation):
  """Represents a new style LRO.

  New Operations have a name and done=true/false. Other than that they have
  service specific metadata that can take any form. Because of this, we don't
  do the normal advancement of the status because we don't know where it is.
  """

  @property
  def status(self):
    return None

  @status.setter
  def status(self, value):
    if value == 'DONE':
      self._parsed_response_body['done'] = True
      self._parsed_response_body['response'] = {}


class _OldOperation(Operation):

  @property
  def status(self):
    return self._parsed_response_body['status']

  @status.setter
  def status(self, value):
    self._parsed_response_body['status'] = value


class HTTPResponsePayload(object):
  """Encapsulates the data of a response payload."""

  HEADER_BLACKLIST_PREFIX = {
      'x-google-', 'alt-svc', '-content-encoding', 'date', 'content-location',
      'expires', 'server', 'transfer-encoding', 'vary',
      'x-content-type-options', 'x-frame-options', 'x-xss-protection',
  }

  def __init__(self, headers, payload, omit_fields):
    self._headers = headers
    if yaml.dict_like(payload):
      payload = json.dumps(payload)
    payload = payload or ''
    self._payload = http_encoding.Encode(payload)
    self._omit_fields = omit_fields

  def _SaveHeader(self, header):
    for prefix in HTTPResponsePayload.HEADER_BLACKLIST_PREFIX:
      if header.lower().startswith(prefix):
        return False
    return True

  def Respond(self):
    return (httplib2.Response(self._headers), self._payload)

  def Update(self, context, headers, body):
    """Updates the canned response data with real API response data."""

    def _ResponseUpdateHook(context, actual):
      """Custom update hook since this is not a real assertion failure."""
      data = context.BackingData()
      h, b = actual

      try:
        json_b = json.loads(b, object_pairs_hook=OrderedDict)
      except (ValueError, TypeError):
        # Not a json object.
        json_b = None

      if json_b and self._omit_fields:
        for omit in self._omit_fields:
          try:
            del json_b[omit]
          except KeyError:
            raise UnknownFieldError(
                'Field [{}] in omit_fields was not found in the API '
                'response data'.format(omit))

      data['return_response']['headers'] = OrderedDict(
          (key, value) for key, value in sorted(six.iteritems(h))
          if self._SaveHeader(key))
      data['return_response']['body'] = json_b or b
      return True

    update_context = context.ForKey(
        'return_response',
        update_mode=assertions.updates.Mode.API_RESPONSE_PAYLOADS,
        custom_update_hook=_ResponseUpdateHook)
    return [assertions.Failure.ForGeneric(
        update_context, 'API Response Payload', (headers, body.decode('utf8')))]


class ReferenceExtraction(object):
  """Encapsulates an extract_reference directive."""

  @classmethod
  def FromData(cls, extraction_data):
    return cls(extraction_data['field'], extraction_data['reference'],
               extraction_data.get('modifiers', {}).get('basename'))

  def __init__(self, field, reference, basename):
    self._field = field
    self._reference = reference
    self._basename = basename

  def Extract(self, json_data, resource_ref_resolver):
    resource_id = resource_transform.GetKeyValue(json_data, self._field)
    if resource_id is None:
      raise Error(
          'Unable to extract resource reference for field: [{}] from data: [{}]'
          .format(self._field, json_data))

    if self._basename:
      resource_id = os.path.basename(resource_id)
    resource_ref_resolver.SetExtractedId(self._reference, resource_id)


class HTTPAssertion(object):
  """Holds all the component assertions of an API request or response assertion.
  """

  @classmethod
  def ForRequest(cls, http_data):
    uri_assertion = assertions.Assertion.ForComplex(http_data.get('uri', ''))
    method_assertion = assertions.EqualsAssertion(
        http_data.get('method', 'GET'))
    return cls._ForCommon('expect_request', http_data, uri_assertion,
                          method_assertion, {})

  @classmethod
  def ForResponse(cls, http_data):
    if not http_data:
      return None
    extract_references = [ReferenceExtraction.FromData(d) for d in
                          http_data.get('extract_references', [])]
    return cls._ForCommon(
        'expect_response', http_data, None, None, extract_references)

  @classmethod
  def _ForCommon(cls, mode, http_data, uri_assertion, method_assertion,
                 extract_references):
    """Builder for the attributes applicable to both requests and responses."""
    header_assertion = assertions.DictAssertion()
    for header, value in six.iteritems(http_data.get('headers', {})):
      header_assertion.AddAssertion(header,
                                    assertions.Assertion.ForComplex(value))

    payload_json_assertion = None
    payload_text_assertion = None
    body_present = True
    body_data = http_data.get('body')
    if 'body' not in http_data or (not body_data and body_data is not None):
      # The body section is missing entirely or it is present and is an empty
      # dictionary. In these cases, the assertions are not present and will be
      # updated always.
      body_present = False
      payload_json_assertion = assertions.JsonAssertion().Matches(
          '', assertions.MISSING_VALUE)
      payload_text_assertion = assertions.EqualsAssertion(
          assertions.MISSING_VALUE)
      http_data['body'] = {'text': None, 'json': {}}
    elif body_data is None:
      # The body section is present and explicitly None. This implies assertions
      # that the body is actual None. If it is not, the assertions will fail.
      body_present = False
      payload_json_assertion = assertions.JsonAssertion().Matches('', None)
      payload_text_assertion = assertions.EqualsAssertion(None)
    else:
      # The body is present, load the assertions that were provided.
      if 'text' in body_data:
        payload_text_assertion = assertions.Assertion.ForComplex(
            body_data['text'])
      if 'json' in body_data:
        payload_json_assertion = assertions.JsonAssertion()
        json_data = body_data['json']
        if not json_data or json_data == assertions.MISSING_VALUE:
          # If explicitly None, this asserts that the request is empty.
          # If explicitly the empty dictionary, the assertion checks nothing.
          payload_json_assertion.Matches('', json_data)
        else:
          for field, struct in six.iteritems(json_data):
            payload_json_assertion.Matches(field, struct)

    return cls(mode, uri_assertion, method_assertion, header_assertion,
               payload_json_assertion, payload_text_assertion, body_present,
               extract_references)

  def __init__(self, mode, uri_assertion, method_assertion,
               headers_assertion, payload_json_assertion,
               payload_text_assertion, body_present, extract_references):
    self._mode = mode
    self._uri_assertion = uri_assertion
    self._method_assertion = method_assertion
    self._headers_assertion = headers_assertion
    self._payload_json_assertion = payload_json_assertion
    self._payload_text_assertion = payload_text_assertion
    self._body_present = body_present
    self._extract_references = extract_references

  def _OrderedUri(self, uri):
    """Sorts URI params to ensure they are always processed in same order."""
    url_parts = urllib.parse.urlsplit(uri)
    params = urllib.parse.parse_qs(url_parts.query)
    ordered_query_params = OrderedDict(sorted(six.iteritems(params)))
    url_parts = list(url_parts)
    # pylint:disable=redundant-keyword-arg, this is valid syntax for this lib
    url_parts[3] = urllib.parse.urlencode(ordered_query_params, doseq=True)
    # pylint:disable=too-many-function-args, This is just bogus.
    return urllib.parse.urlunsplit(url_parts)

  def _Key(self, key):
    return self._mode + '.' + key

  def ExtractReferences(self, resource_ref_resolver, body):
    """Extract any references from an API response.

    If this response assertion has registered references to extract, pull them
    out of the payload data and add them to the resolver for future use.

    Args:
      resource_ref_resolver: ResourceReferenceResolver, the resolver that is
        tracking resource references.
      body: str, The body payload of the response.

    Raises:
      Error: If a given reference cannot be extracted.
    """
    if not self._extract_references:
      return
    json_data = json.loads(body)
    for extraction in self._extract_references:
      extraction.Extract(json_data, resource_ref_resolver)

  def Check(self, context, uri, method, headers, body, dry_run=False):
    """Validates that the assertion matches the real data."""
    failures = []

    if self._uri_assertion:
      failures.extend(
          self._uri_assertion.Check(
              context.ForKey(self._Key('uri')), self._OrderedUri(uri)))
    if self._method_assertion:
      failures.extend(
          self._method_assertion.Check(
              context.ForKey(self._Key('method')), method))

    def _Decode(value):
      return (http_encoding.Decode(value) if isinstance(value, six.binary_type)
              else value)
    failures.extend(
        self._headers_assertion.Check(
            context.ForKey(self._Key('headers')),
            {_Decode(h): _Decode(v) for h, v in six.iteritems(headers)}))

    # Don't differentiate between a None body and an empty body. It's the same.
    if not body:
      body = None

    body = _Decode(body)
    json_data = None
    try:
      json_data = json.loads(body, object_pairs_hook=OrderedDict)
    except (ValueError, TypeError):
      # Not a json object.
      pass

    if json_data is not None and not self._body_present:
      # When there is no body present, we only want to generate one of the text
      # or json assertions (not both). If both are present, we update them
      # accordingly.
      body = None

    body_context = context.ForKey(self._Key('body'))
    backing_data = body_context.BackingData()
    if not dry_run and backing_data.get('body') is None and (body or json_data):
      # Body was explicitly set to None, but there is a body. The assertion
      # updates are going to trigger so we need to make sure there is a
      # dictionary for the values to get put into.
      backing_data['body'] = {}

    def _CleanupHook(context, actual):
      # This just does the normal update, but then sets the body to None if
      # both assertions were removed.
      result = context.StandardUpdateHook(actual)
      if not backing_data['body']:
        backing_data['body'] = None
      return result

    if self._payload_json_assertion:
      failures.extend(
          self._payload_json_assertion.Check(
              context.ForKey(self._Key('body.json'),
                             custom_update_hook=_CleanupHook),
              json_data or None))
    if self._payload_text_assertion:
      failures.extend(
          self._payload_text_assertion.Check(
              context.ForKey(self._Key('body.text'),
                             custom_update_hook=_CleanupHook),
              body))

    return failures


class _UXEvent(six.with_metaclass(abc.ABCMeta, Event)):
  """A base class for events based on the UX JSON blob."""

  @classmethod
  def _Build(cls, backing_data, field, was_missing=False, location=None):
    ux_event_data = backing_data.setdefault(field, OrderedDict())
    update_context = updates.Context(
        backing_data, field, cls.EventType().UpdateMode(),
        was_missing=was_missing, location=location)

    attr_assertions = OrderedDict()
    for a in cls.EventType().UXElementAttributes():
      if was_missing or a in ux_event_data:
        # Only create assertions for things that were specified, or if the event
        # was missing, assert everything so it all gets filled in.
        attr_assertions[a] = assertions.EqualsAssertion(
            ux_event_data.get(a, None))

    return cls(update_context, attr_assertions, ux_event_data)

  def __init__(self, update_context, attr_assertions, ux_event_data):
    del ux_event_data
    super(_UXEvent, self).__init__(update_context)
    self._attr_assertions = attr_assertions

  def Handle(self, ux_event_data):
    failures = []
    for attribute, attribute_assertion in self._attr_assertions.items():
      failures.extend(
          attribute_assertion.Check(self._update_context.ForKey(attribute),
                                    ux_event_data.get(attribute)))
    return failures

  def Summary(self):
    attrs = [{attr: assertion.ValueRepr()}
             for attr, assertion in self._attr_assertions.items()]
    return [{str(self.EventType()): attrs}]


class ProgressBarEvent(_UXEvent):
  """Checks that the Progress Bar Event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.PROGRESS_BAR

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_progress_bar')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(OrderedDict(), 'expect_progress_bar', was_missing=True,
                      location=location)


class ProgressTrackerEvent(_UXEvent):
  """Checks that the tracker event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.PROGRESS_TRACKER

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_progress_tracker')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(OrderedDict(), 'expect_progress_tracker',
                      was_missing=True, location=location)


class StagedProgressTrackerEvent(_UXEvent):
  """Checks that the staged tracker event (from stderr) matches a given value.
  """

  @classmethod
  def EventType(cls):
    return EventType.STAGED_PROGRESS_TRACKER

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_staged_progress_tracker')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(OrderedDict(), 'expect_staged_progress_tracker',
                      was_missing=True, location=location)


class _PromptEvent(six.with_metaclass(abc.ABCMeta, _UXEvent)):
  """Base class for UX events that involve a prompt with user input."""

  def __init__(self, update_context, attr_assertions, ux_event_data):
    super(_PromptEvent, self).__init__(
        update_context, attr_assertions, ux_event_data)
    self._user_input = ux_event_data.get('user_input')

  @classmethod
  def DefaultValue(cls):
    return ''

  def UserInput(self):
    return self._user_input or self.DefaultValue()

  def Handle(self, ux_event_data):
    failures = super(_PromptEvent, self).Handle(ux_event_data)
    if self._user_input is None:
      # Set the answer to 'y' if the entire assertion was missing.
      failures.extend(
          assertions.EqualsAssertion(None).Check(
              self._update_context.ForKey('user_input'), self.DefaultValue()))
    return failures

  def Summary(self):
    attrs = [{attr: assertion.ValueRepr()}
             for attr, assertion in self._attr_assertions.items()]
    attrs.append({'input': self.UserInput()})
    return [{'prompt': attrs}]


class PromptContinueEvent(_PromptEvent):
  """Checks that the prompt event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.PROMPT_CONTINUE

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_prompt_continue')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(OrderedDict(), 'expect_prompt_continue', was_missing=True,
                      location=location)

  @classmethod
  def DefaultValue(cls):
    return 'y'


class PromptChoiceEvent(_PromptEvent):
  """Checks that the prompt choice event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.PROMPT_CHOICE

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_prompt_choice')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(OrderedDict(), 'expect_prompt_choice', was_missing=True,
                      location=location)


class PromptResponseEvent(_PromptEvent):
  """Checks that the prompt response event (from stderr) matches a given value.
  """

  @classmethod
  def EventType(cls):
    return EventType.PROMPT_RESPONSE

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_prompt_response')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(OrderedDict(), 'expect_prompt_response', was_missing=True,
                      location=location)


class EventType(enum.Enum):
  """Describes the set of events we can handle as part of a scenario."""
  STDOUT = (StdoutEvent, assertions.updates.Mode.RESULT, None, False)
  STDERR = (StderrEvent, assertions.updates.Mode.UX, None, False)
  USER_INPUT = (UserInputEvent, assertions.updates.Mode.UX, None, False)
  API_CALL = (ApiCallEvent, assertions.updates.Mode.API_REQUESTS, None, False)
  FILE_WRITTEN = (FileWrittenEvent, assertions.updates.Mode.RESULT, None, None)
  EXIT = (ExitEvent, assertions.updates.Mode.RESULT, None, False)
  PROGRESS_BAR = (ProgressBarEvent, assertions.updates.Mode.UX,
                  console_io.UXElementType.PROGRESS_BAR, False)
  PROGRESS_TRACKER = (ProgressTrackerEvent, assertions.updates.Mode.UX,
                      console_io.UXElementType.PROGRESS_TRACKER, False)
  STAGED_PROGRESS_TRACKER = (StagedProgressTrackerEvent,
                             assertions.updates.Mode.UX,
                             console_io.UXElementType.STAGED_PROGRESS_TRACKER,
                             False)
  PROMPT_CONTINUE = (PromptContinueEvent, assertions.updates.Mode.UX,
                     console_io.UXElementType.PROMPT_CONTINUE, True)
  PROMPT_CHOICE = (PromptChoiceEvent, assertions.updates.Mode.UX,
                   console_io.UXElementType.PROMPT_CHOICE, True)
  PROMPT_RESPONSE = (PromptResponseEvent, assertions.updates.Mode.UX,
                     console_io.UXElementType.PROMPT_RESPONSE, True)

  def __init__(self, impl, update_mode, ux_element_type, has_user_input):
    self._impl = impl
    self._update_mode = update_mode
    self._ux_element_type = ux_element_type
    self._has_user_input = has_user_input

  def Impl(self):
    return self._impl

  def UpdateMode(self):
    return self._update_mode

  def UXElementAttributes(self):
    return self._ux_element_type.GetDataFields()

  def HasUserInput(self):
    return self._has_user_input

  def __str__(self):
    return self.name.lower()
