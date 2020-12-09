"""
The MIT License
Copyright (c) 2015 Fred Stober
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

class BTFailure(Exception):
	pass

# Encoding functions ##############################################

import sys
if sys.version_info[0] >= 3:
	str_to_bytes = lambda x: x.encode('ascii')
else:
	str_to_bytes = lambda x: x

def bencode_proc(result, x):
	t = type(x)
	if t == str:
		result.extend((str_to_bytes(str(len(x))), b':', str_to_bytes(x)))
	elif t == bytes:
		result.extend((str_to_bytes(str(len(x))), b':', x))
	elif t == int:
		result.extend((b'i', str_to_bytes(str(x)), b'e'))
	elif t == dict:
		result.append(b'd')
		for k, v in sorted(x.items()):
			bencode_proc(result, k)
			bencode_proc(result, v)
		result.append(b'e')
	elif t == list:
		result.append(b'l')
		for item in x:
			bencode_proc(result, item)
		result.append(b'e')

def bencode(x):
	result = []
	bencode_proc(result, x)
	return b''.join(result)

# Decoding functions ##############################################

bdecode_marker_int = ord('i')
bdecode_marker_str_min = ord('0')
bdecode_marker_str_max = ord('9')
bdecode_marker_list = ord('l')
bdecode_marker_dict = ord('d')
bdecode_marker_end = ord('e')

def bdecode_proc(msg, pos):
	t = msg[pos]
	if t == bdecode_marker_int:
		pos += 1
		pos_end = msg.index(b'e', pos)
		return (int(msg[pos:pos_end]), pos_end + 1)
	elif t >= bdecode_marker_str_min and t <= bdecode_marker_str_max:
		sep = msg.index(b':', pos)
		n = int(msg[pos:sep])
		sep += 1
		return (bytes(msg[sep:sep + n]), sep + n)
	elif t == bdecode_marker_dict:
		result = {}
		pos += 1
		while msg[pos] != bdecode_marker_end:
			k, pos = bdecode_proc(msg, pos)
			result[k], pos = bdecode_proc(msg, pos)
		return (result, pos + 1)
	elif t == bdecode_marker_list:
		result = []
		pos += 1
		while msg[pos] != bdecode_marker_end:
			v, pos = bdecode_proc(msg, pos)
			result.append(v)
		return (result, pos + 1)
	raise BTFailure("invalid bencoded data (invalid token)! %r" % msg)

def bdecode_extra(msg):
	try:
		result, pos = bdecode_proc(bytearray(msg), 0)
	except (IndexError, KeyError, ValueError):
		raise BTFailure("invalid bencoded data! %r" % msg)
	return (result, pos)

def bdecode(msg):
	try:
		result, pos = bdecode_extra(msg)
	except (IndexError, KeyError, ValueError):
		raise BTFailure("invalid bencoded data: %r" % msg)
	if pos != len(msg):
		raise BTFailure("invalid bencoded value (data after valid prefix)")
	return result

if __name__ == '__main__':
	import logging
	logging.basicConfig()
	test = {b'k1': 145, b'k2': {b'sk1': list(range(10)), b'sk2': b'0'*60}}
	for x in range(100):
		assert(bdecode(bencode(test)) == test)
	for test_bytes in [b'd5:keyi0ee', b'x3:keyi0ee', b'd3:keyi0ee...']:
		try:
			bdecode(test_bytes)
		except BTFailure as ex:
			logging.exception('expected bdecode exception')