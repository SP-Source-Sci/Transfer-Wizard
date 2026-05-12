const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress');
const progressText = document.getElementById('progress-text');
const uploadStatus = document.getElementById('upload-status');
const statusList = document.getElementById('status-list');
const speedText = document.getElementById('speed-text');
const timeLeftText = document.getElementById('time-left-text');

function handleFiles(files) {
    if (files.length > 0) {
        progressContainer.classList.remove('hidden');
        uploadStatus.classList.add('hidden');
        statusList.innerHTML = ''; // Clear previous statuses
        uploadFiles(files);
    }
}

function updateProgress(percentage) {
    progressBar.style.width = `${percentage}%`;
    progressText.textContent = `${percentage.toFixed(0)}%`;
}

async function uploadFiles(files) {
    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const xhr = new XMLHttpRequest();
            let startTime = null;
            let lastLoaded = 0;
            let lastTime = 0;

            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percentage = (event.loaded / event.total) * 100;
                    updateProgress(percentage);

                    const currentTime = new Date().getTime();
                    if (!startTime) {
                        startTime = currentTime;
                        lastTime = startTime;
                        lastLoaded = 0;
                    }

                    const timeElapsed = currentTime - lastTime;
                    const bytesUploaded = event.loaded - lastLoaded;

                    if (timeElapsed > 100) { // Update speed every 100 milliseconds
                        const speed = bytesUploaded / (timeElapsed / 1000); // bytes per second
                        speedText.textContent = `Speed: ${formatBytes(speed)}/s`;

                        const bytesRemaining = event.total - event.loaded;
                        const timeLeftSeconds = bytesRemaining / speed;

                        if (isFinite(timeLeftSeconds) && speed > 0) {
                            timeLeftText.textContent = `Time Left: ${formatTime(timeLeftSeconds)}`;
                        } else {
                            timeLeftText.textContent = `Time Left: Calculating...`;
                        }

                        lastTime = currentTime;
                        lastLoaded = event.loaded;
                    }
                }
            });

            xhr.onload = async () => {
                speedText.textContent = '';
                timeLeftText.textContent = '';
                try {
                    const response = JSON.parse(xhr.responseText);
                    const listItem = document.createElement('li');
                    listItem.textContent = `${file.name}: ${response.message || (xhr.status >= 200 && xhr.status < 300 ? 'Uploaded successfully' : 'Failed to upload')}`;
                    statusList.appendChild(listItem);

                    if (xhr.status < 200 || xhr.status >= 300) {
                        console.error(`Error uploading ${file.name}:`, response.error || xhr.statusText);
                    }
                } catch (error) {
                    console.error(`Error processing response for ${file.name}:`, error);
                    const listItem = document.createElement('li');
                    listItem.textContent = `${file.name}: Error processing response`;
                    statusList.appendChild(listItem);
                } finally {
                    if (statusList.children.length === files.length) {
                        progressContainer.classList.add('hidden');
                        uploadStatus.classList.remove('hidden');
                    }
                }
            };

            xhr.onerror = () => {
                speedText.textContent = '';
                timeLeftText.textContent = '';
                console.error(`Error uploading ${file.name}: Network error`);
                const listItem = document.createElement('li');
                listItem.textContent = `${file.name}: Network error`;
                statusList.appendChild(listItem);
                if (statusList.children.length === files.length) {
                    progressContainer.classList.add('hidden');
                    uploadStatus.classList.remove('hidden');
                }
            };

            xhr.open('POST', '/upload'); // Replace '/upload' with your actual server-side upload endpoint
            xhr.send(formData);

        } catch (error) {
            speedText.textContent = '';
            timeLeftText.textContent = '';
            console.error(`Error setting up upload for ${file.name}:`, error);
            const listItem = document.createElement('li');
            listItem.textContent = `${file.name}: Error - ${error.message}`;
            statusList.appendChild(listItem);
            if (statusList.children.length === files.length) {
                progressContainer.classList.add('hidden');
                uploadStatus.classList.remove('hidden');
            }
        }
    }
}

// Helper function to format bytes into human-readable format
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Helper function to format seconds into human-readable time
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    const parts = [];
    if (hours > 0) {
        parts.push(`${hours} hr`);
    }
    if (minutes > 0) {
        parts.push(`${minutes} min`);
    }
    if (remainingSeconds >= 0 || parts.length === 0) {
        parts.push(`${remainingSeconds} sec`);
    }
    return parts.join(' ');
}

// Drag and drop functionality (remains the same)
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    handleFiles(files);
});

// File input change event (remains the same)
fileInput.addEventListener('change', () => {
    handleFiles(fileInput.files);
    fileInput.value = '';
});