/*
    Setting up the slideshow
 */

class MaskSlideshow extends Slideshow {
    constructor(num_frames, fps) {
        super(num_frames, fps);
    }

    update_slideshow() {
                // Reset interactions in manager
        fetch('/reset_interaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }).catch(error => {
            console.error('Error:', error);
        });

        // Set frame
        this._slides.src = '/frame/' + this._current_frame
        mask.src = '/mask/' + this._current_frame
        try {
            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height)
        } catch (e) {
            // No canvas
        }

        this.value.textContent = "Frame: " + (this._current_frame + 1) + "/" + this.num_frames;
    }
}

/*
    Setting up the canvas
 */
let canvas = document.getElementById("cv1"),
    ctx = canvas.getContext("2d"),
    mask = document.getElementById("mask");

let num_frames = document.currentScript.getAttribute('num_frames'),
    fps = document.currentScript.getAttribute('fps');

let slideshow = new MaskSlideshow(num_frames, fps);

let isDrawing = false,
    lastX = 0,
    lastY = 0;

// A list of points in the current drawing
let current_drawing_points = [];

// Event listeners to track mouse movements
canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', finishDrawing);
canvas.addEventListener('mouseout', stopDrawing);

function startDrawing(e) {
    isDrawing = true;
    [lastX, lastY] = [e.offsetX, e.offsetY];
    // Reset current drawing
    current_drawing_points = [];
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
    current_drawing_points.push([lastX, lastY]);

    [lastX, lastY] = [e.offsetX, e.offsetY];
}

function stopDrawing(e) {
    isDrawing = false;
}

function finishDrawing(e) {
    isDrawing = false;
    upload_drawing()
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
    resize_canvas(slideshow.slides);
}

function upload_drawing() {
    // Convert canvas image to base64 data URL
    let imageData = canvas.toDataURL('image/png');

    // Send the image data to the server
    fetch('/upload_canvas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ points: current_drawing_points, frame_num: slideshow.current_frame})
    }).then(response => {
        if (!response.ok) {
            console.error('Failed to get mask.');
        }
        return response.blob()
    }).then(blob => {
        // Create a URL for the blob
        let imageUrl = URL.createObjectURL(blob);

        // Display processed image
        mask.src = imageUrl;
    }).catch(error => {
        console.error('Error saving image:', error);
    });
}

// TODO: Make a function delete the mask on that frame, set it to reset button

