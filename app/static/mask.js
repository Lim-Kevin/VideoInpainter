/*
    Setting up the canvas
 */
var canvas = document.getElementById("cv1"),
    ctx = canvas.getContext("2d"),
    mask_image = document.getElementById("mask");

var isDrawing = false;
var lastX = 0;
var lastY = 0;

// Event listeners to track mouse movements
canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', stopDrawing);
canvas.addEventListener('mouseout', stopDrawing);

function startDrawing(e) {
    isDrawing = true;
    [lastX, lastY] = [e.offsetX, e.offsetY];
}

function draw(e) {
    if (!isDrawing) return; // Stop the function if not drawing
    ctx.lineWidth = 5;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.strokeStyle = 'blue';
    ctx.lineWidth = 3;

    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(e.offsetX, e.offsetY);
    ctx.stroke();
    ctx.closePath();
    [lastX, lastY] = [e.offsetX, e.offsetY];
}

function stopDrawing() {
    isDrawing = false;
}

// Sets the canvas to the same size as a given element
function resize_canvas(element) {
    let width = element.offsetWidth;
    let height = element.offsetHeight;
    canvas.width = width;
    canvas.height = height;
}

// Resize the canvas so that mouse coordinates are right
window.onload = function () {
    resize_canvas(img)
}

// Saves the drawn mask
function save() {
    const imageData = canvas.toDataURL('image/png');
    fetch('/save_mask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            image_data: imageData,
            current_frame: current_frame
        }),
    }).then(response => {
        if (!response.ok) {
            console.error('Failed to save image.');
        }
        return response.blob()
    }).then(blob => {
        // Create a URL for the blob
        var imageUrl = URL.createObjectURL(blob);

        // Display processed image
        mask_image.src = imageUrl;
    }).catch(error => {
        console.error('Error saving image:', error);
    });
    clear_canvas()
}

var propagate_button = document.getElementById('propagate_button');
propagate_button.addEventListener('click', function(e) {
    e.preventDefault()
    let request = new XMLHttpRequest();
    request.open("GET", "/propagate", true);
    request.send();
})

function clear_canvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
}
