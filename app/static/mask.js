/*
    Setting up the canvas
 */
var canvas = document.getElementById("cv1"),
    ctx = canvas.getContext("2d");
    video = document.getElementById("vd1")

canvas.addEventListener("mousemove", function (e) {
    findxy('move', e)
}, false);
canvas.addEventListener("mousedown", function (e) {
    findxy('down', e)
}, false);
canvas.addEventListener("mouseup", function (e) {
    findxy('up', e)
}, false);
canvas.addEventListener("mouseout", function (e) {
    findxy('out', e)
}, false);

var width, height

// Sets the canvas to the same size as the video
function resize_canvas(element) {
    width = element.offsetWidth;
    height = element.offsetHeight;
    canvas.width = width;
    canvas.height = height;
}

// Configurations for the canvas
var flag = false,
    prevX = 0,
    currX = 0,
    prevY = 0,
    currY = 0,
    dot_flag = false,
    color = "blue",
    lineWidth = 5;

// Draw on canvas
function draw() {
    ctx.beginPath();
    ctx.moveTo(prevX, prevY);
    ctx.lineTo(currX, currY);
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.stroke();
    ctx.closePath();
}

function findxy(res, e) {
    if (res == 'down') {
        prevX = currX;
        prevY = currY;
        currX = e.clientX - canvas.offsetLeft;
        currY = e.clientY - canvas.offsetTop;

        flag = true;
        dot_flag = true;
        if (dot_flag) {
            ctx.beginPath();
            ctx.fillStyle = color;
            ctx.fillRect(currX, currY, 2, 2);
            ctx.closePath();
            dot_flag = false;
        }
    }
    if (res == 'up' || res == "out") {
        flag = false;
    }
    if (res == 'move') {
        if (flag) {
            prevX = currX;
            prevY = currY;
            currX = e.clientX - canvas.offsetLeft;
            currY = e.clientY - canvas.offsetTop;
            draw();
        }
    }
}

// Saves the drawn mask
function save() {
    const imageData = canvas.toDataURL('image/png');
    fetch('/save_image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({image_data: imageData}),
    }).then(response => {
        if (response.ok) {
            console.log('Image saved successfully.');
        } else {
            console.error('Failed to save image.');
        }
    }).catch(error => {
        console.error('Error saving image:', error);
    });
}

/*
    Setting up the seekbar and video controls
 */

// Add options to datalist, which adds tick marks below the input slider
var input = document.getElementById("seekbar")
    datalist = document.getElementById("markers")
var num_steps = input.max;
for (var i = 0; i <= num_steps; i++) {
    var option = document.createElement("option");
    option.value = i;
    datalist.appendChild(option);
}


var value = document.getElementById("frames_display");
// Displays the number of the current frame shown
function update_num_frame_diplay() {
    value.textContent = "Frame: " + input.value + "/" + input.max;
}
update_num_frame_diplay()
input.addEventListener("change", (event) => {
  value.textContent = "Frame: " + event.target.value + "/" + input.max;
});

// var isPlaying = false;
// function update_seekbar() {
//     input.value = video.currentTime / video.duration * input.max;
//     if (isPlaying) requestAnimationFrame(update_seekbar);
//     update_num_frame_diplay()
// }

function play_or_pause() {
    if (video.paused) {
        video.play();
    } else {
        video.pause();
    }
}