/********************************************************
Copyright 2016 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*********************************************************/

var Util = require('../util/util.js');

function Player() {
	// Create an audio graph.
	window.AudioContext = window.AudioContext || window.webkitAudioContext;
	context = new AudioContext();

	var analyser = context.createAnalyser();
	//analyser.fftSize = 2048 * 2 * 2
	// analyser.fftSize = (window.isMobile)? 2048 : 8192;
	//analyser.fftSize = (window.isMobile)?1024 : 2048;
	//analyser.fftSize = 16384;
	analyser.fftSize = 1024;
	analyser.smoothingTimeConstant = 0.5;

	// Create a mix.
	var mix = context.createGain();

	// Create a bandpass filter.
	var bandpass = context.createBiquadFilter();
	bandpass.Q.value = 10;
	bandpass.type = 'bandpass';

	var filterGain = context.createGain();
	filterGain.gain.value = 1;

	// Connect audio processing graph
	mix.connect(analyser);
	analyser.connect(filterGain);
	filterGain.connect(context.destination);

	this.context = context;
	this.mix = mix;
	// this.bandpass = bandpass;
	this.filterGain = filterGain;
	this.analyser = analyser;

	this.buffers = {};

	// Connect an empty source node to the mix.
	Util.loadTrackSrc(this.context, 'bin/snd/empty.mp3', function(buffer) {
		var source = this.createSource_(buffer, true);
		source.loop = true;
		source.start(0);
	}.bind(this));
	
}

Player.prototype.playSrc = function(src) {
	// Stop all of the mic stuff.
	this.filterGain.gain.value = 1;
	if (this.input) {
		this.input.disconnect();
		this.input = null;
		return;
	}

	if (this.buffers[src]) {
		$('#loadingSound').fadeIn(100).delay(1000).fadeOut(500);
		this.playHelper_(src);
		return;
	}

	$('#loadingSound').fadeIn(100);
	Util.loadTrackSrc(this.context, src, function(buffer) {
		this.buffers[src] = buffer;
		this.playHelper_(src);
		$('#loadingSound').delay(500).fadeOut(500);
	}.bind(this));
};

Player.prototype.playUserAudio = function(src) {
  // Stop all of the mic stuff.
  this.filterGain.gain.value = 1;
  if (this.input) {
    this.input.disconnect();
    this.input = null;
    return;
  }
  this.buffers['user'] = src.buffer;
  this.playHelper_('user');
};

Player.prototype.playHelper_ = function(src) {
	var buffer = this.buffers[src];
	this.source = this.createSource_(buffer, true);
	this.source.start(0);

	if (!this.loop) {
		this.playTimer = setTimeout(function() {
			this.stop();
	}.bind(this), buffer.duration * 2000);
	}
};

Player.prototype.live = function() {
	// The AudioContext may be in a suspended state prior to the page receiving a user
	// gesture. If it is, resume it.
	if (this.context.state === 'suspended') {
		this.context.resume();
	}
	if(window.isIOS){
		window.parent.postMessage('error2','*');
		console.log("cant use mic on ios");
	}else{
		if (this.input) {
			this.input.disconnect();
			this.input = null;
			return;
		}

		var self = this;
    navigator.mediaDevices.getUserMedia({audio: true}).then(function(stream) {
      self.onStream_(stream);
		}).catch(function() {
      self.onStreamError(this);
		});

		this.filterGain.gain.value = 0;
	}
};

Player.prototype.onStream_ = function(stream) {
	var input = this.context.createMediaStreamSource(stream);
	input.connect(this.mix);
	this.input = input;
	this.stream = stream;
	console.log(this.mix);
};

Player.prototype.onStreamError_ = function(e) {
	// TODO: Error handling.
};

Player.prototype.setLoop = function(loop) {
	this.loop = loop;
};

Player.prototype.createSource_ = function(buffer, loop) {
	var source = this.context.createBufferSource();
	source.buffer = buffer;
	source.loop = loop;
	source.connect(this.mix);
	return source;
};

Player.prototype.setMicrophoneInput = function() {
	// TODO: Implement me!
};

Player.prototype.stop = function() {
	if (this.source) {
		this.source.stop(0);
		this.source = null;
		clearTimeout(this.playTimer);
		this.playTimer = null;

	}
	if (this.input) {
		this.input.disconnect();
		this.input = null;
		return;
	}
};

Player.prototype.getAnalyserNode = function() {
	return this.analyser;
};

Player.prototype.setBandpassFrequency = function(freq) {
	if (freq == null) {
		console.log('Removing bandpass filter');
		// Remove the effect of the bandpass filter completely, connecting the mix to the analyser directly.
		this.mix.disconnect();
		this.mix.connect(this.analyser);
	} else {
		// console.log('Setting bandpass frequency to %d Hz', freq);
		// Only set the frequency if it's specified, otherwise use the old one.
		this.bandpass.frequency.value = freq;
		this.mix.disconnect();
		this.mix.connect(this.bandpass);
		// bandpass is connected to filterGain.
		this.filterGain.connect(this.analyser);
	}
};

Player.prototype.playTone = function(freq) {
	if (!this.osc) {
		this.osc = this.context.createOscillator();
		this.osc.connect(this.mix);
		this.osc.type = 'sine';
		this.osc.start(0);
	}
	this.osc.frequency.value = freq;
	this.filterGain.gain.value = .2;

	
};

Player.prototype.stopTone = function() {
	this.osc.stop(0);
	this.osc = null;
};

module.exports = Player;
