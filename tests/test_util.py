#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# This file is formatted with Python Black

import logging
import pathlib
import pytest

import ratbag
import ratbag.util


logger = logging.getLogger(__name__)


def test_find_hidraw_devices():
    devices = ratbag.util.find_hidraw_devices()
    for device in devices:
        assert device.startswith("/dev/hidraw")


@pytest.mark.skipif(not pathlib.Path("/dev/hidraw0").exists(), reason="no /dev/hidraw0")
def test_hidraw_info():
    info = ratbag.util.load_device_info("/dev/hidraw0")
    assert info["name"] is not None
    assert info["vid"] is not None
    assert info["pid"] is not None
    assert info["bus"] is not None
    assert info["report_descriptor"] is not None


def test_attr_from_data():
    class Foo(object):
        pass

    bs = bytes(range(16))
    obj = Foo()
    format = [
        ("B", "zero"),
        ("B", "first"),
        (">H", "second"),
        ("<H", "third"),
    ]
    offset = ratbag.util.attr_from_data(obj, format, bs, offset=0)
    assert offset == 6
    assert obj.zero == 0x0
    assert obj.first == 0x1
    assert obj.second == 0x0203
    assert obj.third == 0x0504
    reverse = ratbag.util.attr_to_data(obj, format)
    assert reverse == bs[:offset]

    bs = bytes(range(16))
    obj = Foo()
    format = [("BBB", "list")]
    offset = ratbag.util.attr_from_data(obj, format, bs, offset=0)
    assert offset == 3
    assert obj.list == (0, 1, 2)
    reverse = ratbag.util.attr_to_data(obj, format)
    assert reverse == bs[:offset]

    bs = bytes(range(16))
    obj = Foo()
    format = [("3*BBB", "list")]
    offset = ratbag.util.attr_from_data(obj, format, bs, offset=0)
    assert offset == 9
    assert obj.list == [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
    reverse = ratbag.util.attr_to_data(obj, format)
    assert reverse == bs[:offset]

    bs = bytes(range(16))
    obj = Foo()
    format = [("H", "?"), ("3*BBB", "_")]
    offset = ratbag.util.attr_from_data(obj, format, bs, offset=0)
    assert offset == 11
    reverse = ratbag.util.attr_to_data(obj, format)
    assert reverse == bytes([0] * 11)

    bs = bytes(range(16))
    obj = Foo()
    format = [("H", "something"), ("3*BBB", "other"), ("H", "map_me")]
    offset = ratbag.util.attr_from_data(obj, format, bs, offset=0)
    assert offset == 13
    reverse = ratbag.util.attr_to_data(obj, format, maps={"map_me": lambda x: sum(x)})
    assert reverse[-2] << 8 | reverse[-1] == sum(range(11))


def test_add_to_sparse_tuple():
    t = (None,)
    t = ratbag.util.add_to_sparse_tuple(t, 3, "d")
    assert t == (None, None, None, "d")

    t = ratbag.util.add_to_sparse_tuple(t, 0, "a")
    assert t == ("a", None, None, "d")
    t = ratbag.util.add_to_sparse_tuple(t, 1, "b")
    assert t == ("a", "b", None, "d")

    with pytest.raises(AssertionError):
        ratbag.util.add_to_sparse_tuple(t, 1, "B")

    t = ratbag.util.add_to_sparse_tuple(t, 2, "c")
    assert t == ("a", "b", "c", "d")
    t = ratbag.util.add_to_sparse_tuple(t, 4, "e")
    assert t == ("a", "b", "c", "d", "e")
