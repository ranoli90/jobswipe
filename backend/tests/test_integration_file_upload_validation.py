"""
Integration tests for file upload validation
Tests complete file upload workflow including validation, storage, and parsing
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


class TestFileUploadValidationIntegration:
    """Integration tests for file upload validation workflow"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def valid_pdf_content(self):
        """Create valid PDF content for testing"""
        # Simple PDF header for testing
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF"

    @pytest.fixture
    def valid_docx_content(self):
        """Create valid DOCX content for testing"""
        # Minimal DOCX structure (ZIP with required files)
        import zipfile

        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add required DOCX structure
            zf.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
            )
            zf.writestr(
                "_rels/.rels",
                '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
            )
            zf.writestr(
                "word/_rels/document.xml.rels",
                '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>',
            )
            zf.writestr(
                "word/document.xml",
                '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Test document content</w:t></w:r></w:p></w:body></w:document>',
            )

        return buffer.getvalue()

    @pytest.fixture
    def malicious_exe_content(self):
        """Create malicious executable content for testing"""
        return b"\x4d\x5a\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00\xb8\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x0e\x1f\xba\x0e\x00\xb4\x09\xcd\x21\xb8\x01\x4c\xcd\x21\x54\x68\x69\x73\x20\x70\x72\x6f\x67\x72\x61\x6d\x20\x63\x61\x6e\x6e\x6f\x74\x20\x62\x65\x20\x72\x75\x6e\x20\x69\x6e\x20\x44\x4f\x53\x20\x6d\x6f\x64\x65"

    def test_resume_upload_valid_pdf_success(self, client, valid_pdf_content):
        """Test successful resume upload with valid PDF"""
        # Mock authentication
        with patch("backend.api.routers.profile.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = "test-user-id"
            mock_get_user.return_value = mock_user

            # Mock database
            with patch("backend.db.database.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db

                # Mock profile
                mock_profile = MagicMock()
                mock_db.query.return_value.filter.return_value.first.return_value = (
                    None  # No existing profile
                )

                # Mock storage upload
                with patch("backend.services.storage.upload_file") as mock_upload:
                    # Mock resume parser
                    with patch(
                        "backend.services.resume_parser_enhanced.parse_resume_enhanced",
                        new_callable=AsyncMock,
                    ) as mock_parse:
                        mock_parse.return_value = {
                            "full_name": "John Doe",
                            "email": "john@example.com",
                            "phone": "123-456-7890",
                            "skills": ["Python", "JavaScript"],
                            "work_experience": [
                                {"position": "Developer", "company": "Tech Corp"}
                            ],
                            "education": [{"degree": "BS CS", "school": "University"}],
                            "parsed_at": "2026-01-27T12:00:00",
                        }

                        # Create test file
                        files = {
                            "file": ("resume.pdf", valid_pdf_content, "application/pdf")
                        }

                        response = client.post("/api/profile/resume", files=files)

                        assert response.status_code == 200
                        data = response.json()
                        assert data["full_name"] == "John Doe"
                        assert data["skills"] == ["Python", "JavaScript"]
                        assert "resume_file_url" in data

                        # Verify storage was called
                        mock_upload.assert_called_once()
                        # Verify parser was called
                        mock_parse.assert_called_once_with(
                            valid_pdf_content, "resume.pdf"
                        )

    def test_resume_upload_valid_docx_success(self, client, valid_docx_content):
        """Test successful resume upload with valid DOCX"""
        with patch("backend.api.routers.profile.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = "test-user-id"
            mock_get_user.return_value = mock_user

            with patch("backend.db.database.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db

                mock_profile = MagicMock()
                mock_db.query.return_value.filter.return_value.first.return_value = None

                with patch("backend.services.storage.upload_file"):
                    with patch(
                        "backend.services.resume_parser_enhanced.parse_resume_enhanced",
                        new_callable=AsyncMock,
                    ) as mock_parse:
                        mock_parse.return_value = {
                            "full_name": "Jane Smith",
                            "skills": ["Java", "Spring"],
                            "parsed_at": "2026-01-27T12:00:00",
                        }

                        files = {
                            "file": (
                                "resume.docx",
                                valid_docx_content,
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            )
                        }

                        response = client.post("/api/profile/resume", files=files)

                        assert response.status_code == 200
                        data = response.json()
                        assert data["full_name"] == "Jane Smith"

    def test_resume_upload_malicious_file_blocked(self, client, malicious_exe_content):
        """Test that malicious executable files are blocked"""
        with patch("backend.api.routers.profile.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_get_user.return_value = mock_user

            # Create malicious file with .pdf extension (attempted bypass)
            files = {
                "file": ("malicious.pdf", malicious_exe_content, "application/pdf")
            }

            response = client.post("/api/profile/resume", files=files)

            # Should be blocked by file validation
            assert response.status_code == 400 or response.status_code == 422

    def test_resume_upload_oversized_file_blocked(self, client):
        """Test that oversized files are blocked"""
        with patch("backend.api.routers.profile.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_get_user.return_value = mock_user

            # Create file larger than 5MB limit
            large_content = b"x" * (6 * 1024 * 1024)  # 6MB
            files = {"file": ("large.pdf", large_content, "application/pdf")}

            response = client.post("/api/profile/resume", files=files)

            # Should be blocked by size validation
            assert response.status_code == 413 or response.status_code == 422

    def test_resume_upload_invalid_extension_blocked(self, client, valid_pdf_content):
        """Test that files with invalid extensions are blocked"""
        with patch("backend.api.routers.profile.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_get_user.return_value = mock_user

            # Valid PDF content but with .exe extension
            files = {"file": ("resume.exe", valid_pdf_content, "application/pdf")}

            response = client.post("/api/profile/resume", files=files)

            # Should be blocked by extension validation
            assert response.status_code == 400 or response.status_code == 422

    def test_resume_upload_path_traversal_blocked(self, client, valid_pdf_content):
        """Test that path traversal attempts are blocked"""
        with patch("backend.api.routers.profile.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_get_user.return_value = mock_user

            # Attempt path traversal
            files = {
                "file": (
                    "../../../etc/passwd.pdf",
                    valid_pdf_content,
                    "application/pdf",
                )
            }

            response = client.post("/api/profile/resume", files=files)

            # Should be blocked by filename validation
            assert response.status_code == 400 or response.status_code == 422

    def test_resume_upload_double_extension_blocked(self, client, valid_pdf_content):
        """Test that double extensions are blocked"""
        with patch("backend.api.routers.profile.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_get_user.return_value = mock_user

            # Double extension (common malware technique)
            files = {"file": ("resume.pdf.exe", valid_pdf_content, "application/pdf")}

            response = client.post("/api/profile/resume", files=files)

            # Should be blocked by filename validation
            assert response.status_code == 400 or response.status_code == 422

    def test_resume_upload_parsing_failure_handled(self, client, valid_pdf_content):
        """Test handling of resume parsing failures"""
        with patch("backend.api.routers.profile.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = "test-user-id"
            mock_get_user.return_value = mock_user

            with patch("backend.db.database.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db

                mock_profile = MagicMock()
                mock_db.query.return_value.filter.return_value.first.return_value = None

                with patch("backend.services.storage.upload_file"):
                    # Mock parser failure
                    with patch(
                        "backend.services.resume_parser_enhanced.parse_resume_enhanced",
                        new_callable=AsyncMock,
                    ) as mock_parse:
                        mock_parse.side_effect = Exception("Parsing failed")

                        files = {
                            "file": ("resume.pdf", valid_pdf_content, "application/pdf")
                        }

                        response = client.post("/api/profile/resume", files=files)

                        # Should handle parsing failure gracefully
                        assert response.status_code == 500
                        assert (
                            "Failed to upload and parse resume"
                            in response.json()["detail"]
                        )

    def test_resume_upload_storage_failure_handled(self, client, valid_pdf_content):
        """Test handling of storage upload failures"""
        with patch("backend.api.routers.profile.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = "test-user-id"
            mock_get_user.return_value = mock_user

            with patch("backend.db.database.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db

                mock_profile = MagicMock()
                mock_db.query.return_value.filter.return_value.first.return_value = None

                # Mock storage failure
                with patch(
                    "backend.services.storage.upload_file",
                    side_effect=Exception("Storage unavailable"),
                ):
                    files = {
                        "file": ("resume.pdf", valid_pdf_content, "application/pdf")
                    }

                    response = client.post("/api/profile/resume", files=files)

                    # Should handle storage failure
                    assert response.status_code == 500

    def test_resume_upload_updates_existing_profile(self, client, valid_pdf_content):
        """Test that upload updates existing profile instead of creating new one"""
        with patch("backend.api.routers.profile.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = "test-user-id"
            mock_get_user.return_value = mock_user

            with patch("backend.db.database.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db

                # Mock existing profile
                existing_profile = MagicMock()
                existing_profile.full_name = "Old Name"
                mock_db.query.return_value.filter.return_value.first.return_value = (
                    existing_profile
                )

                with patch("backend.services.storage.upload_file"):
                    with patch(
                        "backend.services.resume_parser_enhanced.parse_resume_enhanced",
                        new_callable=AsyncMock,
                    ) as mock_parse:
                        mock_parse.return_value = {
                            "full_name": "New Name",
                            "skills": ["Python"],
                            "parsed_at": "2026-01-27T12:00:00",
                        }

                        files = {
                            "file": ("resume.pdf", valid_pdf_content, "application/pdf")
                        }

                        response = client.post("/api/profile/resume", files=files)

                        assert response.status_code == 200
                        data = response.json()
                        assert data["full_name"] == "New Name"  # Should be updated

                        # Verify database update
                        mock_db.add.assert_called_with(existing_profile)
                        mock_db.commit.assert_called()

    def test_resume_upload_unauthenticated_blocked(self, client, valid_pdf_content):
        """Test that unauthenticated uploads are blocked"""
        files = {"file": ("resume.pdf", valid_pdf_content, "application/pdf")}

        response = client.post("/api/profile/resume", files=files)

        # Should require authentication
        assert response.status_code == 401 or response.status_code == 403

    def test_file_validation_utility_functions(
        self, valid_pdf_content, malicious_exe_content
    ):
        """Test file validation utility functions"""
        from api.middleware.file_validation import (
            validate_file, validate_resume_file)

        # Test valid PDF
        valid, error = validate_resume_file("resume.pdf", valid_pdf_content)
        assert valid is True
        assert error == ""

        # Test invalid extension
        valid, error = validate_resume_file("resume.exe", valid_pdf_content)
        assert valid is False
        assert "extension" in error.lower()

        # Test malicious content
        valid, error = validate_resume_file("resume.pdf", malicious_exe_content)
        assert valid is False
        assert "dangerous" in error.lower()

        # Test oversized file
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        valid, error = validate_file(
            "test.pdf", large_content, max_size=5 * 1024 * 1024
        )
        assert valid is False
        assert "size exceeds" in error.lower()

    def test_content_type_validation(self, valid_pdf_content):
        """Test MIME type validation"""
        from api.middleware.file_validation import validate_file

        # Valid PDF
        allowed_types = {"application/pdf"}
        valid, error = validate_file(
            "test.pdf", valid_pdf_content, allowed_file_types=allowed_types
        )
        assert valid is True

        # Invalid type
        allowed_types = {"text/plain"}
        valid, error = validate_file(
            "test.pdf", valid_pdf_content, allowed_file_types=allowed_types
        )
        assert valid is False
        assert "not allowed" in error.lower()
