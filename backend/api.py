from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from prompt_manager_core import PromptManager
from datetime import datetime
import sqlite3
import os

app = FastAPI(
    title="Prompt Manager API",
    description="API for managing and retrieving prompts",
    version="1.0.0"
)

# Initialize PromptManager with test database during testing
test_mode = os.environ.get("TEST_MODE") == "1"
pm = PromptManager("test_prompts.db" if test_mode else "prompts.db")

# Pydantic models for request/response validation
class PromptCreate(BaseModel):
    title: str
    content: str
    folder_id: Optional[int] = None

class PromptUpdate(BaseModel):
    title: str
    content: str
    folder_id: Optional[int] = None

class FolderCreate(BaseModel):
    name: str

class PromptResponse(BaseModel):
    id: int
    title: str
    content: str
    folder_id: Optional[int]
    current_version: int

class PromptVersion(BaseModel):
    id: int
    prompt_id: int
    title: str
    content: str
    folder_id: Optional[int]
    created_at: str
    version_number: int

class Folder(BaseModel):
    id: int
    name: str

class ComposedPromptRequest(BaseModel):
    content: str
    variables: Dict[str, str]

class ComposedPromptResponse(BaseModel):
    composed_content: str

@app.get("/")
async def root():
    """API status check."""
    return {"status": "online", "version": "1.0.0"}

# Prompt endpoints
@app.post("/prompts/", response_model=PromptResponse)
async def create_prompt(prompt: PromptCreate):
    """Create a new prompt."""
    try:
        prompt_id = pm.add_prompt(prompt.title, prompt.content, prompt.folder_id)
        result = pm.get_prompt(prompt_id)
        if result:
            return PromptResponse(**result)
        raise HTTPException(status_code=500, detail="Failed to create prompt")
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/prompts/", response_model=List[PromptResponse])
async def get_prompts(
    folder_id: Optional[int] = None,
    search_query: Optional[str] = None
):
    """Get all prompts with optional filtering."""
    try:
        prompts = pm.get_prompts(folder_id, search_query)
        return [PromptResponse(**p) for p in prompts]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: int):
    """Get a specific prompt by ID."""
    prompt = pm.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return PromptResponse(**prompt)

@app.put("/prompts/{prompt_id}", response_model=PromptResponse)
async def update_prompt(prompt_id: int, prompt_update: PromptUpdate):
    """Update a specific prompt."""
    try:
        success = pm.update_prompt(
            prompt_id,
            prompt_update.title,
            prompt_update.content,
            prompt_update.folder_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Prompt not found")
        result = pm.get_prompt(prompt_id)
        if result:
            return PromptResponse(**result)
        raise HTTPException(status_code=500, detail="Failed to update prompt")
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: int):
    """Delete a specific prompt."""
    success = pm.delete_prompt(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"status": "success"}

# Version endpoints
@app.get("/prompts/{prompt_id}/versions", response_model=List[PromptVersion])
async def get_prompt_versions(prompt_id: int):
    """Get all versions of a prompt."""
    versions = pm.get_prompt_versions(prompt_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return [PromptVersion(**v) for v in versions]

@app.post("/prompts/{prompt_id}/restore/{version_number}")
async def restore_version(prompt_id: int, version_number: int):
    """Restore a specific version of a prompt."""
    success = pm.restore_version(prompt_id, version_number)
    if not success:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"status": "success"}

# Folder endpoints
@app.post("/folders/", response_model=Folder)
async def create_folder(folder: FolderCreate):
    """Create a new folder."""
    try:
        folder_id = pm.add_folder(folder.name)
        return Folder(id=folder_id, name=folder.name)
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/folders/", response_model=List[Folder])
async def get_folders():
    """Get all folders."""
    folders = pm.get_folders()
    return [Folder(**f) for f in folders]

# Composition endpoints
@app.post("/compose", response_model=ComposedPromptResponse)
async def compose_prompt(request: ComposedPromptRequest):
    """Compose a prompt with variables."""
    try:
        composed = pm.compose_prompt(request.content, request.variables)
        return ComposedPromptResponse(composed_content=composed)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 