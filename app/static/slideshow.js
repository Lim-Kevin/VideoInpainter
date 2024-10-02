class Slideshow {
    constructor(num_frames, fps, video_id) {
        this.num_frames = num_frames;
        this.fps = fps;
        this.video_id = video_id;
        this._slides = document.getElementById('slideshow');
        this.value = document.getElementById('frames_display');
        this.is_paused = true;
        this._current_frame = 0;
        this.playbutton = document.getElementById('play_button');
        this._frames = [];
        this._masks = [];

        // Add options to datalist, which adds tick marks below the input slider
        this._slider = document.getElementById('slider');

        // Remove tick marks if there are too many
        let num_ticks = (this.num_frames > 200) ? 0 : this.num_frames;

        let markers = document.getElementById("markers");
        for (let i = 0; i < num_ticks; i++) {
            let tick = document.createElement('div');
            tick.classList.add('tick');
            tick.setAttribute('value', i);
            markers.appendChild(tick);
        }

        // Called when slider is being moved
        this._slider.addEventListener("change", (event) => {
            this._current_frame = parseInt(event.target.value);
            this.update_slideshow();
            this.reset_interaction();
        });

        this.playbutton.addEventListener('click', this.play_or_pause.bind(this));

        setInterval(this.play_slideshow.bind(this), 1 / this.fps * 1000);

    }

    load_masks() {
        let promise = Promise.resolve();  // Start with a resolved promise

        for (let i = 0; i < num_frames; i++) {
            promise = promise
                .then(() => fetch('/mask/' + String(this.video_id) + '/' + String(i)))
                .then(response => response.blob())
                .then(blob => {
                    const blob_url = URL.createObjectURL(blob);
                    this._masks[i] = blob_url;
                });
        }

        // Return the final promise that resolves when all fetches are complete
        return promise;
    }

    set_current_mask() {
        let promise = Promise.resolve();  // Start with a resolved promise

        promise = promise
            .then(() => fetch('/mask/'  + String(this.video_id) + '/' + String(this._current_frame)))
            .then(response => response.blob())
            .then(blob => {
                const blob_url = URL.createObjectURL(blob);
                this._masks[this._current_frame] = blob_url;
            });

        // Return the final promise that resolves when all fetches are complete
        return promise;
    }

    preload_frames() {
        let promise = Promise.resolve();  // Start with a resolved promise

        for (let i = 0; i < num_frames; i++) {
            promise = promise
                .then(() => fetch('/frame/' + String(this.video_id) + '/' + String(i)))
                .then(response => response.blob())
                .then(blob => {
                    const blob_url = URL.createObjectURL(blob);
                    this._frames.push(blob_url);
                });
        }

        // Return the final promise that resolves when all fetches are complete
        return promise;
    }

    async initialize() {
        await this.preload_frames();
        await this.load_masks();
        // Set first frame
        this.update_slideshow();
    }

    reset_interaction() {
        // Reset interactions in manager
        fetch('/reset_interaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({video_id: this.video_id})
        }).catch(error => {
            console.error('Error:', error);
        });
    }

    set_seekbar_value(n) {
        this._slider.value = n;
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

    highlight_tick() {
        let tick = document.querySelector(`.tick[value='${this.current_frame}']`);
        tick.classList.add('highlight_tick');
    }

    remove_tick_highlight() {
        let tick = document.querySelector(`.tick[value='${this.current_frame}']`);
        tick.classList.remove('highlight_tick');
    }

    remove_all_highlights() {
        let highlighted_ticks = document.querySelectorAll('.highlight_tick');
        highlighted_ticks.forEach(t => t.classList.remove('highlight_tick'));
    }

    get current_frame() {
        return this._current_frame;
    }

    get slides() {
        return this._slides;
    }

    get slider() {
        return this._slider;
    }

    get frames() {
        return this._frames;
    }

    get masks() {
        return this._masks;
    }

}
