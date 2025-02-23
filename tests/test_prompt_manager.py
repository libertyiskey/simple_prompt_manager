import unittest
import sqlite3
import os
from prompt_manager_core import PromptManager

class TestPromptManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.test_db = "test_prompts.db"
        self.pm = PromptManager(self.test_db)
        
    def tearDown(self):
        """Clean up test environment after each test."""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_folder_operations(self):
        """Test folder CRUD operations."""
        # Test adding folder
        folder_id = self.pm.add_folder("Test Folder")
        self.assertIsInstance(folder_id, int)
        
        # Test getting folders
        folders = self.pm.get_folders()
        self.assertEqual(len(folders), 1)
        self.assertEqual(folders[0]["name"], "Test Folder")
        
        # Test updating folder
        success = self.pm.update_folder(folder_id, "Updated Folder")
        self.assertTrue(success)
        folders = self.pm.get_folders()
        self.assertEqual(folders[0]["name"], "Updated Folder")
        
        # Test folder mapping
        mapping = self.pm.get_folder_mapping()
        self.assertEqual(mapping[folder_id], "Updated Folder")
        
        # Test deleting folder
        success = self.pm.delete_folder(folder_id)
        self.assertTrue(success)
        folders = self.pm.get_folders()
        self.assertEqual(len(folders), 0)

    def test_prompt_operations(self):
        """Test basic prompt CRUD operations."""
        # Test adding prompt
        prompt_id = self.pm.add_prompt("Test Prompt", "Test Content")
        self.assertIsInstance(prompt_id, int)
        
        # Test getting prompt
        prompt = self.pm.get_prompt(prompt_id)
        self.assertEqual(prompt["title"], "Test Prompt")
        self.assertEqual(prompt["content"], "Test Content")
        self.assertEqual(prompt["current_version"], 1)
        
        # Test getting all prompts
        prompts = self.pm.get_prompts()
        self.assertEqual(len(prompts), 1)
        
        # Test updating prompt
        success = self.pm.update_prompt(prompt_id, "Updated Prompt", "Updated Content")
        self.assertTrue(success)
        prompt = self.pm.get_prompt(prompt_id)
        self.assertEqual(prompt["title"], "Updated Prompt")
        self.assertEqual(prompt["content"], "Updated Content")
        self.assertEqual(prompt["current_version"], 2)
        
        # Test deleting prompt
        success = self.pm.delete_prompt(prompt_id)
        self.assertTrue(success)
        prompt = self.pm.get_prompt(prompt_id)
        self.assertIsNone(prompt)

    def test_prompt_versioning(self):
        """Test prompt versioning functionality."""
        # Create a prompt and make multiple updates
        prompt_id = self.pm.add_prompt("Version Test", "Content v1")
        self.pm.update_prompt(prompt_id, "Version Test", "Content v2")
        self.pm.update_prompt(prompt_id, "Version Test", "Content v3")
        
        # Test version history
        versions = self.pm.get_prompt_versions(prompt_id)
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0]["version_number"], 3)  # Latest version first
        self.assertEqual(versions[2]["version_number"], 1)  # First version last
        
        # Test getting specific version
        v2 = self.pm.get_prompt_version(prompt_id, 2)
        self.assertEqual(v2["content"], "Content v2")
        
        # Test restoring version
        success = self.pm.restore_version(prompt_id, 1)
        self.assertTrue(success)
        prompt = self.pm.get_prompt(prompt_id)
        self.assertEqual(prompt["content"], "Content v1")
        self.assertEqual(prompt["current_version"], 4)  # New version created

    def test_prompt_references(self):
        """Test prompt reference resolution."""
        # Create test prompts
        p1_id = self.pm.add_prompt("Prompt One", "Content One")
        p2_id = self.pm.add_prompt("Prompt Two", "Content Two")
        
        # Test reference by ID
        content = f"Reference by ID: {{{{1}}}} and {{{{2}}}}"
        resolved = self.pm.resolve_prompt_references(content)
        self.assertIn("Content One", resolved)
        self.assertIn("Content Two", resolved)
        
        # Test reference by title
        content = f"Reference by title: {{{{Prompt One}}}} and {{{{Prompt Two}}}}"
        resolved = self.pm.resolve_prompt_references(content)
        self.assertIn("Content One", resolved)
        self.assertIn("Content Two", resolved)
        
        # Test invalid references
        content = "Invalid references: {{999}} and {{Nonexistent}}"
        resolved = self.pm.resolve_prompt_references(content)
        self.assertEqual(resolved, content)  # Should remain unchanged

    def test_folder_prompt_relationship(self):
        """Test relationship between folders and prompts."""
        # Create folder and prompt
        folder_id = self.pm.add_folder("Test Folder")
        prompt_id = self.pm.add_prompt("Test Prompt", "Content", folder_id)
        
        # Test prompt in folder
        prompt = self.pm.get_prompt(prompt_id)
        self.assertEqual(prompt["folder_id"], folder_id)
        
        # Test getting prompts by folder
        folder_prompts = self.pm.get_prompts(folder_id=folder_id)
        self.assertEqual(len(folder_prompts), 1)
        self.assertEqual(folder_prompts[0]["id"], prompt_id)
        
        # Test folder deletion cascading
        self.pm.delete_folder(folder_id)
        prompt = self.pm.get_prompt(prompt_id)
        self.assertIsNone(prompt["folder_id"])  # Prompt should be uncategorized

    def test_edge_cases(self):
        """Test various edge cases and error conditions."""
        # Test nonexistent IDs
        self.assertIsNone(self.pm.get_prompt(999))
        self.assertFalse(self.pm.update_prompt(999, "title", "content"))
        self.assertFalse(self.pm.delete_prompt(999))
        self.assertFalse(self.pm.update_folder(999, "name"))
        self.assertFalse(self.pm.delete_folder(999))
        
        # Test empty inputs
        with self.assertRaises(sqlite3.Error):
            self.pm.add_prompt("", "")
        with self.assertRaises(sqlite3.Error):
            self.pm.add_folder("")
        
        # Test special characters in content
        special_content = "Special chars: !@#$%^&*()\n\t"
        prompt_id = self.pm.add_prompt("Special", special_content)
        prompt = self.pm.get_prompt(prompt_id)
        self.assertEqual(prompt["content"], special_content)

if __name__ == '__main__':
    unittest.main() 