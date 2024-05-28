/*
    Setting up the slideshow
 */

class MaskSlideshow extends Slideshow {
    constructor(num_frames, fps) {
        super(num_frames, fps);
    }

    update_slideshow() {
        fetch('/check', {
            method: 'POST'
        }).then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            }
        })
        // Set frame
        this._slides.src = '/frame/' + this._current_frame

        // Set mask
        fetch('/mask/' + this._current_frame).then(response => {
            if (response.status === 304) {
                // Image not modified
                return;
            } else if (!response.ok) {
                console.error('Failed to get mask.');
            }
            return response.blob();
        }).then(blob => {
            // Create a URL for the blob
            let imageUrl = URL.createObjectURL(blob);

            // Display processed image
            mask.src = imageUrl;
        }).catch(error => {
            console.error('Error saving image:', error);
        });

        clear_canvas();
        this.value.textContent = 'Frame: ' + (this._current_frame + 1) + '/' + this.num_frames;
        undo_button.disabled = true;
    }
}

window.onbeforeunload = () => fetch('/delete_session').then(response => {
    if (response.redirected) {
        window.location.href = response.url;
    }
})

/*
    Setting up the canvas
 */
let undo_button = document.getElementById('undo_button')

let canvas = document.getElementById('cv1'),
    ctx = canvas.getContext('2d'),
    mask = document.getElementById('mask');

let num_frames = document.currentScript.getAttribute('num_frames'),
    fps = document.currentScript.getAttribute('fps');

let slideshow = new MaskSlideshow(num_frames, fps);

let is_drawing = false,

    is_pos_scribbles = true,
    lastX = 0,
    lastY = 0;

// A list of points in the current drawing
let current_drawing_points = [];

let change_button = document.getElementById('change_button');

function change_pos_neg() {
    is_pos_scribbles = !is_pos_scribbles;
}

change_button.onclick = change_pos_neg;

// Event listeners to track mouse movements
canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', finishDrawing);
canvas.addEventListener('mouseout', stopDrawing);

function startDrawing(e) {
    if (e.button === 2) {
        return;
    }
    is_drawing = true;
    if (is_pos_scribbles) {
        ctx.strokeStyle = 'green'
    } else {
        ctx.strokeStyle = 'blue';
    }
    ctx.lineWidth = 5;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.lineWidth = 3;

    [lastX, lastY] = [e.offsetX, e.offsetY];
    // Reset current drawing
    current_drawing_points = [];
}

function draw(e) {
    if (!is_drawing) return; // Stop the function if not drawing

    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(e.offsetX, e.offsetY);
    ctx.stroke();
    ctx.closePath();

    current_drawing_points.push([lastX, lastY]);

    [lastX, lastY] = [e.offsetX, e.offsetY];
}

function stopDrawing(e) {
    is_drawing = false;
}

function finishDrawing(e) {
    // If right mouse button was released, do nothing
    if (e.button === 2) {
        return;
    }

    is_drawing = false;
    upload_drawing();
}

function clear_canvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function reset_scribble() {
    fetch('/reset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            frame_num: slideshow.current_frame
        })
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
        if (!response.ok) {
            console.error('Failed to get mask.');
        }
        return response.blob();
    }).then(blob => {
        // Create a URL for the blob
        let imageUrl = URL.createObjectURL(blob);

        // Display processed image
        mask.src = imageUrl;
    }).catch(error => {
        console.error('Error saving image:', error);
    });
    clear_canvas()
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
    // Send the image data to the server
    fetch('/upload_canvas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            points: current_drawing_points,
            frame_num: slideshow.current_frame,
            k: is_pos_scribbles,
            height: canvas.height,
            width: canvas.width
        })
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }

        if (!response.ok) {
            console.error('Failed to get mask.');
        }
        return response.blob();
    }).then(blob => {
        // Create a URL for the blob
        let imageUrl = URL.createObjectURL(blob);

        // Display processed image
        mask.src = imageUrl;
    }).catch(error => {
        console.error('Error saving image:', error);
    });
    undo_button.disabled = false;
}

function propagate() {
    // Send the image data to the server
    fetch('/propagate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            frame_num: slideshow.current_frame
        })
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
        if (!response.ok) {
            console.error('Failed to get mask.');
        }
        return response.blob();
    }).then(blob => {
        // Create a URL for the blob
        let imageUrl = URL.createObjectURL(blob);

        // Display processed image
        mask.src = imageUrl;
    }).catch(error => {
        console.error('Error saving image:', error);
    });
    undo_button.disabled = true;
}


function undo() {
    // Send the image data to the server
    fetch('/undo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            frame_num: slideshow.current_frame
        })
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
        if (!response.ok) {
            console.error('Failed to get mask.');
        }
        return response.blob();
    }).then(blob => {
        // Create a URL for the blob
        let imageUrl = URL.createObjectURL(blob);

        // Display processed image
        mask.src = imageUrl;
    }).catch(error => {
        console.error('Error saving image:', error);
    });
    clear_canvas();
}

function inpaint() {
    fetch('inpaint', {
        method: 'POST'
    }).then((response) => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    }).catch(error => {
        console.error('Error inpainting:', error);
    });
}

