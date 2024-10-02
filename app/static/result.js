class ResultSlideshow extends Slideshow {
    constructor(num_frames, fps, video_id) {
        super(num_frames, fps, video_id);
        this.remove_all_highlights();
    }

    update_slideshow() {
        // Set frame
        this._slides.src = this._frames[this._current_frame];

        this.value.textContent = 'Frame: ' + (this._current_frame + 1) + '/' + this.num_frames;
    }
}

let num_frames = document.currentScript.getAttribute('num_frames'),
    fps = document.currentScript.getAttribute('fps'),
    video_id = document.currentScript.getAttribute('video_id');

let slideshow = new ResultSlideshow(num_frames, fps, video_id);
slideshow.initialize();

// If the window is smaller than 600px (on smartphone) then remove the markers
function check_window_size() {
    if (window.innerWidth < 600) {
        slideshow.slider.removeAttribute('list');
    }
}
check_window_size();

function again() {
    fetch('/again', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            video_id: video_id
        })
    }).then((response) => {
        if (!response.ok) {
            window.location.href = '/';
        }
        if (response.redirected) {
            window.location.href = response.url
        }
    }).catch(error => {
        console.error('Error:', error);
    });
}

async function save_video() {
    try {
        // Make a POST request to the Flask API endpoint
        const response = await fetch('/save_video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_id: video_id
            })
        });
        if (!response.ok) {
            window.location.href = '/';
            return;
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        // Create a temporary anchor element
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'inpainted.mp4';

        // Append the anchor to the body
        document.body.appendChild(a);

        // Programmatically click the anchor to trigger the download
        a.click();

        // Remove the anchor element from the DOM
        document.body.removeChild(a);
        // Revoke the object URL to free up memory
        window.URL.revokeObjectURL(url);
    } catch (error) {
        // Handle any other errors
        console.error('Error:', error);
    }
}