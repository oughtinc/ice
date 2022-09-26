from ice.formatter.transform.value import numbered_list
from ice.formatter.transform.value import ValueTransform


def test_numbered_list():
    value = ["Paragraph Uno.", "Paragraph Dos  "]
    xform = numbered_list(value, separator="\n\n")
    assert isinstance(xform, ValueTransform)
    assert xform.transform() == "1. Paragraph Uno.\n\n2. Paragraph Dos"
