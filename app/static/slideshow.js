class Slideshow {

    constructor(num_frames, fps) {
        this.num_frames = num_frames;
        this.fps = fps;
        this._slides = document.getElementById('slideshow');
        this.value = document.getElementById('frames_display');
        this.is_paused = true;
        this._current_frame = 0;
        this.playbutton = document.getElementById('play_button');

        // Set first frame
        this.update_slideshow();

        // Add options to datalist, which adds tick marks below the input slider
        this.input = document.getElementById('slider');

        // Remove tick marks if there are too many
        let num_options = (this.num_frames > 200) ? 0 : this.num_frames;

        let datalist = document.getElementById("markers");
        for (let i = 0; i < num_options; i++) {
            let option = document.createElement("option");
            option.value = i;
            datalist.appendChild(option);
        }

        // Called when slider is being moved
        this.input.addEventListener("change", (event) => {
            this._current_frame = parseInt(event.target.value);
            this.update_slideshow();
            this.reset_interaction();
        });

        this.playbutton.addEventListener('click', this.play_or_pause.bind(this));

        setInterval(this.play_slideshow.bind(this), 1/this.fps* 1000);

    }

    reset_interaction() {
            // Reset interactions in manager
        fetch('/reset_interaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }).catch(error => {
            console.error('Error:', error);
        });
    }

    set_seekbar_value(n) {
        this.input.value = n;
    }

    play_or_pause() {
        this.is_paused = !this.is_paused;
    }

    /*
        Simulate video playing by changing the image
     */
    update_slideshow() {
        throw new Error('Not implemented');
    }

    play_slideshow() {
        if (!this.is_paused) {
            this._current_frame++;
            if (this._current_frame > this.num_frames - 1) {
                this._current_frame = 0;
            }
            this.set_seekbar_value(this._current_frame);
            this.update_slideshow();
        }
    }

    get current_frame() {
        return this._current_frame;
    }

    get slides() {
        return this._slides;
    }

}
