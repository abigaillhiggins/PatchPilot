# PatchPilot

A powerful AI-driven code generation and patch management system with a beautiful web interface.

## Features

- 🤖 **AI-Powered Code Generation** - Generate code from natural language descriptions
- 📝 **Todo Management** - Create and manage coding tasks with requirements
- 🔧 **Code Patches** - Generate, execute, and manage code patches
- 🚀 **Git Integration** - Full Git operations for version control
- 🎨 **Beautiful Frontend** - Modern Jekyll-based web interface with red theme
- ⚡ **Real-time Execution** - Execute and monitor code patches in real-time
- 🔄 **Auto-regeneration** - Intelligent code regeneration on execution failures

## Architecture

PatchPilot consists of two main components:

1. **FastAPI Backend** (`src/api/server.py`) - RESTful API for all operations
2. **Jekyll Frontend** (`frontend/`) - Beautiful web interface built with Ruby/Jekyll

## Quick Start

### 1. Start the Backend API

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
python run.py
```

The API will be available at `http://localhost:8000`

### 2. Start the Frontend

```bash
# Option 1: Use the startup script
./start_frontend.sh

# Option 2: Manual setup
cd frontend
bundle install
bundle exec jekyll serve --livereload
```

The frontend will be available at `http://localhost:4000`

## Frontend Features

The Jekyll frontend provides a beautiful, responsive interface with:

- **Dashboard** - Overview with statistics and quick actions
- **Todo Management** - Full CRUD operations with search and filtering
- **Patch Management** - View, execute, and manage generated code
- **Git Operations** - Complete repository management
- **Red Theme** - Modern, cohesive design with red color scheme

### Frontend Technology Stack

- **Jekyll** - Static site generator
- **Ruby** - Backend language
- **Tailwind CSS** - Utility-first CSS framework
- **Font Awesome** - Icon library
- **JavaScript (ES6+)** - Frontend interactivity

## API Endpoints

### Todos
- `GET /todos/` - List all todos
- `POST /todos/` - Create new todo
- `PUT /todos/{id}/complete` - Mark todo as complete
- `PUT /todos/{id}/uncomplete` - Mark todo as incomplete
- `DELETE /todos/{id}` - Delete todo
- `DELETE /todos/clear-all` - Clear all todos

### Code Generation
- `POST /generate-code/{todo_id}` - Generate code from todo
- `POST /run-patch/{todo_id}` - Run patch execution
- `POST /execute-patch/` - Execute patch directly
- `GET /patch-status/{patch_id}` - Get patch execution status

### Patches
- `GET /patches/list` - List all patches
- `DELETE /patches/clear` - Clear patches

### Git Operations
- `POST /git/init` - Initialize repository
- `POST /git/config` - Configure Git user
- `POST /git/remote` - Add remote
- `POST /git/commit` - Create commit
- `POST /git/push` - Push changes
- `POST /git/push-patch/{patch_id}` - Push specific patch
- `GET /git/status` - Get repository status

## Usage Examples

### Creating a Todo and Generating Code

1. **Create a Todo**:
   ```bash
   curl -X POST "http://localhost:8000/todos/" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Web Scraper",
       "description": "Create a web scraper for news articles",
       "language": "python",
       "requirements": [
         "Scrape news articles from a website",
         "Extract title, content, and date",
         "Save to CSV file"
       ],
       "package_requirements": [
         "requests>=2.25.0",
         "beautifulsoup4>=4.9.0",
         "pandas>=1.3.0"
       ]
     }'
   ```

2. **Generate Code**:
   ```bash
   curl -X POST "http://localhost:8000/generate-code/1"
   ```

3. **Execute the Patch**:
   ```bash
   curl -X POST "http://localhost:8000/execute-patch/" \
     -H "Content-Type: application/json" \
     -d '{"patch_id": "generated_patch_id", "analyze": true}'
   ```

### Using the Web Interface

1. Open `http://localhost:4000` in your browser
2. Navigate to the **Todos** page
3. Click **New Todo** to create a task
4. Fill in the requirements and click **Create Todo**
5. Click **Generate** to create code from the todo
6. View the generated patch in the **Patches** page
7. Click **Execute** to run the code
8. Use **Git Operations** to commit and push your changes

## Configuration

### Backend Configuration

Environment variables:
- `DB_PATH` - Path to SQLite database (default: `todos.db`)
- `GROQ_API_KEY` - Your Groq API key for code generation

### Frontend Configuration

Edit `frontend/_config.yml`:
```yaml
api_base_url: "http://localhost:8000"
theme_colors:
  primary: "#dc2626"      # Main red color
  secondary: "#991b1b"    # Darker red
  accent: "#fca5a5"       # Light red
```

## Development

### Backend Development

The backend is built with FastAPI and includes:
- SQLite database for todo storage
- Groq API integration for code generation
- Isolated environment execution
- Git operations management

### Frontend Development

The frontend is built with Jekyll and includes:
- Responsive design with Tailwind CSS
- Real-time API integration
- Modal-based interactions
- Search and filtering capabilities

## Project Structure

```
PatchPilot-groq/
├── src/
│   ├── api/
│   │   └── server.py          # FastAPI server
│   ├── core/
│   │   ├── models.py          # Data models
│   │   ├── db_utils.py        # Database utilities
│   │   └── todo_commands.py   # Todo operations
│   ├── generators/
│   │   └── code_generator.py  # Code generation logic
│   └── utils/
│       ├── env_manager.py     # Environment management
│       └── git_manager.py     # Git operations
├── frontend/                  # Jekyll frontend
│   ├── _config.yml           # Jekyll configuration
│   ├── _layouts/
│   │   └── default.html      # Main layout
│   ├── assets/js/            # JavaScript files
│   ├── index.html            # Dashboard
│   ├── todos.html            # Todo management
│   ├── patches.html          # Patch management
│   ├── git.html              # Git operations
│   └── README.md             # Frontend documentation
├── patches/                   # Generated code patches
├── requirements.txt           # Python dependencies
├── run.py                    # Backend startup script
├── start_frontend.sh         # Frontend startup script
└── README.md                 # This file
```

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure the FastAPI server is running on port 8000
   - Check the `api_base_url` in `frontend/_config.yml`

2. **Jekyll Build Errors**
   - Install Ruby 2.7+ and Bundler
   - Run `bundle install` in the frontend directory

3. **Code Generation Fails**
   - Verify your Groq API key is set
   - Check the API logs for detailed error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both backend and frontend
5. Submit a pull request

## License

This project is licensed under the MIT License.

---

Built with ❤️ using FastAPI, Jekyll, and AI-powered code generation. 
