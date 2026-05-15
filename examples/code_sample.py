"""Code-sample fixture for Engineering Copilot demo runs.

This is benign Python the agent reviews. Keep it small enough that the LLM
response stays well under token budget, and obviously non-secret so judges
don't have to ask 'is that real production code?'."""


def fibonacci(n: int) -> int:
    """Return the n-th Fibonacci number. n=0 -> 0, n=1 -> 1, etc."""
    if n < 0:
        raise ValueError("n must be non-negative")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True
