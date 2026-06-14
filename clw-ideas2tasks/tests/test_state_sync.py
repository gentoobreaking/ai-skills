#!/usr/bin/env python3
"""
ideas2tasks 單元測試：state_sync.py
"""
import sys
import os
import tempfile
from pathlib import Path
from unittest import TestCase, main

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
os.environ["IDEAS2TASKS_TASKS_DIR"] = tempfile.mkdtemp()
os.environ["IDEAS2TASKS_IDEAS_DIR"] = tempfile.mkdtemp()

from state_sync import (
    read_frontmatter_field,
    read_task_status,
    write_task_status,
    get_tasks_dir_status,
    _normalize_title,
    is_title_duplicate,
    should_skip_task,
    clean_duplicate_status,
    read_task_title,
)


class TestReadFrontmatterField(TestCase):
    """測試 read_frontmatter_field 函數"""

    def test_simple_status(self):
        content = "status: done"
        self.assertEqual(read_frontmatter_field(content, "status"), "done")

    def test_with_markdown_bold(self):
        content = "- **Status**: done"
        self.assertEqual(read_frontmatter_field(content, "Status"), "done")

    def test_with_asterisks(self):
        content = "***Status***:  pending  "
        self.assertEqual(read_frontmatter_field(content, "status"), "pending")

    def test_with_quotes(self):
        content = 'status: "in-progress"'
        self.assertEqual(read_frontmatter_field(content, "status"), "in-progress")

    def test_case_insensitive(self):
        content = "STATUS: Done"
        self.assertEqual(read_frontmatter_field(content, "status"), "Done")

    def test_with_inline_comment(self):
        content = "status: done # 這是註解"
        self.assertEqual(read_frontmatter_field(content, "status"), "done")

    def test_missing_field(self):
        content = "title: My Task"
        self.assertEqual(read_frontmatter_field(content, "status"), "")


class TestReadTaskStatus(TestCase):
    """測試 read_task_status 函數"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_done_emoji(self):
        f = self.temp_dir / "T001.md"
        f.write_text("---\nstatus: ✅\n---")
        self.assertEqual(read_task_status(f), "done")

    def test_done_text(self):
        f = self.temp_dir / "T001.md"
        f.write_text("---\nstatus: done\n---")
        self.assertEqual(read_task_status(f), "done")

    def test_in_progress_emoji(self):
        f = self.temp_dir / "T001.md"
        f.write_text("---\nstatus: 🔄\n---")
        self.assertEqual(read_task_status(f), "in-progress")

    def test_pending_default(self):
        f = self.temp_dir / "T001.md"
        f.write_text("---\ntitle: Test\n---")
        self.assertEqual(read_task_status(f), "pending")

    def test_nonexistent_file(self):
        f = self.temp_dir / "T999.md"
        self.assertEqual(read_task_status(f), "pending")


class TestWriteTaskStatus(TestCase):
    """測試 write_task_status 函數"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_update_existing_status(self):
        f = self.temp_dir / "T001.md"
        f.write_text("---\nstatus: pending\n---\n# T001 - Test")
        write_task_status(f, "done")
        content = f.read_text()
        self.assertIn("**status**: done", content.lower())

    def test_add_status_when_missing(self):
        f = self.temp_dir / "T001.md"
        f.write_text("---\ntitle: Test\n---\n# T001 - Test")
        write_task_status(f, "pending")
        content = f.read_text()
        self.assertIn("Status", content)


class TestNormalizeTitle(TestCase):
    """測試 _normalize_title 函數"""

    def test_remove_task_prefix(self):
        result = _normalize_title("T002 - 請檢查問題")
        self.assertEqual(result, "請檢查問題")

    def test_remove_date(self):
        result = _normalize_title("2024/01/01 任務")
        self.assertEqual(result, "任務")

    def test_remove_url(self):
        result = _normalize_title("任務 https://example.com")
        self.assertEqual(result, "任務")

    def test_lowercase(self):
        result = _normalize_title("TASK NAME")
        self.assertEqual(result, "taskname")


class TestIsTitleDuplicate(TestCase):
    """測試 is_title_duplicate 函數"""

    def test_exact_match(self):
        existing = {"請檢查問題"}
        self.assertTrue(is_title_duplicate("請檢查問題", existing))

    def test_no_match(self):
        existing = {"請檢查問題"}
        self.assertFalse(is_title_duplicate("新任務", existing))


class TestCleanDuplicateStatus(TestCase):
    """測試 clean_duplicate_status 函數"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_remove_body_status(self):
        f = self.temp_dir / "T001.md"
        f.write_text(
            "---\nstatus: done\n---\n\n# T001\n\n- **Status**: pending\n"
        )
        result = clean_duplicate_status(f)
        self.assertTrue(result)
        content = f.read_text()
        self.assertNotIn("**Status**: pending", content)


class TestReadTaskTitle(TestCase):
    """測試 read_task_title 函數"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_from_frontmatter(self):
        f = self.temp_dir / "T001.md"
        f.write_text("---\ntitle: My Task\n---\n# T001")
        self.assertEqual(read_task_title(f), "My Task")

    def test_from_markdown_heading(self):
        f = self.temp_dir / "T001.md"
        f.write_text("# T001 - From Heading")
        self.assertEqual(read_task_title(f), "From Heading")

    def test_fallback_to_stem(self):
        f = self.temp_dir / "T001.md"
        f.write_text("no title here")
        self.assertEqual(read_task_title(f), "T001")


if __name__ == "__main__":
    main()