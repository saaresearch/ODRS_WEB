let inputFile = document.querySelector('.input-file input[type=file]');

inputFile.addEventListener('change', function() {
  let file = this.files[0];
  let inputParent = this.closest('.input-file');
  let inputText = inputParent.querySelector('.input-file-text');
  if (file) {
    inputText.textContent = file.name;
    const errorMessage = document.getElementById('training-button');
    errorMessage.style.background = '#51AB32';
    errorMessage.textContent = "Training";
  }
});

function validateForm() {
  const fileInput = document.querySelector('input[type="file"]');
  if (fileInput.value === '') {
    const errorMessage = document.getElementById('training-button');
    errorMessage.style.background = 'red';
    errorMessage.textContent = "Please choose a file";
    return false; // Prevent form submission
  }
  else {
    let loader = document.getElementById("loader");
    loader.style.display = "block";
  }
}

let iconsId = ['gpu-icon', 'dataset-path-icon', 'classes-path-icon', 'speed-icon', 'accuracy-icon'];
let popupId = ['gpu-popup', 'dataset-path-popup', 'classes-path-popup', 'speed-popup', 'accuracy-popup'];

iconsId.forEach(function(iconId, index) {
  const icon = document.getElementById(iconId);
  const popup = document.getElementById(popupId[index]);

  document.addEventListener('click', function(event) {
      if (event.target.matches('#' + iconId)) {
        popup.style.display = 'block';
      } else {
        popup.style.display = 'none';
      }
    });
});
