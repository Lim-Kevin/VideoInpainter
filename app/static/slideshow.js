// Play/Pause button
var is_paused = true;

function play_or_pause() {
    is_paused = !is_paused;
}

/*
    Simulate video playing by changing the image
 */
var num_frames = document.currentScript.getAttribute('num_frames'),
    fps = document.currentScript.getAttribute('fps'),
    img = document.getElementById('slideshow'),
    current_frame = 0;

// Set slideshow to the current frame and overlay mask if it exists
function update_slideshow() {
    // Set frame
    img.src = '/frame/' + current_frame;

    try {
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height)
    } catch (e) {
        // No canvas
    }

    // Set composed mask
    fetch('/mask/' + current_frame).then(response => {
        if (response.status === 204) {
            mask_image.style.display = 'none'
        } else {
            return response.blob()
        }
    }).then(blob => {
        if (blob) {
            mask_image.style.display = 'block'
            // Create a URL for the blob
            let imageUrl = URL.createObjectURL(blob);
            // Display processed image
            mask_image.src = imageUrl;
        }
    }).catch(error => {
        // No mask overlay
    });
}

function play_slideshow() {
    if (!is_paused) {
        current_frame++;
        if (current_frame > num_frames - 1) {
            current_frame = 0;
        }
        set_seekbar_value(current_frame);
        update_num_frame_diplay();
        update_slideshow()
    }
}

setInterval(function () {
    play_slideshow();
}, 1 / fps * 1000);


/*
    Setting up the seekbar
 */

// Add options to datalist, which adds tick marks below the input slider
var input = document.getElementById("slider"),
    datalist = document.getElementById("markers"),
    num_options = num_frames;
// Hide markers if there are too many steps
if (num_options > 200) {
    num_options = 0;
}
for (var i = 0; i < num_options; i++) {
    var option = document.createElement("option");
    option.value = i;
    datalist.appendChild(option);
}


var value = document.getElementById("frames_display");

// Displays the number of the current frame shown
function update_num_frame_diplay() {
    value.textContent = "Frame: " + (current_frame + 1) + "/" + num_frames;
}

function set_seekbar_value(n) {
    input.value = n;
}

input.addEventListener("change", (event) => {
    current_frame = parseInt(event.target.value);
    update_num_frame_diplay();
    update_slideshow();
});