import subprocess


def run_command(command):
    """
    Run a shell command and return the output, error and return code.

    :param command: Command to be executed as a string.
    :return: A tuple containing (stdout, stderr, return_code).
    """
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout, result.stderr, result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode
