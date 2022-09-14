#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from parameterized import parameterized
from osman.example import fibonacci


@parameterized.expand(
    [
        ('Fibonacci test for n = 0', 0, 0),
        ('Fibonacci test for n = 1', 1, 1),
        ('Fibonacci test for n = 2', 2, 1),
        ('Fibonacci test for n = 10', 10, 55),
    ]
)
def test_fibonacci_with_allowed_argument(_, n, expected):
    result = fibonacci(n)
    assert result == expected


@parameterized.expand(
    [
        ('Fibonacci test for n = -1', -1),
    ]
)
def test_fibonacci_with_wrong_argument(_, n):
    with pytest.raises(ValueError):
        _ = fibonacci(n)


@parameterized.expand(
    [
        ('Fibonacci test for n as None', None),
        ('Fibonacci test for n as str', '1'),
        ('Fibonacci test for n as float', 1.5),
    ]
)
def test_fibonacci_with_missing_argument(_, n):
    with pytest.raises(TypeError):
        _ = fibonacci(n)
