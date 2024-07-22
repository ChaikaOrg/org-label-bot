import os


def main():
    secret_input = os.getenv('INPUT_SECRET_INPUT')
    print(f'Secret Input is: {secret_input}')


if __name__ == "__main__":
    main()