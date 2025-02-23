import sys
import os
import unittest
from fastapi.testclient import TestClient

# Set test mode
os.environ["TEST_MODE"] = "1"

# Add the backend/src directory to the Python path
backend_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))
sys.path.insert(0, backend_src_path)

from api import app, pm

class TestPromptManagerAPI(unittest.TestCase):
    def setUp(self):
        """Set up test client and test data."""
        # Initialize the database
        if os.path.exists("test_prompts.db"):
            os.remove("test_prompts.db")
        pm.init_db()
        
        self.client = TestClient(app)
        self.test_prompt = {
            "title": "Test Prompt",
            "content": "This is a test prompt with {variable}",
            "folder_id": None
        }
        self.test_folder = {
            "name": "Test Folder"
        }

    def tearDown(self):
        """Clean up test environment after each test."""
        if os.path.exists("test_prompts.db"):
            os.remove("test_prompts.db")

    def test_root(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "online")

    def test_create_prompt(self):
        """Test creating a new prompt."""
        response = self.client.post("/prompts/", json=self.test_prompt)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], self.test_prompt["title"])
        self.assertEqual(data["content"], self.test_prompt["content"])

    def test_create_duplicate_prompt(self):
        """Test creating a prompt with a duplicate title."""
        # Create first prompt
        self.client.post("/prompts/", json=self.test_prompt)
        # Try to create duplicate
        response = self.client.post("/prompts/", json=self.test_prompt)
        self.assertEqual(response.status_code, 400)

    def test_get_prompts(self):
        """Test getting all prompts and filtering."""
        # Create a test prompt
        self.client.post("/prompts/", json=self.test_prompt)
        
        # Test getting all prompts
        response = self.client.get("/prompts/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)
        
        # Test search
        response = self.client.get("/prompts/", params={"search_query": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)

    def test_get_single_prompt(self):
        """Test getting a specific prompt."""
        # Create a test prompt
        create_response = self.client.post("/prompts/", json=self.test_prompt)
        prompt_id = create_response.json()["id"]
        
        # Get the prompt
        response = self.client.get(f"/prompts/{prompt_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], self.test_prompt["title"])
        
        # Test non-existent prompt
        response = self.client.get("/prompts/9999")
        self.assertEqual(response.status_code, 404)

    def test_update_prompt(self):
        """Test updating a prompt."""
        # Create a test prompt
        create_response = self.client.post("/prompts/", json=self.test_prompt)
        prompt_id = create_response.json()["id"]
        
        # Update the prompt
        updated_data = {
            "title": "Updated Title",
            "content": "Updated content",
            "folder_id": None
        }
        response = self.client.put(f"/prompts/{prompt_id}", json=updated_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], updated_data["title"])

    def test_delete_prompt(self):
        """Test deleting a prompt."""
        # Create a test prompt
        create_response = self.client.post("/prompts/", json=self.test_prompt)
        prompt_id = create_response.json()["id"]
        
        # Delete the prompt
        response = self.client.delete(f"/prompts/{prompt_id}")
        self.assertEqual(response.status_code, 200)
        
        # Verify deletion
        response = self.client.get(f"/prompts/{prompt_id}")
        self.assertEqual(response.status_code, 404)

    def test_prompt_versions(self):
        """Test prompt versioning functionality."""
        # Create a test prompt
        create_response = self.client.post("/prompts/", json=self.test_prompt)
        prompt_id = create_response.json()["id"]
        
        # Update the prompt to create a new version
        updated_data = {
            "title": "Updated Title",
            "content": "Updated content",
            "folder_id": None
        }
        self.client.put(f"/prompts/{prompt_id}", json=updated_data)
        
        # Get versions
        response = self.client.get(f"/prompts/{prompt_id}/versions")
        self.assertEqual(response.status_code, 200)
        versions = response.json()
        self.assertTrue(len(versions) > 1)
        
        # Restore previous version
        response = self.client.post(f"/prompts/{prompt_id}/restore/1")
        self.assertEqual(response.status_code, 200)

    def test_folder_operations(self):
        """Test folder operations."""
        # Create a folder
        response = self.client.post("/folders/", json=self.test_folder)
        self.assertEqual(response.status_code, 200)
        folder_id = response.json()["id"]
        
        # Get all folders
        response = self.client.get("/folders/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)
        
        # Create a prompt in the folder
        prompt_with_folder = self.test_prompt.copy()
        prompt_with_folder["folder_id"] = folder_id
        response = self.client.post("/prompts/", json=prompt_with_folder)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["folder_id"], folder_id)

    def test_compose_prompt(self):
        """Test prompt composition with variables."""
        compose_request = {
            "content": "Hello {name}!",
            "variables": {"name": "World"}
        }
        response = self.client.post("/compose", json=compose_request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["composed_content"], "Hello World!")

if __name__ == '__main__':
    unittest.main() 