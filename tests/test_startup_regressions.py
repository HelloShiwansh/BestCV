import io
import unittest
import zipfile
from unittest.mock import patch

from docx import Document

from backend.core.config import SPACY_MODEL_SECONDARY
from backend.services import groq_parser, resume_parser


class StartupRegressionTests(unittest.TestCase):
    def test_fallback_spacy_model_has_valid_name(self):
        self.assertEqual(SPACY_MODEL_SECONDARY, "en_core_web_sm")

    def test_empty_upload_returns_validation_tuple(self):
        with patch.object(resume_parser.magic, "from_buffer") as detect_type:
            valid, message, file_type = resume_parser.validate_file(b"", "resume.pdf")
        self.assertFalse(valid)
        self.assertIn("empty", message)
        self.assertIsNone(file_type)
        detect_type.assert_not_called()

    def test_empty_upload_preserves_specific_validation_message(self):
        with self.assertRaisesRegex(resume_parser.FileValidationError, "empty"):
            resume_parser.parse_resume_file(b"", "resume.pdf")

    def test_generated_docx_accepted_with_ambiguous_mime(self):
        document = Document()
        document.add_paragraph("Alex Example - Python developer")
        output = io.BytesIO()
        document.save(output)
        for mime in ("application/octet-stream", "application/zip", "application/x-zip-compressed"):
            with self.subTest(mime=mime), \
                    patch.object(resume_parser.magic, "from_buffer", return_value=mime):
                self.assertEqual(resume_parser.validate_file(output.getvalue(), "resume.docx"),
                                 (True, "", "docx"))

    def test_generic_zip_and_relabelled_text_are_rejected(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr("readme.txt", "This is not a Word document.")
        for content in (archive.getvalue(), b"plain text renamed to resume.docx", b"PK\x03\x04broken zip"):
            with self.subTest(content=content[:20]), \
                    patch.object(resume_parser.magic, "from_buffer", return_value="application/octet-stream"):
                valid, message, file_type = resume_parser.validate_file(content, "resume.docx")
                self.assertFalse(valid)
                self.assertIn("Unsupported file type", message)
                self.assertIsNone(file_type)

    def test_zip_requires_word_document_content_type(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr("word/document.xml", "<document/>")
            package.writestr("[Content_Types].xml", """
                <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
                    <Override PartName="/word/document.xml" ContentType="text/plain"/>
                </Types>""")
        with patch.object(resume_parser.magic, "from_buffer", return_value="application/zip"):
            self.assertFalse(resume_parser.validate_file(archive.getvalue(), "resume.docx")[0])

    def test_valid_json_returns_on_first_attempt(self):
        cases = (
            (groq_parser.parse_resume, '{"name": "Alex"}', "name", "Alex"),
            (groq_parser.parse_job_description, '{"job_title": "Engineer"}',
             "job_title", "Engineer"),
        )
        for parse, response, field, expected in cases:
            with self.subTest(parser=parse.__name__), \
                    patch.object(groq_parser, "_get_client", return_value=object()), \
                    patch.object(groq_parser, "_call_groq", return_value=response) as call:
                result = parse("Example text")
                self.assertEqual(result[field], expected)
                self.assertIsInstance(result["keywords"], list)
                call.assert_called_once()

    def test_invalid_json_or_non_object_response_fails_after_retry(self):
        for parse in (groq_parser.parse_resume, groq_parser.parse_job_description):
            for invalid_response in ("not JSON", "[]", "null"):
                with self.subTest(parser=parse.__name__, response=invalid_response), \
                        patch.object(groq_parser, "_get_client", return_value=object()), \
                        patch.object(groq_parser, "_call_groq",
                                     side_effect=[invalid_response, "[]"]) as call:
                    with self.assertRaisesRegex(ValueError, "after retry"):
                        parse("Example text")
                    self.assertEqual(call.call_count, 2)

    def test_retry_accepts_valid_json(self):
        for parse in (groq_parser.parse_resume, groq_parser.parse_job_description):
            with self.subTest(parser=parse.__name__), \
                    patch.object(groq_parser, "_get_client", return_value=object()), \
                    patch.object(groq_parser, "_call_groq",
                                 side_effect=["not JSON", "```json\n{}\n``` "]) as call:
                result = parse("Example text")
                self.assertEqual(result["keywords"], [])
                self.assertEqual(call.call_count, 2)
                self.assertIn("previous response was not valid JSON", call.call_args.args[2])


if __name__ == "__main__":
    unittest.main()
