from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from sector.cli import result
from sector.github import ReleaseData


class TestResultCommand:
    """Test the result command functionality."""

    @patch("sector.github.get_kuadrant_operator_release_yaml")
    @patch("sector.github.parse_release_yaml_to_repos")
    @patch("sector.github.Repo")
    @patch("sector.logger.get_logger")
    @patch("builtins.print")
    def test_result_includes_kuadrant_operator(
        self,
        mock_print,
        mock_get_logger,
        mock_repo_class,
        mock_parse_yaml,
        mock_get_release_yaml,
    ):
        """Test that the result command includes kuadrant-operator in the repository list."""
        # Mock the logger
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Mock the release.yaml content and parsing
        test_yaml_content = """
dependencies:
  authorino: "1.0.0"
  limitador: "2.0.0"
        """

        # Mock parsed repos from YAML (without kuadrant-operator)
        mock_authorino_repo = Mock()
        mock_authorino_repo.__str__ = Mock(return_value="authorino@v1.0.0")
        mock_limitador_repo = Mock()
        mock_limitador_repo.__str__ = Mock(return_value="limitador@v2.0.0")

        mock_parse_yaml.return_value = [mock_authorino_repo, mock_limitador_repo]

        # Mock kuadrant-operator release data
        mock_get_release_yaml.return_value = ("v3.0.0", test_yaml_content)

        # Mock the kuadrant-operator repo creation
        mock_kuadrant_repo = Mock()
        mock_kuadrant_repo.__str__ = Mock(return_value="kuadrant-operator@v3.0.0")
        mock_repo_class.return_value = mock_kuadrant_repo

        # Call the result function using CliRunner
        runner = CliRunner()
        result_output = runner.invoke(result, ["--owner", "kuadrant"])

        # Verify the command executed successfully
        assert result_output.exit_code == 0

        # Verify that the kuadrant-operator release.yaml was fetched
        mock_get_release_yaml.assert_called_once_with("kuadrant", mock_logger)

        # Verify that the YAML was parsed
        mock_parse_yaml.assert_called_once_with(test_yaml_content)

        # Verify that kuadrant-operator Repo was created with the correct tag
        mock_repo_class.assert_called_once_with("kuadrant-operator@v3.0.0")

        # Verify the output contains the expected information
        output_text = result_output.output

        # Check that we printed information about 3 repositories (kuadrant-operator + 2 dependencies)
        assert "Extracted 3 repositories:" in output_text

        # Verify that kuadrant-operator appears in the printed output
        assert "kuadrant-operator@v3.0.0" in output_text
        assert "authorino@v1.0.0" in output_text
        assert "limitador@v2.0.0" in output_text

    @patch("sector.github.get_kuadrant_operator_release_yaml")
    @patch("sector.logger.get_logger")
    @patch("builtins.print")
    def test_result_handles_error(
        self, mock_print, mock_get_logger, mock_get_release_yaml
    ):
        """Test that the result command handles errors gracefully."""
        # Mock the logger
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Mock an error when fetching release.yaml
        mock_get_release_yaml.side_effect = ValueError(
            "No release found for kuadrant-operator"
        )

        # Call the result function using CliRunner
        runner = CliRunner()
        result_output = runner.invoke(result, ["--owner", "kuadrant"])

        # Verify the command executed successfully (errors are handled gracefully)
        assert result_output.exit_code == 0

        # Verify that the error was printed
        output_text = result_output.output
        assert "Error:" in output_text
        assert "No release found for kuadrant-operator" in output_text
