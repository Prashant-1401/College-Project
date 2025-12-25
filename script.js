// DOM Elements
const emailForm = document.getElementById('emailForm');
const senderEmail = document.getElementById('senderEmail');
const recipientEmail = document.getElementById('recipientEmail');
const subject = document.getElementById('subject');
const toneOption = document.getElementById('toneOption'); // Added in previous step
const emailBody = document.getElementById('emailBody');
const charCount = document.getElementById('charCount');
const polishBtn = document.getElementById('polishBtn');
const polishedOutput = document.getElementById('polishedOutput');
const metricsPanel = document.getElementById('metricsPanel');
const toneValue = document.getElementById('toneValue');
const readabilityValue = document.getElementById('readabilityValue');
const actionButtons = document.getElementById('actionButtons');
const copyBtn = document.getElementById('copyBtn');
const sendBtn = document.getElementById('sendBtn');
const toast = document.getElementById('toast');
// NEW: Theme Toggle Elements
const themeToggle = document.getElementById('themeToggle');
const moonIcon = document.getElementById('moonIcon');
const sunIcon = document.getElementById('sunIcon');


let polishedText = '';
let polishedSubject = '';

// --- Theme Management Logic ---

// Function to set the theme based on the mode string ('light' or 'dark')
function setTheme(mode) {
    const isLight = mode === 'light';
    
    // 1. Update body class
    document.body.classList.toggle('light-mode', isLight);
    
    // 2. Update toggle button icon visibility
    moonIcon.classList.toggle('hidden', isLight);
    sunIcon.classList.toggle('hidden', !isLight);
    
    // 3. Save preference
    localStorage.setItem('theme', mode);
}

// Function to handle the toggle button click
function toggleTheme() {
    const currentMode = document.body.classList.contains('light-mode') ? 'light' : 'dark';
    const newMode = currentMode === 'dark' ? 'light' : 'dark';
    setTheme(newMode);
}

// Initial theme load on page load
function loadTheme() {
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme) {
        // Use saved theme
        setTheme(savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
        // Use system preference if no theme is saved
        setTheme('light');
    } else {
        // Default to dark mode
        setTheme('dark');
    }
}

// Attach event listener to the toggle button
themeToggle.addEventListener('click', toggleTheme);

// Load the theme when the script runs
loadTheme();

// --- End Theme Management Logic ---


// Character count update
emailBody.addEventListener('input', () => {
    const count = emailBody.value.length;
    charCount.textContent = `${count} character${count !== 1 ? 's' : ''}`;
});

// Email validation
function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

// Sanitize input to prevent XSS
function sanitizeInput(input) {
    const div = document.createElement('div');
    div.textContent = input;
    return div.innerHTML;
}

// Show toast notification
function showToast(message, duration = 3000) {
    toast.textContent = message;
    toast.classList.remove('hidden');
    setTimeout(() => {
        toast.classList.add('hidden');
    }, duration);
}

// Toggle loading state
function setLoading(isLoading) {
    const btnText = polishBtn.querySelector('.btn-text');
    const loader = polishBtn.querySelector('.loader');

    if (isLoading) {
        btnText.textContent = 'Polishing...';
        loader.classList.remove('hidden');
        polishBtn.disabled = true;
    } else {
        btnText.textContent = 'Polish Email';
        loader.classList.add('hidden');
        polishBtn.disabled = false;
    }
}

// Polish email handler
polishBtn.addEventListener('click', async () => {
    // Validate inputs
    if (!isValidEmail(senderEmail.value)) {
        showToast('Please enter a valid sender email address');
        return;
    }

    if (!isValidEmail(recipientEmail.value)) {
        showToast('Please enter a valid recipient email address');
        return;
    }

    if (!subject.value.trim()) {
        showToast('Please enter a subject');
        return;
    }

    if (!emailBody.value.trim()) {
        showToast('Please enter an email body');
        return;
    }

    setLoading(true);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                subject: sanitizeInput(subject.value),
                body: sanitizeInput(emailBody.value),
                toneOption: toneOption.value 
            })
        });

        if (!response.ok) {
            throw new Error('Failed to analyze email');
        }

        const data = await response.json();

        // Update polished output
        polishedText = data.polishedBody;
        polishedSubject = data.polishedSubject;

        // Display the polished subject and body
        polishedOutput.innerHTML = `<strong>Subject:</strong> ${data.polishedSubject}<br><br>${data.polishedBody.replace(/\n/g, '<br>')}`;

        // Update metrics (using the tone returned from the backend)
        toneValue.textContent = data.tone || 'Professional';
        readabilityValue.textContent = data.readability || 'High';

        // Show metrics and action buttons
        metricsPanel.classList.remove('hidden');
        actionButtons.classList.remove('hidden');

        showToast('Email polished successfully!');

    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to polish email. Please try again.');
    } finally {
        setLoading(false);
    }
});

// Copy to clipboard
copyBtn.addEventListener('click', () => {
    const textToCopy = `Subject: ${polishedSubject}\n\n${polishedText}`;

    // Note: document.execCommand('copy') is sometimes necessary in iFrame environments 
    // where navigator.clipboard might be restricted, but we will use the modern API first.
    navigator.clipboard.writeText(textToCopy).then(() => {
        showToast('Copied to clipboard!');
    }).catch(err => {
        // Fallback for failed copy (e.g., if modern API fails in restrictive environments)
        const textarea = document.createElement('textarea');
        textarea.value = textToCopy;
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            showToast('Copied to clipboard! (Fallback)');
        } catch (execErr) {
            console.error('Failed to copy using fallback:', execErr);
            showToast('Failed to copy text. Please copy manually.');
        } finally {
            document.body.removeChild(textarea);
        }
    });
});

// Send email
sendBtn.addEventListener('click', async () => {
    if (!polishedText) {
        showToast('Please polish the email first');
        return;
    }

    // Disable send button
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';

    try {
        const response = await fetch('/api/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                from: sanitizeInput(senderEmail.value),
                to: sanitizeInput(recipientEmail.value),
                subject: polishedSubject,
                body: polishedText
            })
        });

        if (!response.ok) {
            throw new Error('Failed to send email');
        }

        const data = await response.json();

        showToast('Email sent successfully! ✓', 4000);

        // Reset form after successful send
        setTimeout(() => {
            emailForm.reset();
            polishedOutput.innerHTML = '<p class="placeholder-text">Your polished email will appear here...</p>';
            metricsPanel.classList.add('hidden');
            actionButtons.classList.add('hidden');
            charCount.textContent = '0 characters';
            polishedText = '';
            polishedSubject = '';
        }, 2000);

    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to send email. Please try again.');
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Confirm & Send';
    }
});

// Prevent form submission
emailForm.addEventListener('submit', (e) => {
    e.preventDefault();
});