#! /usr/bin/env python
#
# Protocol Buffers - Google's data interchange format
# Copyright 2008 Google Inc.  All rights reserved.
# https://developers.google.com/protocol-buffers/
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Test for google.protobuf.text_format."""

__author__ = 'kenton@google.com (Kenton Varda)'

import re
import unittest

from google.protobuf.internal import _parameterized

from google.protobuf import unittest_mset_pb2
from google.protobuf import unittest_pb2
from google.protobuf import unittest_proto3_arena_pb2
from google.protobuf.internal import api_implementation
from google.protobuf.internal import test_util
from google.protobuf import text_format

# Base class with some common functionality.
class TextFormatBase(unittest.TestCase):

  def ReadGolden(self, golden_filename):
    with test_util.GoldenFile(golden_filename) as f:
      return (f.readlines() if str is bytes else  # PY3
              [golden_line.decode('utf-8') for golden_line in f])

  def CompareToGoldenFile(self, text, golden_filename):
    golden_lines = self.ReadGolden(golden_filename)
    self.assertMultiLineEqual(text, ''.join(golden_lines))

  def CompareToGoldenText(self, text, golden_text):
    self.assertMultiLineEqual(text, golden_text)

  def RemoveRedundantZeros(self, text):
    # Some platforms print 1e+5 as 1e+005.  This is fine, but we need to remove
    # these zeros in order to match the golden file.
    text = text.replace('e+0','e+').replace('e+0','e+') \
               .replace('e-0','e-').replace('e-0','e-')
    # Floating point fields are printed with .0 suffix even if they are
    # actualy integer numbers.
    text = re.compile('\.0$', re.MULTILINE).sub('', text)
    return text


@_parameterized.Parameters(
    (unittest_pb2),
    (unittest_proto3_arena_pb2))
class TextFormatTest(TextFormatBase):

  def testPrintExotic(self, message_module):
    message = message_module.TestAllTypes()
    message.repeated_int64.append(-9223372036854775808)
    message.repeated_uint64.append(18446744073709551615)
    message.repeated_double.append(123.456)
    message.repeated_double.append(1.23e22)
    message.repeated_double.append(1.23e-18)
    message.repeated_string.append('\000\001\a\b\f\n\r\t\v\\\'"')
    message.repeated_string.append(u'\u00fc\ua71f')
    self.CompareToGoldenText(
        self.RemoveRedundantZeros(text_format.MessageToString(message)),
        'repeated_int64: -9223372036854775808\n'
        'repeated_uint64: 18446744073709551615\n'
        'repeated_double: 123.456\n'
        'repeated_double: 1.23e+22\n'
        'repeated_double: 1.23e-18\n'
        'repeated_string:'
        ' "\\000\\001\\007\\010\\014\\n\\r\\t\\013\\\\\\\'\\""\n'
        'repeated_string: "\\303\\274\\352\\234\\237"\n')

  def testPrintExoticUnicodeSubclass(self, message_module):
    class UnicodeSub(unicode):
      pass
    message = message_module.TestAllTypes()
    message.repeated_string.append(UnicodeSub(u'\u00fc\ua71f'))
    self.CompareToGoldenText(
        text_format.MessageToString(message),
        'repeated_string: "\\303\\274\\352\\234\\237"\n')

  def testPrintNestedMessageAsOneLine(self, message_module):
    message = message_module.TestAllTypes()
    msg = message.repeated_nested_message.add()
    msg.bb = 42
    self.CompareToGoldenText(
        text_format.MessageToString(message, as_one_line=True),
        'repeated_nested_message { bb: 42 }')

  def testPrintRepeatedFieldsAsOneLine(self, message_module):
    message = message_module.TestAllTypes()
    message.repeated_int32.append(1)
    message.repeated_int32.append(1)
    message.repeated_int32.append(3)
    message.repeated_string.append('Google')
    message.repeated_string.append('Zurich')
    self.CompareToGoldenText(
        text_format.MessageToString(message, as_one_line=True),
        'repeated_int32: 1 repeated_int32: 1 repeated_int32: 3 '
        'repeated_string: "Google" repeated_string: "Zurich"')

  def testPrintNestedNewLineInStringAsOneLine(self, message_module):
    message = message_module.TestAllTypes()
    message.optional_string = 'a\nnew\nline'
    self.CompareToGoldenText(
        text_format.MessageToString(message, as_one_line=True),
        'optional_string: "a\\nnew\\nline"')

  def testPrintExoticAsOneLine(self, message_module):
    message = message_module.TestAllTypes()
    message.repeated_int64.append(-9223372036854775808)
    message.repeated_uint64.append(18446744073709551615)
    message.repeated_double.append(123.456)
    message.repeated_double.append(1.23e22)
    message.repeated_double.append(1.23e-18)
    message.repeated_string.append('\000\001\a\b\f\n\r\t\v\\\'"')
    message.repeated_string.append(u'\u00fc\ua71f')
    self.CompareToGoldenText(
        self.RemoveRedundantZeros(
            text_format.MessageToString(message, as_one_line=True)),
        'repeated_int64: -9223372036854775808'
        ' repeated_uint64: 18446744073709551615'
        ' repeated_double: 123.456'
        ' repeated_double: 1.23e+22'
        ' repeated_double: 1.23e-18'
        ' repeated_string: '
        '"\\000\\001\\007\\010\\014\\n\\r\\t\\013\\\\\\\'\\""'
        ' repeated_string: "\\303\\274\\352\\234\\237"')

  def testRoundTripExoticAsOneLine(self, message_module):
    message = message_module.TestAllTypes()
    message.repeated_int64.append(-9223372036854775808)
    message.repeated_uint64.append(18446744073709551615)
    message.repeated_double.append(123.456)
    message.repeated_double.append(1.23e22)
    message.repeated_double.append(1.23e-18)
    message.repeated_string.append('\000\001\a\b\f\n\r\t\v\\\'"')
    message.repeated_string.append(u'\u00fc\ua71f')

    # Test as_utf8 = False.
    wire_text = text_format.MessageToString(
        message, as_one_line=True, as_utf8=False)
    parsed_message = message_module.TestAllTypes()
    r = text_format.Parse(wire_text, parsed_message)
    self.assertIs(r, parsed_message)
    self.assertEquals(message, parsed_message)

    # Test as_utf8 = True.
    wire_text = text_format.MessageToString(
        message, as_one_line=True, as_utf8=True)
    parsed_message = message_module.TestAllTypes()
    r = text_format.Parse(wire_text, parsed_message)
    self.assertIs(r, parsed_message)
    self.assertEquals(message, parsed_message,
                      '\n%s != %s' % (message, parsed_message))

  def testPrintRawUtf8String(self, message_module):
    message = message_module.TestAllTypes()
    message.repeated_string.append(u'\u00fc\ua71f')
    text = text_format.MessageToString(message, as_utf8=True)
    self.CompareToGoldenText(text, 'repeated_string: "\303\274\352\234\237"\n')
    parsed_message = message_module.TestAllTypes()
    text_format.Parse(text, parsed_message)
    self.assertEquals(message, parsed_message,
                      '\n%s != %s' % (message, parsed_message))

  def testPrintFloatFormat(self, message_module):
    # Check that float_format argument is passed to sub-message formatting.
    message = message_module.NestedTestAllTypes()
    # We use 1.25 as it is a round number in binary.  The proto 32-bit float
    # will not gain additional imprecise digits as a 64-bit Python float and
    # show up in its str.  32-bit 1.2 is noisy when extended to 64-bit:
    #  >>> struct.unpack('f', struct.pack('f', 1.2))[0]
    #  1.2000000476837158
    #  >>> struct.unpack('f', struct.pack('f', 1.25))[0]
    #  1.25
    message.payload.optional_float = 1.25
    # Check rounding at 15 significant digits
    message.payload.optional_double = -.000003456789012345678
    # Check no decimal point.
    message.payload.repeated_float.append(-5642)
    # Check no trailing zeros.
    message.payload.repeated_double.append(.000078900)
    formatted_fields = ['optional_float: 1.25',
                        'optional_double: -3.45678901234568e-6',
                        'repeated_float: -5642',
                        'repeated_double: 7.89e-5']
    text_message = text_format.MessageToString(message, float_format='.15g')
    self.CompareToGoldenText(
        self.RemoveRedundantZeros(text_message),
        'payload {{\n  {}\n  {}\n  {}\n  {}\n}}\n'.format(*formatted_fields))
    # as_one_line=True is a separate code branch where float_format is passed.
    text_message = text_format.MessageToString(message, as_one_line=True,
                                               float_format='.15g')
    self.CompareToGoldenText(
        self.RemoveRedundantZeros(text_message),
        'payload {{ {} {} {} {} }}'.format(*formatted_fields))

  def testMessageToString(self, message_module):
    message = message_module.ForeignMessage()
    message.c = 123
    self.assertEqual('c: 123\n', str(message))

  def testParseAllFields(self, message_module):
    message = message_module.TestAllTypes()
    test_util.SetAllFields(message)
    ascii_text = text_format.MessageToString(message)

    parsed_message = message_module.TestAllTypes()
    text_format.Parse(ascii_text, parsed_message)
    self.assertEqual(message, parsed_message)
    if message_module is unittest_pb2:
      test_util.ExpectAllFieldsSet(self, message)

  def testParseExotic(self, message_module):
    message = message_module.TestAllTypes()
    text = ('repeated_int64: -9223372036854775808\n'
            'repeated_uint64: 18446744073709551615\n'
            'repeated_double: 123.456\n'
            'repeated_double: 1.23e+22\n'
            'repeated_double: 1.23e-18\n'
            'repeated_string: \n'
            '"\\000\\001\\007\\010\\014\\n\\r\\t\\013\\\\\\\'\\""\n'
            'repeated_string: "foo" \'corge\' "grault"\n'
            'repeated_string: "\\303\\274\\352\\234\\237"\n'
            'repeated_string: "\\xc3\\xbc"\n'
            'repeated_string: "\xc3\xbc"\n')
    text_format.Parse(text, message)

    self.assertEqual(-9223372036854775808, message.repeated_int64[0])
    self.assertEqual(18446744073709551615, message.repeated_uint64[0])
    self.assertEqual(123.456, message.repeated_double[0])
    self.assertEqual(1.23e22, message.repeated_double[1])
    self.assertEqual(1.23e-18, message.repeated_double[2])
    self.assertEqual(
        '\000\001\a\b\f\n\r\t\v\\\'"', message.repeated_string[0])
    self.assertEqual('foocorgegrault', message.repeated_string[1])
    self.assertEqual(u'\u00fc\ua71f', message.repeated_string[2])
    self.assertEqual(u'\u00fc', message.repeated_string[3])

  def testParseTrailingCommas(self, message_module):
    message = message_module.TestAllTypes()
    text = ('repeated_int64: 100;\n'
            'repeated_int64: 200;\n'
            'repeated_int64: 300,\n'
            'repeated_string: "one",\n'
            'repeated_string: "two";\n')
    text_format.Parse(text, message)

    self.assertEqual(100, message.repeated_int64[0])
    self.assertEqual(200, message.repeated_int64[1])
    self.assertEqual(300, message.repeated_int64[2])
    self.assertEqual(u'one', message.repeated_string[0])
    self.assertEqual(u'two', message.repeated_string[1])

  def testParseEmptyText(self, message_module):
    message = message_module.TestAllTypes()
    text = ''
    text_format.Parse(text, message)
    self.assertEquals(message_module.TestAllTypes(), message)

  def testParseInvalidUtf8(self, message_module):
    message = message_module.TestAllTypes()
    text = 'repeated_string: "\\xc3\\xc3"'
    self.assertRaises(text_format.ParseError, text_format.Parse, text, message)

  def testParseSingleWord(self, message_module):
    message = message_module.TestAllTypes()
    text = 'foo'
    self.assertRaisesRegexp(
        text_format.ParseError,
        (r'1:1 : Message type "\w+.TestAllTypes" has no field named '
         r'"foo".'),
        text_format.Parse, text, message)

  def testParseUnknownField(self, message_module):
    message = message_module.TestAllTypes()
    text = 'unknown_field: 8\n'
    self.assertRaisesRegexp(
        text_format.ParseError,
        (r'1:1 : Message type "\w+.TestAllTypes" has no field named '
         r'"unknown_field".'),
        text_format.Parse, text, message)

  def testParseGroupNotClosed(self, message_module):
    message = message_module.TestAllTypes()
    text = 'RepeatedGroup: <'
    self.assertRaisesRegexp(
        text_format.ParseError, '1:16 : Expected ">".',
        text_format.Parse, text, message)

    text = 'RepeatedGroup: {'
    self.assertRaisesRegexp(
        text_format.ParseError, '1:16 : Expected "}".',
        text_format.Parse, text, message)

  def testParseEmptyGroup(self, message_module):
    message = message_module.TestAllTypes()
    text = 'OptionalGroup: {}'
    text_format.Parse(text, message)
    self.assertTrue(message.HasField('optionalgroup'))

    message.Clear()

    message = message_module.TestAllTypes()
    text = 'OptionalGroup: <>'
    text_format.Parse(text, message)
    self.assertTrue(message.HasField('optionalgroup'))

  def testParseBadEnumValue(self, message_module):
    message = message_module.TestAllTypes()
    text = 'optional_nested_enum: BARR'
    self.assertRaisesRegexp(
        text_format.ParseError,
        (r'1:23 : Enum type "\w+.TestAllTypes.NestedEnum" '
         r'has no value named BARR.'),
        text_format.Parse, text, message)

    message = message_module.TestAllTypes()
    text = 'optional_nested_enum: 100'
    self.assertRaisesRegexp(
        text_format.ParseError,
        (r'1:23 : Enum type "\w+.TestAllTypes.NestedEnum" '
         r'has no value with number 100.'),
        text_format.Parse, text, message)

  def testParseBadIntValue(self, message_module):
    message = message_module.TestAllTypes()
    text = 'optional_int32: bork'
    self.assertRaisesRegexp(
        text_format.ParseError,
        ('1:17 : Couldn\'t parse integer: bork'),
        text_format.Parse, text, message)

  def testParseStringFieldUnescape(self, message_module):
    message = message_module.TestAllTypes()
    text = r'''repeated_string: "\xf\x62"
               repeated_string: "\\xf\\x62"
               repeated_string: "\\\xf\\\x62"
               repeated_string: "\\\\xf\\\\x62"
               repeated_string: "\\\\\xf\\\\\x62"
               repeated_string: "\x5cx20"'''
    text_format.Parse(text, message)

    SLASH = '\\'
    self.assertEqual('\x0fb', message.repeated_string[0])
    self.assertEqual(SLASH + 'xf' + SLASH + 'x62', message.repeated_string[1])
    self.assertEqual(SLASH + '\x0f' + SLASH + 'b', message.repeated_string[2])
    self.assertEqual(SLASH + SLASH + 'xf' + SLASH + SLASH + 'x62',
                     message.repeated_string[3])
    self.assertEqual(SLASH + SLASH + '\x0f' + SLASH + SLASH + 'b',
                     message.repeated_string[4])
    self.assertEqual(SLASH + 'x20', message.repeated_string[5])

  def testMergeDuplicateScalars(self, message_module):
    message = message_module.TestAllTypes()
    text = ('optional_int32: 42 '
            'optional_int32: 67')
    r = text_format.Merge(text, message)
    self.assertIs(r, message)
    self.assertEqual(67, message.optional_int32)

  def testMergeDuplicateNestedMessageScalars(self, message_module):
    message = message_module.TestAllTypes()
    text = ('optional_nested_message { bb: 1 } '
            'optional_nested_message { bb: 2 }')
    r = text_format.Merge(text, message)
    self.assertTrue(r is message)
    self.assertEqual(2, message.optional_nested_message.bb)

  def testParseOneof(self, message_module):
    m = message_module.TestAllTypes()
    m.oneof_uint32 = 11
    m2 = message_module.TestAllTypes()
    text_format.Parse(text_format.MessageToString(m), m2)
    self.assertEqual('oneof_uint32', m2.WhichOneof('oneof_field'))


# These are tests that aren't fundamentally specific to proto2, but are at
# the moment because of differences between the proto2 and proto3 test schemas.
# Ideally the schemas would be made more similar so these tests could pass.
class OnlyWorksWithProto2RightNowTests(TextFormatBase):

  def testParseGolden(self):
    golden_text = '\n'.join(self.ReadGolden('text_format_unittest_data.txt'))
    parsed_message = unittest_pb2.TestAllTypes()
    r = text_format.Parse(golden_text, parsed_message)
    self.assertIs(r, parsed_message)

    message = unittest_pb2.TestAllTypes()
    test_util.SetAllFields(message)
    self.assertEquals(message, parsed_message)

  def testPrintAllFields(self):
    message = unittest_pb2.TestAllTypes()
    test_util.SetAllFields(message)
    self.CompareToGoldenFile(
        self.RemoveRedundantZeros(text_format.MessageToString(message)),
        'text_format_unittest_data_oneof_implemented.txt')

  def testPrintAllFieldsPointy(self):
    message = unittest_pb2.TestAllTypes()
    test_util.SetAllFields(message)
    self.CompareToGoldenFile(
        self.RemoveRedundantZeros(
            text_format.MessageToString(message, pointy_brackets=True)),
        'text_format_unittest_data_pointy_oneof.txt')

  def testPrintInIndexOrder(self):
    message = unittest_pb2.TestFieldOrderings()
    message.my_string = '115'
    message.my_int = 101
    message.my_float = 111
    message.optional_nested_message.oo = 0
    message.optional_nested_message.bb = 1
    self.CompareToGoldenText(
        self.RemoveRedundantZeros(text_format.MessageToString(
            message, use_index_order=True)),
        'my_string: \"115\"\nmy_int: 101\nmy_float: 111\n'
        'optional_nested_message {\n  oo: 0\n  bb: 1\n}\n')
    self.CompareToGoldenText(
        self.RemoveRedundantZeros(text_format.MessageToString(
            message)),
        'my_int: 101\nmy_string: \"115\"\nmy_float: 111\n'
        'optional_nested_message {\n  bb: 1\n  oo: 0\n}\n')

  def testMergeLinesGolden(self):
    opened = self.ReadGolden('text_format_unittest_data.txt')
    parsed_message = unittest_pb2.TestAllTypes()
    r = text_format.MergeLines(opened, parsed_message)
    self.assertIs(r, parsed_message)

    message = unittest_pb2.TestAllTypes()
    test_util.SetAllFields(message)
    self.assertEqual(message, parsed_message)

  def testParseLinesGolden(self):
    opened = self.ReadGolden('text_format_unittest_data.txt')
    parsed_message = unittest_pb2.TestAllTypes()
    r = text_format.ParseLines(opened, parsed_message)
    self.assertIs(r, parsed_message)

    message = unittest_pb2.TestAllTypes()
    test_util.SetAllFields(message)
    self.assertEquals(message, parsed_message)


# Tests of proto2-only features (MessageSet and extensions).
class Proto2Tests(TextFormatBase):

  def testPrintMessageSet(self):
    message = unittest_mset_pb2.TestMessageSetContainer()
    ext1 = unittest_mset_pb2.TestMessageSetExtension1.message_set_extension
    ext2 = unittest_mset_pb2.TestMessageSetExtension2.message_set_extension
    message.message_set.Extensions[ext1].i = 23
    message.message_set.Extensions[ext2].str = 'foo'
    self.CompareToGoldenText(
        text_format.MessageToString(message),
        'message_set {\n'
        '  [protobuf_unittest.TestMessageSetExtension1] {\n'
        '    i: 23\n'
        '  }\n'
        '  [protobuf_unittest.TestMessageSetExtension2] {\n'
        '    str: \"foo\"\n'
        '  }\n'
        '}\n')

  def testPrintMessageSetAsOneLine(self):
    message = unittest_mset_pb2.TestMessageSetContainer()
    ext1 = unittest_mset_pb2.TestMessageSetExtension1.message_set_extension
    ext2 = unittest_mset_pb2.TestMessageSetExtension2.message_set_extension
    message.message_set.Extensions[ext1].i = 23
    message.message_set.Extensions[ext2].str = 'foo'
    self.CompareToGoldenText(
        text_format.MessageToString(message, as_one_line=True),
        'message_set {'
        ' [protobuf_unittest.TestMessageSetExtension1] {'
        ' i: 23'
        ' }'
        ' [protobuf_unittest.TestMessageSetExtension2] {'
        ' str: \"foo\"'
        ' }'
        ' }')

  def testParseMessageSet(self):
    message = unittest_pb2.TestAllTypes()
    text = ('repeated_uint64: 1\n'
            'repeated_uint64: 2\n')
    text_format.Parse(text, message)
    self.assertEqual(1, message.repeated_uint64[0])
    self.assertEqual(2, message.repeated_uint64[1])

    message = unittest_mset_pb2.TestMessageSetContainer()
    text = ('message_set {\n'
            '  [protobuf_unittest.TestMessageSetExtension1] {\n'
            '    i: 23\n'
            '  }\n'
            '  [protobuf_unittest.TestMessageSetExtension2] {\n'
            '    str: \"foo\"\n'
            '  }\n'
            '}\n')
    text_format.Parse(text, message)
    ext1 = unittest_mset_pb2.TestMessageSetExtension1.message_set_extension
    ext2 = unittest_mset_pb2.TestMessageSetExtension2.message_set_extension
    self.assertEquals(23, message.message_set.Extensions[ext1].i)
    self.assertEquals('foo', message.message_set.Extensions[ext2].str)

  def testPrintAllExtensions(self):
    message = unittest_pb2.TestAllExtensions()
    test_util.SetAllExtensions(message)
    self.CompareToGoldenFile(
        self.RemoveRedundantZeros(text_format.MessageToString(message)),
        'text_format_unittest_extensions_data.txt')

  def testPrintAllExtensionsPointy(self):
    message = unittest_pb2.TestAllExtensions()
    test_util.SetAllExtensions(message)
    self.CompareToGoldenFile(
        self.RemoveRedundantZeros(text_format.MessageToString(
            message, pointy_brackets=True)),
        'text_format_unittest_extensions_data_pointy.txt')

  def testParseGoldenExtensions(self):
    golden_text = '\n'.join(self.ReadGolden(
        'text_format_unittest_extensions_data.txt'))
    parsed_message = unittest_pb2.TestAllExtensions()
    text_format.Parse(golden_text, parsed_message)

    message = unittest_pb2.TestAllExtensions()
    test_util.SetAllExtensions(message)
    self.assertEquals(message, parsed_message)

  def testParseAllExtensions(self):
    message = unittest_pb2.TestAllExtensions()
    test_util.SetAllExtensions(message)
    ascii_text = text_format.MessageToString(message)

    parsed_message = unittest_pb2.TestAllExtensions()
    text_format.Parse(ascii_text, parsed_message)
    self.assertEqual(message, parsed_message)

  def testParseBadExtension(self):
    message = unittest_pb2.TestAllExtensions()
    text = '[unknown_extension]: 8\n'
    self.assertRaisesRegexp(
        text_format.ParseError,
        '1:2 : Extension "unknown_extension" not registered.',
        text_format.Parse, text, message)
    message = unittest_pb2.TestAllTypes()
    self.assertRaisesRegexp(
        text_format.ParseError,
        ('1:2 : Message type "protobuf_unittest.TestAllTypes" does not have '
         'extensions.'),
        text_format.Parse, text, message)

  def testMergeDuplicateExtensionScalars(self):
    message = unittest_pb2.TestAllExtensions()
    text = ('[protobuf_unittest.optional_int32_extension]: 42 '
            '[protobuf_unittest.optional_int32_extension]: 67')
    text_format.Merge(text, message)
    self.assertEqual(
        67,
        message.Extensions[unittest_pb2.optional_int32_extension])

  def testParseDuplicateExtensionScalars(self):
    message = unittest_pb2.TestAllExtensions()
    text = ('[protobuf_unittest.optional_int32_extension]: 42 '
            '[protobuf_unittest.optional_int32_extension]: 67')
    self.assertRaisesRegexp(
        text_format.ParseError,
        ('1:96 : Message type "protobuf_unittest.TestAllExtensions" '
         'should not have multiple '
         '"protobuf_unittest.optional_int32_extension" extensions.'),
        text_format.Parse, text, message)

  def testParseDuplicateNestedMessageScalars(self):
    message = unittest_pb2.TestAllTypes()
    text = ('optional_nested_message { bb: 1 } '
            'optional_nested_message { bb: 2 }')
    self.assertRaisesRegexp(
        text_format.ParseError,
        ('1:65 : Message type "protobuf_unittest.TestAllTypes.NestedMessage" '
         'should not have multiple "bb" fields.'),
        text_format.Parse, text, message)

  def testParseDuplicateScalars(self):
    message = unittest_pb2.TestAllTypes()
    text = ('optional_int32: 42 '
            'optional_int32: 67')
    self.assertRaisesRegexp(
        text_format.ParseError,
        ('1:36 : Message type "protobuf_unittest.TestAllTypes" should not '
         'have multiple "optional_int32" fields.'),
        text_format.Parse, text, message)


class TokenizerTest(unittest.TestCase):

  def testSimpleTokenCases(self):
    text = ('identifier1:"string1"\n     \n\n'
            'identifier2 : \n \n123  \n  identifier3 :\'string\'\n'
            'identifiER_4 : 1.1e+2 ID5:-0.23 ID6:\'aaaa\\\'bbbb\'\n'
            'ID7 : "aa\\"bb"\n\n\n\n ID8: {A:inf B:-inf C:true D:false}\n'
            'ID9: 22 ID10: -111111111111111111 ID11: -22\n'
            'ID12: 2222222222222222222 ID13: 1.23456f ID14: 1.2e+2f '
            'false_bool:  0 true_BOOL:t \n true_bool1:  1 false_BOOL1:f ')
    tokenizer = text_format._Tokenizer(text.splitlines())
    methods = [(tokenizer.ConsumeIdentifier, 'identifier1'),
               ':',
               (tokenizer.ConsumeString, 'string1'),
               (tokenizer.ConsumeIdentifier, 'identifier2'),
               ':',
               (tokenizer.ConsumeInt32, 123),
               (tokenizer.ConsumeIdentifier, 'identifier3'),
               ':',
               (tokenizer.ConsumeString, 'string'),
               (tokenizer.ConsumeIdentifier, 'identifiER_4'),
               ':',
               (tokenizer.ConsumeFloat, 1.1e+2),
               (tokenizer.ConsumeIdentifier, 'ID5'),
               ':',
               (tokenizer.ConsumeFloat, -0.23),
               (tokenizer.ConsumeIdentifier, 'ID6'),
               ':',
               (tokenizer.ConsumeString, 'aaaa\'bbbb'),
               (tokenizer.ConsumeIdentifier, 'ID7'),
               ':',
               (tokenizer.ConsumeString, 'aa\"bb'),
               (tokenizer.ConsumeIdentifier, 'ID8'),
               ':',
               '{',
               (tokenizer.ConsumeIdentifier, 'A'),
               ':',
               (tokenizer.ConsumeFloat, float('inf')),
               (tokenizer.ConsumeIdentifier, 'B'),
               ':',
               (tokenizer.ConsumeFloat, -float('inf')),
               (tokenizer.ConsumeIdentifier, 'C'),
               ':',
               (tokenizer.ConsumeBool, True),
               (tokenizer.ConsumeIdentifier, 'D'),
               ':',
               (tokenizer.ConsumeBool, False),
               '}',
               (tokenizer.ConsumeIdentifier, 'ID9'),
               ':',
               (tokenizer.ConsumeUint32, 22),
               (tokenizer.ConsumeIdentifier, 'ID10'),
               ':',
               (tokenizer.ConsumeInt64, -111111111111111111),
               (tokenizer.ConsumeIdentifier, 'ID11'),
               ':',
               (tokenizer.ConsumeInt32, -22),
               (tokenizer.ConsumeIdentifier, 'ID12'),
               ':',
               (tokenizer.ConsumeUint64, 2222222222222222222),
               (tokenizer.ConsumeIdentifier, 'ID13'),
               ':',
               (tokenizer.ConsumeFloat, 1.23456),
               (tokenizer.ConsumeIdentifier, 'ID14'),
               ':',
               (tokenizer.ConsumeFloat, 1.2e+2),
               (tokenizer.ConsumeIdentifier, 'false_bool'),
               ':',
               (tokenizer.ConsumeBool, False),
               (tokenizer.ConsumeIdentifier, 'true_BOOL'),
               ':',
               (tokenizer.ConsumeBool, True),
               (tokenizer.ConsumeIdentifier, 'true_bool1'),
               ':',
               (tokenizer.ConsumeBool, True),
               (tokenizer.ConsumeIdentifier, 'false_BOOL1'),
               ':',
               (tokenizer.ConsumeBool, False)]

    i = 0
    while not tokenizer.AtEnd():
      m = methods[i]
      if type(m) == str:
        token = tokenizer.token
        self.assertEqual(token, m)
        tokenizer.NextToken()
      else:
        self.assertEqual(m[1], m[0]())
      i += 1

  def testConsumeIntegers(self):
    # This test only tests the failures in the integer parsing methods as well
    # as the '0' special cases.
    int64_max = (1 << 63) - 1
    uint32_max = (1 << 32) - 1
    text = '-1 %d %d' % (uint32_max + 1, int64_max + 1)
    tokenizer = text_format._Tokenizer(text.splitlines())
    self.assertRaises(text_format.ParseError, tokenizer.ConsumeUint32)
    self.assertRaises(text_format.ParseError, tokenizer.ConsumeUint64)
    self.assertEqual(-1, tokenizer.ConsumeInt32())

    self.assertRaises(text_format.ParseError, tokenizer.ConsumeUint32)
    self.assertRaises(text_format.ParseError, tokenizer.ConsumeInt32)
    self.assertEqual(uint32_max + 1, tokenizer.ConsumeInt64())

    self.assertRaises(text_format.ParseError, tokenizer.ConsumeInt64)
    self.assertEqual(int64_max + 1, tokenizer.ConsumeUint64())
    self.assertTrue(tokenizer.AtEnd())

    text = '-0 -0 0 0'
    tokenizer = text_format._Tokenizer(text.splitlines())
    self.assertEqual(0, tokenizer.ConsumeUint32())
    self.assertEqual(0, tokenizer.ConsumeUint64())
    self.assertEqual(0, tokenizer.ConsumeUint32())
    self.assertEqual(0, tokenizer.ConsumeUint64())
    self.assertTrue(tokenizer.AtEnd())

  def testConsumeByteString(self):
    text = '"string1\''
    tokenizer = text_format._Tokenizer(text.splitlines())
    self.assertRaises(text_format.ParseError, tokenizer.ConsumeByteString)

    text = 'string1"'
    tokenizer = text_format._Tokenizer(text.splitlines())
    self.assertRaises(text_format.ParseError, tokenizer.ConsumeByteString)

    text = '\n"\\xt"'
    tokenizer = text_format._Tokenizer(text.splitlines())
    self.assertRaises(text_format.ParseError, tokenizer.ConsumeByteString)

    text = '\n"\\"'
    tokenizer = text_format._Tokenizer(text.splitlines())
    self.assertRaises(text_format.ParseError, tokenizer.ConsumeByteString)

    text = '\n"\\x"'
    tokenizer = text_format._Tokenizer(text.splitlines())
    self.assertRaises(text_format.ParseError, tokenizer.ConsumeByteString)

  def testConsumeBool(self):
    text = 'not-a-bool'
    tokenizer = text_format._Tokenizer(text.splitlines())
    self.assertRaises(text_format.ParseError, tokenizer.ConsumeBool)


if __name__ == '__main__':
  unittest.main()
