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
    slideshow = document.getElementById('slideshow'),
    value = document.getElementById('frames_display'),
    current_frame = 0;

// Set slideshow to the current frame and overlay mask if it exists
function update_slideshow() {
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
    slideshow.src = '/frame/' + current_frame
    mask.src = '/mask/'  + current_frame
    try {
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height)
    } catch (e) {
        // No canvas
    }

     value.textContent = "Frame: " + (current_frame + 1) + "/" + num_frames;
}

// Setting first frame
update_slideshow()

function play_slideshow() {
    if (!is_paused) {
        current_frame++;
        if (current_frame > num_frames - 1) {
            current_frame = 0;
        }
        set_seekbar_value(current_frame);
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

function set_seekbar_value(n) {
    input.value = n;
}

input.addEventListener("change", (event) => {
    current_frame = parseInt(event.target.value);
    update_slideshow();
});