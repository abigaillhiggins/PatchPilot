# PatchPilot Frontend

A beautiful, modern frontend for the PatchPilot API built with Jekyll and Ruby, featuring a red theme and comprehensive functionality for managing todos and code patches.

## Features

- 🎨 **Beautiful Red Theme** - Modern, responsive design with a cohesive red color scheme
- 📊 **Dashboard** - Overview with statistics, recent activity, and quick actions
- ✅ **Todo Management** - Full CRUD operations with search, filtering, and status tracking
- 🔧 **Code Generation** - AI-powered code generation from todo requirements
- 📦 **Patch Management** - View, execute, and manage generated code patches
- 🚀 **Git Integration** - Complete Git operations including repository management
- 📱 **Responsive Design** - Works perfectly on desktop, tablet, and mobile devices
- ⚡ **Real-time Updates** - Live status updates and notifications

## Screenshots

### Dashboard
- Overview statistics and recent activity
- Quick action buttons for common tasks
- Real-time status indicators

### Todos
- Create, edit, and delete todos
- Search and filter functionality
- Status tracking and code generation
- Requirements and package management

### Patches
- View generated code patches
- Execute patches with real-time output
- Git integration for version control
- Detailed execution results and analysis

### Git Operations
- Repository initialization and configuration
- Remote management and pushing
- Commit and push operations
- Patch-specific Git operations

## Technology Stack

- **Jekyll** - Static site generator
- **Ruby** - Backend language
- **Tailwind CSS** - Utility-first CSS framework
- **Font Awesome** - Icon library
- **JavaScript (ES6+)** - Frontend interactivity
- **Fetch API** - HTTP requests

## Prerequisites

- Ruby 2.7 or higher
- RubyGems
- Node.js (optional, for development)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd PatchPilot-groq/frontend
   ```

2. **Install Ruby dependencies**:
   ```bash
   bundle install
   ```

3. **Configure the API endpoint**:
   Edit `_config.yml` and update the `api_base_url` to point to your FastAPI server:
   ```yaml
   api_base_url: "http://localhost:8000"
   ```

## Running the Frontend

### Development Mode
```bash
bundle exec jekyll serve --livereload
```

The frontend will be available at `http://localhost:4000`

### Production Build
```bash
bundle exec jekyll build
```

The built site will be in the `_site` directory.

## Configuration

### API Configuration
Edit `_config.yml` to configure API endpoints:

```yaml
api_base_url: "http://localhost:8000"
api_endpoints:
  todos: "/todos/"
  patches: "/patches/"
  git: "/git/"
  generate_code: "/generate-code/"
  run_patch: "/run-patch/"
  execute_patch: "/execute-patch/"
  patch_status: "/patch-status/"
```

### Theme Colors
Customize the red theme in `_config.yml`:

```yaml
theme_colors:
  primary: "#dc2626"      # Main red color
  secondary: "#991b1b"    # Darker red
  accent: "#fca5a5"       # Light red
  background: "#fef2f2"   # Very light red background
  surface: "#ffffff"      # White surface
  text: "#1f2937"         # Dark text
  text_light: "#6b7280"   # Light text
```

## Project Structure

```
frontend/
├── _config.yml              # Jekyll configuration
├── _layouts/
│   └── default.html         # Main layout template
├── assets/
│   └── js/
│       ├── dashboard.js     # Dashboard functionality
│       ├── todos.js         # Todo management
│       ├── patches.js       # Patch management
│       └── git.js           # Git operations
├── index.html               # Dashboard page
├── todos.html               # Todos page
├── patches.html             # Patches page
├── git.html                 # Git operations page
├── Gemfile                  # Ruby dependencies
└── README.md               # This file
```

## API Integration

The frontend integrates with the PatchPilot FastAPI server through the following endpoints:

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

## Development

### Adding New Pages
1. Create a new HTML file in the root directory
2. Add front matter with layout and metadata
3. Add navigation link in `_layouts/default.html`

### Adding New JavaScript
1. Create a new JS file in `assets/js/`
2. Add it to the page's front matter scripts array
3. Follow the existing patterns for API calls and UI updates

### Styling
- Use Tailwind CSS classes for styling
- Custom CSS variables are defined in `_layouts/default.html`
- Follow the red theme color scheme

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check that the FastAPI server is running on the correct port
   - Verify the `api_base_url` in `_config.yml`
   - Check browser console for CORS errors

2. **Jekyll Build Errors**
   - Ensure Ruby and Jekyll are properly installed
   - Run `bundle install` to install dependencies
   - Check for syntax errors in YAML files

3. **JavaScript Errors**
   - Check browser console for errors
   - Verify API endpoints are correct
   - Ensure all required functions are defined

### Debug Mode
Enable debug logging by adding to `_config.yml`:
```yaml
debug: true
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review the API documentation
- Open an issue on GitHub

---

Built with ❤️ using Jekyll, Ruby, and a beautiful red theme. 