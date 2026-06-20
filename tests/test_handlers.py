from handlers import _format_code


def test_format_code_six_digits():
    assert _format_code("123456") == "123 456"


def test_format_code_other_length_unchanged():
    assert _format_code("12345") == "12345"
    assert _format_code("") == ""
