import argparse
import os


# Search and replace terms
search_for = "debug_mode"
replace_with = "testing_mode"

# Parse command line arguments
parser = argparse.ArgumentParser(description="GlideinMonitor's Filtering Example")
parser.add_argument('-i', help="Input Directory", required=True)
parser.add_argument('-o', help="Output Directory", required=True)
args = parser.parse_args()

input_directory = args.i
output_directory = args.o

# In practice, use a loop until no files have been found in the input directory for better performance
input_directory_files = [file
                         for file in os.listdir(input_directory)
                         if os.path.isfile(os.path.join(input_directory, file))]

# Iterate through each file in the input directory
for file_name in input_directory_files:
    # Read in the file from the input directory
    with open(os.path.join(input_directory, file_name), 'r') as input_file_handle:
        input_file_contents = input_file_handle.read()

    # Replace the target string
    output_file_contents = input_file_contents.replace(search_for, replace_with)

    # Write the file to the output directory
    with open(os.path.join(output_directory, file_name), 'w') as file:
        file.write(output_file_contents)

    # Delete the file from the input directory
    os.remove(os.path.join(input_directory, file_name))
