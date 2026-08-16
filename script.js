const WORD_LENGTH = 5;
const MAX_ATTEMPTS = 6;

let allowedGuesses = new Set();
let possibleAnswers = [];
let secretWord = "";

let currentRow = 0;
let currentGuess = "";
let gameOver = false;

const board = document.getElementById("board");
const keyboard = document.getElementById("keyboard");
const message = document.getElementById("message");

const keyboardStatus = {};
const statusPriority = {
  gray: 1,
  yellow: 2,
  green: 3
};

const keyboardRows = [
  ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
  ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
  ["enter", "z", "x", "c", "v", "b", "n", "m", "backspace"]
];


async function loadWordList(filename) {
  const response = await fetch(filename);

  if (!response.ok) {
    throw new Error(`Could not load ${filename}`);
  }

  const text = await response.text();

  return text
    .split(/\r?\n/)
    .map(word => word.trim().toLowerCase())
    .filter(word =>
      word.length === WORD_LENGTH &&
      /^[a-z]+$/.test(word)
    );
}


async function initializeGame() {
  try {
    const allowed = await loadWordList("allowed_guesses.txt");
    const answers = await loadWordList("possible_answers.txt");

    allowedGuesses = new Set(allowed);
    possibleAnswers = answers.filter(word => allowedGuesses.has(word));

    if (possibleAnswers.length === 0) {
      throw new Error(
        "No possible answers are also present in allowed_guesses.txt."
      );
    }

    secretWord =
      possibleAnswers[
        Math.floor(Math.random() * possibleAnswers.length)
      ];

    createBoard();
    createKeyboard();

    // Uncomment this while debugging if you want to see the answer:
    // console.log("Secret word:", secretWord);

  } catch (error) {
    showMessage(
      "Could not load the word lists. Run the game through a local web server."
    );
    console.error(error);
  }
}


function createBoard() {
  board.innerHTML = "";

  for (let row = 0; row < MAX_ATTEMPTS; row++) {
    for (let col = 0; col < WORD_LENGTH; col++) {
      const tile = document.createElement("div");
      tile.classList.add("tile");
      tile.dataset.row = row;
      tile.dataset.col = col;
      board.appendChild(tile);
    }
  }
}


function createKeyboard() {
  keyboard.innerHTML = "";

  for (const row of keyboardRows) {
    const rowElement = document.createElement("div");
    rowElement.classList.add("keyboard-row");

    for (const keyValue of row) {
      const button = document.createElement("button");
      button.classList.add("key");
      button.dataset.key = keyValue;

      if (keyValue === "enter") {
        button.textContent = "Enter";
        button.classList.add("wide");
      } else if (keyValue === "backspace") {
        button.textContent = "⌫";
        button.classList.add("wide");
      } else {
        button.textContent = keyValue;
      }

      button.addEventListener("click", () => handleKey(keyValue));
      rowElement.appendChild(button);
    }

    keyboard.appendChild(rowElement);
  }
}


function handleKey(key) {
  if (gameOver || !secretWord) {
    return;
  }

  if (key === "enter") {
    submitGuess();
    return;
  }

  if (key === "backspace") {
    removeLetter();
    return;
  }

  if (/^[a-z]$/.test(key)) {
    addLetter(key);
  }
}


function addLetter(letter) {
  if (currentGuess.length >= WORD_LENGTH) {
    return;
  }

  currentGuess += letter;
  drawCurrentGuess();
  clearMessage();
}


function removeLetter() {
  if (currentGuess.length === 0) {
    return;
  }

  currentGuess = currentGuess.slice(0, -1);
  drawCurrentGuess();
  clearMessage();
}


function drawCurrentGuess() {
  for (let col = 0; col < WORD_LENGTH; col++) {
    const tile = getTile(currentRow, col);
    const letter = currentGuess[col] || "";

    tile.textContent = letter;
    tile.classList.toggle("filled", letter !== "");
  }
}


function submitGuess() {
  if (currentGuess.length !== WORD_LENGTH) {
    showMessage("Not enough letters.");
    return;
  }

  if (!allowedGuesses.has(currentGuess)) {
    showMessage("Not in word list.");
    return;
  }

  const result = evaluateGuess(secretWord, currentGuess);

  revealGuess(currentGuess, result);
  updateKeyboard(currentGuess, result);

  if (currentGuess === secretWord) {
    gameOver = true;
    showMessage(
      currentRow === 0
        ? "Amazing! You got it on the first try!"
        : `You got it in ${currentRow + 1} tries!`
    );
    return;
  }

  currentRow++;

  if (currentRow === MAX_ATTEMPTS) {
    gameOver = true;
    showMessage(`The word was ${secretWord.toUpperCase()}.`);
    return;
  }

  currentGuess = "";
  clearMessage();
}


function evaluateGuess(secret, guess) {
  const result = Array(WORD_LENGTH).fill("gray");
  const remainingLetters = secret.split("");

  // Pass 1: greens
  for (let i = 0; i < WORD_LENGTH; i++) {
    if (guess[i] === secret[i]) {
      result[i] = "green";
      remainingLetters[i] = null;
    }
  }

  // Pass 2: yellows
  for (let i = 0; i < WORD_LENGTH; i++) {
    if (result[i] === "green") {
      continue;
    }

    const matchIndex = remainingLetters.indexOf(guess[i]);

    if (matchIndex !== -1) {
      result[i] = "yellow";
      remainingLetters[matchIndex] = null;
    }
  }

  return result;
}


function revealGuess(guess, result) {
  for (let col = 0; col < WORD_LENGTH; col++) {
    const tile = getTile(currentRow, col);

    tile.textContent = guess[col];
    tile.classList.remove("filled");
    tile.classList.add(result[col]);
  }
}


function updateKeyboard(guess, result) {
  for (let i = 0; i < WORD_LENGTH; i++) {
    const letter = guess[i];
    const newStatus = result[i];
    const oldStatus = keyboardStatus[letter];

    if (
      !oldStatus ||
      statusPriority[newStatus] > statusPriority[oldStatus]
    ) {
      keyboardStatus[letter] = newStatus;

      const key = document.querySelector(
        `.key[data-key="${letter}"]`
      );

      key.classList.remove("gray", "yellow", "green");
      key.classList.add(newStatus);
    }
  }
}


function getTile(row, col) {
  return document.querySelector(
    `.tile[data-row="${row}"][data-col="${col}"]`
  );
}


function showMessage(text) {
  message.textContent = text;
}


function clearMessage() {
  message.textContent = "";
}


document.addEventListener("keydown", event => {
  if (gameOver || !secretWord) {
    return;
  }

  const key = event.key.toLowerCase();

  if (key === "enter") {
    handleKey("enter");
  } else if (key === "backspace") {
    handleKey("backspace");
  } else if (/^[a-z]$/.test(key)) {
    handleKey(key);
  }
});


initializeGame();
