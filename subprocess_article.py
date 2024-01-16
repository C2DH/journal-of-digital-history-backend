import subprocess

notebook_file = 'notebook_with_ref.ipynb'
output_format = 'pdf'
command = f'jupyter nbconvert --to {output_format} {notebook_file}'

try:
    result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
    print("Conversion successful!")
    print(result)  # Print the entire output
except subprocess.CalledProcessError as e:
    print(f"Error during conversion: {e}")
    print("Command output:\n", e.output)