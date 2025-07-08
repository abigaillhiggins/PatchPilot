import pytest
from create_a_function_to_calculate_factorial_of_a_numb import factorial

def test_positive_numbers():
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120
    assert factorial(10) == 3628800

def test_negative_numbers():
    assert factorial(-1) == "Input must be a non-negative integer."
    assert factorial(-100) == "Input must be a non-negative integer."

def test_invalid_types():
    assert factorial(3.14) == "Input must be a non-negative integer."
    assert factorial("5") == "Input must be a non-negative integer."
    assert factorial([1, 2, 3]) == "Input must be a non-negative integer."

def test_large_numbers():
    # Test with a moderately large number
    assert factorial(15) == 1307674368000
    
def test_edge_cases():
    # Test with boolean values
    assert factorial(True) == 1  # True is equivalent to 1
    assert factorial(False) == 1  # False is equivalent to 0 