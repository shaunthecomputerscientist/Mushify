document.querySelector("#errorAlert button.close").addEventListener("click", function() {
    document.querySelector("#errorAlert").classList.remove("show");
  });
  
  // Close the success alert when the button is clicked
  document.querySelector("#successAlert button.close").addEventListener("click", function() {
    document.querySelector("#successAlert").classList.remove("show");
  });

  const audioElements = {};

  document.querySelectorAll('.play-song').forEach(function (button) {
      button.addEventListener('click', function () {
          const playlistId = this.parentElement.querySelector('select').id;
          const selectedSong = this.parentElement.querySelector('select').value;

          if (selectedSong) {
              // Check if the audio element already exists
              if (!audioElements[playlistId]) {
                  // Create a new audio element
                  const audioElement = new Audio();
                  audioElement.src = `data:audio/mpeg;base64,${selectedSongData}`; // Set the src to the Base64-encoded data URI
                  audioElement.play();
                  audioElements[playlistId] = audioElement;
                  this.innerText = 'Pause'; // Update button text to "Pause"
              } else {
                  // Toggle between play and pause
                  if (audioElements[playlistId].paused) {
                      audioElements[playlistId].play();
                      this.innerText = 'Pause';
                  } else {
                      audioElements[playlistId].pause();
                      this.innerText = 'Play';
                  }
              }
          }
      });
  });


  document.addEventListener("DOMContentLoaded", function () {
    const checkbox = document.getElementById("exampleCheck1");
    const submitButton = document.getElementById("submitButton");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password1");
    const password2Input = document.getElementById("password2")

    checkbox.addEventListener("change", function () {
        submitButton.disabled = !checkbox.checked;
    });
    });
document.addEventListener("DOMContentLoaded", function () {
const emailInput = document.getElementById("email");
const emailError = document.getElementById("emailError");
const passwordInput = document.getElementById("password1");
const password2Input = document.getElementById("password2")
const passwordError = document.getElementById("passwordError");

emailInput.addEventListener("input", function () {
const email = emailInput.value;
if (!validateEmail(email)) {
  emailError.textContent = "Invalid email format";
  emailError.style.display = "block";
} else {
  emailError.style.display = "none";
}
});

passwordInput.addEventListener("input", function () {
const password = passwordInput.value;
if (password.length < 8) {
  passwordError.textContent = "Password must be at least 8 characters long";
  passwordError.style.display = "block";
} else {
  passwordError.style.display = "none";
}
});

function handlepasswordInput(){
const password1Input = document.getElementById("password1");
const password2Input = document.getElementById("password2");
const passwordError = document.getElementById("passwordError");

const password1 = password1Input.value;
const password2 = password2Input.value;

if (password1 !== password2) {
    passwordError.textContent = "Passwords do not match";
    passwordError.style.display = "block";
} else {
    passwordError.style.display = "none";
}
}





function validateEmail(email) {
// You can implement a more robust email validation regex
return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
});