import ffmpeg
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

input_file = "only_streams_name.xlsx"
output_file = "OUTPUT/streams_checked.xlsx"

# docker build -t stream-checker .
# docker run --rm -v "$PWD":/app stream-checker

df = pd.read_excel(input_file)
df.columns = df.columns.str.strip()

print("Columns in the Excel file:", df.columns)

# Define common bitrates
STANDARD_BITRATES = [32, 48, 64, 96, 128, 160, 192, 256, 320]
TOLERANCE = 1.5  # kbps

def snap_to_nearest_standard(kbps):
    for standard in STANDARD_BITRATES:
        if abs(kbps - standard) <= TOLERANCE:
            return standard
    # If no match within tolerance, round up to next standard
    for standard in STANDARD_BITRATES:
        if kbps < standard:
            return standard
    return STANDARD_BITRATES[-1]  # If higher than all, return the max

def process_url(row):
    url = row['Streams']
    print(f"Processing URL: {url}")

    result = {'Bitrate': None, 'Audio Codec': None}

    try:
        url_lower = str(url).lower()

        # Detect m3u / m3u8, including URLs with tokens like ?token=abc
        is_hls = ".m3u" in url_lower or ".m3u8" in url_lower

        # Probe first to check if the stream actually works
        probe = ffmpeg.probe(url, select_streams="a")

        # If it is m3u / m3u8 and probe worked, force hls 128
        if is_hls:
            result['Audio Codec'] = 'hls'
            result['Bitrate'] = 128
            print('hls', 128, 'kbps')
            return result

        for stream in probe.get('streams', []):
            codec = stream.get('codec_name', '').lower()
            bitrate = stream.get('bit_rate')

            if codec in ['aac', 'mp4a', 'mp3']:
                result['Audio Codec'] = codec

                if bitrate:
                    kbps = int(bitrate) / 1000
                    result['Bitrate'] = snap_to_nearest_standard(kbps)
                else:
                    result['Bitrate'] = 'Not Available'

                print(codec, result['Bitrate'], 'kbps')
                break

        else:
            result['Audio Codec'] = 'Unknown'
            result['Bitrate'] = 'Not Available'
            print('Unknown', 'Not Available')

    except Exception as e:
        print(f"Error processing URL {url}: {e}")
        result['Audio Codec'] = 'Error'
        result['Bitrate'] = 'Error'

    return result

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(process_url, df.to_dict('records')))

df['Audio Codec'] = [result['Audio Codec'] for result in results]
df['Bitrate'] = [result['Bitrate'] for result in results]

df.to_excel(output_file, index=False)

print(f"Done {output_file}")