import easyocr
import numpy as np


def arrange_in_lines(data):
    lines = []
    current_line = []

    heights = []

    prev_center = None

    for item in data:
        height = item[0][2][1] - item[0][1][1]
        heights.append(height)

        center = (item[0][2][1]+item[0][1][1])/2

        if prev_center:
            avg_height = np.mean(heights)
            #print(avg_height)

            if prev_center + avg_height/2 >= center >= prev_center - avg_height/2:
                current_line.append(item)
            else:
                lines.append(current_line)

                prev_center = center
                current_line = [item]
        else:
            prev_center = center
            current_line.append(item)

    lines.append(current_line)

    return lines


class OcrReader:
    def __init__(self, lang):
        self.reader = easyocr.Reader([lang])

    def parse_text(self, page_data):
        results = self.reader.readtext(page_data)

        sorted_results = sorted(results, key=lambda i1: i1[0][2][1])
        lines = arrange_in_lines(sorted_results)

        final_text = ""

        for line in lines:
            reversed_line = sorted(line, key=lambda i1: i1[0][2][0], reverse=True)

            final_text += " ".join([item[1] for item in reversed_line])
            final_text += "\n"

        return final_text







