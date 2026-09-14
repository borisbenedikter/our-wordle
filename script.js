const WORD_LENGTH = 5;
const MAX_ATTEMPTS = 6;

let allowedGuesses = new Set();
let possibleAnswers = [];
let possibleAnswersSet = new Set();

let secretWord = "";
let challengeMode = false;

let currentRow = 0;
let currentGuess = "";
let gameOver = false;

let definitions = {};

const keyboardStatus = {};

const board = document.getElementById("board");
const keyboard = document.getElementById("keyboard");
const message = document.getElementById("message");
const subtitle = document.getElementById("subtitle");

const newGameButton = document.getElementById("new-game-button");
const createChallengeButton = document.getElementById("create-challenge-button");
const challengePanel = document.getElementById("challenge-panel");
const challengeNameInput = document.getElementById("challenge-name");
const challengeWordInput = document.getElementById("challenge-word");
const generateLinkButton = document.getElementById("generate-link-button");
const challengeError = document.getElementById("challenge-error");
const shareArea = document.getElementById("share-area");
const challengeLinkInput = document.getElementById("challenge-link");
const copyLinkButton = document.getElementById("copy-link-button");
const copyStatus = document.getElementById("copy-status");

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

const definitionCard =
  document.getElementById("definition-card");

const definitionWord =
  document.getElementById("definition-word");

const definitionContent =
  document.getElementById("definition-content");

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


async function loadDefinitions(filename) {
  const response = await fetch(filename);

  if (!response.ok) {
    throw new Error(`Could not load ${filename}`);
  }

  return await response.json();
}


async function initializeGame() {
  try {
    const allowed = await loadWordList("allowed_guesses.txt");
    const answers = await loadWordList("possible_answers.txt");

    try {
      definitions = await loadDefinitions("definitions.json");
    } catch (error) {
      console.warn(
        "Definitions could not be loaded. The game will continue without them.",
        error
      );

      definitions = {};
    }

    allowedGuesses = new Set(allowed);

    possibleAnswers = answers.filter(word => allowedGuesses.has(word));
    possibleAnswersSet = new Set(possibleAnswers);

    if (possibleAnswers.length === 0) {
      throw new Error(
        "No possible answers are also present in allowed_guesses.txt."
      );
    }

    createBoard();
    createKeyboard();

    const challengeWord = getChallengeWordFromURL();
    const challengeCreator = getChallengeCreatorFromURL();

    if (challengeWord && possibleAnswersSet.has(challengeWord)) {
      startGame(challengeWord, true, challengeCreator);
    } else {
      if (challengeWord) {
        removeChallengeFromURL();
      }
      startRandomGame();
    }

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



function startGame(word, isChallenge, creator = null) {
  secretWord = word;
  challengeMode = isChallenge;

  currentRow = 0;
  currentGuess = "";
  gameOver = false;

  for (const letter of Object.keys(keyboardStatus)) {
    delete keyboardStatus[letter];
  }

  resetBoardDisplay();
  resetKeyboardDisplay();
  clearMessage();
  closeChallengePanel();
  hideDefinition();

  if (challengeMode) {
    subtitle.textContent = creator
      ? `${creator} chose a word for you.`
      : "Someone chose a word for you.";
  } else {
    subtitle.textContent =
      "Guess the five-letter word in six tries.";
  }
  // Helpful during development:
  // console.log("Secret word:", secretWord);
}


function startRandomGame() {
  removeChallengeFromURL();

  const randomWord =
    possibleAnswers[
      Math.floor(Math.random() * possibleAnswers.length)
    ];

  startGame(randomWord, false);
}


function resetBoardDisplay() {
  const tiles = document.querySelectorAll(".tile");

  for (const tile of tiles) {
    tile.textContent = "";
    tile.className = "tile";
  }
}


function resetKeyboardDisplay() {
  const keys = document.querySelectorAll(".key");

  for (const key of keys) {
    key.classList.remove("gray", "yellow", "green");
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

    showDefinition(secretWord);

    return;
  }

  currentRow++;

  if (currentRow === MAX_ATTEMPTS) {
    gameOver = true;
    showMessage(`The word was ${secretWord.toUpperCase()}.`);
    showDefinition(secretWord);
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


function toggleChallengePanel() {
  const savedName =
    localStorage.getItem("challengeCreatorName");

  if (savedName) {
    challengeNameInput.value = savedName;
  }

  const isHidden = challengePanel.classList.contains("hidden");

  if (isHidden) {
    challengePanel.classList.remove("hidden");
    challengeWordInput.value = "";
    challengeError.textContent = "";
    shareArea.classList.add("hidden");
    copyStatus.textContent = "";
    challengeWordInput.focus();
  } else {
    closeChallengePanel();
  }
}


function closeChallengePanel() {
  challengePanel.classList.add("hidden");
}


function generateChallengeLink() {
  const name = challengeNameInput.value.trim();
  if (name) {
    localStorage.setItem("challengeCreatorName", name);
  }
  const word = challengeWordInput.value.trim().toLowerCase();

  challengeError.textContent = "";
  copyStatus.textContent = "";
  shareArea.classList.add("hidden");

  if (word.length !== WORD_LENGTH || !/^[a-z]+$/.test(word)) {
    challengeError.textContent = "Enter exactly five letters.";
    return;
  }

  if (!possibleAnswersSet.has(word)) {
    challengeError.textContent =
      "That word is not in the possible-answer list.";
    return;
  }

  const encodedWord = encodeChallengeWord(word);

  const url = new URL(window.location.href);
  url.search = "";
  url.hash = "";
  url.searchParams.set("c", encodedWord);
  if (name) {
    url.searchParams.set("from", name);
  }

  challengeLinkInput.value = url.toString();
  shareArea.classList.remove("hidden");
}


function encodeChallengeWord(word) {
  // This hides the word from casual inspection, but it is NOT encryption.
  // That is acceptable for a static GitHub Pages version.
  return btoa(word)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}


function decodeChallengeWord(encoded) {
  try {
    const base64 = encoded
      .replace(/-/g, "+")
      .replace(/_/g, "/");

    const padding = "=".repeat((4 - (base64.length % 4)) % 4);

    return atob(base64 + padding).toLowerCase();
  } catch {
    return null;
  }
}


function getChallengeWordFromURL() {
  const params = new URLSearchParams(window.location.search);
  const encoded = params.get("c");

  if (!encoded) {
    return null;
  }

  const decoded = decodeChallengeWord(encoded);

  if (
    !decoded ||
    decoded.length !== WORD_LENGTH ||
    !/^[a-z]+$/.test(decoded)
  ) {
    return null;
  }

  return decoded;
}


function getChallengeCreatorFromURL() {
  const params = new URLSearchParams(window.location.search);

  const creator = params.get("from");

  if (!creator) {
    return null;
  }

  return creator.trim();
}


function removeChallengeFromURL() {
  const url = new URL(window.location.href);
  url.searchParams.delete("c");
  url.searchParams.delete("from");
  history.replaceState({}, "", url.pathname + url.search + url.hash);
}


async function copyChallengeLink() {
  const text = challengeLinkInput.value;

  if (!text) {
    return;
  }

  try {
    await navigator.clipboard.writeText(text);
    copyStatus.textContent = "Copied!";
  } catch {
    challengeLinkInput.select();
    document.execCommand("copy");
    copyStatus.textContent = "Copied!";
  }
}

function showDefinition(word) {
  const entries = definitions[word];

  definitionWord.textContent = word.toUpperCase();
  definitionContent.innerHTML = "";

  if (!entries || entries.length === 0) {
    const unavailable = document.createElement("div");

    unavailable.classList.add("definition-unavailable");
    unavailable.textContent = "Definition unavailable.";

    definitionContent.appendChild(unavailable);
    definitionCard.classList.remove("hidden");

    return;
  }

  entries.forEach((entry, index) => {
    const sense = document.createElement("div");
    sense.classList.add("definition-sense");

    const pos = document.createElement("div");
    pos.classList.add("definition-pos");

    const number =
      entries.length > 1 ? `${index + 1}. ` : "";

    pos.textContent =
      `${number}${entry.partOfSpeech || ""}`;

    const definition = document.createElement("div");
    definition.classList.add("definition-text");
    definition.textContent = entry.definition;

    sense.appendChild(pos);
    sense.appendChild(definition);

    if (entry.example) {
      const example = document.createElement("div");
      example.classList.add("definition-example");
      example.textContent = `“${entry.example}”`;

      sense.appendChild(example);
    }

    definitionContent.appendChild(sense);
  });

  definitionCard.classList.remove("hidden");
}


function hideDefinition() {
  definitionCard.classList.add("hidden");
  definitionWord.textContent = "";
  definitionContent.innerHTML = "";
}


newGameButton.addEventListener("click", startRandomGame);
createChallengeButton.addEventListener("click", toggleChallengePanel);
generateLinkButton.addEventListener("click", generateChallengeLink);
copyLinkButton.addEventListener("click", copyChallengeLink);

challengeWordInput.addEventListener("input", () => {
  challengeWordInput.value =
    challengeWordInput.value.replace(/[^a-zA-Z]/g, "").slice(0, 5);
});

challengeWordInput.addEventListener("keydown", event => {
  if (event.key === "Enter") {
    event.preventDefault();
    generateChallengeLink();
  }

  // Prevent challenge-panel typing from also entering letters in the game.
  event.stopPropagation();
});

document.addEventListener("keydown", event => {
  if (gameOver || !secretWord) {
    return;
  }

  // Do not control the game while typing into an input box.
  if (event.target.tagName === "INPUT") {
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
