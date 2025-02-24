# Prompt Manager

A simple application for managing and organizing prompts using Streamlit. It helps you store, organize, and version your prompts in a clean interface.

## Features

### Basic Features
- Create and manage prompts with titles and content
- Organize prompts into folders
- Search prompts by title
- Edit prompts with live preview
- Delete prompts and folders

### Additional Features
- Version History
  - Keep track of changes
  - Access previous versions
  - Restore older versions
  - View version differences

- Prompt References
  - Include other prompts using `{{prompt_id}}` or `{{prompt_title}}`
  - Preview referenced content
  - Support for nested references

- Folder Organization
  - Create and manage folders
  - Move prompts between folders
  - Filter by folder
  - View uncategorized prompts

- API Endpoints
  - RESTful API for programmatic access
  - Status checking
  - CRUD operations for prompts and folders
  - Version management
  - Prompt composition with variables

## API Reference

The application provides a RESTful API with the following endpoints:

### Status
- `GET /` - Check API status

### Prompts
- `POST /prompts/` - Create a new prompt
- `GET /prompts/` - Get all prompts (supports filtering by folder and search)
- `GET /prompts/{prompt_id}` - Get a specific prompt
- `PUT /prompts/{prompt_id}` - Update a prompt
- `DELETE /prompts/{prompt_id}` - Delete a prompt

### Versions
- `GET /prompts/{prompt_id}/versions` - Get all versions of a prompt
- `POST /prompts/{prompt_id}/restore/{version_number}` - Restore a specific version

### Folders
- `POST /folders/` - Create a new folder
- `GET /folders/` - Get all folders

### Composition
- `POST /compose` - Compose a prompt with variables

## Project Structure

```
prompt_manager/
├── backend/
│   ├── __init__.py
│   ├── api.py           # FastAPI endpoints
│   └── prompt_manager_core.py  # Core functionality
├── frontend/
│   ├── __init__.py
│   └── prompt_manager.py       # Streamlit interface
└── tests/
    ├── __init__.py
    ├── test_api.py         # API tests
    ├── test_prompt_manager.py      # Core tests
    └── test_prompt_manager_ui.py   # Interface tests
```

## Requirements

- Python 3.9+
- SQLite3
- Streamlit
- Additional dependencies listed in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/prompt_manager.git
cd prompt_manager
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
# From the project root directory
streamlit run frontend/prompt_manager.py
```

2. The interface will open in your default web browser.

3. Use the sidebar to:
   - Add prompts
   - View and edit prompts
   - Manage folders

## Development

### Running Tests

The project includes three test suites: core functionality, API, and UI tests. To run the tests, make sure you're in the project root directory.

Run all tests:
```bash
PYTHONPATH=$PYTHONPATH:backend python3 -m unittest discover tests
```

Run specific test suites:
```bash
# Core functionality tests
PYTHONPATH=$PYTHONPATH:backend python3 -m unittest -v tests/test_prompt_manager.py

# API tests
PYTHONPATH=$PYTHONPATH:backend python3 -m unittest -v tests/test_api.py

# UI tests
PYTHONPATH=$PYTHONPATH:backend python3 -m unittest -v tests/test_prompt_manager_ui.py
```

Note: When running UI tests, you may see warnings about "missing ScriptRunContext". These warnings can be safely ignored when running in test mode.

Test Coverage:
- Core Tests: Database operations, versioning, references
- API Tests: Endpoints, request handling, error cases
- UI Tests: Interface functionality, user workflows

### Components

#### Backend (`prompt_manager_core.py`)
- Database management
- Basic operations (create, read, update, delete)
- Version tracking
- Reference handling
- Input validation

#### Frontend (`prompt_manager.py`)
- Streamlit interface
- Content preview
- Form handling
- Navigation
- Search

#### Tests
- Unit tests
- Interface tests
- Database tests
- Error handling tests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Docker Installation

You can run the application using Docker:

```bash
# Build and start the container
docker-compose up --build

# Or run in detached mode
docker-compose up -d
```

The services will be available at:
- Streamlit UI: http://localhost:8501
- FastAPI: http://localhost:8000

The SQLite database (`prompts.db`) will be persisted in the project root directory.

To stop the services:
```bash
docker-compose down
``` 