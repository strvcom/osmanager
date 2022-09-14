#!/usr/bin/env python
# -*- coding: utf-8 -*-

def fibonacci(n: int) -> int:
    """Return nth number from Fibonacci sequence."""
    if not isinstance(n, int):
        raise TypeError(f"Type '{type(n)}' is not supported for 'n' argument")

    if n < 0:
        raise ValueError("Only positive integers are allowed for 'n'")

    if n == 0:
        return 0

    if n in [1, 2]:
        return 1

    return fibonacci(n - 1) + fibonacci(n - 2)
