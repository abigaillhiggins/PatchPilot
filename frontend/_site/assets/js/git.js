// Git Operations JavaScript
let recentOperations = [];

document.addEventListener('DOMContentLoaded', function() {
    loadGitStatus();
    setupEventListeners();
});

function setupEventListeners() {
    // Git config form
    const gitConfigForm = document.getElementById('git-config-form');
    if (gitConfigForm) {
        gitConfigForm.addEventListener('submit', handleGitConfig);
    }

    // Add remote form
    const addRemoteForm = document.getElementById('add-remote-form');
    if (addRemoteForm) {
        addRemoteForm.addEventListener('submit', handleAddRemote);
    }

    // Commit form
    const commitForm = document.getElementById('commit-form');
    if (commitForm) {
        commitForm.addEventListener('submit', handleCommit);
    }

    // Push form
    const pushForm = document.getElementById('push-form');
    if (pushForm) {
        pushForm.addEventListener('submit', handlePush);
    }

    // Push patch form
    const pushPatchForm = document.getElementById('push-patch-form');
    if (pushPatchForm) {
        pushPatchForm.addEventListener('submit', handlePushPatch);
    }
}

async function loadGitStatus() {
    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.git}status`);
        if (response.ok) {
            const data = await response.json();
            displayGitStatus(data.status);
        } else {
            displayGitStatus('Repository not initialized');
        }
    } catch (error) {
        console.error('Error loading git status:', error);
        displayGitStatus('Failed to load status');
    }
}

function displayGitStatus(status) {
    const statusElement = document.getElementById('git-status');
    if (statusElement) {
        statusElement.innerHTML = `
            <div class="bg-gray-50 rounded-lg p-4">
                <pre class="text-sm text-gray-700 whitespace-pre-wrap">${status}</pre>
            </div>
        `;
    }
}

// Git operations
async function initRepository() {
    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.git}init`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            window.utils.showNotification(result.message, 'success');
            addRecentOperation('Initialize Repository', 'success', result.message);
            loadGitStatus();
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to initialize repository: ${error.detail}`, 'error');
            addRecentOperation('Initialize Repository', 'error', error.detail);
        }
    } catch (error) {
        console.error('Error initializing repository:', error);
        window.utils.showNotification('Failed to initialize repository', 'error');
        addRecentOperation('Initialize Repository', 'error', 'Network error');
    }
}

// Modal functions
function showGitConfigModal() {
    document.getElementById('git-config-modal').classList.remove('hidden');
}

function hideGitConfigModal() {
    document.getElementById('git-config-modal').classList.add('hidden');
    document.getElementById('git-config-form').reset();
}

function showAddRemoteModal() {
    document.getElementById('add-remote-modal').classList.remove('hidden');
}

function hideAddRemoteModal() {
    document.getElementById('add-remote-modal').classList.add('hidden');
    document.getElementById('add-remote-form').reset();
}

function showCommitModal() {
    document.getElementById('commit-modal').classList.remove('hidden');
}

function hideCommitModal() {
    document.getElementById('commit-modal').classList.add('hidden');
    document.getElementById('commit-form').reset();
}

function showPushModal() {
    document.getElementById('push-modal').classList.remove('hidden');
}

function hidePushModal() {
    document.getElementById('push-modal').classList.add('hidden');
    document.getElementById('push-form').reset();
}

function showPushPatchModal() {
    // Load patches for the select dropdown
    loadPatchesForSelect();
    document.getElementById('push-patch-modal').classList.remove('hidden');
}

function hidePushPatchModal() {
    document.getElementById('push-patch-modal').classList.add('hidden');
    document.getElementById('push-patch-form').reset();
}

// Form handlers
async function handleGitConfig(event) {
    event.preventDefault();
    
    const name = document.getElementById('git-name').value;
    const email = document.getElementById('git-email').value;

    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.git}config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email })
        });

        if (response.ok) {
            const result = await response.json();
            window.utils.showNotification(result.message, 'success');
            addRecentOperation('Configure Git User', 'success', `Configured ${name} <${email}>`);
            hideGitConfigModal();
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to configure git: ${error.detail}`, 'error');
            addRecentOperation('Configure Git User', 'error', error.detail);
        }
    } catch (error) {
        console.error('Error configuring git:', error);
        window.utils.showNotification('Failed to configure git', 'error');
        addRecentOperation('Configure Git User', 'error', 'Network error');
    }
}

async function handleAddRemote(event) {
    event.preventDefault();
    
    const name = document.getElementById('remote-name').value;
    const url = document.getElementById('remote-url').value;

    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.git}remote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, url })
        });

        if (response.ok) {
            const result = await response.json();
            window.utils.showNotification(result.message, 'success');
            addRecentOperation('Add Remote', 'success', `Added remote ${name}: ${url}`);
            hideAddRemoteModal();
            loadGitStatus();
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to add remote: ${error.detail}`, 'error');
            addRecentOperation('Add Remote', 'error', error.detail);
        }
    } catch (error) {
        console.error('Error adding remote:', error);
        window.utils.showNotification('Failed to add remote', 'error');
        addRecentOperation('Add Remote', 'error', 'Network error');
    }
}

async function handleCommit(event) {
    event.preventDefault();
    
    const message = document.getElementById('commit-message').value;
    const files = document.getElementById('commit-files').value.split('\n').filter(file => file.trim());

    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.git}commit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message, 
                files: files.length > 0 ? files : ['*'] // Use all files if none specified
            })
        });

        if (response.ok) {
            const result = await response.json();
            window.utils.showNotification(result.message, 'success');
            addRecentOperation('Commit Changes', 'success', `Committed: ${message}`);
            hideCommitModal();
            loadGitStatus();
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to commit: ${error.detail}`, 'error');
            addRecentOperation('Commit Changes', 'error', error.detail);
        }
    } catch (error) {
        console.error('Error committing:', error);
        window.utils.showNotification('Failed to commit', 'error');
        addRecentOperation('Commit Changes', 'error', 'Network error');
    }
}

async function handlePush(event) {
    event.preventDefault();
    
    const remote = document.getElementById('push-remote').value;
    const branch = document.getElementById('push-branch').value;

    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.git}push`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ remote, branch })
        });

        if (response.ok) {
            const result = await response.json();
            window.utils.showNotification(result.message, 'success');
            addRecentOperation('Push Changes', 'success', `Pushed to ${remote}/${branch}`);
            hidePushModal();
            loadGitStatus();
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to push: ${error.detail}`, 'error');
            addRecentOperation('Push Changes', 'error', error.detail);
        }
    } catch (error) {
        console.error('Error pushing:', error);
        window.utils.showNotification('Failed to push', 'error');
        addRecentOperation('Push Changes', 'error', 'Network error');
    }
}

async function handlePushPatch(event) {
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
            addRecentOperation('Push Patch', 'success', `Pushed patch ${patchId} to ${remote}/${branch}`);
            hidePushPatchModal();
            loadGitStatus();
        } else {
            const error = await response.json();
            window.utils.showNotification(`Failed to push patch: ${error.detail}`, 'error');
            addRecentOperation('Push Patch', 'error', error.detail);
        }
    } catch (error) {
        console.error('Error pushing patch:', error);
        window.utils.showNotification('Failed to push patch', 'error');
        addRecentOperation('Push Patch', 'error', 'Network error');
    }
}

// Utility functions
async function loadPatchesForSelect() {
    try {
        const response = await fetch(`${window.API_CONFIG.baseUrl}${window.API_CONFIG.endpoints.patches}list`);
        const data = await response.json();
        const patches = data.patches || [];

        const select = document.getElementById('patch-select');
        select.innerHTML = '<option value="">Select a patch...</option>';
        
        patches.forEach(patch => {
            const option = document.createElement('option');
            option.value = patch.patch_id;
            option.textContent = `${patch.patch_id} - ${patch.description}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading patches for select:', error);
    }
}

function addRecentOperation(operation, status, message) {
    const operationObj = {
        operation,
        status,
        message,
        timestamp: new Date().toLocaleString()
    };

    recentOperations.unshift(operationObj);
    if (recentOperations.length > 10) {
        recentOperations = recentOperations.slice(0, 10);
    }

    renderRecentOperations();
}

function renderRecentOperations() {
    const container = document.getElementById('recent-operations');
    if (!container) return;

    if (recentOperations.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-history text-2xl mb-2"></i>
                <p>No recent operations</p>
            </div>
        `;
        return;
    }

    container.innerHTML = recentOperations.map(op => `
        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center space-x-3">
                <div class="flex-shrink-0">
                    <div class="w-8 h-8 rounded-full flex items-center justify-center ${
                        op.status === 'success' ? 'bg-green-100' : 'bg-red-100'
                    }">
                        <i class="fas ${
                            op.status === 'success' ? 'fa-check text-green-600' : 'fa-times text-red-600'
                        } text-sm"></i>
                    </div>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-900">${op.operation}</p>
                    <p class="text-xs text-gray-500">${op.message}</p>
                </div>
            </div>
            <div class="text-xs text-gray-400">
                ${op.timestamp}
            </div>
        </div>
    `).join('');
}

function refreshGitStatus() {
    loadGitStatus();
} 