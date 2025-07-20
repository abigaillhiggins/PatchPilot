// Todos JavaScript
let todos = [];
let filteredTodos = [];

document.addEventListener('DOMContentLoaded', function() {
    loadTodos();
    setupEventListeners();
});

function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', window.utils.debounce(handleSearch, 300));
    }

    // Filters
    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', handleFilter);
    }

    const languageFilter = document.getElementById('language-filter');
    if (languageFilter) {
        languageFilter.addEventListener('change', handleFilter);
    }

    // Todo form
    const todoForm = document.getElementById('todo-form');
    if (todoForm) {
        todoForm.addEventListener('submit', handleTodoSubmit);
    }
}

async function loadTodos() {
    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.todos}`);
        todos = await response.json();
        filteredTodos = [...todos];
        renderTodos();
        updateTodoCount();
    } catch (error) {
        console.error('Error loading todos:', error);
        window.utils.showNotification('Failed to load todos', 'error');
    }
}

function renderTodos() {
    const container = document.getElementById('todos-container');
    const emptyState = document.getElementById('empty-state');

    if (filteredTodos.length === 0) {
        container.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    container.classList.remove('hidden');
    emptyState.classList.add('hidden');

    container.innerHTML = filteredTodos.map(todo => `
        <div class="card p-6 fade-in">
            <div class="flex items-start justify-between">
                <div class="flex items-start space-x-4 flex-1">
                    <div class="flex-shrink-0 mt-1">
                        <input type="checkbox" 
                               ${todo.completed ? 'checked' : ''} 
                               onchange="toggleTodoStatus(${todo.id}, this.checked)"
                               class="rounded border-gray-300 text-red-600 focus:ring-red-500">
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center space-x-2 mb-2">
                            <h3 class="text-lg font-medium text-gray-900 ${todo.completed ? 'line-through' : ''}">${todo.title}</h3>
                            ${todo.completed ? `
                                <span class="success-badge inline-flex items-center px-2 py-1 rounded-full text-xs font-medium">
                                    <i class="fas fa-check mr-1"></i>Completed
                                </span>
                            ` : ''}
                            ${todo.patch_id ? `
                                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                    <i class="fas fa-code mr-1"></i>Generated
                                </span>
                            ` : ''}
                        </div>
                        
                        ${todo.description ? `<p class="text-gray-600 mb-2">${todo.description}</p>` : ''}
                        
                        <div class="flex items-center space-x-4 text-sm text-gray-500">
                            ${todo.language ? `
                                <span class="inline-flex items-center">
                                    <i class="fas fa-code mr-1"></i>${todo.language}
                                </span>
                            ` : ''}
                            <span class="inline-flex items-center">
                                <i class="fas fa-calendar mr-1"></i>${window.utils.formatDate(todo.created_at)}
                            </span>
                        </div>

                        ${todo.requirements && todo.requirements.length > 0 ? `
                            <div class="mt-3">
                                <h4 class="text-sm font-medium text-gray-700 mb-1">Requirements:</h4>
                                <ul class="text-sm text-gray-600 space-y-1">
                                    ${todo.requirements.map(req => `<li>• ${req}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}

                        ${todo.package_requirements && todo.package_requirements.length > 0 ? `
                            <div class="mt-3">
                                <h4 class="text-sm font-medium text-gray-700 mb-1">Package Requirements:</h4>
                                <div class="flex flex-wrap gap-1">
                                    ${todo.package_requirements.map(pkg => `
                                        <span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800">
                                            ${pkg}
                                        </span>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="flex items-center space-x-2 ml-4">
                    ${!todo.completed && !todo.patch_id ? `
                        <button onclick="generateCode(${todo.id})" class="btn-primary px-3 py-1 rounded-md text-sm">
                            <i class="fas fa-magic mr-1"></i>Generate
                        </button>
                    ` : ''}
                    ${todo.patch_id ? `
                        <button onclick="runPatch(${todo.id})" class="btn-secondary px-3 py-1 rounded-md text-sm">
                            <i class="fas fa-play mr-1"></i>Run
                        </button>
                    ` : ''}
                    <button onclick="editTodo(${todo.id})" class="px-3 py-1 text-gray-600 bg-gray-100 rounded-md text-sm hover:bg-gray-200">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteTodo(${todo.id}, '${todo.title}')" class="px-3 py-1 text-red-600 bg-red-100 rounded-md text-sm hover:bg-red-200">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function updateTodoCount() {
    const countElement = document.getElementById('todo-count');
    if (countElement) {
        countElement.textContent = `${filteredTodos.length} todo${filteredTodos.length !== 1 ? 's' : ''}`;
    }
}

function handleSearch(event) {
    const query = event.target.value.toLowerCase();
    filteredTodos = todos.filter(todo => 
        todo.title.toLowerCase().includes(query) ||
        (todo.description && todo.description.toLowerCase().includes(query))
    );
    renderTodos();
    updateTodoCount();
}

function handleFilter() {
    const statusFilter = document.getElementById('status-filter').value;
    const languageFilter = document.getElementById('language-filter').value;
    const searchQuery = document.getElementById('search-input').value.toLowerCase();

    filteredTodos = todos.filter(todo => {
        // Status filter
        if (statusFilter === 'completed' && !todo.completed) return false;
        if (statusFilter === 'pending' && todo.completed) return false;

        // Language filter
        if (languageFilter && todo.language !== languageFilter) return false;

        // Search filter
        if (searchQuery && !todo.title.toLowerCase().includes(searchQuery) && 
            !(todo.description && todo.description.toLowerCase().includes(searchQuery))) {
            return false;
        }

        return true;
    });

    renderTodos();
    updateTodoCount();
}

function clearFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('status-filter').value = '';
    document.getElementById('language-filter').value = '';
    filteredTodos = [...todos];
    renderTodos();
    updateTodoCount();
}

// Modal functions
function showCreateTodoModal() {
    document.getElementById('modal-title').textContent = 'Create New Todo';
    document.getElementById('todo-id').value = '';
    document.getElementById('todo-form').reset();
    document.getElementById('todo-modal').classList.remove('hidden');
}

function hideTodoModal() {
    document.getElementById('todo-modal').classList.add('hidden');
}

function editTodo(todoId) {
    const todo = todos.find(t => t.id === todoId);
    if (!todo) return;

    document.getElementById('modal-title').textContent = 'Edit Todo';
    document.getElementById('todo-id').value = todo.id;
    document.getElementById('todo-title').value = todo.title;
    document.getElementById('todo-description').value = todo.description || '';
    document.getElementById('todo-language').value = todo.language || 'python';
    document.getElementById('todo-requirements').value = todo.requirements ? todo.requirements.join('\n') : '';
    document.getElementById('todo-package-requirements').value = todo.package_requirements ? todo.package_requirements.join('\n') : '';
    document.getElementById('todo-context').value = todo.context || '';

    document.getElementById('todo-modal').classList.remove('hidden');
}

async function handleTodoSubmit(event) {
    event.preventDefault();
    
    const todoId = document.getElementById('todo-id').value;
    const todoData = {
        title: document.getElementById('todo-title').value,
        description: document.getElementById('todo-description').value,
        language: document.getElementById('todo-language').value,
        requirements: document.getElementById('todo-requirements').value.split('\n').filter(req => req.trim()),
        package_requirements: document.getElementById('todo-package-requirements').value.split('\n').filter(req => req.trim()),
        context: document.getElementById('todo-context').value
    };

    try {
        const url = todoId ? 
            `${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.todos}${todoId}` :
            `${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.todos}`;
        
        const method = todoId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(todoData)
        });

        if (response.ok) {
            window.utils.showNotification(`Todo ${todoId ? 'updated' : 'created'} successfully!`, 'success');
            hideTodoModal();
            loadTodos();
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to ${todoId ? 'update' : 'create'} todo: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error saving todo:', error);
        window.utils.showNotification(`Failed to ${todoId ? 'update' : 'create'} todo`, 'error');
    }
}

// Todo operations
async function toggleTodoStatus(todoId, completed) {
    try {
        const endpoint = completed ? 'complete' : 'uncomplete';
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.todos}${todoId}/${endpoint}`, {
            method: 'PUT'
        });

        if (response.ok) {
            window.utils.showNotification(`Todo ${completed ? 'completed' : 'uncompleted'}!`, 'success');
            loadTodos();
        } else {
            window.utils.showNotification('Failed to update todo status', 'error');
        }
    } catch (error) {
        console.error('Error updating todo status:', error);
        window.utils.showNotification('Failed to update todo status', 'error');
    }
}

async function generateCode(todoId) {
    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.generate_code}${todoId}`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            window.utils.showNotification(`Code generated successfully! Patch ID: ${result.patch_id}`, 'success');
            loadTodos();
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to generate code: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error generating code:', error);
        window.utils.showNotification('Failed to generate code', 'error');
    }
}

async function runPatch(todoId) {
    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.run_patch}${todoId}`, {
            method: 'POST'
        });

        if (response.ok) {
            window.utils.showNotification('Patch execution started!', 'success');
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to run patch: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error running patch:', error);
        window.utils.showNotification('Failed to run patch', 'error');
    }
}

function deleteTodo(todoId, title) {
    document.getElementById('delete-todo-title').textContent = title;
    document.getElementById('delete-modal').classList.remove('hidden');
    window.deleteTodoId = todoId;
}

function hideDeleteModal() {
    document.getElementById('delete-modal').classList.add('hidden');
    window.deleteTodoId = null;
}

async function confirmDeleteTodo() {
    if (!window.deleteTodoId) return;

    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.todos}${window.deleteTodoId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            window.utils.showNotification('Todo deleted successfully!', 'success');
            hideDeleteModal();
            loadTodos();
        } else {
            window.utils.showNotification('Failed to delete todo', 'error');
        }
    } catch (error) {
        console.error('Error deleting todo:', error);
        window.utils.showNotification('Failed to delete todo', 'error');
    }
}

async function clearCompletedTodos() {
    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.todos}clear-all?completed_only=true`, {
            method: 'DELETE'
        });

        if (response.ok) {
            const result = await response.json();
            window.utils.showNotification(result.message, 'success');
            loadTodos();
        } else {
            window.utils.showNotification('Failed to clear completed todos', 'error');
        }
    } catch (error) {
        console.error('Error clearing completed todos:', error);
        window.utils.showNotification('Failed to clear completed todos', 'error');
    }
}

function refreshTodos() {
    loadTodos();
} 