class ChordAnalyzer {
    constructor(chords, realCore) {
        this.chords = chords;
        this.realCore = realCore;
        this.player = document.getElementById('player');
        this.conveyor = document.getElementById('conveyor');
        this.coreDisplay = document.getElementById('core-display');
        this.menu = document.getElementById('chord-menu');
        
        this.SLOT_WIDTH = 250;
        this.currentIdx = -1;
        this.currentMode = 'guess';
        this.hasChecked = false;

        // State management
        this.userGuesses = realCore.map(() => null);
        this.correctStatus = realCore.map(() => false);
        this.activeGuessIdx = -1;

        this.init();
    }

    init() {
        this.bindGlobalEvents();
        this.setMode('guess');
        if (this.player) this.renderFrame();
    }

    bindGlobalEvents() {
        // Global click to close menu
        document.addEventListener('click', () => {
            if (this.menu) this.menu.classList.add('d-none');
        });
        // Prevent closing when clicking inside the menu
        if (this.menu) {
            this.menu.addEventListener('click', (e) => e.stopPropagation());
        }
    }

    setMode(mode) {
        this.currentMode = mode;
        const btnShow = document.getElementById('btn-show');
        const btnGuess = document.getElementById('btn-guess');
        const checkBtn = document.getElementById('check-btn');

        if (btnShow) btnShow.className = mode === 'show' ? 'btn btn-sm btn-primary btn-check-mode' : 'btn btn-sm btn-outline-primary btn-check-mode';
        if (btnGuess) btnGuess.className = mode === 'guess' ? 'btn btn-sm btn-primary btn-check-mode' : 'btn btn-sm btn-outline-primary btn-check-mode';
        if (checkBtn) checkBtn.classList.toggle('d-none', mode === 'show');
        
        this.renderCore();
        this.updateVisuals(this.currentIdx);
    }

    renderCore() {
        if (!this.coreDisplay) return;
        this.coreDisplay.innerHTML = ''; // Clear for fresh render
        
        this.realCore.forEach((chord, i) => {
            const span = document.createElement('span');
            
            if (this.currentMode === 'show') {
                span.innerText = chord;
                span.style.color = '#0d6efd';
                span.style.pointerEvents = 'none';
            } else {
                span.innerText = this.userGuesses[i] || '?';
                
                if (this.correctStatus[i]) {
                    span.className = 'correct';
                } else if (this.userGuesses[i] !== null && this.hasChecked) {
                    span.className = (this.userGuesses[i] === this.realCore[i]) ? 'correct' : 'wrong';
                } else if (this.userGuesses[i] !== null) {
                    span.className = 'guess-filled';
                } else {
                    span.className = 'guess-slot';
                }

                // Explicit click binding using addEventListener
                span.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (!this.correctStatus[i]) this.openMenu(e, i);
                });
            }
            
            this.coreDisplay.appendChild(span);

            if (i < this.realCore.length - 1) {
                const arrow = document.createElement('small');
                arrow.innerHTML = ' &rarr; ';
                arrow.className = 'mx-2';
                arrow.style.color = '#444';
                arrow.style.pointerEvents = 'none';
                this.coreDisplay.appendChild(arrow);
            }
        });
    }

    openMenu(e, idx) {
        this.activeGuessIdx = idx;
        this.menu.classList.remove('d-none');
        // Smart positioning
        const menuWidth = 250;
        let leftPos = e.pageX;
        if (leftPos + menuWidth > window.innerWidth) leftPos = window.innerWidth - menuWidth - 20;
        
        this.menu.style.top = `${e.pageY + 10}px`;
        this.menu.style.left = `${leftPos}px`;
    }

    selectChord(chord) {
        this.userGuesses[this.activeGuessIdx] = chord;
        this.hasChecked = false; // Reset "check" state so user can fix mistakes
        this.menu.classList.add('d-none');
        this.renderCore();
    }

    checkAnswers() {
        this.hasChecked = true;
        this.userGuesses.forEach((guess, i) => {
            if (guess === this.realCore[i]) {
                this.correctStatus[i] = true;
            }
        });
        this.renderCore();
        this.updateVisuals(this.currentIdx);
    }

    updateVisuals(idx) {
        if (idx === -1 || !this.conveyor) return;
        this.conveyor.style.transform = `translateX(-${idx * this.SLOT_WIDTH}px)`;
        
        const units = document.querySelectorAll('.chord-unit');
        units.forEach((el, i) => {
            el.style.left = `${i * this.SLOT_WIDTH}px`;
            const realChord = this.chords[i].chord;
            
            if (this.currentMode === 'guess') {
                const coreIdx = this.realCore.indexOf(realChord);
                el.innerText = (coreIdx !== -1 && this.correctStatus[coreIdx]) ? realChord : '?';
            } else {
                el.innerText = realChord;
            }

            if (i === idx) {
                el.style.fontSize = "4.5rem"; el.style.color = "#0d6efd"; el.style.opacity = "1";
            } else {
                el.style.fontSize = "1.5rem"; el.style.color = "#555"; el.style.opacity = "0.2";
            }
        });
    }

    renderFrame() {
        const time = this.player.currentTime;
        const idx = this.chords.findIndex(c => time >= c.start && time < (c.end || 999));
        if (idx !== -1 && idx !== this.currentIdx) {
            this.currentIdx = idx;
            this.updateVisuals(idx);
        }
        requestAnimationFrame(() => this.renderFrame());
    }
}
