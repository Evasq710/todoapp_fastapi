import pytest

class Student:
    def __init__(self, first_name: str, last_name: str, major: str, years: int):
        self.first_name = first_name
        self.last_name = last_name
        self.major = major
        self.years = years


def test_equal_or_not_equal():
    assert 3 == 3
    assert isinstance(3, int)


# The value that the function returns is the value that the test functions will use
# Combined with "yield", we can set up the resource first, execute the test, and then tear down the resource
@pytest.fixture
def default_student() -> Student:
    return Student('John', 'Doe', 'Computer Science', 3)

def test_person_initialization(default_student):
    assert default_student.first_name == 'John', 'First name should be "John".'
    assert default_student.last_name == 'Doe', 'Last name should be "Doe"'
    assert default_student.major == 'Computer Science'
    assert default_student.years == 3