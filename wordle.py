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


def display_board(guesses, results):
    """
    Draw the complete 6 x 5 Wordle board.

    Previous guesses are displayed with their colors.
    Unused rows are displayed as empty tiles.
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


def get_valid_guess():
    """
    Ask the player for a valid five-letter guess.
    """

    while True:
        guess = input("Enter your guess: ").strip().lower()

        if len(guess) != WORD_LENGTH:
            print(f"Your guess must contain exactly {WORD_LENGTH} letters.")
            continue

        if not guess.isalpha():
            print("Your guess must contain letters only.")
            continue

        return guess


def play_wordle(secret_word):
    """
    Run one complete game.
    """

    secret_word = secret_word.strip().lower()

    if len(secret_word) != WORD_LENGTH or not secret_word.isalpha():
        raise ValueError(
            f"The secret word must contain exactly {WORD_LENGTH} letters."
        )

    # Store the history of the game
    guesses = []
    results = []

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

    # Show the empty board before the first guess
    display_board(guesses, results)

    for attempt in range(1, MAX_ATTEMPTS + 1):

        print(f"Attempt {attempt}/{MAX_ATTEMPTS}")

        guess = get_valid_guess()

        result = evaluate_guess(secret_word, guess)

        # Add this attempt to the game history
        guesses.append(guess)
        results.append(result)

        # Redraw the complete board
        display_board(guesses, results)

        if guess == secret_word:
            print(f"🎉 You got it in {attempt} attempt(s)!")
            return

    print("Game over!")
    print(f"The word was: {secret_word.upper()}")


# =============================================================
# START THE GAME
# =============================================================

if __name__ == "__main__":

    # For now, change the secret word manually.
    secret_word = "plant"

    play_wordle(secret_word)
