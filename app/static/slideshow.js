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

function set_slideshow_to_current_frame() {
    img.src = 'frame/' + current_frame;
}

function play_slideshow() {
    if (!is_paused) {
        current_frame++;
        if (current_frame > num_frames - 1) {
            current_frame = 0;
        }
        set_seekbar_value(current_frame);
        update_num_frame_diplay();
        set_slideshow_to_current_frame()
    }
}
setInterval(function () {
    play_slideshow();
}, 1/fps * 1000);


/*
    Setting up the seekbar
 */

// Add options to datalist, which adds tick marks below the input slider
var input = document.getElementById("seekbar"),
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
    console.log(event.target.value);
    update_num_frame_diplay();
    set_slideshow_to_current_frame();
});