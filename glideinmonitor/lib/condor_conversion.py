import gzip
import io
import os
import base64
import zlib

condorPlaceholders = [("MasterLog\n========", 'MasterLog'),
                      ("StartdLog\n========", 'StartdLog'),
                      ("StarterLog\n========", 'StarterLog'),
                      ("StartdHistoryLog\n========", 'StartdHist'),
                      ("=== Encoded XML description of glidein activity ===", "XMLDesc")]


def whole_to_unpacked(job_uuid, input_dir, output_dir):
    # Extract condor logs unpacking the hashed content - only process .err files
    # Returns a list of the unpacked file(s)
    unpacked_file_list = []

    # Process the '.err' file, based on the JS script's method
    # (changes here should also be reflected in the JS version)
    # At some point, search the file byte by byte might be a better approach for performance
    # Rather than loading the whole file in memory
    with open(os.path.join(input_dir, job_uuid + '.err'), 'r') as file:
        file_err_data = file.read()

        # Iterate through each placeholder
        for currentCondorLog in condorPlaceholders:
            # Check if the placeholder exists in the file
            if currentCondorLog[0] in file_err_data:
                try:
                    # Get the base64 encoded text
                    base64_begin = file_err_data.index("644 -", file_err_data.index(currentCondorLog[0])) + 6
                    base64_end = file_err_data.index('\n', file_err_data.index("=", base64_begin))  # Get all '=' for
                    # padding protection
                    base64_content = file_err_data[base64_begin:base64_end]

                    # Decode the base64 content
                    decoded_condor_log = base64.b64decode(base64_content)

                    # Decompress the decoded base64 content
                    decompressed_condor_log = zlib.decompress(decoded_condor_log, 16 + zlib.MAX_WBITS)

                    # Send the output to the appropriate file
                    output_file_name = os.path.join(output_dir, job_uuid + '.err' + '.' + currentCondorLog[1])
                    with open(output_file_name, 'w+b') as f:
                        f.write(decompressed_condor_log)
                        unpacked_file_list.append(job_uuid + '.err' + '.' + currentCondorLog[1])

                    # Strip the content from the file's data and replace with the placeholder
                    # file_err_data.replace(base64_content, '[[['+currentCondorLog[1]+']]]')
                    file_err_data = file_err_data[:base64_begin] + '[[[' + currentCondorLog[1] + ']]]' + file_err_data[
                                                                                                         base64_end:]
                except ValueError:
                    continue
            continue

        # Save the file's content with any placeholders
        output_file_name = os.path.join(output_dir, job_uuid + '.err')
        with open(output_file_name, 'w') as f:
            f.write(file_err_data)

    # Finally, delete the original .err file
    os.remove(os.path.join(input_dir, job_uuid + ".err"))

    # Return list of the unpacked files (but not the '.err' file itself)
    return unpacked_file_list


def unpacked_to_whole(job_uuid, input_dir, output_dir):
    # Pack condor logs back into their .err files - only process .err files

    # Process the .err file
    with open(os.path.join(input_dir, job_uuid + '.err'), 'r') as err_file:
        file_err_data = err_file.read()

        # Iterate through each condor log, and check if the corresponding file exists
        for currentCondorLog in condorPlaceholders:
            current_log_path = os.path.join(input_dir, job_uuid + '.err.' + currentCondorLog[1])

            if not os.path.isfile(current_log_path):
                continue

            # It exists, open it, compress it, and base64 encode it
            with open(current_log_path, 'r') as condor_log_file:
                condor_log_data = condor_log_file.read()

                # Gzip compression in-memory
                out = io.BytesIO()
                with gzip.GzipFile(fileobj=out, mode='w') as fo:
                    fo.write(condor_log_data.encode())
                condor_log_data_gzip = out.getvalue()

                # Base64 encoding
                condor_log_base64 = base64.b64encode(condor_log_data_gzip)

                # Replace placeholder in err file
                placeholder_name = '[[[' + currentCondorLog[1] + ']]]'
                file_err_data = file_err_data[:file_err_data.index(placeholder_name)] + condor_log_base64.decode(
                    "utf-8") + file_err_data[file_err_data.index(placeholder_name) + len(placeholder_name):]

            # Remove the file from the input folder
            os.remove(os.path.join(input_dir, job_uuid + '.err.' + currentCondorLog[1]))

        # Save the .err file
        output_file_name = os.path.join(output_dir, job_uuid + '.err')
        with open(output_file_name, 'w') as f:
            f.write(file_err_data)

    # Finally, delete the original .err file
    os.remove(os.path.join(input_dir, job_uuid + ".err"))
