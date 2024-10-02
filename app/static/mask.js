/*
    Setting up the slideshow
 */

class MaskSlideshow extends Slideshow {
    constructor(num_frames, fps, video_id) {
        super(num_frames, fps, video_id);
    }

    update_slideshow() {
        // Set frame
        this._slides.src = this._frames[this._current_frame];

        // Set mask
        mask.src = this._masks[this._current_frame];

        clear_canvas();
        this.value.textContent = 'Frame: ' + (this._current_frame + 1) + '/' + this.num_frames;
        undo_button.disabled = true;
    }
}

/*
    Setting up the canvas
 */
let undo_button = document.getElementById('undo_button'),
    propagation_button = document.getElementById('propagate_button'),
    reset_button = document.getElementById('reset_button'),
    inpaint_button = document.getElementById('inpaint_button');

let canvas = document.getElementById('cv1'),
    ctx = canvas.getContext('2d'),
    mask = document.getElementById('mask');

let num_frames = document.currentScript.getAttribute('num_frames'),
    fps = document.currentScript.getAttribute('fps'),
    video_id = document.currentScript.getAttribute('video_id');
let slideshow = new MaskSlideshow(num_frames, fps, video_id);
slideshow.initialize();

let is_drawing = false,
    is_pos_scribbles = true,
    lastX = 0,
    lastY = 0;

// A list of points in the current drawing
let current_drawing_points = [];

// If the window is smaller than 600px (on smartphone) then remove the markers
function check_window_size() {
    if (window.innerWidth < 600) {
        slideshow.slider.removeAttribute('list');
    }
}

check_window_size();

function change_pos_neg() {
    is_pos_scribbles = !is_pos_scribbles;
}

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
        finishDrawing(e);
        return;
    }

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
    if (e.button === 2 || !is_drawing) {
        return;
    }

    is_drawing = false;
    slideshow.highlight_tick();
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
            frame_num: slideshow.current_frame,
            video_id: video_id
        })
    }).then(response => {
        if (response.status === 410) {
            window.location.href = '/';
            return;
        }
        if (!response.ok) {
            console.error('Failed to get mask.');
            return;
        }
        return response.blob();
    }).then(blob => {
        if (blob) {
            // Create a URL for the blob
            let imageUrl = URL.createObjectURL(blob);

            // Display processed image
            mask.src = imageUrl;
            slideshow.set_current_mask();
        }
    }).catch(error => {
        console.error('Error saving image:', error);
    });
    slideshow.remove_tick_highlight();
    clear_canvas();
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

function disable_buttons() {
    inpaint_button.disabled = true;
    propagation_button.disabled = true;
    reset_button.disabled = true;
}

function enable_buttons() {
    inpaint_button.disabled = false;
    propagation_button.disabled = false;
    reset_button.disabled = false;
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
            width: canvas.width,
            video_id: video_id
        })
    }).then(response => {
        if (response.status === 410) {
            window.location.href = '/';
            return;
        }
        if (!response.ok) {
            console.error('Failed to get mask.');
            return;
        }
        return response.blob();
    }).then(blob => {
        // Create a URL for the blob
        let imageUrl = URL.createObjectURL(blob);

        // Display processed image
        mask.src = imageUrl;
        slideshow.set_current_mask();
    }).catch(error => {
        console.error('Error saving image:', error);
    });
    undo_button.disabled = false;
}

function propagate() {
    disable_buttons();
    undo_button.disabled = true;
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
            video_id: video_id
        })
    }).then(response => {
        if (response.status === 410) {
            window.location.href = '/';
            return;
        }

        clearInterval(intervalId);
        let totalDuration = ((Date.now() - startTime) / 1000).toFixed(2);
        timer.textContent = `Time Elapsed: ${totalDuration} seconds`;

        if (!response.ok) {
            console.error('Failed to get mask.');
            show_alert('First draw a mask to propagate');
            enable_buttons();
        }
    }).then(response => {
        slideshow.load_masks().then(r => slideshow.update_slideshow());
        enable_buttons();
    }).catch(error => {
        clearInterval(intervalId);
        console.error('Error saving image:', error);
    });
}


function undo() {
    // Send the image data to the server
    fetch('/undo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            frame_num: slideshow.current_frame,
            video_id: video_id
        })
    }).then(response => {
        if (response.status === 410) {
            window.location.href = '/';
            return;
        }
        if (!response.ok) {
            console.error('Failed to get mask.');
            return;
        }
        if (response.headers.get('error')) {
            // If mask is empty
            undo_button.disabled = true;
            slideshow.remove_tick_highlight();
        }
        return response.blob();
    }).then(blob => {
        // Create a URL for the blob
        let imageUrl = URL.createObjectURL(blob);
        // Display processed image
        mask.src = imageUrl;
        slideshow.set_current_mask();
    }).catch(error => {
        console.error('Error saving image:', error);
    });
    clear_canvas();
}

function inpaint() {
    disable_buttons();
    undo_button.disabled = true;

    let startTime = Date.now();
    let timer = document.getElementById('timer');
    let intervalId = setInterval(function () {
        let elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        timer.textContent = `Time Elapsed: ${elapsed} seconds`;
    }, 100);

    fetch('/inpaint', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            video_id: video_id
        })
    }).then((response) => {
        if (response.redirected) {
            window.location.href = response.url;
        }
        clearInterval(intervalId);
        let totalDuration = ((Date.now() - startTime) / 1000).toFixed(2);
        timer.textContent = `Time Elapsed: ${totalDuration} seconds`;

        if (response.status === 410) {
            window.location.href = '/';
            return;
        }
        if (!response.ok) {
            console.error('Failed to inpaint.');
            if (response.status === 404) {
                show_alert('No mask to inpaint');
            } else {
                show_alert('Error: Inpainting failed')
            }
        }
        enable_buttons();
        undo_button.disabled = false;
    }).catch(error => {
        clearInterval(intervalId);
        console.error('Error inpainting:', error);
    });
}

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