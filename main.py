"""
This is a redacting bad redactions add-on for DocumentCloud.
Use the x-ray library, identify where bad redactions are and redact those bad redactions.

It demonstrates how to write a add-on which can be activated from the
DocumentCloud add-on system and run using Github Actions.  It receives data
from DocumentCloud via the request dispatch and writes data back to
DocumentCloud using the standard API
"""

from documentcloud.addon import AddOn
import xray
import csv
from listcrunch import uncrunch


class RedactBadRedactions(AddOn):
    """An identifying bad redactions Add-On for DocumentCloud."""

    def main(self):
        """The main add-on functionality goes here."""
        # fetch your add-on specific data
        if not self.documents:
            print("not documents")
            self.set_message("Please select at least one document")
            return

        self.set_message("Redacting Bad Redactions start!")

        # creating a csv file
        with open("bad_redactions.csv", "w+") as file_:
            field_names = ['document_id', 'page_num', 'bbox', 'text']
            writer = csv.DictWriter(file_, fieldnames=field_names)
            writer.writeheader()

            counter = 0

            for document in self.client.documents.list(id__in=self.documents):
                # identifying bad redactions using the x-ray library
                bad_redactions = xray.inspect(document.pdf)
                # to hold the redacttion json dictionary for each individual page in this document
                eachPage = []
                for page in bad_redactions.keys():
                    # get the page spec from the api
                    dimensions = uncrunch(document.page_spec)
                    # dimensions is now a list of strings
                    dimension = dimensions[3]
                    # dimension is now the dimension of the 4th (0 indexed) page
                    width, height = [float(d) for d in dimension.split("x")]
                    # the dimension is a string "612.0x792.0" two floats as string separated by a "x"

                    for i in range(len(bad_redactions[page])):
                        counter += 1
                        bbox = bad_redactions[page][i]['bbox']
                        writer.writerow({'document_id': document.id,
                                         'page_num': page,
                                         'bbox': bbox,
                                         'text': bad_redactions[page][i]['text']})

                        # redact bad redactions
                        # append the specific json dict for this page to global dict
                        eachPage.append(
                            {"page_number": page-1, "x1": bbox[0]/width, "y1": bbox[1]/height, "x2": bbox[2]/width, "y2": bbox[3]/height})

                        # make the api call for this document
                        self.client.post(
                            f"documents/{document.id}/redactions/", json=eachPage)
            if counter == 0:
                self.set_message("No Bad Redactions Found")
            else:
                self.set_message(str(counter) + " Bad Redactions Found")
                self.upload_file(file_)


if __name__ == "__main__":
    RedactBadRedactions().main()
