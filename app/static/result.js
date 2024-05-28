class ResultSlideshow extends Slideshow {
    constructor(num_frames, fps) {
        super(num_frames, fps);
    }

    update_slideshow() {
        fetch('/check', {
            method: 'POST'
        }).then(response => {
            if(response.redirected){
            window.location.href = response.url;
            }
        })
        // Set frame
        this._slides.src = '/frame/' + this._current_frame
        this.value.textContent = 'Frame: ' + (this._current_frame + 1) + '/' + this.num_frames;
    }
}

let num_frames = document.currentScript.getAttribute('num_frames'),
    fps = document.currentScript.getAttribute('fps');

let slideshow = new ResultSlideshow(num_frames, fps);


function again() {
    fetch('again', {
        method: 'POST'
    }).then((response)=>{
        if(response.redirected){
            window.location.href = response.url;
        }
    }).catch(error => {
        console.error('Error:', error);
    });
}