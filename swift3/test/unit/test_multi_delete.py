# Copyright (c) 2014 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from datetime import datetime
from hashlib import md5

from swift.common import swob
from swift.common.swob import Request

from swift3.test.unit import Swift3TestCase
from swift3.etree import fromstring, tostring, Element, SubElement
from swift3.cfg import CONF
from swift3.test.unit.test_s3_acl import s3acl


class TestSwift3MultiDelete(Swift3TestCase):

    def setUp(self):
        super(TestSwift3MultiDelete, self).setUp()

    @s3acl
    def test_object_multi_DELETE_to_object(self):
        elem = Element('Delete')
        obj = SubElement(elem, 'Object')
        SubElement(obj, 'Key').text = 'object'
        body = tostring(elem, use_s3ns=False)
        content_md5 = md5(body).digest().encode('base64').strip()

        req = Request.blank('/bucket/object?delete',
                            environ={'REQUEST_METHOD': 'POST'},
                            headers={'Authorization': 'AWS test:tester:hmac',
                                     'Content-MD5': content_md5},
                            body=body)

        status, headers, body = self.call_swift3(req)
        self.assertEquals(status.split()[0], '200')

    @s3acl
    def test_object_multi_DELETE(self):
        self.swift.register('DELETE', '/v1/AUTH_test/bucket/Key1',
                            swob.HTTPNoContent, {}, None)
        self.swift.register('DELETE', '/v1/AUTH_test/bucket/Key2',
                            swob.HTTPNotFound, {}, None)

        elem = Element('Delete')
        for key in ['Key1', 'Key2']:
            obj = SubElement(elem, 'Object')
            SubElement(obj, 'Key').text = key
        body = tostring(elem, use_s3ns=False)
        content_md5 = md5(body).digest().encode('base64').strip()

        req = Request.blank('/bucket?delete',
                            environ={'REQUEST_METHOD': 'POST'},
                            headers={'Authorization': 'AWS test:tester:hmac',
                                     'Content-MD5': content_md5},
                            body=body)
        req.date = datetime.now()
        req.content_type = 'text/plain'
        status, headers, body = self.call_swift3(req)
        self.assertEquals(status.split()[0], '200')

        elem = fromstring(body)
        self.assertEquals(len(elem.findall('Deleted')), 2)

    @s3acl
    def test_object_multi_DELETE_quiet(self):
        self.swift.register('DELETE', '/v1/AUTH_test/bucket/Key1',
                            swob.HTTPNoContent, {}, None)
        self.swift.register('DELETE', '/v1/AUTH_test/bucket/Key2',
                            swob.HTTPNotFound, {}, None)

        elem = Element('Delete')
        SubElement(elem, 'Quiet').text = 'true'
        for key in ['Key1', 'Key2']:
            obj = SubElement(elem, 'Object')
            SubElement(obj, 'Key').text = key
        body = tostring(elem, use_s3ns=False)
        content_md5 = md5(body).digest().encode('base64').strip()

        req = Request.blank('/bucket?delete',
                            environ={'REQUEST_METHOD': 'POST'},
                            headers={'Authorization': 'AWS test:tester:hmac',
                                     'Content-MD5': content_md5},
                            body=body)
        status, headers, body = self.call_swift3(req)
        self.assertEquals(status.split()[0], '200')

        elem = fromstring(body)
        self.assertEquals(len(elem.findall('Deleted')), 0)

    @s3acl
    def test_object_multi_DELETE_no_key(self):
        self.swift.register('DELETE', '/v1/AUTH_test/bucket/Key1',
                            swob.HTTPNoContent, {}, None)
        self.swift.register('DELETE', '/v1/AUTH_test/bucket/Key2',
                            swob.HTTPNotFound, {}, None)

        elem = Element('Delete')
        SubElement(elem, 'Quiet').text = 'true'
        for key in ['Key1', 'Key2']:
            obj = SubElement(elem, 'Object')
            SubElement(obj, 'Key')
        body = tostring(elem, use_s3ns=False)
        content_md5 = md5(body).digest().encode('base64').strip()

        req = Request.blank('/bucket?delete',
                            environ={'REQUEST_METHOD': 'POST'},
                            headers={'Authorization': 'AWS test:tester:hmac',
                                     'Content-MD5': content_md5},
                            body=body)
        status, headers, body = self.call_swift3(req)
        self.assertEquals(self._get_error_code(body), 'UserKeyMustBeSpecified')

    @s3acl
    def test_object_multi_DELETE_with_invalid_md5(self):
        elem = Element('Delete')
        for key in ['Key1', 'Key2']:
            obj = SubElement(elem, 'Object')
            SubElement(obj, 'Key').text = key
        body = tostring(elem, use_s3ns=False)

        req = Request.blank('/bucket?delete',
                            environ={'REQUEST_METHOD': 'POST'},
                            headers={'Authorization': 'AWS test:tester:hmac',
                                     'Content-MD5': 'XXXX'},
                            body=body)
        status, headers, body = self.call_swift3(req)
        self.assertEquals(self._get_error_code(body), 'InvalidDigest')

    @s3acl
    def test_object_multi_DELETE_without_md5(self):
        elem = Element('Delete')
        for key in ['Key1', 'Key2']:
            obj = SubElement(elem, 'Object')
            SubElement(obj, 'Key').text = key
        body = tostring(elem, use_s3ns=False)

        req = Request.blank('/bucket?delete',
                            environ={'REQUEST_METHOD': 'POST'},
                            headers={'Authorization': 'AWS test:tester:hmac'},
                            body=body)
        status, headers, body = self.call_swift3(req)
        self.assertEquals(self._get_error_code(body), 'InvalidRequest')

    @s3acl
    def test_object_multi_DELETE_too_many_keys(self):
        elem = Element('Delete')
        for i in range(CONF.max_multi_delete_objects + 1):
            obj = SubElement(elem, 'Object')
            SubElement(obj, 'Key').text = str(i)
        body = tostring(elem, use_s3ns=False)
        content_md5 = md5(body).digest().encode('base64').strip()

        req = Request.blank('/bucket?delete',
                            environ={'REQUEST_METHOD': 'POST'},
                            headers={'Authorization': 'AWS test:tester:hmac',
                                     'Content-MD5': content_md5},
                            body=body)
        status, headers, body = self.call_swift3(req)
        self.assertEquals(self._get_error_code(body), 'MalformedXML')

    def _test_object_multi_DELETE(self, account):
        self.swift.register('DELETE', '/v1/AUTH_test/bucket/Key1',
                            swob.HTTPNoContent, {}, None)
        self.swift.register('DELETE', '/v1/AUTH_test/bucket/Key2',
                            swob.HTTPNotFound, {}, None)

        elem = Element('Delete')
        for key in ['Key1', 'Key2']:
            obj = SubElement(elem, 'Object')
            SubElement(obj, 'Key').text = key
        body = tostring(elem, use_s3ns=False)
        content_md5 = md5(body).digest().encode('base64').strip()

        req = Request.blank('/bucket?delete',
                            environ={'REQUEST_METHOD': 'POST'},
                            headers={'Authorization': 'AWS %s:hmac' % account,
                                     'Content-MD5': content_md5},
                            body=body)
        req.date = datetime.now()
        req.content_type = 'text/plain'

        return self.call_swift3(req)

    @s3acl(s3acl_only=True)
    def test_object_multi_DELETE_without_permission(self):
        status, headers, body = self._test_object_multi_DELETE('test:other')
        self.assertEquals(self._get_error_code(body), 'AccessDenied')

    @s3acl(s3acl_only=True)
    def test_object_multi_DELETE_with_write_permission(self):
        status, headers, body = self._test_object_multi_DELETE('test:write')
        self.assertEquals(status.split()[0], '200')
        elem = fromstring(body)
        self.assertEquals(len(elem.findall('Deleted')), 2)

    @s3acl(s3acl_only=True)
    def test_object_multi_DELETE_with_fullcontrol_permission(self):
        status, headers, body = \
            self._test_object_multi_DELETE('test:full_control')
        self.assertEquals(status.split()[0], '200')
        elem = fromstring(body)
        self.assertEquals(len(elem.findall('Deleted')), 2)

if __name__ == '__main__':
    unittest.main()
