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
            upload_label.classList.add("disabled");
            form.submit();
            file_input.disabled = true;
        }
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