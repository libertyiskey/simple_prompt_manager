import sqlite3
from typing import List, Tuple, Dict, Optional
from typing_extensions import TypedDict
from datetime import datetime
import re

class PromptVersion(TypedDict):
    id: int
    prompt_id: int
    title: str
    content: str
    folder_id: Optional[int]
    created_at: str
    version_number: int

class Prompt(TypedDict):
    id: int
    title: str
    content: str
    folder_id: Optional[int]
    current_version: int

class Folder(TypedDict):
    id: int
    name: str

class PromptManager:
    def __init__(self, db_file: str = "prompts.db"):
        self.db_file = db_file
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with foreign key support."""
        conn = sqlite3.connect(self.db_file)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self) -> None:
        """Initialize the SQLite database and create tables if they don't exist."""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Create folders table
        c.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        
        # Check if prompts table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prompts'")
        prompts_exists = c.fetchone() is not None
        
        if not prompts_exists:
            # Create new prompts table with current_version
            c.execute("""
                CREATE TABLE prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    folder_id INTEGER,
                    current_version INTEGER DEFAULT 1,
                    FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE SET NULL
                )
            """)
            
            # Create versions table
            c.execute("""
                CREATE TABLE IF NOT EXISTS prompt_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    folder_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version_number INTEGER NOT NULL,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
                    FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE SET NULL
                )
            """)
        else:
            # Check if we need to migrate the prompts table
            c.execute("PRAGMA table_info(prompts)")
            columns = [column[1] for column in c.fetchall()]
            
            if "current_version" not in columns:
                # Backup existing prompts
                c.execute("CREATE TABLE prompts_backup AS SELECT * FROM prompts")
                
                # Drop existing prompts table
                c.execute("DROP TABLE IF EXISTS prompts")
                
                # Create new prompts table with current_version
                c.execute("""
                    CREATE TABLE prompts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        folder_id INTEGER,
                        current_version INTEGER DEFAULT 1,
                        FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE SET NULL
                    )
                """)
                
                # Create versions table
                c.execute("""
                    CREATE TABLE IF NOT EXISTS prompt_versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prompt_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        folder_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        version_number INTEGER NOT NULL,
                        FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
                        FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE SET NULL
                    )
                """)
                
                # Migrate existing prompts
                c.execute("SELECT id, title, content, folder_id FROM prompts_backup")
                old_prompts = c.fetchall()
                
                # Insert prompts with version 1
                for prompt in old_prompts:
                    # Insert into prompts table
                    c.execute(
                        "INSERT INTO prompts (id, title, content, folder_id, current_version) VALUES (?, ?, ?, ?, 1)",
                        prompt
                    )
                    
                    # Insert first version
                    c.execute(
                        """INSERT INTO prompt_versions 
                           (prompt_id, title, content, folder_id, version_number) 
                           VALUES (?, ?, ?, ?, 1)""",
                        prompt
                    )
                
                # Drop backup table
                c.execute("DROP TABLE prompts_backup")
            else:
                # Create versions table if it doesn't exist
                c.execute("""
                    CREATE TABLE IF NOT EXISTS prompt_versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prompt_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        folder_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        version_number INTEGER NOT NULL,
                        FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
                        FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE SET NULL
                    )
                """)
                
                # Check if we need to create initial versions for existing prompts
                c.execute("SELECT COUNT(*) FROM prompt_versions")
                if c.fetchone()[0] == 0:
                    c.execute("SELECT id, title, content, folder_id FROM prompts")
                    prompts = c.fetchall()
                    for prompt in prompts:
                        c.execute(
                            """INSERT INTO prompt_versions 
                               (prompt_id, title, content, folder_id, version_number) 
                               VALUES (?, ?, ?, ?, 1)""",
                            prompt
                        )
        
        conn.commit()
        conn.close()

    def add_prompt(self, title: str, content: str, folder_id: Optional[int] = None) -> int:
        """Add a new prompt and its first version, then return its ID."""
        # Validate inputs
        if not title.strip() or not content.strip():
            raise sqlite3.Error("Title and content cannot be empty")
            
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            # Check for duplicate title
            c.execute("SELECT id FROM prompts WHERE LOWER(title) = LOWER(?)", (title.strip(),))
            if c.fetchone() is not None:
                raise sqlite3.Error("A prompt with this title already exists")
            
            # Insert the prompt
            c.execute(
                "INSERT INTO prompts (title, content, folder_id, current_version) VALUES (?, ?, ?, 1)",
                (title, content, folder_id)
            )
            prompt_id = c.lastrowid
            
            # Insert the first version
            c.execute(
                """INSERT INTO prompt_versions 
                   (prompt_id, title, content, folder_id, version_number) 
                   VALUES (?, ?, ?, ?, 1)""",
                (prompt_id, title, content, folder_id)
            )
            
            conn.commit()
            return prompt_id
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_prompts(self, folder_id: Optional[int] = None, search_query: Optional[str] = None) -> List[Prompt]:
        """Get prompts with optional filtering by folder and search query."""
        conn = self.get_connection()
        c = conn.cursor()
        
        query = "SELECT id, title, content, folder_id, current_version FROM prompts"
        params = []
        
        conditions = []
        if folder_id is not None:
            conditions.append("folder_id = ?")
            params.append(folder_id)
        
        if search_query:
            conditions.append("LOWER(title) LIKE ?")
            params.append(f"%{search_query.lower()}%")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        c.execute(query, params)
        prompts = [
            {
                "id": p[0], 
                "title": p[1], 
                "content": p[2], 
                "folder_id": p[3],
                "current_version": p[4]
            }
            for p in c.fetchall()
        ]
        conn.close()
        return prompts

    def get_prompt(self, prompt_id: int) -> Optional[Prompt]:
        """Get a single prompt by ID."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT id, title, content, folder_id, current_version FROM prompts WHERE id = ?",
            (prompt_id,)
        )
        result = c.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "title": result[1],
                "content": result[2],
                "folder_id": result[3],
                "current_version": result[4]
            }
        return None

    def get_prompt_versions(self, prompt_id: int) -> List[PromptVersion]:
        """Get all versions of a prompt."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            """SELECT id, prompt_id, title, content, folder_id, created_at, version_number 
               FROM prompt_versions 
               WHERE prompt_id = ? 
               ORDER BY version_number DESC""",
            (prompt_id,)
        )
        versions = [
            {
                "id": v[0],
                "prompt_id": v[1],
                "title": v[2],
                "content": v[3],
                "folder_id": v[4],
                "created_at": v[5],
                "version_number": v[6]
            }
            for v in c.fetchall()
        ]
        conn.close()
        return versions

    def get_prompt_version(self, prompt_id: int, version_number: int) -> Optional[PromptVersion]:
        """Get a specific version of a prompt."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            """SELECT id, prompt_id, title, content, folder_id, created_at, version_number 
               FROM prompt_versions 
               WHERE prompt_id = ? AND version_number = ?""",
            (prompt_id, version_number)
        )
        result = c.fetchone()
        conn.close()

        if result:
            return {
                "id": result[0],
                "prompt_id": result[1],
                "title": result[2],
                "content": result[3],
                "folder_id": result[4],
                "created_at": result[5],
                "version_number": result[6]
            }
        return None

    def update_prompt(self, prompt_id: int, title: str, content: str, folder_id: Optional[int] = None) -> bool:
        """Update a prompt and create a new version."""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Get current version number
        c.execute("SELECT current_version FROM prompts WHERE id = ?", (prompt_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            return False
        
        current_version = result[0]
        new_version = current_version + 1
        
        # Create new version
        c.execute(
            """INSERT INTO prompt_versions 
               (prompt_id, title, content, folder_id, version_number) 
               VALUES (?, ?, ?, ?, ?)""",
            (prompt_id, title, content, folder_id, new_version)
        )
        
        # Update prompt with new content and version
        c.execute(
            """UPDATE prompts 
               SET title = ?, content = ?, folder_id = ?, current_version = ? 
               WHERE id = ?""",
            (title, content, folder_id, new_version, prompt_id)
        )
        
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def restore_version(self, prompt_id: int, version_number: int) -> bool:
        """Restore a prompt to a specific version."""
        version = self.get_prompt_version(prompt_id, version_number)
        if not version:
            return False
            
        return self.update_prompt(
            prompt_id,
            version["title"],
            version["content"],
            version["folder_id"]
        )

    # Folder CRUD operations
    def add_folder(self, name: str) -> int:
        """Add a new folder and return its ID."""
        # Validate input
        if not name.strip():
            raise sqlite3.Error("Folder name cannot be empty")
            
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            c.execute("INSERT INTO folders (name) VALUES (?)", (name,))
            folder_id = c.lastrowid
            conn.commit()
            return folder_id
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_folders(self) -> List[Folder]:
        """Get all folders."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id, name FROM folders")
        folders = [{"id": f[0], "name": f[1]} for f in c.fetchall()]
        conn.close()
        return folders

    def update_folder(self, folder_id: int, new_name: str) -> bool:
        """Update a folder's name. Returns True if successful."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("UPDATE folders SET name = ? WHERE id = ?", (new_name, folder_id))
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def delete_folder(self, folder_id: int) -> bool:
        """Delete a folder. Returns True if successful."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def get_prompts_by_folder(self, folder_id: Optional[int] = None) -> List[Prompt]:
        """Get all prompts in a specific folder (or uncategorized if folder_id is None)."""
        return self.get_prompts(folder_id=folder_id)

    def get_folder_mapping(self) -> Dict[int, str]:
        """Get a mapping of folder IDs to names."""
        folders = self.get_folders()
        return {folder["id"]: folder["name"] for folder in folders}

    def resolve_prompt_references(self, content: str) -> str:
        """
        Resolve references to other prompts in the content.
        Supports both {{prompt_id}} and {{prompt_title}} formats.
        """
        import re
        
        def replace_match(match):
            ref = match.group(1)
            try:
                # Try to interpret as ID first
                if ref.isdigit():
                    prompt = self.get_prompt(int(ref))
                    if prompt:
                        return prompt['content']
                
                # If not ID or prompt not found, try as title
                conn = self.get_connection()
                c = conn.cursor()
                c.execute("SELECT content FROM prompts WHERE title = ?", (ref,))
                result = c.fetchone()
                conn.close()
                
                if result:
                    return result[0]
                
                # If no match found, return the original reference
                return match.group(0)
            except:
                return match.group(0)
        
        # Replace all {{references}} in the content
        pattern = r'\{\{([^}]+)\}\}'
        resolved = re.sub(pattern, replace_match, content)
        return resolved

    def delete_prompt(self, prompt_id: int) -> bool:
        """Delete a prompt and all its versions. Returns True if successful."""
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            # The prompt_versions table will be automatically cleaned up due to ON DELETE CASCADE
            c.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
            success = c.rowcount > 0
            conn.commit()
            return success
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def compose_prompt(self, content: str, variables: Dict[str, str]) -> str:
        """
        Compose a prompt by replacing variables in the content.
        Variables are specified in the format {variable_name}.
        """
        try:
            # First resolve any prompt references
            content = self.resolve_prompt_references(content)
            
            # Then replace variables
            for var_name, var_value in variables.items():
                content = content.replace(f"{{{var_name}}}", var_value)
            
            return content
        except Exception as e:
            raise ValueError(f"Error composing prompt: {str(e)}") 