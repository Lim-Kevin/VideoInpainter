// If a form is uploaded, then automatically submit the form and disable the buttons
let file_input = document.getElementById("video_file");
let upload_label = document.getElementById("upload_label");
let form = document.getElementById("upload_form");
let drop_area = document.getElementById('drop_area');


// Resetting uploaded video on page loading
window.onload = function () {
    let form = document.getElementById("upload_form");
    form.reset();
}

/*
    Setting up drop area for files
 */

document.addEventListener("DOMContentLoaded", function () {
    file_input.addEventListener("change", function () {
        if (file_input.files.length > 0) {
            upload_label.textContent = "Uploading...";
            form.submit();
            file_input.disabled = true;
        }
    });

    // Click to open file dialog
    drop_area.addEventListener("click", () => {
        file_input.click();
    });

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        drop_area.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        drop_area.addEventListener(eventName, () => drop_area.classList.add('highlight'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        drop_area.addEventListener(eventName, () => drop_area.classList.remove('highlight'), false);
    });

    // Handle dropped files
    drop_area.addEventListener('drop', handleDrop, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleDrop(e) {
        let dt = e.dataTransfer;
        let files = dt.files;
        handleFiles(files)
    }

    function handleFiles(files) {
        if (files.length > 0) {
            file_input.files = files;
            file_input.dispatchEvent(new Event('change'))
        }
    }
});

/*
    Setting up alerts
 */
let alert_message = document.getElementById('alert_message');
let alert_div = document.getElementById('alert');
let alert_close_button = document.getElementById('close_button');
let alert_timeout;

function show_alert(message) {
    alert_message.innerText = message;
    alert_div.classList.add('show');
    alert_div.classList.add('visible')

    if (alert_timeout) {
        clearTimeout(alert_timeout);
    }

    alert_timeout = setTimeout(() => {
        close_alert();
    }, 7000);
}

function close_alert() {
    alert_div.classList.remove('visible')

    if (alert_timeout) {
        clearTimeout(alert_timeout);
    }
    // Delay hiding the alert box to allow for the fade-out transition
    setTimeout(() => {
        alert_div.classList.remove('show');
    }, 500); // Match this to the CSS transition duration
}

alert_close_button.addEventListener("click", close_alert);