
(() => {
  "use strict";

  const input = document.getElementById("message-input");
  const form = document.getElementById("chat-form");
  const voiceButton = document.getElementById("voice-button");
  const languageSelect = document.getElementById("voice-language");
  const voiceStatus = document.getElementById("voice-status");

  if (!input || !form || !voiceButton || !languageSelect || !voiceStatus) {
    console.error("Voice search: Required chatbot elements were not found.");
    return;
  }

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    voiceButton.disabled = true;
    voiceButton.title = "Voice search is not supported by this browser";
    voiceStatus.textContent =
      "Voice search is not supported here. Please use text search.";
    return;
  }

  const recognition = new SpeechRecognition();

  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  let isListening = false;
  let finalTranscript = "";
  let submitAfterRecognition = false;
  let recognitionError = false;

  function setListening(listening) {
    isListening = listening;

    voiceButton.classList.toggle("is-listening", listening);
    voiceButton.setAttribute("aria-pressed", String(listening));
    voiceButton.setAttribute(
      "aria-label",
      listening ? "Stop voice search" : "Start voice search"
    );

    voiceButton.title = listening
      ? "Stop voice search"
      : "Search using your voice";
  }

  function stopRecognition() {
    submitAfterRecognition = false;

    if (isListening) {
      recognition.stop();
    }
  }

  voiceButton.addEventListener("click", () => {
    if (isListening) {
      stopRecognition();
      voiceStatus.textContent = "Stopping voice search...";
      return;
    }

    if (!window.isSecureContext) {
      voiceStatus.textContent =
        "Voice search needs HTTPS or localhost. Open the secure site and try again.";
      return;
    }

    finalTranscript = "";
    submitAfterRecognition = true;
    recognitionError = false;

    recognition.lang = languageSelect.value;
    recognition.interimResults = true;

    try {
      recognition.start();
      setListening(true);
      voiceStatus.textContent = "Listening... Speak now 🎙️";
    } catch (error) {
      submitAfterRecognition = false;
      setListening(false);
      voiceStatus.textContent =
        "Could not start the microphone. Please try again.";
      console.error("Voice recognition start error:", error);
    }
  });

  recognition.addEventListener("result", (event) => {
    let interimTranscript = "";

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;

      if (event.results[i].isFinal) {
        finalTranscript += transcript;
      } else {
        interimTranscript += transcript;
      }
    }

    const currentTranscript =
      (finalTranscript + " " + interimTranscript).trim();

    if (currentTranscript) {
      input.value = currentTranscript.slice(0, 180);
      input.dispatchEvent(new Event("input", { bubbles: true }));
      voiceStatus.textContent = interimTranscript
        ? "Recognizing: " + interimTranscript
        : "Speech recognized. Preparing your search...";
    }
  });

  recognition.addEventListener("error", (event) => {
    recognitionError = true;
    submitAfterRecognition = false;

    const messages = {
      "not-allowed": "Microphone permission denied. Allow microphone access in your browser.",
      "service-not-allowed": "Speech recognition is blocked by the browser.",
      "no-speech": "No speech detected. Tap the microphone and try again.",
      "audio-capture": "No microphone found. Check your microphone connection.",
      "network": "Voice recognition needs a working network connection.",
      "language-not-supported": "This voice language is not supported by your browser.",
      "aborted": "Voice search was cancelled."
    };

    voiceStatus.textContent =
      messages[event.error] || "Voice search failed. Please try again.";

    setListening(false);
  });

  recognition.addEventListener("end", () => {
    setListening(false);

    if (recognitionError) {
      recognitionError = false;
      return;
    }

    const shouldSubmit = submitAfterRecognition;
    submitAfterRecognition = false;

    if (shouldSubmit && input.value.trim()) {
      voiceStatus.textContent = "Searching for your music...";
      // Uses the existing chatbot form handler.
      if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
      } else {
        form.dispatchEvent(
          new Event("submit", { bubbles: true, cancelable: true })
        );
      }
    } else if (input.value.trim()) {
      voiceStatus.textContent = "Voice input ready. Press Send to search.";
    } else {
      voiceStatus.textContent = "Tap the microphone to try again.";
    }
  });

  // Let users edit recognized words or type a new search normally.
  input.addEventListener("input", () => {
    if (!isListening && input.value.trim()) {
      voiceStatus.textContent = "Search text ready.";
    }
  });

  languageSelect.addEventListener("change", () => {
    if (!isListening) {
      const selected =
        languageSelect.options[languageSelect.selectedIndex].text;
      voiceStatus.textContent = "Voice language: " + selected;
    }
  });

  // Do not let Enter or manual form submission leave recognition running.
  form.addEventListener("submit", () => {
    if (isListening) {
      stopRecognition();
    }
  });
})();
