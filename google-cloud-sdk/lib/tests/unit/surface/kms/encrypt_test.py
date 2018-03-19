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
"""Tests that exercise the 'gcloud kms encrypt' command."""

import os

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.kms import base


class KeysEncryptTest(base.KmsMockTest):

  def SetUp(self):
    self.key_name = self.project_name.Descendant('global/my_kr/my_key')

  def testEncrypt(self):
    pt_path = self.Touch(self.temp_path, name='plaintext', contents='foo bar')
    ct_path = self.Touch(self.temp_path, name='ciphertext')

    self.kms.projects_locations_keyRings_cryptoKeys.Encrypt.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysEncryptRequest(
            name=self.key_name.RelativeName(),
            encryptRequest=self.messages.EncryptRequest(plaintext='foo bar')),
        response=self.messages.EncryptResponse(
            name=self.key_name.RelativeName(), ciphertext='encrypted foo bar'))

    self.Run('kms encrypt --location={0} --keyring={1} --key={2} '
             '--plaintext-file={3} --ciphertext-file={4}'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id, pt_path, ct_path))

    self.AssertFileExistsWithContents('encrypted foo bar', ct_path)

  def testEncryptWithNonPrimaryVersion(self):
    version_name = self.project_name.Descendant('global/my_kr/my_key/2')

    pt_path = self.Touch(self.temp_path, name='plaintext', contents='foo bar')
    ct_path = self.Touch(self.temp_path, name='ciphertext')

    self.kms.projects_locations_keyRings_cryptoKeys.Encrypt.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysEncryptRequest(
            name=version_name.RelativeName(),
            encryptRequest=self.messages.EncryptRequest(plaintext='foo bar')),
        response=self.messages.EncryptResponse(
            name=version_name.RelativeName(), ciphertext='encrypted foo bar'))

    self.Run('kms encrypt --location={0} --keyring={1} --key={2} '
             '--plaintext-file={3} --ciphertext-file={4} --version={5}'.format(
                 version_name.location_id, version_name.key_ring_id,
                 version_name.crypto_key_id, pt_path, ct_path,
                 version_name.version_id))

    self.AssertFileExistsWithContents('encrypted foo bar', ct_path)

  def testEncryptWithAad(self):
    pt_path = self.Touch(self.temp_path, name='plaintext', contents='foo bar')
    aad_path = self.Touch(self.temp_path, name='aad', contents='authed data')
    ct_path = self.Touch(self.temp_path, name='ciphertext')

    self.kms.projects_locations_keyRings_cryptoKeys.Encrypt.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysEncryptRequest(
            name=self.key_name.RelativeName(),
            encryptRequest=self.messages.EncryptRequest(
                plaintext='foo bar',
                additionalAuthenticatedData='authed data')),
        response=self.messages.EncryptResponse(
            name=self.key_name.RelativeName(), ciphertext='encrypted foo bar'))

    self.Run('kms encrypt --location={0} --keyring={1} --key={2} '
             '--plaintext-file={3} --ciphertext-file={4} '
             '--additional-authenticated-data-file={5}'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id, pt_path, ct_path, aad_path))

    self.AssertFileExistsWithContents('encrypted foo bar', ct_path)

  def testEncryptStdio(self):
    self.WriteInput('foo bar')

    self.kms.projects_locations_keyRings_cryptoKeys.Encrypt.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysEncryptRequest(
            name=self.key_name.RelativeName(),
            # WriteInput appends the \n.
            encryptRequest=self.messages.EncryptRequest(plaintext='foo bar\n')),
        response=self.messages.EncryptResponse(
            name=self.key_name.RelativeName(), ciphertext='encrypted foo bar'))

    self.Run(
        'kms encrypt --location={0} --keyring={1} --key={2} --plaintext-file=- '
        '--ciphertext-file=-'.format(self.key_name.location_id,
                                     self.key_name.key_ring_id,
                                     self.key_name.crypto_key_id))

    self.AssertOutputEquals('encrypted foo bar')

  def testEncryptMissingPlaintextFile(self):
    pt_path = os.path.join(self.temp_path, 'file-that-does-not-exist')
    ct_path = self.Touch(self.temp_path, name='ciphertext')

    with self.assertRaisesRegexp(exceptions.BadFileException,
                                 'Failed to read plaintext file.*No such file'):
      self.Run('kms encrypt --location={0} --keyring={1} --key={2} '
               '--plaintext-file={3} --ciphertext-file={4}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, pt_path, ct_path))

  def testEncryptMissingAadFile(self):
    pt_path = self.Touch(self.temp_path, name='plaintext', contents='foo bar')
    aad_path = os.path.join(self.temp_path, 'file-that-does-not-exist')
    ct_path = self.Touch(self.temp_path, name='ciphertext')

    with self.assertRaisesRegexp(
        exceptions.BadFileException,
        'Failed to read additional authenticated data file.*No such file'):
      self.Run(
          'kms encrypt --location={0} --keyring={1} --key={2} '
          '--plaintext-file={3} --ciphertext-file={4} '
          '--additional-authenticated-data-file={5}'.
          format(self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id, pt_path, ct_path, aad_path))

  def testEncryptUnwritableOutput(self):
    pt_path = self.Touch(self.temp_path, name='plaintext', contents='foo bar')
    ct_path = os.path.join(self.temp_path, 'nested', 'nonexistent', 'file')

    self.kms.projects_locations_keyRings_cryptoKeys.Encrypt.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysEncryptRequest(
            name=self.key_name.RelativeName(),
            encryptRequest=self.messages.EncryptRequest(plaintext='foo bar')),
        response=self.messages.EncryptResponse(
            name=self.key_name.RelativeName(), ciphertext='encrypted foo bar'))

    with self.assertRaisesRegexp(exceptions.BadFileException,
                                 'No such file or directory'):
      self.Run('kms encrypt --location={0} --keyring={1} --key={2} '
               '--plaintext-file={3} --ciphertext-file={4}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, pt_path, ct_path))

  def testEncryptMissingCiphertext(self):
    file_path = self.Touch(self.temp_path, name='foo')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --ciphertext-file: Must be specified.'):
      self.Run('kms encrypt --location={0} --keyring={1} --key={2} '
               '--plaintext-file={3}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, file_path))

  def testEncryptMissingPlaintext(self):
    file_path = self.Touch(self.temp_path, name='foo')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --plaintext-file: Must be specified.'):
      self.Run('kms encrypt --location={0} --keyring={1} --key={2} '
               '--ciphertext-file={3}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, file_path))

  def testEncryptTooLarge(self):
    contents = 'a' * 65537  # API limit is 65536
    pt_path = self.Touch(self.temp_path, name='plaintext', contents=contents)
    ct_path = self.Touch(self.temp_path, name='ciphertext')

    with self.assertRaisesRegexp(
        exceptions.BadFileException,
        r'is larger than the maximum size of 65536 bytes.'):
      self.Run('kms encrypt --location={0} --keyring={1} --key={2} '
               '--plaintext-file={3} --ciphertext-file={4}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, pt_path, ct_path))

  def testRejectPlaintextAndAadFromStdin(self):
    ct_path = self.Touch(self.temp_path, name='ciphertext')

    with self.assertRaisesRegexp(
        exceptions.InvalidArgumentException,
        r'--plaintext-file.*--additional-authenticated-data-file'):
      self.Run('kms encrypt --location={0} --keyring={1} --key={2} '
               '--plaintext-file=- --additional-authenticated-data-file=- '
               '--ciphertext-file={3}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, ct_path))


if __name__ == '__main__':
  test_case.main()