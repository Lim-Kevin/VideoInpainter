var video = document.getElementById("vd1"),
    timeline = document.getElementsByClassName('timeline')[0],
    timelineProgress = document.getElementsByClassName('timeline_progress')[0],
    drag = document.getElementsByClassName('timeline_drag')[0];

// on interaction with video controls
video.onplay = function () {
    TweenMax.ticker.addEventListener('tick', vidUpdate);
};
video.onpause = function () {
    TweenMax.ticker.removeEventListener('tick', vidUpdate);
};
video.onended = function () {
    TweenMax.ticker.removeEventListener('tick', vidUpdate);
    TweenMax.set(drag, {
        x: (timeline.offsetWidth - drag.offsetWidth) // Make drag snap to end of timeline
    });
    TweenMax.set(timelineProgress, {
        scaleX: (1)
    });
};

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

var width, height

function resize_canvas(element) {
    width = element.offsetWidth;
    height = element.offsetHeight;
    canvas.width = width;
    canvas.height = height;
}

function play_or_pause() {
    if (video.paused) {
        video.play();
    } else {
        video.pause();
    }
}

// Sync the timeline with the video duration
function vidUpdate() {
    TweenMax.set(timelineProgress, {
        scaleX: (video.currentTime / video.duration)
    });
    TweenMax.set(drag, {
        x: (video.currentTime / video.duration * timeline.offsetWidth)
    });
}

// Make the timeline draggable
Draggable.create(drag, {
    type: 'x',
    trigger: timeline,
    bounds: timeline,
    onPress: function (e) {
        video.currentTime = this.x / this.maxX * video.duration;
        TweenMax.set(this.target, {
            x: this.pointerX - timeline.getBoundingClientRect().left
        });
        this.update();
        var progress = this.x / timeline.offsetWidth;
        TweenMax.set(timelineProgress, {
            scaleX: progress
        });
    },
    onDrag: function () {
        video.currentTime = this.x / this.maxX * video.duration;
        var progress = this.x / timeline.offsetWidth;
        TweenMax.set(timelineProgress, {
            scaleX: progress
        });
    },
    onRelease: function (e) {
        e.preventDefault();
    }
});

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