"""HTML Generator utility class for generating HTML content."""

class HtmlGenerator:
    def __init__(self):
        pass
        
    def generate_html(self, content: str, title: str = "Generated Content") -> str:
        """Generate an HTML document with the given content."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    {content}
</body>
</html>
""" 