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
                window.removeEventListener('beforeunload', handle_before_unload);
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
                window.removeEventListener('beforeunload', handle_before_unload);
                window.location.href = '/';
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

function handle_before_unload() {
    fetch('/delete_session', {
        method: 'POST'
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    });
}

window.addEventListener('beforeunload', handle_before_unload);


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

// Convert touch event on mobile to mouse event
canvas.addEventListener("touchstart", startDrawing);
canvas.addEventListener("touchmove", draw);
canvas.addEventListener("touchend", finishDrawing);

// Event listeners to track mouse movements
canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', finishDrawing);
canvas.addEventListener('mouseout', finishDrawing);

function startDrawing(e) {
    e.preventDefault();
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

    let x, y;
    if (e.type === 'touchstart') {
        let rect = e.target.getBoundingClientRect();
        x = e.targetTouches[0].pageX - rect.left;
        y = e.targetTouches[0].pageY - rect.top;
    } else if (e.type === 'mousedown') {
        x = e.offsetX;
        y = e.offsetY;
    }

    [lastX, lastY] = [x, y];
    // Reset current drawing
    current_drawing_points = [];
}

function draw(e) {
    e.preventDefault();
    if (!is_drawing) return; // Stop the function if not drawing

    if (e.type === 'touchmove' && is_touch_out(e)) {
        console.log('in')
        finishDrawing(e);
        return;
    }
    console.log('out')

    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    let x, y;
    if (e.type === 'touchmove') {
        let rect = e.target.getBoundingClientRect();
        x = e.targetTouches[0].pageX - rect.left;
        y = e.targetTouches[0].pageY - rect.top;
    } else if (e.type === 'mousemove') {
        x = e.offsetX;
        y = e.offsetY;
    }
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.closePath();

    current_drawing_points.push([lastX, lastY]);

    [lastX, lastY] = [x, y];
}

function finishDrawing(e) {
    // If right mouse button was released, do nothing
    if (e.button === 2) {
        return;
    }

    is_drawing = false;
    upload_drawing();
}

// simulate mouseout event for touchevents
function is_touch_out(e) {
    let item = e.changedTouches.item(0);
    if (e.target === null || item === null) return false;
    let rect = e.target.getBoundingClientRect();
    let is_in = rect.right > item.clientX &&
        rect.left < item.clientX &&
        rect.top < item.clientY &&
        rect.bottom > item.clientY;
    return !is_in;
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
            window.removeEventListener('beforeunload', handle_before_unload);
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

// Sets the canvas to the same size as the slideshow
function resize_canvas() {
    const img = slideshow.slides;
    const canvas = document.getElementById('cv1');

    const container = document.getElementById('canvas_container');
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    const imgAspectRatio = img.naturalWidth / img.naturalHeight;
    const containerAspectRatio = containerWidth / containerHeight;

    let drawWidth, drawHeight;

    if (imgAspectRatio > containerAspectRatio) {
        drawWidth = containerWidth;
        drawHeight = containerWidth / imgAspectRatio;
    } else {
        drawWidth = containerHeight * imgAspectRatio;
        drawHeight = containerHeight;
    }

    canvas.width = drawWidth;
    canvas.height = drawHeight;
}

slideshow.slides.addEventListener('load', resize_canvas);
window.addEventListener('resize', resize_canvas);

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
            window.removeEventListener('beforeunload', handle_before_unload);
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
    let startTime = Date.now();
    let timer = document.getElementById('timer');
    let intervalId = setInterval(function () {
        let elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        timer.textContent = `Time Elapsed: ${elapsed} seconds`;
    }, 100);

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
            window.removeEventListener('beforeunload', handle_before_unload);
            window.location.href = response.url;
        }
        if (!response.ok) {
            console.error('Failed to get mask.');
        }

        clearInterval(intervalId);
        let totalDuration = ((Date.now() - startTime) / 1000).toFixed(2);
        timer.textContent = `Time Elapsed: ${totalDuration} seconds`;

        return response.blob();
    }).then(blob => {
        // Create a URL for the blob
        let imageUrl = URL.createObjectURL(blob);

        // Display processed image
        mask.src = imageUrl;
    }).catch(error => {
        clearInterval(intervalId);
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
            window.removeEventListener('beforeunload', handle_before_unload);
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
    let startTime = Date.now();
    let timer = document.getElementById('timer');
    let intervalId = setInterval(function () {
        let elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        timer.textContent = `Time Elapsed: ${elapsed} seconds`;
    }, 100);

    fetch('inpaint', {
        method: 'POST'
    }).then((response) => {
        if (response.redirected) {
            window.removeEventListener('beforeunload', handle_before_unload);
            window.location.href = response.url;
        }

        clearInterval(intervalId);
        let totalDuration = ((Date.now() - startTime) / 1000).toFixed(2);
        timer.textContent = `Time Elapsed: ${totalDuration} seconds`;
    }).catch(error => {
        clearInterval(intervalId);
        console.error('Error inpainting:', error);
    });
}

