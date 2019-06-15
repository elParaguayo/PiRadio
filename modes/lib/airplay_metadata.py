import base64
from threading import Thread
import xml.etree.ElementTree as ET

# Name of the pipe provided by shairport-sync
META_PIPE = "/tmp/shairport-sync-metadata"

# Lookup codes to identify the relevant data
CODE_ARTIST = "61736172"  # hex for "asar"
CODE_ALBUM = "6173616c"  # hex for "asal"
CODE_TRACK = "6d696e6d"  # hex for "minm" (I don't know why this is track name!)
CODES = (CODE_ALBUM, CODE_ARTIST, CODE_TRACK)
CODE_MAP = {CODE_ARTIST: "Artist",
            CODE_ALBUM: "Album",
            CODE_TRACK: "Title"}

METADATA_START = "6d647374"  # hex for "mdst"
METADATA_END = "6d64656e"  # hex for "mden"


class AirplayMetadataReader(Thread):
    '''Class object to parse information in the shairport-sync metadata pipe
       and extract the relevant metadata for the PiRadio.

       Runs as a separate thread.
    '''

    def __init__(self, callback=None):
        # Initialise thread
        super(AirplayMetadataReader, self).__init__()

        # Set up a reference to our callback function
        self.callback = callback

        # Have a base metadata dictionary
        self.base_meta = {"Artist": "",
                          "Album": "",
                          "Title": ""}

        # Flag for exiting thread
        self.running = True

    def get_data(self, pipe):
        '''Parses line from the pipe. Makes sure that it reads a whole line
           of xml.
        '''
        # Blank line to start with
        line = ""

        while line == "":
            # get the next line in the pipe
            data = pipe.readline().strip()

            # If the line doesn't start with <item> then we're in the middle of
            # a line
            if not data.startswith("<item>"):

                # so go back to start of loop
                continue

            # We've got the start of the line so let's use that
            line = data

            # We need a valid xml line so check for the closing tag
            while not line.endswith("</item>"):

                # keep adding lines until we find it
                line += pipe.readline().strip()

            try:
                # Return a parsed line
                return ET.fromstring(line)

            except ET.ParseError:
                # Or None if there's an error
                return None

    def decode_metadata(self, line):
        '''Strips out the relevant metadata lines'''

        # The information we need is Base64 encoded in the data tag
        data = line.find("data")

        # Does this line have any data?
        if data is not None:

            # Find the code
            code = line.find("code").text

            # Is it one of the ones we want?
            if code in CODES:

                # If so, return a tuple of metadata type and value
                return (CODE_MAP[code], base64.b64decode(data.text))


    def run(self):
        '''Main loop'''

        # Open our pipe like any other file
        with open(META_PIPE, "r") as pipe:

            # Start loop
            while self.running:

                # get the next line
                line = self.get_data(pipe)

                # We've got a bad line so start again
                if line is None:
                    continue

                # Have we found the start of a metadata block?
                if not line.find("code").text == METADATA_START:

                    # If not, go back to start
                    continue

                # We've found the metadata block so let's create a template
                metadata = self.base_meta.copy()

                # New loop within the metadata block
                while line.find("code").text != METADATA_END:

                    # get next line
                    xml = self.get_data(pipe)

                    # Check if there's an error
                    if xml is None:
                        # if so, break out of this loop
                        break

                    # parse the metadata line
                    decoded = self.decode_metadata(xml)

                    # did we successfully match the line?
                    if decoded:

                        # if so, let's add the data to our dictionary
                        key, value = decoded
                        metadata[key] = value

                        # If we've got metadata then let's send it to the radio
                        if metadata != self.base_meta and self.callback:
                            self.callback(metadata)
