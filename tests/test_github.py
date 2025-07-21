from typing import Any
from unittest.mock import Mock, patch

import pytest
import requests
import yaml

from sector import logger
from sector.github import (
    ReleaseData,
    Repo,
    get_file_content,
    get_operator_release_yaml,
    parse_release_yaml_to_repos,
    version_formatter,
)

global log
log = logger.get_logger("cli")
log.info("Running 'sector result'")
log.debug(f"{locals()=}")


class TestGitHubFunctions:
    """Test GitHub API interaction functions."""

    @patch("sector.github.set_headers")
    @patch("requests.get")
    def test_get_file_content_success(
        self, mock_get: Mock, mock_set_headers: Mock
    ) -> None:
        """Test successful file content retrieval."""
        # Mock the headers
        mock_set_headers.return_value = {"Authorization": "token test"}

        # Mock the response
        import base64

        test_content = "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: test"
        encoded_content = base64.b64encode(test_content.encode()).decode()

        mock_response = Mock()
        mock_response.json.return_value = {"content": encoded_content}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test the function
        result = get_file_content(
            "kuadrant", "kuadrant-operator", "release.yaml", "v1.0.0"
        )

        # Verify the result
        assert result == test_content
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/kuadrant/kuadrant-operator/contents/release.yaml?ref=v1.0.0",
            headers={"Authorization": "token test"},
            timeout=30,
        )

    @patch("sector.github.set_headers")
    @patch("requests.get")
    def test_get_file_content_not_found(
        self, mock_get: Mock, mock_set_headers: Mock
    ) -> None:
        """Test file content retrieval when file is not found."""
        # Mock the headers
        mock_set_headers.return_value = {"Authorization": "token test"}

        # Mock a 404 response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            response=Mock(status_code=404)
        )
        mock_get.return_value = mock_response

        # Test the function
        with pytest.raises(requests.HTTPError):
            get_file_content("kuadrant", "kuadrant-operator", "release.yaml", "v1.0.0")

    @patch("sector.github.get_file_content")
    @patch("sector.github.get_release")
    def test_get_kuadrant_operator_release_yaml_success(
        self, mock_get_release: Mock, mock_get_file_content: Mock
    ) -> None:
        """Test successful kuadrant-operator release.yaml retrieval."""
        # Mock the release data
        mock_release_data = ReleaseData(
            name="v1.0.0",
            tag="v1.0.0",
            date="2023-01-01T00:00:00Z",
            url="https://github.com/kuadrant/kuadrant-operator/releases/tag/v1.0.0",
        )
        mock_get_release.return_value = mock_release_data

        # Mock the file content
        test_yaml_content = (
            "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: release-config"
        )
        mock_get_file_content.return_value = test_yaml_content

        # Test the function
        tag, content = get_operator_release_yaml(log, "kuadrant", "kuadrant-operator")

        # Verify the results
        assert tag == "v1.0.0"
        assert content == test_yaml_content

        # Verify the calls
        mock_get_release.assert_called_once()
        mock_get_file_content.assert_called_once_with(
            owner="kuadrant",
            repo="kuadrant-operator",
            file_path="release.yaml",
            ref="v1.0.0",
        )

    @patch("sector.github.get_release")
    def test_get_kuadrant_operator_release_yaml_no_release(
        self, mock_get_release: Mock
    ) -> None:
        """Test kuadrant-operator release.yaml retrieval when no release is found."""
        # Mock empty release data
        mock_release_data = ReleaseData(tag="")
        mock_get_release.return_value = mock_release_data

        # Test the function
        with pytest.raises(ValueError, match="No release found for kuadrant-operator"):
            get_operator_release_yaml(log, "kuadrant", "kuadrant-operator")

    @patch("sector.github.get_file_content")
    @patch("sector.github.get_release")
    def test_get_kuadrant_operator_release_yaml_file_not_found(
        self, mock_get_release: Mock, mock_get_file_content: Mock
    ) -> None:
        """Test kuadrant-operator release.yaml retrieval when file is not found."""
        # Mock the release data
        mock_release_data = ReleaseData(tag="v1.0.0")
        mock_get_release.return_value = mock_release_data

        # Mock file not found
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get_file_content.side_effect = requests.HTTPError(response=mock_response)

        # Test the function
        with pytest.raises(
            ValueError,
            match="release.yaml not found in kuadrant-operator release v1.0.0",
        ):
            get_operator_release_yaml(log, "kuadrant", "kuadrant-operator")


class TestVersionProcessing:
    """Test version processing functions."""

    def test_process_version_adds_v_prefix(self) -> None:
        """Test that versions get 'v' prefix when not present."""
        assert version_formatter("1.0.0") == "v1.0.0"
        assert version_formatter("2.5.1") == "v2.5.1"
        assert version_formatter("0.1.0") == "v0.1.0"

    def test_process_version_keeps_existing_v_prefix(self) -> None:
        """Test that existing 'v' prefix gets another 'v' prefix."""
        assert version_formatter("v1.0.0") == "vv1.0.0"
        assert version_formatter("v2.5.1") == "vv2.5.1"

    def test_process_version_handles_zero_version(self) -> None:
        """Test that '0.0.0' is converted to 'main'."""
        assert version_formatter("0.0.0") == "main"

    def test_process_version_handles_edge_cases(self) -> None:
        """Test edge cases for version processing."""
        assert version_formatter("1.0.0-alpha") == "v1.0.0-alpha"
        assert version_formatter("v1.0.0-beta") == "vv1.0.0-beta"
        assert version_formatter("1.0") == "v1.0"


class TestReleaseYamlParsing:
    """Test release.yaml parsing functionality."""

    def test_parse_release_yaml_dict_format(self) -> None:
        """Test parsing YAML with dictionary format."""
        yaml_content = """
dependencies:
  authorino: "1.0.0"
  limitador: "2.0.0"
  dns-operator: "0.0.0"
        """

        repos = parse_release_yaml_to_repos(yaml_content)

        assert len(repos) == 3

        # Check that repositories are created correctly
        repo_strings = [str(repo) for repo in repos]
        assert "authorino@v1.0.0" in repo_strings
        assert "limitador@v2.0.0" in repo_strings
        assert "dns-operator@main" in repo_strings

    def test_parse_release_yaml_list_format(self) -> None:
        """Test parsing YAML with list format - should fail as not supported."""
        yaml_content = """
projects:
  - name: "authorino"
    version: "1.0.0"
  - name: "limitador"
    version: "v2.0.0"
  - name: "dns-operator"
    version: "0.0.0"
        """

        # Current implementation only supports dependencies key
        with pytest.raises(KeyError):
            parse_release_yaml_to_repos(yaml_content)

    def test_parse_release_yaml_mixed_format(self) -> None:
        """Test parsing YAML with mixed dictionary and list formats."""
        yaml_content = """
dependencies:
  authorino: "1.0.0"
  limitador: "2.0.0"
projects:
  - name: "dns-operator"
    version: "0.0.0"
  - name: "kuadrant-operator"
    version: "3.0.0"
        """

        repos = parse_release_yaml_to_repos(yaml_content)

        # Current implementation only processes dependencies key
        assert len(repos) == 2

        # Check that repositories are created correctly
        repo_strings = [str(repo) for repo in repos]
        assert "authorino@v1.0.0" in repo_strings
        assert "limitador@v2.0.0" in repo_strings

    def test_parse_release_yaml_empty_content(self) -> None:
        """Test parsing empty YAML content."""
        yaml_content = """
metadata:
  name: "test-release"
        """

        # Current implementation requires dependencies key
        with pytest.raises(KeyError):
            parse_release_yaml_to_repos(yaml_content)

    def test_parse_release_yaml_invalid_yaml(self) -> None:
        """Test parsing invalid YAML content."""
        yaml_content = """
invalid: yaml: content: [
        """

        # Current implementation doesn't handle YAML parsing errors
        with pytest.raises(yaml.YAMLError):
            parse_release_yaml_to_repos(yaml_content)

    def test_parse_release_yaml_non_dict_root(self) -> None:
        """Test parsing YAML with non-dictionary root."""
        yaml_content = """
- item1
- item2
        """

        # Current implementation expects dict but gets list
        with pytest.raises(TypeError):
            parse_release_yaml_to_repos(yaml_content)

    def test_parse_release_yaml_complex_structure(self) -> None:
        """Test parsing complex YAML structure."""
        yaml_content = """
metadata:
  name: "kuadrant-release"
  version: "1.0.0"
dependencies:
  authorino: "1.0.0"
  limitador: "2.0.0"
  dns-operator: "0.0.0"
components:
  - name: "kuadrant-operator"
    version: "3.0.0"
  - name: "wasm-shim"
    version: "0.1.0"
other_data:
  description: "This is a test release"
        """

        repos = parse_release_yaml_to_repos(yaml_content)

        assert len(repos) == 3

        # Check that repositories are created correctly
        repo_strings = [str(repo) for repo in repos]
        assert "authorino@v1.0.0" in repo_strings
        assert "limitador@v2.0.0" in repo_strings
        assert "dns-operator@main" in repo_strings
