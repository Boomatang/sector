from typing import Any
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from sector.cli import current
from sector.github import ReleaseData


class TestResultCommand:
    """Test the result command functionality."""

    @patch("sector.github.info")
    @patch("sector.github.get_related_images")
    @patch("sector.configuration.load")
    @patch("sector.github.get_operator_release_yaml")
    @patch("sector.github.parse_release_yaml_to_repos")
    @patch("sector.logger.get_logger")
    @patch("builtins.print")
    def test_result_includes_kuadrant_operator(
        self,
        mock_print: Mock,
        mock_get_logger: Mock,
        mock_parse_yaml: Mock,
        mock_get_release_yaml: Mock,
        mock_config_load: Mock,
        mock_get_related_images: Mock,
        mock_info: Mock,
    ) -> None:
        """Test that the result command includes kuadrant-operator in the repository list."""
        # Mock the logger
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Mock configuration
        mock_config_load.return_value = {"mapper": {}}

        # Mock get_related_images to raise ValueError for all calls
        mock_get_related_images.side_effect = ValueError("file not found")

        # Mock the release.yaml content and parsing
        test_yaml_content = """
dependencies:
  authorino: "1.0.0"
  limitador: "2.0.0"
        """

        # Mock parsed repos from YAML (without kuadrant-operator)
        class MockRepo:
            def __init__(self, name: str):
                self.name = name
                self.tag = "v1.0.0" if "authorino" in name else "v2.0.0"

            def __str__(self) -> str:
                return self.name

        mock_authorino_repo = MockRepo("authorino@v1.0.0")
        mock_limitador_repo = MockRepo("limitador@v2.0.0")

        mock_parse_yaml.return_value = [mock_authorino_repo, mock_limitador_repo]

        # Mock kuadrant-operator release data - first call for main project, then ValueError for sub-repos
        mock_get_release_yaml.side_effect = [
            ("v3.0.0", test_yaml_content),  # First call for kuadrant-operator
            ValueError("No release found"),  # Second call for authorino
            ValueError("No release found"),  # Third call for limitador
        ]

        # Call the current function using CliRunner
        runner = CliRunner()
        result_output = runner.invoke(current, ["--owner", "kuadrant"])

        # Verify the command executed successfully
        assert result_output.exit_code == 0

        # Verify that the kuadrant-operator release.yaml was fetched (first call)
        assert mock_get_release_yaml.call_count == 3
        mock_get_release_yaml.assert_any_call(
            mock_logger, "kuadrant", "kuadrant-operator", "latest"
        )

        # Verify that the YAML was parsed
        mock_parse_yaml.assert_called_once_with(test_yaml_content)

        # Verify the output contains the expected information
        output_text = result_output.output

        # Check that we printed information about 3 repositories (kuadrant-operator + 2 dependencies)
        assert "Extracted 3 repositories:" in output_text

        # Verify that kuadrant-operator appears in the printed output
        assert "kuadrant-operator@v3.0.0" in output_text
        assert "authorino@v1.0.0" in output_text
        assert "limitador@v2.0.0" in output_text

    @patch("sector.configuration.load")
    @patch("sector.logger.get_logger")
    @patch("builtins.print")
    def test_result_handles_error(
        self,
        mock_print: Mock,
        mock_get_logger: Mock,
        mock_config_load: Mock,
    ) -> None:
        """Test that the result command handles errors gracefully."""
        # Mock the logger
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Mock an error when loading configuration
        mock_config_load.side_effect = ValueError("Configuration file not found")

        # Call the current function using CliRunner
        runner = CliRunner()
        result_output = runner.invoke(current, ["--owner", "kuadrant"])

        # Verify the command executed successfully (errors are handled gracefully)
        assert result_output.exit_code == 0

        # Verify that the error was printed
        output_text = result_output.output
        assert "Error:" in output_text
        assert "Configuration file not found" in output_text
