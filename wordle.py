MAX_ATTEMPTS = 6
WORD_LENGTH = 5


def evaluate_guess(secret_word, guess):
    """
    Compare a guess with the secret word.

    Returns a list containing:
        "green"  -> correct letter, correct position
        "yellow" -> correct letter, wrong position
        "gray"   -> letter not present / no remaining occurrences
    """

    result = ["gray"] * WORD_LENGTH

    # Convert the secret word into a mutable list so that
    # matched letters can be "used up".
    remaining_letters = list(secret_word)

    # ---------------------------------------------------------
    # PASS 1: Find letters in the correct position (green)
    # ---------------------------------------------------------
    for i in range(WORD_LENGTH):
        if guess[i] == secret_word[i]:
            result[i] = "green"
            remaining_letters[i] = None

    # ---------------------------------------------------------
    # PASS 2: Find correct letters in the wrong position (yellow)
    # ---------------------------------------------------------
    for i in range(WORD_LENGTH):

        # Skip letters that were already marked green.
        if result[i] == "green":
            continue

        if guess[i] in remaining_letters:
            result[i] = "yellow"

            # Remove one occurrence so that repeated letters
            # are not counted more times than they appear
            # in the secret word.
            matched_index = remaining_letters.index(guess[i])
            remaining_letters[matched_index] = None

    return result


def get_symbol(letter, color):
    """
    Convert a letter/color combination into a terminal representation.

    Since emoji squares cannot contain letters, we display the colored
    square followed by the corresponding letter.
    """

    symbols = {
        "green": "🟩",
        "yellow": "🟨",
        "gray": "⬛"
    }

    return f"{symbols[color]}{letter.upper()}"


def update_keyboard(keyboard_status, guess, result):
    """
    Update the status of letters on the on-screen keyboard.

    A letter's status can only improve:

        unused -> gray -> yellow -> green

    For example, once a letter has been identified as green,
    a later guess cannot downgrade it to yellow or gray.
    """

    priority = {
        None: 0,
        "gray": 1,
        "yellow": 2,
        "green": 3
    }

    for letter, color in zip(guess, result):

        current_color = keyboard_status.get(letter)

        if priority[color] > priority[current_color]:
            keyboard_status[letter] = color


def display_keyboard(keyboard_status):
    """
    Display a QWERTY keyboard underneath the board.
    """

    keyboard_rows = [
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm"
    ]

    print("Keyboard:")
    print()

    for row_number, row in enumerate(keyboard_rows):

        # Add a little indentation to resemble a real keyboard.
        if row_number == 1:
            print(" ", end="")
        elif row_number == 2:
            print("   ", end="")

        for letter in row:

            status = keyboard_status.get(letter)

            if status is None:
                # Letter has not been used yet
                key = f"▫️{letter.upper()}"
            else:
                key = get_symbol(letter, status)

            print(key, end=" ")

        print()

    print()


def display_board(guesses, results, keyboard_status):
    """
    Draw the complete 6 x 5 Wordle board and keyboard.
    """

    print()
    print("        WORD GAME")
    print()

    for row in range(MAX_ATTEMPTS):

        # A completed guess exists for this row
        if row < len(guesses):

            guess = guesses[row]
            result = results[row]

            tiles = []

            for i in range(WORD_LENGTH):
                tiles.append(get_symbol(guess[i], result[i]))

            print("  ".join(tiles))

        # No guess yet: display an empty row
        else:
            print("⬜  ⬜  ⬜  ⬜  ⬜")

    print()

    display_keyboard(keyboard_status)

def get_valid_guess(allowed_guesses):
    """
    Ask the player for a valid five-letter English word.
    """

    while True:

        guess = input("Enter your guess: ").strip().lower()

        if len(guess) != WORD_LENGTH:
            print(
                f"Your guess must contain exactly {WORD_LENGTH} letters."
            )
            continue

        if not guess.isalpha():
            print("Your guess must contain letters only.")
            continue

        if guess not in allowed_guesses:
            print("Not in word list.")
            continue

        return guess


def load_word_list(filename):
    """
    Load five-letter words from a text file.
    """

    with open(filename, "r", encoding="utf-8") as file:
        words = {
            line.strip().lower()
            for line in file
            if len(line.strip()) == WORD_LENGTH
            and line.strip().isalpha()
        }

    return words

def play_wordle(secret_word, allowed_guesses, possible_answers):
    """
    Run one complete game.
    """

    secret_word = secret_word.strip().lower()

    if len(secret_word) != WORD_LENGTH or not secret_word.isalpha():
        raise ValueError(
            f"The secret word must contain exactly {WORD_LENGTH} letters."
        )

    if secret_word not in possible_answers:
        raise ValueError(
            f"'{secret_word}' is not in the possible-answer list."
        )

    # Store game history
    guesses = []
    results = []

    # Store keyboard state.
    #
    # Examples:
    # {
    #     "a": "green",
    #     "r": "yellow",
    #     "x": "gray"
    # }
    keyboard_status = {}

    print()
    print("==============================")
    print("          WORD GAME")
    print("==============================")
    print()
    print(f"Guess the {WORD_LENGTH}-letter word.")
    print(f"You have {MAX_ATTEMPTS} attempts.")
    print()
    print("🟩 = correct letter and position")
    print("🟨 = correct letter, wrong position")
    print("⬛ = letter not in the word")
    print()

    # Show empty board and keyboard
    display_board(guesses, results, keyboard_status)

    for attempt in range(1, MAX_ATTEMPTS + 1):

        print(f"Attempt {attempt}/{MAX_ATTEMPTS}")

        guess = get_valid_guess(allowed_guesses)

        result = evaluate_guess(secret_word, guess)

        # Store current attempt
        guesses.append(guess)
        results.append(result)

        # Update keyboard based on everything learned
        update_keyboard(keyboard_status, guess, result)

        # Redraw complete board and keyboard
        display_board(guesses, results, keyboard_status)

        if guess == secret_word:
            print(f"🎉 You got it in {attempt} attempt(s)!")
            return

    print("Game over!")
    print(f"The word was: {secret_word.upper()}")


# =============================================================
# START THE GAME
# =============================================================

if __name__ == "__main__":

    allowed_guesses = load_word_list("allowed_guesses.txt")
    possible_answers = load_word_list("possible_answers.txt")

    missing_words = possible_answers - allowed_guesses

    if missing_words:
        raise ValueError(
            "Some possible answers are not contained in the allowed-guesses list: "
            + ", ".join(sorted(missing_words))
        )

    secret_word = "plant"

    play_wordle(secret_word, allowed_guesses, possible_answers)
