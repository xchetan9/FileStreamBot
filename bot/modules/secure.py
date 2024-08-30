import random
import string


def generate_random_salt(length=8):
    """Generate a random salt of the specified length."""
    characters = string.ascii_letters + string.digits
    salt = "".join(random.choice(characters) for _ in range(length))
    return salt


def seed_shuffle(array, seed):
    """Shuffle array using a seed."""
    random.seed(seed)
    for i in range(len(array) - 1, 0, -1):
        j = random.randint(0, i)
        array[i], array[j] = array[j], array[i]
    return array


def generate_mapping(salt):
    """Generate a random mapping based on a given salt."""
    seed = sum(ord(char) for char in salt)
    characters = list(string.ascii_letters + string.digits)
    shuffled_characters = seed_shuffle(characters, seed)
    number_to_char = {i: shuffled_characters[i] for i in range(62)}
    char_to_number = {shuffled_characters[i]: i for i in range(62)}
    return number_to_char, char_to_number


def encrypt(number, salt=None):
    """Encrypt a number to a URL-friendly character string using a random salt."""
    if salt is None:
        salt = generate_random_salt()
    number_to_char, _ = generate_mapping(salt)
    encrypted = "".join(number_to_char[int(digit) % 62] for digit in str(number))
    return f"{salt}{encrypted}"


def decrypt(encrypted):
    """Decrypt a URL-friendly character string to a number using the included salt."""
    salt = encrypted[:8]  # Assuming salt length is 8
    encrypted_message = encrypted[8:]
    _, char_to_number = generate_mapping(salt)
    decrypted = "".join(str(char_to_number[char]) for char in encrypted_message)
    return decrypted


print(encrypt(13258))
