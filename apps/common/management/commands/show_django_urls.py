from django.core.management.base import BaseCommand
from django.urls import get_resolver


class Command(BaseCommand):
    help = "Extracts all URL paths from the project"

    def handle(self, *args, **options):
        # Get the URL resolver
        resolver = get_resolver()

        # List to store all URL paths
        all_paths = []

        def extract_paths(patterns, prefix=""):
            """Extract all URL paths recursively."""
            for pattern in patterns:
                current_path = prefix

                # Extract pattern string based on pattern type
                if hasattr(pattern, "pattern"):
                    # Try different pattern attributes based on Django version
                    if hasattr(pattern.pattern, "regex"):
                        # Django 1.x style
                        pattern_str = pattern.pattern.regex.pattern.replace("^", "").replace("$", "")
                    elif hasattr(pattern.pattern, "_route"):
                        # Django 3.x+ path() style
                        pattern_str = pattern.pattern._route
                    else:
                        # Fallback
                        pattern_str = str(pattern.pattern)

                    current_path += pattern_str
                    all_paths.append(current_path)

                # Process nested patterns
                if hasattr(pattern, "url_patterns"):
                    new_prefix = current_path
                    extract_paths(pattern.url_patterns, new_prefix)

        # Extract all paths
        extract_paths(resolver.url_patterns)

        # Display results with nice formatting
        self.stdout.write(self.style.SUCCESS(f"Found {len(all_paths)} URL paths:"))
        for path in all_paths:
            self.stdout.write(f"  {path}")
