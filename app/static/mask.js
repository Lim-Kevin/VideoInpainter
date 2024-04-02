/*
    Setting up the canvas
 */
var canvas = document.getElementById("cv1"),
    ctx = canvas.getContext("2d");

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

// Sets the canvas to the same size as the video
function resize_canvas(element) {
    let width = element.offsetWidth;
    let height = element.offsetHeight;
    canvas.width = width;
    canvas.height = height;
}

var img = document.getElementById("slideshow")
window.onload = function () {
    resize_canvas(img)
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
        body: JSON.stringify({
            image_data: imageData,
            current_frame: current_frame
        }),
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

