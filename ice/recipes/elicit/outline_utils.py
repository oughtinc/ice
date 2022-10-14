def parse_outline(outline_str: str):
    # A helper function to create a nested outline from a list of lines
    def make_nested_outline(outline_str):
        """
        Create a nested outline from a list of lines.

        Approach: Split by "\n-" for top-level, recurse, split by "\n -" for level 1, etc.
        """
        if not outline_str:
            return []
        split_str = "\n-"
        assert outline_str.startswith("-")
        outline_str = outline_str[1:]
        groups = outline_str.split(split_str)
        for group in groups:
            if not group:
                continue
            title, *content_lines = group.split("\n")
            if not content_lines:
                yield {"title": title.strip(), "content": []}
                continue
            leading_spaces = len(content_lines[0]) - len(content_lines[0].lstrip())
            content_lines = [line[leading_spaces:] for line in content_lines]
            yield {
                "title": title.strip(),
                "content": list(make_nested_outline("\n".join(content_lines))),
            }

    return list(make_nested_outline(outline_str.strip()))


def test_parse_outline():
    # Test case 1: a simple outline with two top-level items and one sub-item each
    outline_str_1 = """
- Item 1
  - Sub-item 1.1
- Item 2
  - Sub-item 2.1
"""
    expected_1 = [
        {"title": "Item 1", "content": [{"title": "Sub-item 1.1", "content": []}]},
        {"title": "Item 2", "content": [{"title": "Sub-item 2.1", "content": []}]},
    ]
    actual_1 = parse_outline(outline_str_1)
    assert actual_1 == expected_1

    # Test case 2: a more complex outline with multiple levels and mixed bullet types
    outline_str_2 = """
- Introduction
  - Motivation
  - Scope
- Methods
  - Data collection
    - Surveys
    - Interviews
  - Data analysis
    - Descriptive statistics
    - Inferential statistics
- Results
  - Summary
  - Discussion
- Conclusion
  - Implications
  - Limitations
  - Future work
"""
    expected_2 = [
        {
            "title": "Introduction",
            "content": [
                {"title": "Motivation", "content": []},
                {"title": "Scope", "content": []},
            ],
        },
        {
            "title": "Methods",
            "content": [
                {
                    "title": "Data collection",
                    "content": [
                        {"title": "Surveys", "content": []},
                        {"title": "Interviews", "content": []},
                    ],
                },
                {
                    "title": "Data analysis",
                    "content": [
                        {"title": "Descriptive statistics", "content": []},
                        {"title": "Inferential statistics", "content": []},
                    ],
                },
            ],
        },
        {
            "title": "Results",
            "content": [
                {"title": "Summary", "content": []},
                {"title": "Discussion", "content": []},
            ],
        },
        {
            "title": "Conclusion",
            "content": [
                {"title": "Implications", "content": []},
                {"title": "Limitations", "content": []},
                {"title": "Future work", "content": []},
            ],
        },
    ]
    assert parse_outline(outline_str_2) == expected_2

    # Test case 3: an empty outline
    outline_str_3 = ""
    expected_3 = []
    assert parse_outline(outline_str_3) == expected_3


test_parse_outline()
