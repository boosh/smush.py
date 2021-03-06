import os.path
import os
import shlex
import subprocess
import sys
import shutil

class Optimiser(object):
    """
    Super-class for optimisers
    """

    input_placeholder = "__INPUT__"
    output_placeholder = "__OUTPUT__"

    # string to place between the basename and extension of output images
    output_suffix = "-opt.smush"


    def __init__(self, **kwargs):
        # the number of times the _get_command iterator has been run
        self.iterations = 0
        self.files_scanned = 0
        self.files_optimised = 0
        self.bytes_saved = 0

    
    def set_input(self, input):
        self.iterations = 0
        self.input = input


    def _get_command(self):
        """
        Returns the next command to apply
        """
        command = False
        
        if self.iterations < len(self.commands):
            command = self.commands[self.iterations]
            self.iterations += 1

        return command


    def _get_output_file_name(self):
        """
        Returns the input file name with Optimiser.output_suffix inserted before the extension
        """
        return self.input + Optimiser.output_suffix


    def __replace_placeholders(self, command, input, output):
        """
        Replaces the input and output placeholders in a string with actual parameter values
        """
        return command.replace(Optimiser.input_placeholder, input).replace(Optimiser.output_placeholder, output)


    def _keep_smallest_file(self, input, output):
        """
        Compares the sizes of two files, and discards the larger one
        """
        input_size = os.path.getsize(input)
        output_size = os.path.getsize(output)

        # if the image was optimised (output is smaller than input), overwrite the input file with the output
        # file.
        if (output_size > 0 and output_size < input_size):
            try:
                shutil.copyfile(output, input)
                self.files_optimised += 1
                self.bytes_saved += (input_size - output_size)
            except IOError:
                print "Unable to copy %s to %s: %s" % (output, input, IOError)
                sys.exit(1)
        
        # delete the output file
        os.unlink(output)
        

    def _is_acceptable_image(self, input):
        """
        Returns whether the input image can be used by a particular optimiser.

        All optimisers are expected to define a variable called 'format' containing the file format
        as returned by 'identify -format %m'
        """
        test_command = 'identify -format %%m "%s"' % input
        args = shlex.split(test_command)
        try:
            output = subprocess.check_output(args)
        except OSError:
            print "Error executing command %s. Error was %s" % (test_command, OSError)
            sys.exit(1)
        except CalledProcessError:
            return False

        return output.startswith(self.format)


    def optimise(self):
        """
        Calls the 'optimise_image' method on the object. Tests the 'optimised' file size. If the
        generated file is larger than the original file, discard it, otherwise discard the input file.
        """
        # make sure the input image is acceptable for this optimiser
        if not self._is_acceptable_image(self.input):
            print self.input, "is not a valid image for this optimiser"
            return

        self.files_scanned += 1

        while True:
            command = self._get_command()

            if not command:
                break

            output_file_name = self._get_output_file_name()
            command = self.__replace_placeholders(command, self.input, output_file_name)

            print "Executing " + command
            
            args = shlex.split(command)
            
            try:
                return_code = subprocess.call(args)
            except OSError:
                print "Error executing command %s. Error was %s" % (command, OSError)
                sys.exit(1)

            if not return_code:
                # compare file sizes if the command executed successfully
                self._keep_smallest_file(self.input, output_file_name)