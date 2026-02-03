"""Tests for HTML mapper functions."""

from src.mappers.html_mapper import clean_html


class TestCleanHtml:
    """Tests for clean_html function."""

    def test_removes_script_tags(self) -> None:
        """Removes script tags from HTML."""
        # Arrange
        html = "<html><head><script>alert('test')</script></head><body>Content</body></html>"

        # Act
        result = clean_html(html)

        # Assert
        assert "alert" not in result
        assert "Content" in result

    def test_removes_style_tags(self) -> None:
        """Removes style tags from HTML."""
        # Arrange
        html = "<html><head><style>.test{color:red}</style></head><body>Content</body></html>"

        # Act
        result = clean_html(html)

        # Assert
        assert "color:red" not in result
        assert "Content" in result

    def test_removes_noscript_tags(self) -> None:
        """Removes noscript tags from HTML."""
        # Arrange
        html = "<html><body><noscript>Enable JS</noscript>Content</body></html>"

        # Act
        result = clean_html(html)

        # Assert
        assert "Enable JS" not in result
        assert "Content" in result

    def test_preserves_text_content(self) -> None:
        """Preserves regular text content."""
        # Arrange
        html = "<html><body><h1>Title</h1><p>Paragraph text</p></body></html>"

        # Act
        result = clean_html(html)

        # Assert
        assert "Title" in result
        assert "Paragraph text" in result

    def test_handles_empty_html(self) -> None:
        """Handles empty HTML string."""
        # Arrange / Act
        result = clean_html("")

        # Assert
        assert result.strip() == ""

    def test_handles_multiple_script_tags(self) -> None:
        """Removes multiple script tags."""
        # Arrange
        html = """<html>
            <script>first()</script>
            <body>Content<script>second()</script></body>
            <script>third()</script>
        </html>"""

        # Act
        result = clean_html(html)

        # Assert
        assert "first" not in result
        assert "second" not in result
        assert "third" not in result
        assert "Content" in result
