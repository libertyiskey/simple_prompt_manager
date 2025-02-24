import unittest
from streamlit.testing.v1 import AppTest
import os
import sqlite3
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestPromptManagerUI(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        # Use a test database
        self.test_db = "test_prompts.db"
        # Initialize the app test client
        self.at = AppTest.from_file("frontend/prompt_manager.py")
        
    def tearDown(self):
        """Clean up test environment after each test."""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_initial_page_load(self):
        """Test that the app loads correctly with initial state."""
        # Run the app
        self.at.run()
        
        # Check that there are no exceptions
        self.assertFalse(self.at.exception)
        
        # Verify main title is present
        self.assertEqual(self.at.title[0].value, "Prompt & Folder Manager")
        
        # Verify navigation buttons exist in sidebar
        sidebar_buttons = self.at.sidebar.button
        self.assertTrue(any("Add Prompt" in btn.label for btn in sidebar_buttons))
        self.assertTrue(any("Manage Prompts" in btn.label for btn in sidebar_buttons))
        self.assertTrue(any("Manage Folders" in btn.label for btn in sidebar_buttons))

    def test_add_prompt_workflow(self):
        """Test the complete workflow of adding a new prompt."""
        self.at.run()
        
        # Navigate to Add Prompt (should be default)
        self.assertTrue("Add a New Prompt" in self.at.subheader[0].value)
        
        # Fill in the prompt form
        title_input = self.at.text_input[0]
        title_input.input("Test Prompt").run()
        
        content_area = self.at.text_area[0]
        content_area.input("Test Content").run()
        
        # Click the Add Prompt button
        add_buttons = [btn for btn in self.at.button if "Add Prompt" in btn.label]
        self.assertTrue(len(add_buttons) > 0)
        add_buttons[0].click().run()
        
        # Navigate to Manage Prompts to verify the prompt was added
        manage_buttons = [btn for btn in self.at.sidebar.button if "Manage Prompts" in btn.label]
        self.assertTrue(len(manage_buttons) > 0)
        manage_buttons[0].click().run()
        
        # Verify the prompt appears in the list
        markdown_texts = [md.value for md in self.at.markdown]
        self.assertTrue(
            any("Test Prompt" in text for text in markdown_texts),
            "Added prompt not found in the list"
        )

    def test_add_duplicate_prompt(self):
        """Test that adding a prompt with duplicate title shows error."""
        self.at.run()
        
        # Add first prompt
        title_input = self.at.text_input[0]
        content_area = self.at.text_area[0]
        
        title_input.input("Test Prompt").run()
        content_area.input("Test Content").run()
        
        add_buttons = [btn for btn in self.at.button if "Add Prompt" in btn.label]
        add_buttons[0].click().run()
        
        # Try to add second prompt with same title
        title_input.input("Test Prompt").run()
        content_area.input("Different Content").run()
        
        add_buttons = [btn for btn in self.at.button if "Add Prompt" in btn.label]
        add_buttons[0].click().run()
        
        # Verify error message appears in error elements
        self.assertTrue(any("already exists" in error.value for error in self.at.error))

    def test_manage_folders_workflow(self):
        """Test the complete workflow of managing folders."""
        self.at.run()
        
        # Click Manage Folders in sidebar
        folder_buttons = [btn for btn in self.at.sidebar.button if "Manage Folders" in btn.label]
        self.assertTrue(len(folder_buttons) > 0)
        folder_buttons[0].click().run()
        
        # Verify we're on the folders page
        self.assertTrue("Manage Folders" in self.at.subheader[0].value)
        
        # Add a new folder
        folder_input = self.at.text_input[0]
        folder_input.input("Test Folder").run()
        
        # Find and click the Add Folder button
        form_buttons = [btn for btn in self.at.button if "Add Folder" in btn.label]
        self.assertTrue(len(form_buttons) > 0)
        form_buttons[0].click().run()
        
        # Verify success message appears in success elements
        self.assertTrue(any("Folder added successfully" in success.value for success in self.at.success))

    def test_prompt_versioning(self):
        """Test the versioning functionality in the UI."""
        self.at.run()
        
        # First add a prompt
        title_input = self.at.text_input[0]
        content_area = self.at.text_area[0]
        
        title_input.input("Version Test").run()
        content_area.input("Version 1").run()
        
        add_buttons = [btn for btn in self.at.button if "Add Prompt" in btn.label]
        add_buttons[0].click().run()
        
        # Navigate to Manage Prompts
        manage_buttons = [btn for btn in self.at.sidebar.button if "Manage Prompts" in btn.label]
        manage_buttons[0].click().run()
        
        # Click Edit
        edit_buttons = [btn for btn in self.at.button if "✏️ Edit" in btn.label]
        self.assertTrue(len(edit_buttons) > 0)
        edit_buttons[0].click().run()
        
        # Update content
        content_areas = [area for area in self.at.text_area]
        self.assertTrue(len(content_areas) > 0)
        content_areas[0].input("Version 2").run()
        
        # Find and click the Save Changes button
        save_buttons = [btn for btn in self.at.button if "Save Changes" in btn.label]
        self.assertTrue(len(save_buttons) > 0)
        save_buttons[0].click().run()
        
        # Verify version history exists in markdown elements
        self.assertTrue(any("Version History" in md.value for md in self.at.markdown))

    def test_prompt_preview(self):
        """Test the preview functionality with prompt references."""
        self.at.run()
        
        # Add first prompt
        title_input = self.at.text_input[0]
        content_area = self.at.text_area[0]
        
        title_input.input("Base Prompt").run()
        content_area.input("Base Content").run()
        
        add_buttons = [btn for btn in self.at.button if "Add Prompt" in btn.label]
        add_buttons[0].click().run()
        
        # Add second prompt with reference
        title_input.input("Reference Prompt").run()
        content_area.input("Reference to {{Base Prompt}}").run()
        
        add_buttons = [btn for btn in self.at.button if "Add Prompt" in btn.label]
        add_buttons[0].click().run()
        
        # Check preview content appears in markdown elements
        self.assertTrue(any("Base Content" in md.value for md in self.at.markdown))

    def test_search_functionality(self):
        """Test the search functionality in the prompt list."""
        self.at.run()
        
        # Add first prompt
        title_input = self.at.text_input[0]
        content_area = self.at.text_area[0]
        
        title_input.input("Alpha Prompt").run()
        content_area.input("Content A").run()
        
        add_buttons = [btn for btn in self.at.button if "Add Prompt" in btn.label]
        add_buttons[0].click().run()
        
        # Add second prompt
        title_input.input("Beta Prompt").run()
        content_area.input("Content B").run()
        
        add_buttons = [btn for btn in self.at.button if "Add Prompt" in btn.label]
        add_buttons[0].click().run()
        
        # Navigate to Manage Prompts
        manage_buttons = [btn for btn in self.at.sidebar.button if "Manage Prompts" in btn.label]
        manage_buttons[0].click().run()
        
        # Search for "Alpha"
        search_inputs = [ti for ti in self.at.text_input if "Search prompts" in ti.label]
        self.assertTrue(len(search_inputs) > 0)
        search_inputs[0].input("Alpha").run()
        
        # Verify only Alpha prompt is shown in markdown elements
        markdown_texts = [md.value for md in self.at.markdown]
        self.assertTrue(any("Alpha Prompt" in text for text in markdown_texts))
        self.assertFalse(any("Beta Prompt" in text for text in markdown_texts))

if __name__ == '__main__':
    unittest.main() 