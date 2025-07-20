// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    setupEventListeners();
});

function setupEventListeners() {
    // Create todo form
    const createTodoForm = document.getElementById('create-todo-form');
    if (createTodoForm) {
        createTodoForm.addEventListener('submit', handleCreateTodo);
    }

    // Generate code form
    const generateCodeForm = document.getElementById('generate-code-form');
    if (generateCodeForm) {
        generateCodeForm.addEventListener('submit', handleGenerateCode);
    }
}

async function loadDashboardData() {
    try {
        // Load todos and patches in parallel
        const [todosResponse, patchesResponse] = await Promise.all([
            fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.todos}`),
            fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.patches}list`)
        ]);

        const todos = await todosResponse.json();
        const patches = await patchesResponse.json();

        updateDashboardStats(todos, patches);
        updateRecentTodos(todos);
        updateRecentPatches(patches.patches || []);
        populateTodoSelect(todos);

    } catch (error) {
        console.error('Error loading dashboard data:', error);
        window.utils.showNotification('Failed to load dashboard data', 'error');
    }
}

function updateDashboardStats(todos, patches) {
    const totalTodos = todos.length;
    const completedTodos = todos.filter(todo => todo.completed).length;
    const totalPatches = patches.patches ? patches.patches.length : 0;
    const generatedPatches = totalPatches; // All patches are generated

    document.getElementById('total-todos').textContent = totalTodos;
    document.getElementById('completed-todos').textContent = completedTodos;
    document.getElementById('total-patches').textContent = totalPatches;
    document.getElementById('generated-patches').textContent = generatedPatches;
}

function updateRecentTodos(todos) {
    const container = document.getElementById('recent-todos');
    const recentTodos = todos.slice(0, 5); // Show last 5 todos

    if (recentTodos.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4 text-gray-500">
                <i class="fas fa-tasks text-2xl mb-2"></i>
                <p>No todos yet</p>
            </div>
        `;
        return;
    }

    container.innerHTML = recentTodos.map(todo => `
        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center space-x-3">
                <div class="flex-shrink-0">
                    <input type="checkbox" 
                           ${todo.completed ? 'checked' : ''} 
                           onchange="toggleTodoStatus(${todo.id}, this.checked)"
                           class="rounded border-gray-300 text-red-600 focus:ring-red-500">
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-900">${todo.title}</p>
                    <p class="text-xs text-gray-500">${todo.language || 'No language'}</p>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                ${todo.patch_id ? `
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <i class="fas fa-code mr-1"></i>Generated
                    </span>
                ` : ''}
                <button onclick="location.href='/todos'" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function updateRecentPatches(patches) {
    const container = document.getElementById('recent-patches');
    const recentPatches = patches.slice(0, 5); // Show last 5 patches

    if (recentPatches.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4 text-gray-500">
                <i class="fas fa-code text-2xl mb-2"></i>
                <p>No patches yet</p>
            </div>
        `;
        return;
    }

    container.innerHTML = recentPatches.map(patch => `
        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center space-x-3">
                <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <i class="fas fa-code text-blue-600 text-sm"></i>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-900">${patch.description}</p>
                    <p class="text-xs text-gray-500">${patch.language} • ${patch.created_at}</p>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                <button onclick="viewPatch('${patch.patch_id}')" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-eye"></i>
                </button>
                <button onclick="location.href='/patches'" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function populateTodoSelect(todos) {
    const select = document.getElementById('todo-select');
    if (!select) return;

    // Clear existing options except the first one
    select.innerHTML = '<option value="">Select a todo...</option>';

    // Add todo options
    todos.filter(todo => !todo.completed && !todo.patch_id).forEach(todo => {
        const option = document.createElement('option');
        option.value = todo.id;
        option.textContent = todo.title;
        select.appendChild(option);
    });
}

// Modal functions
function showCreateTodoModal() {
    document.getElementById('create-todo-modal').classList.remove('hidden');
}

function hideCreateTodoModal() {
    document.getElementById('create-todo-modal').classList.add('hidden');
    document.getElementById('create-todo-form').reset();
}

function showGenerateCodeModal() {
    document.getElementById('generate-code-modal').classList.remove('hidden');
    // Refresh todo list
    loadDashboardData();
}

function hideGenerateCodeModal() {
    document.getElementById('generate-code-modal').classList.add('hidden');
    document.getElementById('generate-code-form').reset();
}

// Form handlers
async function handleCreateTodo(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const requirements = formData.get('todo-requirements').split('\n').filter(req => req.trim());
    const packageRequirements = formData.get('todo-package-requirements').split('\n').filter(req => req.trim());

    const todoData = {
        title: formData.get('todo-title'),
        description: formData.get('todo-description'),
        language: formData.get('todo-language'),
        requirements: requirements,
        package_requirements: packageRequirements,
        context: formData.get('todo-context')
    };

    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.todos}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(todoData)
        });

        if (response.ok) {
            window.utils.showNotification('Todo created successfully!', 'success');
            hideCreateTodoModal();
            loadDashboardData(); // Refresh dashboard
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to create todo: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error creating todo:', error);
        window.utils.showNotification('Failed to create todo', 'error');
    }
}

async function handleGenerateCode(event) {
    event.preventDefault();
    
    const todoId = document.getElementById('todo-select').value;
    if (!todoId) {
        window.utils.showNotification('Please select a todo', 'warning');
        return;
    }

    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.generate_code}${todoId}`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            window.utils.showNotification(`Code generated successfully! Patch ID: ${result.patch_id}`, 'success');
            hideGenerateCodeModal();
            loadDashboardData(); // Refresh dashboard
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to generate code: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error generating code:', error);
        window.utils.showNotification('Failed to generate code', 'error');
    }
}

// Utility functions
async function toggleTodoStatus(todoId, completed) {
    try {
        const endpoint = completed ? 'complete' : 'uncomplete';
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.todos}${todoId}/${endpoint}`, {
            method: 'PUT'
        });

        if (response.ok) {
            window.utils.showNotification(`Todo ${completed ? 'completed' : 'uncompleted'}!`, 'success');
            loadDashboardData(); // Refresh dashboard
        } else {
            window.utils.showNotification('Failed to update todo status', 'error');
        }
    } catch (error) {
        console.error('Error updating todo status:', error);
        window.utils.showNotification('Failed to update todo status', 'error');
    }
}

function viewPatch(patchId) {
    // Navigate to patches page with the specific patch
    window.location.href = `/patches?patch=${patchId}`;
}

// Update form field names to match the form structure
document.addEventListener('DOMContentLoaded', function() {
    const createTodoForm = document.getElementById('create-todo-form');
    if (createTodoForm) {
        createTodoForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const todoData = {
                title: document.getElementById('todo-title').value,
                description: document.getElementById('todo-description').value,
                language: document.getElementById('todo-language').value,
                requirements: document.getElementById('todo-requirements').value.split('\n').filter(req => req.trim()),
                package_requirements: document.getElementById('todo-package-requirements').value.split('\n').filter(req => req.trim()),
                context: document.getElementById('todo-context').value
            };

            createTodo(todoData);
        });
    }

    const generateCodeForm = document.getElementById('generate-code-form');
    if (generateCodeForm) {
        generateCodeForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const todoId = document.getElementById('todo-select').value;
            if (!todoId) {
                window.utils.showNotification('Please select a todo', 'warning');
                return;
            }

            generateCode(todoId);
        });
    }
});

async function createTodo(todoData) {
    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.todos}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(todoData)
        });

        if (response.ok) {
            window.utils.showNotification('Todo created successfully!', 'success');
            hideCreateTodoModal();
            loadDashboardData();
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to create todo: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error creating todo:', error);
        window.utils.showNotification('Failed to create todo', 'error');
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
            hideGenerateCodeModal();
            loadDashboardData();
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to generate code: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error generating code:', error);
        window.utils.showNotification('Failed to generate code', 'error');
    }
} 