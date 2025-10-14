// Security System JavaScript
let securityEnabled = false;
let liveFeedInterval = null;

// Initialize security section
async function initSecurity() {
    // Start live feed immediately (camera is always on in I/O mode)
    startLiveFeed();
    
    updateSecurityStatus();
    loadRecentDetections();
    loadKnownCars();
    loadPatrolPositions();
    initPatrolControls();
    
    // Update every 5 seconds
    setInterval(() => {
        updateSecurityStatus();
        loadRecentDetections();
        updatePatrolStatus();
    }, 5000);
}

// Update security status display
async function updateSecurityStatus() {
    try {
        const status = await fetch('/api/security/status').then(r => r.json());
        
        if (status.error) {
            console.error('Security status error:', status.error);
            return;
        }
        
        // Update status badges
        document.getElementById('status-detection').textContent = status.detection_running ? 'Active' : 'Inactive';
        document.getElementById('status-detection').className = 'badge ' + (status.detection_running ? 'badge-car' : 'badge-unknown');
        
        document.getElementById('status-camera').textContent = status.camera_enabled ? 'Online' : 'Offline';
        document.getElementById('status-camera').className = 'badge ' + (status.camera_enabled ? 'badge-car' : 'badge-unknown');
        
        document.getElementById('status-pantilt').textContent = status.pantilt_enabled ? 'Online' : 'Offline';
        document.getElementById('status-pantilt').className = 'badge ' + (status.pantilt_enabled ? 'badge-car' : 'badge-unknown');
        
        document.getElementById('status-ai').textContent = status.detector_enabled ? 'Connected' : 'Disconnected';
        document.getElementById('status-ai').className = 'badge ' + (status.detector_enabled ? 'badge-car' : 'badge-unknown');
        
        document.getElementById('status-count').textContent = status.current_detections || 0;
        document.getElementById('status-tracking').textContent = status.tracking_target ? 'Active' : 'Inactive';
        
        // Update detection button
        const btn = document.getElementById('toggle-detection-btn');
        if (status.detection_running) {
            btn.innerHTML = 'Stop Detection';
            btn.className = 'btn btn-danger';
        } else {
            btn.innerHTML = 'Start Detection';
            btn.className = 'btn btn-success';
        }
        
        // In I/O mode, camera is always on, so keep feed running
        // (Don't stop the feed based on detection status)
        
        securityEnabled = status.detection_running;
        
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

// Toggle detection on/off
async function toggleDetection() {
    try {
        const endpoint = securityEnabled ? '/api/security/disable' : '/api/security/enable';
        const response = await fetch(endpoint, { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            await updateSecurityStatus();
        } else {
            alert('Failed to toggle detection: ' + result.message);
        }
    } catch (error) {
        console.error('Error toggling detection:', error);
        alert('Error: ' + error.message);
    }
}

// Live feed using canvas and snapshot polling (more reliable than MJPEG in img tag)
let liveFeedCanvas = null;
let liveFeedCtx = null;

// Start live feed
function startLiveFeed() {
    const canvas = document.getElementById('live-feed-canvas');
    const errorDiv = document.getElementById('feed-error');
    
    if (!canvas) {
        console.error('Canvas element not found');
        return;
    }
    
    liveFeedCanvas = canvas;
    liveFeedCtx = canvas.getContext('2d');
    
    // Show canvas, hide error
    canvas.style.display = 'block';
    errorDiv.style.display = 'none';
    
    console.log('Live feed started (snapshot mode)');
    
    // Start polling for frames
    updateLiveFeed();
    if (liveFeedInterval) {
        clearInterval(liveFeedInterval);
    }
    liveFeedInterval = setInterval(updateLiveFeed, 100); // 10 FPS (adjust as needed)
}

// Update live feed with latest snapshot
async function updateLiveFeed() {
    if (!liveFeedCanvas || !liveFeedCtx) return;
    
    try {
        const img = new Image();
        
        img.onload = function() {
            // Set canvas size to match image on first load
            if (liveFeedCanvas.width !== img.width || liveFeedCanvas.height !== img.height) {
                liveFeedCanvas.width = img.width;
                liveFeedCanvas.height = img.height;
            }
            
            // Draw image on canvas
            liveFeedCtx.drawImage(img, 0, 0);
        };
        
        img.onerror = function() {
            console.error('Failed to load frame');
        };
        
        // Load latest snapshot with cache-busting
        img.src = '/api/security/snapshot?' + new Date().getTime();
        
    } catch (error) {
        console.error('Error updating live feed:', error);
    }
}

// Stop live feed
function stopLiveFeed() {
    if (liveFeedInterval) {
        clearInterval(liveFeedInterval);
        liveFeedInterval = null;
    }
    
    if (liveFeedCanvas) {
        liveFeedCanvas.style.display = 'none';
    }
    
    console.log('Live feed stopped');
}

// Pan-Tilt control
async function movePanTilt(panDelta, tiltDelta) {
    try {
        const response = await fetch('/api/security/pantilt/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pan: panDelta, tilt: tiltDelta, speed: 5 })
        });
        const result = await response.json();
        if (!result.success) {
            console.error('Pan-Tilt move failed:', result.error);
        }
    } catch (error) {
        console.error('Error moving pan-tilt:', error);
    }
}

async function pantiltHome() {
    try {
        const response = await fetch('/api/security/pantilt/home', { method: 'POST' });
        const result = await response.json();
        if (!result.success) {
            console.error('Pan-Tilt home failed:', result.error);
        }
    } catch (error) {
        console.error('Error homing pan-tilt:', error);
    }
}

// Load recent detections
async function loadRecentDetections() {
    try {
        const detections = await fetch('/api/security/detections?limit=10').then(r => r.json());
        const tbody = document.getElementById('detections-tbody');
        
        if (!Array.isArray(detections) || detections.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px; color: var(--gray-600);">
                        No detections yet. Walk in front of the camera to test!
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = detections.map(det => `
            <tr>
                <td>
                    ${det.image_path ? `<img src="/${det.image_path}" class="detection-thumbnail" onclick="showDetectionDetails(${det.id})">` : 'N/A'}
                </td>
                <td>
                    <span class="badge badge-${det.object_type === 'person' ? 'person' : 'car'}">${det.object_type}</span>
                    ${det.car_id ? `<br><small>${det.car_id}</small>` : ''}
                </td>
                <td>${new Date(det.timestamp).toLocaleString()}</td>
                <td>${(det.confidence * 100).toFixed(1)}%</td>
                <td>${det.action_taken || 'None'}</td>
                <td>
                    <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.85em;" onclick="showDetectionDetails(${det.id})">
                        View
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading detections:', error);
    }
}

// Show detection details modal
async function showDetectionDetails(detectionId) {
    try {
        const detection = await fetch(`/api/security/detections/${detectionId}`).then(r => r.json());
        
        document.getElementById('modal-title').textContent = `Detection #${detection.id} - ${detection.object_type}`;
        document.getElementById('modal-body').innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    ${detection.image_path ? `<img src="/${detection.image_path}" style="width: 100%; border-radius: 8px;">` : ''}
                </div>
                <div>
                    <p><strong>Time:</strong> ${new Date(detection.timestamp).toLocaleString()}</p>
                    <p><strong>Type:</strong> ${detection.object_type}</p>
                    <p><strong>Confidence:</strong> ${(detection.confidence * 100).toFixed(1)}%</p>
                    ${detection.car_id ? `<p><strong>Car ID:</strong> ${detection.car_id}</p>` : ''}
                    <p><strong>Action Taken:</strong> ${detection.action_taken || 'None'}</p>
                    ${detection.bbox ? `<p><strong>Bounding Box:</strong> ${JSON.stringify(detection.bbox)}</p>` : ''}
                </div>
            </div>
        `;
        
        document.getElementById('detection-modal').classList.add('active');
    } catch (error) {
        console.error('Error loading detection details:', error);
    }
}

function closeDetectionModal() {
    document.getElementById('detection-modal').classList.remove('active');
}

// Load known cars
async function loadKnownCars() {
    try {
        const cars = await fetch('/api/security/cars').then(r => r.json());
        const container = document.getElementById('known-cars-list');
        
        if (!Array.isArray(cars) || cars.length === 0) {
            container.innerHTML = '<p style="color: var(--gray-600); text-align: center; padding: 20px;">No cars registered yet.</p>';
            return;
        }
        
        container.innerHTML = cars.map(car => `
            <div style="background: white; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>${car.car_id}</strong>
                    <div style="font-size: 0.9em; color: var(--gray-600);">${car.owner}</div>
                </div>
                <button class="btn btn-danger" style="padding: 6px 12px; font-size: 0.85em;" onclick="removeKnownCar('${car.car_id}')">
                    Delete
                </button>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading known cars:', error);
    }
}

// Show add car modal
function showAddCarModal() {
    document.getElementById('add-car-modal').classList.add('active');
}

function closeAddCarModal() {
    document.getElementById('add-car-modal').classList.remove('active');
}

// Add known car
async function addKnownCar() {
    const carId = document.getElementById('new-car-id').value.trim();
    const owner = document.getElementById('new-car-owner').value.trim();
    
    if (!carId || !owner) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        const response = await fetch('/api/security/cars', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ car_id: carId, owner: owner })
        });
        
        const result = await response.json();
        
        if (result.success) {
            closeAddCarModal();
            loadKnownCars();
            document.getElementById('new-car-id').value = '';
            document.getElementById('new-car-owner').value = '';
        } else {
            alert('Failed to add car: ' + result.message);
        }
    } catch (error) {
        console.error('Error adding car:', error);
        alert('Error: ' + error.message);
    }
}

// Remove known car
async function removeKnownCar(carId) {
    if (!confirm(`Remove car "${carId}"?`)) return;
    
    try {
        const response = await fetch(`/api/security/cars/${carId}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            loadKnownCars();
        } else {
            alert('Failed to remove car: ' + result.message);
        }
    } catch (error) {
        console.error('Error removing car:', error);
        alert('Error: ' + error.message);
    }
}



// Garage door control
async function openGarage() {
    if (!confirm('⚠ Open garage door?\n\nMake sure Sub-GHz app is open on Flipper with garage.sub loaded!')) {
        return;
    }
    
    try {
        const response = await fetch('/api/flipper/trigger', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'garage_open' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✓ Garage door command sent!');
        } else {
            alert('✗ Failed to send garage command: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        alert('✗ Error: ' + error.message);
    }
}


// ==================== Patrol Mode Functions ====================

// Initialize patrol controls
function initPatrolControls() {
    // Speed slider update
    const speedSlider = document.getElementById('patrol-speed');
    const speedValue = document.getElementById('patrol-speed-value');
    
    if (speedSlider && speedValue) {
        speedSlider.addEventListener('input', function() {
            speedValue.textContent = this.value;
        });
    }
}

// Update patrol status display
async function updatePatrolStatus() {
    try {
        const response = await fetch('/api/pantilt/patrol/status');
        const status = await response.json();
        
        if (status.error) {
            console.error('Patrol status error:', status.error);
            return;
        }
        
        // Update status badge
        const statusElement = document.getElementById('patrol-status');
        const startBtn = document.getElementById('patrol-start-btn');
        const stopBtn = document.getElementById('patrol-stop-btn');
        
        if (status.active) {
            statusElement.textContent = status.interrupted ? 'Interrupted' : 'Active';
            statusElement.className = 'badge ' + (status.interrupted ? 'badge-person' : 'badge-car');
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            statusElement.textContent = 'Inactive';
            statusElement.className = 'badge badge-unknown';
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
        
        // Update position count
        document.getElementById('patrol-position-count').textContent = status.position_count || 0;
        
    } catch (error) {
        console.error('Error updating patrol status:', error);
    }
}

// Load and display patrol positions
async function loadPatrolPositions() {
    try {
        const response = await fetch('/api/pantilt/patrol/positions');
        const data = await response.json();
        
        if (data.error) {
            console.error('Error loading patrol positions:', data.error);
            return;
        }
        
        const positionsList = document.getElementById('patrol-positions-list');
        
        if (!data.positions || data.positions.length === 0) {
            positionsList.innerHTML = `
                <p style="color: var(--gray-600); text-align: center; padding: 20px; font-size: 0.9em;">
                    No positions saved. Use Pan-Tilt controls to move camera, then click "Save Position".
                </p>
            `;
            return;
        }
        
        // Build positions list
        let html = '';
        data.positions.forEach((pos, index) => {
            html += `
                <div style="background: white; padding: 12px; border-radius: 8px; border: 1px solid var(--gray-200); margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>Position ${pos.id}</strong>
                            <div style="font-size: 0.9em; color: var(--gray-600);">
                                Pan: ${pos.pan}°, Tilt: ${pos.tilt}°, Dwell: ${pos.dwell_time}s
                            </div>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-secondary" onclick="editPatrolPosition(${pos.id}, ${pos.dwell_time})" style="padding: 4px 8px; font-size: 0.8em;">
                                ✏ Edit
                            </button>
                            <button class="btn btn-danger" onclick="deletePatrolPosition(${pos.id})" style="padding: 4px 8px; font-size: 0.8em;">
                                🗑 Delete
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        positionsList.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading patrol positions:', error);
    }
}

// Save current position as patrol waypoint
async function savePatrolPosition() {
    try {
        const dwellTime = parseInt(document.getElementById('patrol-dwell-time').value) || 10;
        
        if (dwellTime < 5 || dwellTime > 60) {
            alert('Dwell time must be between 5 and 60 seconds');
            return;
        }
        
        const response = await fetch('/api/pantilt/patrol/positions/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dwell_time: dwellTime })
        });
        
        const result = await response.json();
        
        if (result.success) {
            await loadPatrolPositions();
            await updatePatrolStatus();
            
            // Show success message
            const pos = result.position;
            alert(`✓ Position saved!\nPan: ${pos.pan}°, Tilt: ${pos.tilt}°, Dwell: ${pos.dwell_time}s`);
        } else {
            alert('✗ Failed to save position: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error saving patrol position:', error);
        alert('✗ Error: ' + error.message);
    }
}

// Delete a patrol position
async function deletePatrolPosition(positionId) {
    if (!confirm(`Delete position ${positionId}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/pantilt/patrol/positions/${positionId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            await loadPatrolPositions();
            await updatePatrolStatus();
        } else {
            alert('✗ Failed to delete position: ' + (result.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error deleting patrol position:', error);
        alert('✗ Error: ' + error.message);
    }
}

// Edit patrol position dwell time
async function editPatrolPosition(positionId, currentDwellTime) {
    const newDwellTime = prompt(`Edit dwell time for position ${positionId}:`, currentDwellTime);
    
    if (newDwellTime === null) return; // Cancelled
    
    const dwellTime = parseInt(newDwellTime);
    if (isNaN(dwellTime) || dwellTime < 5 || dwellTime > 60) {
        alert('Dwell time must be a number between 5 and 60 seconds');
        return;
    }
    
    try {
        const response = await fetch(`/api/pantilt/patrol/positions/${positionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dwell_time: dwellTime })
        });
        
        const result = await response.json();
        
        if (result.success) {
            await loadPatrolPositions();
        } else {
            alert('✗ Failed to update position: ' + (result.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error updating patrol position:', error);
        alert('✗ Error: ' + error.message);
    }
}

// Start patrol mode
async function startPatrol() {
    try {
        const speed = parseInt(document.getElementById('patrol-speed').value) || 5;
        
        const response = await fetch('/api/pantilt/patrol/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ speed: speed })
        });
        
        const result = await response.json();
        
        if (result.success) {
            await updatePatrolStatus();
            alert(`✓ Patrol started at speed ${speed}!`);
        } else {
            alert('✗ Failed to start patrol: ' + (result.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error starting patrol:', error);
        alert('✗ Error: ' + error.message);
    }
}

// Stop patrol mode
async function stopPatrol() {
    try {
        const response = await fetch('/api/pantilt/patrol/stop', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            await updatePatrolStatus();
            alert('✓ Patrol stopped!');
        } else {
            alert('✗ Failed to stop patrol: ' + (result.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error stopping patrol:', error);
        alert('✗ Error: ' + error.message);
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSecurity);
} else {
    initSecurity();
}

