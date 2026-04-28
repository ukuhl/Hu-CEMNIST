"use strict";

class Paint {
    coord = {x: 0 , y: 0};
    painting = false;
    brushDefaultColor = "black";
    highlightBrushDefaultColor = "yellow";
    brushColor = "black";
    lineWidth = 20;
    lineCap = "square";
    opacity = 1;
    history = [];
    trackHistory = false;
    calledUndo = false;
    imgSrc = undefined;
    imgOriginal = undefined;
    callbackUpdate = undefined;
    pixelGridScaling = 20;
    imgSize = 28;

    init(imgSrc, callbackUpdate) {
        this.imgSrc = imgSrc;
        this.callbackUpdate = callbackUpdate;

        this.canvas = document.querySelector("#canvas");
        this.ctx = canvas.getContext("2d", { willReadFrequently: true });

        document.addEventListener("mousedown", this.onMouseDown.bind(this));
        document.addEventListener("mouseup", this.onMouseUp.bind(this));
        document.addEventListener("mousemove", this.onMouseMove.bind(this));
        document.getElementById("btnBrush").addEventListener("click", this.onClickBrush.bind(this));
        document.getElementById("btnEraser").addEventListener("click", this.onClickEraser.bind(this));
        document.getElementById("btnReset").addEventListener("click", this.onClickReset.bind(this));

        this.loadImage();

        this.trackHistory = true;
    }

    loadImage() {
        this.history = [];
        this.imgOriginal= new Image();
        this.imgOriginal.src = this.imgSrc;
        this.imgOriginal.onload = () => {
            this.canvas.width = this.imgOriginal.width;
            this.canvas.height = this.imgOriginal.height;
            this.ctx.drawImage(this.imgOriginal, 0, 0);
            this.imageOriginalData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height).data;
        }
    }

    reset() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    getData(callback) {
        this.canvas.toBlob((blob) => {
            callback(blob)
        });
    }

    getAllStrokes() {
        return this.history;
    }

    getDataAsBase64() {
        return this.canvas.toDataURL();
    }

    computePercentageOfChange() {
        var imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height).data;
        
        var numChanges = 0;
        for (let i = 0; i < imageData.length; i += 1) {
            if(this.imageOriginalData[i] != imageData[i]) {
                numChanges += 1;
            }
        }

        var score = numChanges / imageData.length;
        if(this.callbackUpdate != undefined) {
            this.callbackUpdate(score);
        }
        return score;
    }

    enableHighlightMode() {
        this.opacity = 0.08;
        this.brushDefaultColor = this.highlightBrushDefaultColor;
        this.brushColor = this.brushDefaultColor;
        this.trackHistory = true;

        document.getElementById("btnEraser").style.display = "none";
    }

    onClickBrush() {
        if(this.brushColor != this.brushDefaultColor) {
            document.getElementById("canvas").style.cursor = "url('static/brush.svg'),auto";
            this.brushColor = this.brushDefaultColor;
        }
    }

    onClickEraser() {
        if(this.brushColor != "white") {;
            document.getElementById("canvas").style.cursor = "url('static/eraser.svg'),auto";
            this.brushColor = "white";
        }
    }

    onClickReset() {
        if(this.trackHistory == false) {
            this.reset();
            this.loadImage();
        }
        else {
            if(this.history.length > 0) {
                if(this.calledUndo == false && this.history.length > 1) {
                    this.history.pop();
                }
                var prevState = this.history.pop();

                this.reset();
                this.imgOriginal = new Image();
                this.imgOriginal.src = prevState;
                this.imgOriginal.onload = () => {
                    var oldOpacity = this.opacity;
                    this.ctx.globalAlpha = 1.0
                    this.ctx.drawImage(this.imgOriginal, 0, 0);
                    this.ctx.globalAlpha = oldOpacity;
                }      
                this.calledUndo = true;          
            }
            else {
                this.reset();
                this.loadImage();
            }
        }
    }

    updatePosition(event) {
        this.coord.x = event.clientX - this.canvas.getBoundingClientRect().left;
        this.coord.y = event.clientY - this.canvas.getBoundingClientRect().top + 16;  // Cursor: 16x16
    }

    drawPixel() {
        this.ctx.beginPath();

        var x_ = this.coord.x;
        var y_ = this.coord.y;
        var x = (this.imgSize) * ((x_ - (Math.ceil(x_) % this.pixelGridScaling)) / this.imgSize);
        var y = (this.imgSize) * ((y_ - (Math.ceil(y_) % this.pixelGridScaling)) / this.imgSize);

        this.ctx.rect(x, y, this.pixelGridScaling, this.pixelGridScaling);
        this.ctx.fillStyle = this.brushColor;
        this.ctx.fill();
    }

    onMouseDown(event) {
        var rect = this.canvas.getBoundingClientRect();
        const isInRect = function (x, y) {
            return (rect.x <= x) && (rect.x + rect.width >= x) &&
                   (rect.y <= y) && (rect.y + rect.height >= y);
        }
        if(isInRect(event.clientX, event.clientY)) {
            this.painting = true;
            this.updatePosition(event);
            this.onMouseMove(event);  // Draw one pixel
        }
    }
    onMouseUp() {
        if(this.trackHistory == true && this.painting == true) {
            this.history.push(this.getDataAsBase64());
            this.calledUndo = false;
        }

        this.painting = false;
        this.computePercentageOfChange();
    }

    onMouseMove(event){
        if (!this.painting) {
            return;
        }

        this.drawPixel();
        this.updatePosition(event);
    }
}
