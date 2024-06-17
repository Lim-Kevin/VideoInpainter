class ResultSlideshow extends Slideshow {
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
        fetch('/frame/' + this._current_frame).then(response => {
            if (!response.ok) {
                window.removeEventListener('beforeunload', handle_before_unload);
                window.location.href = '/'
            }
            this._slides.src = '/frame/' + this._current_frame
        });
        this.value.textContent = 'Frame: ' + (this._current_frame + 1) + '/' + this.num_frames;
    }
}

let num_frames = document.currentScript.getAttribute('num_frames'),
    fps = document.currentScript.getAttribute('fps');

let slideshow = new ResultSlideshow(num_frames, fps);

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

function again() {
    fetch('again', {
        method: 'POST'
    }).then((response) => {
        if (response.redirected) {
            window.removeEventListener('beforeunload', handle_before_unload);
            window.location.href = response.url;
        }
    }).catch(error => {
        console.error('Error:', error);
    });
}

async function save_video() {
    try {
        // Make a POST request to the Flask API endpoint
        const response = await fetch('/save_video', {
            method: 'POST'
        });
        if (response.redirected) {
            window.removeEventListener('beforeunload', handle_before_unload);
            window.location.href = response.url;
        }
        if (response.ok) {
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
        } else {
            // Handle the error if the response is not okay
            console.error('Failed to download video');
        }
    } catch (error) {
        // Handle any other errors
        console.error('Error:', error);
    }
}