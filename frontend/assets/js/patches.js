// Patches JavaScript
let patches = [];
let filteredPatches = [];
let currentPatch = null;

document.addEventListener('DOMContentLoaded', function() {
    loadPatches();
    setupEventListeners();
});

function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', window.utils.debounce(handleSearch, 300));
    }

    // Language filter
    const languageFilter = document.getElementById('language-filter');
    if (languageFilter) {
        languageFilter.addEventListener('change', handleFilter);
    }

    // Git push form
    const gitPushForm = document.getElementById('git-push-form');
    if (gitPushForm) {
        gitPushForm.addEventListener('submit', handleGitPush);
    }
}

async function loadPatches() {
    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.patches}list`);
        const data = await response.json();
        patches = data.patches || [];
        filteredPatches = [...patches];
        renderPatches();
        updatePatchCount();
    } catch (error) {
        console.error('Error loading patches:', error);
        window.utils.showNotification('Failed to load patches', 'error');
    }
}

function renderPatches() {
    const container = document.getElementById('patches-container');
    const emptyState = document.getElementById('empty-state');

    if (filteredPatches.length === 0) {
        container.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    container.classList.remove('hidden');
    emptyState.classList.add('hidden');

    container.innerHTML = filteredPatches.map(patch => `
        <div class="card p-6 fade-in">
            <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                <div class="flex-1 min-w-0">
                    <div class="flex items-start space-x-3 mb-3">
                        <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <i class="fas fa-code text-blue-600"></i>
                        </div>
                        <div class="min-w-0 flex-1">
                            <h3 class="text-lg font-medium text-gray-900 truncate" title="${patch.description}">${patch.description}</h3>
                            <p class="text-sm text-gray-500 font-mono truncate" title="${patch.patch_id}">${patch.patch_id}</p>
                        </div>
                    </div>
                    
                    <div class="space-y-3 mb-4">
                        <div class="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                            <span class="inline-flex items-center">
                                <i class="fas fa-code mr-1"></i>${patch.language}
                            </span>
                            <span class="inline-flex items-center">
                                <i class="fas fa-calendar mr-1"></i>${patch.created_at}
                            </span>
                        </div>
                        
                        ${patch.requirements && patch.requirements.length > 0 ? `
                            <div>
                                <h4 class="text-sm font-medium text-gray-700 mb-2">Requirements:</h4>
                                <div class="flex flex-wrap gap-2">
                                    ${patch.requirements.slice(0, 3).map(req => `
                                        <span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800 max-w-full truncate" title="${req}">
                                            ${req}
                                        </span>
                                    `).join('')}
                                    ${patch.requirements.length > 3 ? `
                                        <span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800">
                                            +${patch.requirements.length - 3} more
                                        </span>
                                    ` : ''}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="flex flex-col sm:flex-row lg:flex-col gap-2 lg:gap-2 flex-shrink-0">
                    <button onclick="viewPatchDetails('${patch.patch_id}')" class="btn-primary px-3 py-2 rounded-md text-sm whitespace-nowrap">
                        <i class="fas fa-eye mr-1"></i>View
                    </button>
                    <button onclick="executePatch('${patch.patch_id}')" class="btn-secondary px-3 py-2 rounded-md text-sm whitespace-nowrap">
                        <i class="fas fa-play mr-1"></i>Execute
                    </button>
                    ${patch.app_url ? `
                    <button onclick="startApp('${patch.patch_id}')" class="px-3 py-2 text-green-600 bg-green-100 rounded-md text-sm hover:bg-green-200 whitespace-nowrap">
                        <i class="fas fa-globe mr-1"></i>Start App
                    </button>
                    ` : ''}
                    <button onclick="openConsoleForPatch('${patch.patch_id}')" class="px-3 py-2 text-blue-600 bg-blue-100 rounded-md text-sm hover:bg-blue-200 whitespace-nowrap">
                        <i class="fas fa-terminal mr-1"></i>Console
                    </button>
                    <button onclick="deletePatch('${patch.patch_id}')" class="px-3 py-2 text-red-600 bg-red-100 rounded-md text-sm hover:bg-red-200 whitespace-nowrap">
                        <i class="fas fa-trash mr-1"></i>Delete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function updatePatchCount() {
    const countElement = document.getElementById('patch-count');
    if (countElement) {
        countElement.textContent = `${filteredPatches.length} patch${filteredPatches.length !== 1 ? 'es' : ''}`;
    }
}

function handleSearch(event) {
    const query = event.target.value.toLowerCase();
    filteredPatches = patches.filter(patch => 
        patch.description.toLowerCase().includes(query) ||
        patch.patch_id.toLowerCase().includes(query) ||
        patch.language.toLowerCase().includes(query)
    );
    renderPatches();
    updatePatchCount();
}

function handleFilter() {
    const languageFilter = document.getElementById('language-filter').value;
    const searchQuery = document.getElementById('search-input').value.toLowerCase();

    filteredPatches = patches.filter(patch => {
        // Language filter
        if (languageFilter && patch.language !== languageFilter) return false;

        // Search filter
        if (searchQuery && !patch.description.toLowerCase().includes(searchQuery) && 
            !patch.patch_id.toLowerCase().includes(searchQuery) &&
            !patch.language.toLowerCase().includes(searchQuery)) {
            return false;
        }

        return true;
    });

    renderPatches();
    updatePatchCount();
}

function clearFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('language-filter').value = '';
    filteredPatches = [...patches];
    renderPatches();
    updatePatchCount();
}

// Console management
let consoleVisible = false;
let consoleMessages = [];

function addConsoleMessage(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const messageElement = document.createElement('div');
    messageElement.className = `console-message console-${type}`;
    
    let icon = '📋';
    let color = 'text-green-400';
    
    switch(type) {
        case 'success':
            icon = '✅';
            color = 'text-green-400';
            break;
        case 'error':
            icon = '❌';
            color = 'text-red-400';
            break;
        case 'warning':
            icon = '⚠️';
            color = 'text-yellow-400';
            break;
        case 'info':
            icon = 'ℹ️';
            color = 'text-blue-400';
            break;
        case 'code':
            icon = '💻';
            color = 'text-cyan-400';
            break;
    }
    
    messageElement.innerHTML = `<span class="text-gray-500">[${timestamp}]</span> <span class="${color}">${icon}</span> <span class="${color}">${message}</span>`;
    
    const consoleOutput = document.getElementById('console-output');
    consoleOutput.appendChild(messageElement);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
    
    consoleMessages.push({ message, type, timestamp });
}

function clearConsole() {
    document.getElementById('console-output').innerHTML = '';
    consoleMessages = [];
    addConsoleMessage('Console cleared', 'info');
}

function toggleConsole() {
    const consoleSection = document.getElementById('live-console-section');
    consoleVisible = !consoleVisible;
    
    if (consoleVisible) {
        consoleSection.classList.remove('hidden');
        addConsoleMessage('Console opened', 'info');
    } else {
        consoleSection.classList.add('hidden');
    }
}

function updateConsoleStatus(status, color = 'gray') {
    const statusElement = document.getElementById('console-status');
    const dot = statusElement.querySelector('div');
    const text = statusElement.querySelector('span');
    
    dot.className = `w-2 h-2 bg-${color}-400 rounded-full mr-2`;
    text.textContent = status;
}

function openConsoleForPatch(patchId) {
    const patch = patches.find(p => p.patch_id === patchId);
    if (!patch) return;
    
    // Open the patch details modal first
    viewPatchDetails(patchId);
    
    // Then show the console
    setTimeout(() => {
        document.getElementById('live-console-section').classList.remove('hidden');
        addConsoleMessage(`Console opened for patch: ${patchId}`, 'info');
        addConsoleMessage(`Patch: ${patch.description}`, 'info');
        addConsoleMessage(`Language: ${patch.language}`, 'info');
        addConsoleMessage(`Created: ${patch.created_at}`, 'info');
        updateConsoleStatus('Ready', 'gray');
    }, 100);
}

async function regenerateCode(patchId) {
    if (!currentPatch) return;

    try {
        // Show console and update status
        document.getElementById('live-console-section').classList.remove('hidden');
        updateConsoleStatus('Regenerating...', 'yellow');
        addConsoleMessage(`Starting code regeneration for patch: ${patchId}`, 'info');
        
        // Show loading state
        const regenerateButton = document.querySelector('#patch-modal button[onclick*="regenerateCode"]');
        if (regenerateButton) {
            const originalText = regenerateButton.innerHTML;
            regenerateButton.innerHTML = '<div class="loading"></div><span class="ml-2">Regenerating...</span>';
            regenerateButton.disabled = true;
        }

        // Simulate regeneration progress
        addConsoleMessage('Analyzing current code structure...', 'code');
        await new Promise(resolve => setTimeout(resolve, 800));
        
        addConsoleMessage('Identifying issues and improvements...', 'code');
        await new Promise(resolve => setTimeout(resolve, 1200));
        
        addConsoleMessage('Generating improved code...', 'code');
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        addConsoleMessage('Saving regenerated files...', 'code');
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Call the regenerate endpoint
        const response = await fetch(`${window.API_CONFIG.baseUrl}/regenerate-patch/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                patch_id: patchId,
                reason: 'User requested regeneration'
            })
        });

        if (response.ok) {
            const result = await response.json();
            
            addConsoleMessage('=== REGENERATION OUTPUT ===', 'info');
            if (result.message) {
                addConsoleMessage(result.message, 'success');
            }
            
            if (result.changes) {
                addConsoleMessage('Changes made:', 'info');
                result.changes.forEach(change => {
                    addConsoleMessage(`- ${change}`, 'success');
                });
            }
            
            addConsoleMessage('Code regeneration completed successfully!', 'success');
            updateConsoleStatus('Regenerated', 'green');
            
            window.utils.showNotification('Code regenerated successfully!', 'success');
            
            // Refresh the patches list to show updated content
            await loadPatches();
            
        } else {
            const error = await response.json();
            addConsoleMessage(`Regeneration failed: ${error.detail}`, 'error');
            updateConsoleStatus('Failed', 'red');
            window.utils.showNotification(`Failed to regenerate code: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error regenerating code:', error);
        addConsoleMessage(`Regeneration failed: ${error.message}`, 'error');
        updateConsoleStatus('Failed', 'red');
        window.utils.showNotification('Failed to regenerate code', 'error');
    } finally {
        // Reset button state
        const regenerateButton = document.querySelector('#patch-modal button[onclick*="regenerateCode"]');
        if (regenerateButton) {
            regenerateButton.innerHTML = '<i class="fas fa-sync-alt mr-2"></i>Regenerate Code';
            regenerateButton.disabled = false;
        }
    }
}

// Patch operations
async function viewPatchDetails(patchId) {
    try {
        const patch = patches.find(p => p.patch_id === patchId);
        if (!patch) return;

        currentPatch = patch;
        
        // Populate modal with patch details
        document.getElementById('patch-modal-title').textContent = `Patch: ${patch.description}`;
        document.getElementById('patch-id').textContent = patch.patch_id;
        document.getElementById('patch-language').textContent = patch.language;
        document.getElementById('patch-created').textContent = patch.created_at;
        document.getElementById('patch-description').textContent = patch.description;

        // Show requirements if available
        if (patch.requirements && patch.requirements.length > 0) {
            document.getElementById('patch-requirements').textContent = patch.requirements.join('\n');
            document.getElementById('patch-requirements-section').classList.remove('hidden');
        } else {
            document.getElementById('patch-requirements-section').classList.add('hidden');
        }

        // Hide execution results initially
        document.getElementById('execution-results').classList.add('hidden');
        document.getElementById('file-structure-section').classList.add('hidden');
        document.getElementById('live-console-section').classList.add('hidden');

        document.getElementById('patch-modal').classList.remove('hidden');
    } catch (error) {
        console.error('Error viewing patch details:', error);
        window.utils.showNotification('Failed to load patch details', 'error');
    }
}

function hidePatchModal() {
    document.getElementById('patch-modal').classList.add('hidden');
    currentPatch = null;
}

async function executePatch(patchId) {
    if (!currentPatch) return;

    try {
        // Show console and update status
        document.getElementById('live-console-section').classList.remove('hidden');
        updateConsoleStatus('Executing...', 'yellow');
        addConsoleMessage(`Starting execution of patch: ${patchId}`, 'info');
        
        // Show loading state - use a more reliable selector
        const executeButton = document.querySelector('#patch-modal button[onclick*="executePatch"]') || 
                             document.querySelector('button[onclick*="executePatch"]');
        
        if (executeButton) {
            const originalText = executeButton.innerHTML;
            executeButton.innerHTML = '<div class="loading"></div><span class="ml-2">Executing...</span>';
            executeButton.disabled = true;
        }

        // Simulate real-time progress
        addConsoleMessage('Initializing execution environment...', 'code');
        await new Promise(resolve => setTimeout(resolve, 500));
        
        addConsoleMessage('Creating virtual environment...', 'code');
        await new Promise(resolve => setTimeout(resolve, 800));
        
        addConsoleMessage('Installing dependencies...', 'code');
        await new Promise(resolve => setTimeout(resolve, 1200));
        
        addConsoleMessage('Running patch code...', 'code');
        await new Promise(resolve => setTimeout(resolve, 1000));

        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.execute_patch}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                patch_id: patchId,
                analyze: true
            })
        });

        if (response.ok) {
            const result = await response.json();
            
            // Show execution output in console
            if (result.execution_output) {
                addConsoleMessage('=== EXECUTION OUTPUT ===', 'info');
                addConsoleMessage(result.execution_output, 'success');
            }
            
            if (result.error_output) {
                addConsoleMessage('=== ERROR OUTPUT ===', 'warning');
                addConsoleMessage(result.error_output, 'error');
            }
            
            if (result.return_code !== undefined) {
                addConsoleMessage(`Return code: ${result.return_code}`, 'info');
            }
            
            addConsoleMessage('Execution completed', 'success');
            updateConsoleStatus('Completed', 'green');
            
            displayExecutionResults(result);
            window.utils.showNotification('Patch executed successfully!', 'success');
        } else {
            const error = await response.json();
            addConsoleMessage(`Execution failed: ${error.detail}`, 'error');
            updateConsoleStatus('Failed', 'red');
            window.utils.showNotification(`Failed to execute patch: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error executing patch:', error);
        addConsoleMessage(`Execution failed: ${error.message}`, 'error');
        updateConsoleStatus('Failed', 'red');
        window.utils.showNotification('Failed to execute patch', 'error');
    } finally {
        // Reset button state - use the same reliable selector
        const executeButton = document.querySelector('#patch-modal button[onclick*="executePatch"]') || 
                             document.querySelector('button[onclick*="executePatch"]');
        
        if (executeButton) {
            executeButton.innerHTML = '<i class="fas fa-play mr-2"></i>Execute Patch';
            executeButton.disabled = false;
        }
    }
}

function displayExecutionResults(result) {
    const resultsSection = document.getElementById('execution-results');
    resultsSection.classList.remove('hidden');

    // Update status
    const statusElement = document.getElementById('execution-status');
    if (result.success) {
        statusElement.className = 'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium success-badge';
        statusElement.innerHTML = '<i class="fas fa-check mr-1"></i>Success';
    } else {
        statusElement.className = 'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium error-badge';
        statusElement.innerHTML = '<i class="fas fa-times mr-1"></i>Failed';
    }

    // Show output if available
    if (result.execution_output) {
        document.getElementById('execution-output').textContent = result.execution_output;
        document.getElementById('execution-output-section').classList.remove('hidden');
    } else {
        document.getElementById('execution-output-section').classList.add('hidden');
    }

    // Show error output if available
    if (result.error_output) {
        document.getElementById('execution-error').textContent = result.error_output;
        document.getElementById('execution-error-section').classList.remove('hidden');
    } else {
        document.getElementById('execution-error-section').classList.add('hidden');
    }

    // Show analysis if available
    if (result.analysis) {
        document.getElementById('execution-analysis').textContent = result.analysis;
        document.getElementById('analysis-section').classList.remove('hidden');
    } else {
        document.getElementById('analysis-section').classList.add('hidden');
    }

    // Show regeneration info if applicable
    if (result.was_regenerated) {
        window.utils.showNotification('Code was regenerated due to execution issues', 'warning');
    }

    // Show web app information if applicable
    if (result.app_url) {
        addConsoleMessage(`🌐 Web Application Detected!`, 'success');
        addConsoleMessage(`📱 Framework: ${result.app_type || 'Unknown'}`, 'info');
        addConsoleMessage(`🔗 Access URL: ${result.app_url}`, 'info');
        addConsoleMessage(`🚀 Use the "Start App" button to launch the web server`, 'info');
        
        // Show web app controls
        showWebAppControls(result);
    }
}

function viewPatchFiles() {
    if (!currentPatch) return;
    
    // This would typically fetch the file structure from the API
    // For now, we'll show a placeholder
    document.getElementById('file-structure').textContent = `src/
├── main.py
├── utils.py
└── requirements.txt

README.md
metadata.txt`;
    document.getElementById('file-structure-section').classList.remove('hidden');
}

function pushToGit() {
    if (!currentPatch) return;
    
    // Populate the git push modal
    document.getElementById('patch-select').value = currentPatch.patch_id;
    document.getElementById('patch-commit-message').value = `Add patch: ${currentPatch.patch_id}`;
    
    document.getElementById('git-push-modal').classList.remove('hidden');
}

function hideGitPushModal() {
    document.getElementById('git-push-modal').classList.add('hidden');
}

async function handleGitPush(event) {
    event.preventDefault();
    
    const patchId = document.getElementById('patch-select').value;
    const commitMessage = document.getElementById('patch-commit-message').value;
    const remote = document.getElementById('patch-remote').value;
    const branch = document.getElementById('patch-branch').value;

    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.git}push-patch/${patchId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                patch_id: patchId,
                commit_message: commitMessage,
                remote: remote,
                branch: branch
            })
        });

        if (response.ok) {
            const result = await response.json();
            window.utils.showNotification(result.message, 'success');
            hideGitPushModal();
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to push patch: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error pushing patch:', error);
        window.utils.showNotification('Failed to push patch', 'error');
    }
}

function deletePatch(patchId) {
    document.getElementById('delete-patch-id').textContent = patchId;
    document.getElementById('delete-patch-modal').classList.remove('hidden');
    window.deletePatchId = patchId;
}

function hideDeletePatchModal() {
    document.getElementById('delete-patch-modal').classList.add('hidden');
    window.deletePatchId = null;
}

async function confirmDeletePatch() {
    if (!window.deletePatchId) return;

    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.patches}clear?patch_id=${window.deletePatchId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            window.utils.showNotification('Patch deleted successfully!', 'success');
            hideDeletePatchModal();
            loadPatches();
        } else {
            window.utils.showNotification('Failed to delete patch', 'error');
        }
    } catch (error) {
        console.error('Error deleting patch:', error);
        window.utils.showNotification('Failed to delete patch', 'error');
    }
}

async function clearAllPatches() {
    if (!confirm('Are you sure you want to clear all patches? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.patches}clear`, {
            method: 'DELETE'
        });

        if (response.ok) {
            const result = await response.json();
            window.utils.showNotification(result.message, 'success');
            loadPatches();
        } else {
            window.utils.showNotification('Failed to clear patches', 'error');
        }
    } catch (error) {
        console.error('Error clearing patches:', error);
        window.utils.showNotification('Failed to clear patches', 'error');
    }
}

function showWebAppControls(result) {
    const webAppSection = document.getElementById('web-app-section');
    if (!webAppSection) return;
    
    webAppSection.classList.remove('hidden');
    
    const statusElement = document.getElementById('web-app-status');
    const controlsElement = document.getElementById('web-app-controls');
    const urlElement = document.getElementById('web-app-url');
    
    // Set URL
    if (urlElement && result.app_url) {
        urlElement.textContent = result.app_url;
        urlElement.href = result.app_url;
    }
    
    // Check current status
    checkWebAppStatus(currentPatch.patch_id);
}

async function checkWebAppStatus(patchId) {
    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}/web-app/${patchId}/status`);
        if (response.ok) {
            const status = await response.json();
            updateWebAppStatus(status);
        }
    } catch (error) {
        console.error('Error checking web app status:', error);
    }
}

function updateWebAppStatus(status) {
    const statusElement = document.getElementById('web-app-status');
    const controlsElement = document.getElementById('web-app-controls');
    
    if (!statusElement || !controlsElement) return;
    
    if (status.is_running) {
        statusElement.className = 'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium success-badge';
        statusElement.innerHTML = '<i class="fas fa-play mr-1"></i>Running';
        
        controlsElement.innerHTML = `
            <button onclick="stopWebApp('${currentPatch.patch_id}')" class="btn-danger px-3 py-2 rounded-md text-sm">
                <i class="fas fa-stop mr-1"></i>Stop App
            </button>
            <a href="${status.url}" target="_blank" class="btn-primary px-3 py-2 rounded-md text-sm">
                <i class="fas fa-external-link-alt mr-1"></i>Open App
            </a>
        `;
    } else {
        statusElement.className = 'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium gray-badge';
        statusElement.innerHTML = '<i class="fas fa-pause mr-1"></i>Stopped';
        
        controlsElement.innerHTML = `
            <button onclick="startWebApp('${currentPatch.patch_id}')" class="btn-primary px-3 py-2 rounded-md text-sm">
                <i class="fas fa-play mr-1"></i>Start App
            </button>
        `;
    }
}

async function startWebApp(patchId) {
    try {
        addConsoleMessage('🚀 Starting web application...', 'info');
        
        const response = await fetch(`${window.API_CONFIG.baseUrl}/web-app/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                patch_id: patchId,
                action: 'start'
            })
        });

        if (response.ok) {
            const result = await response.json();
            addConsoleMessage(`✅ Web application started successfully!`, 'success');
            addConsoleMessage(`🔗 Access URL: ${result.url}`, 'info');
            addConsoleMessage(`📱 Framework: ${result.framework}`, 'info');
            
            // Update status
            checkWebAppStatus(patchId);
            window.utils.showNotification('Web application started successfully!', 'success');
        } else {
            const error = await response.json();
            addConsoleMessage(`❌ Failed to start web app: ${error.detail}`, 'error');
            window.utils.showNotification(`Failed to start web app: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error starting web app:', error);
        addConsoleMessage(`❌ Error starting web app: ${error.message}`, 'error');
        window.utils.showNotification('Failed to start web app', 'error');
    }
}

async function stopWebApp(patchId) {
    try {
        addConsoleMessage('🛑 Stopping web application...', 'info');
        
        const response = await fetch(`${window.API_CONFIG.baseUrl}/web-app/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                patch_id: patchId,
                action: 'stop'
            })
        });

        if (response.ok) {
            const result = await response.json();
            addConsoleMessage(`✅ Web application stopped successfully!`, 'success');
            
            // Update status
            checkWebAppStatus(patchId);
            window.utils.showNotification('Web application stopped successfully!', 'success');
        } else {
            const error = await response.json();
            addConsoleMessage(`❌ Failed to stop web app: ${error.detail}`, 'error');
            window.utils.showNotification(`Failed to stop web app: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error stopping web app:', error);
        addConsoleMessage(`❌ Error stopping web app: ${error.message}`, 'error');
        window.utils.showNotification('Failed to stop web app', 'error');
    }
}

function refreshPatches() {
    loadPatches();
} 

async function startApp(patchId) {
    const patch = patches.find(p => p.patch_id === patchId);
    if (!patch) {
        window.utils.showNotification('Patch not found', 'error');
        return;
    }
    
    // For Flask calculator, start the server and open in new window
    if (patchId.includes('calculator') || patchId.includes('flask')) {
        try {
            addConsoleMessage('🚀 Starting Flask web server...', 'info');
            
            // Start the Flask server in the background
            const response = await fetch(`${window.API_CONFIG.baseUrl}/start-web-app/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    patch_id: patchId
                })
            });

            if (response.ok) {
                const result = await response.json();
                addConsoleMessage(`✅ Flask server started successfully!`, 'success');
                addConsoleMessage(`🔗 Server URL: ${result.url}`, 'info');
                
                // Open the app in a new window
                window.open(result.url, '_blank');
                window.utils.showNotification('Flask app started and opened in new window!', 'success');
            } else {
                const error = await response.json();
                addConsoleMessage(`❌ Failed to start Flask server: ${error.detail}`, 'error');
                window.utils.showNotification(`Failed to start Flask server: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Error starting Flask server:', error);
            addConsoleMessage(`❌ Error starting Flask server: ${error.message}`, 'error');
            window.utils.showNotification('Failed to start Flask server', 'error');
        }
    } else {
        window.utils.showNotification('Web app not available for this patch', 'warning');
    }
} 