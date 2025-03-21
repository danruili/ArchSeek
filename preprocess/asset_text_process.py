from utils.app_types import RawTextItem

def split_text(raw_text_file_path: str, 
              ) -> RawTextItem:
    """
    Split the raw text into chunks of 500 words each.
    """
    # read the text file using utf-8 encoding
    with open(raw_text_file_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    # split the text into chunks
    chunked_content = []
    words = raw_content.split()
    chunk_size = 70
    sliding_window = 50
    for i in range(0, len(words), sliding_window):
        chunk = " ".join(words[i:i+chunk_size])
        chunked_content.append(chunk)

    return RawTextItem(raw_text_file_path, raw_content, chunked_content)
