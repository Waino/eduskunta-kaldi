import re
import os.path
from pympi import Elan
from collections import Counter
from glob import glob

# Words ending in these characters indicate sentence breaks
PUNCTUATION = '.'

# Format for utterance ids
UTT_FORMAT = '{speaker}-{recording}-{start}-{end}'

RE_PARTY = re.compile(r'/.*')
RE_MINISTERI = re.compile(r'.*ministeri ')

def normalize_speaker(speaker):
    speaker = speaker.replace('\xa0', ' ')
    speaker = RE_PARTY.sub('', speaker)
    speaker = RE_MINISTERI.sub('', speaker)
    speaker = speaker.strip()
    speaker = speaker.replace(' ', '-')
    return speaker

def words_to_utterances(annotations):
    utt_start = None
    utt = []
    for word_start, word_end, word in annotations:
        if utt_start is None:
            utt_start = word_start
        utt.append(word)
        if word[-1] in PUNCTUATION:
            # last word of utterance
            yield (utt_start, word_end, ' '.join(utt))
            # reset
            utt_start = None
            utt = []
        # else: utterance internal word
    if len(utt) > 0:
        # last utterance didn't end in punctuation
        yield (utt_start, word_end, ' '.join(utt))

def process_eaf(file_path):
    dir_path, file_name = os.path.split(file_path)
    recording_id, _ = os.path.splitext(file_name)
    base_path = os.path.join(dir_path, recording_id)
    print('Recording:', recording_id)

    speakers = set()

    with open(base_path + '.segments', 'w') as segments_file, \
         open(base_path + '.text', 'w') as text_file, \
         open(base_path + '.utt2spk', 'w') as utt2spk_file, \
         open(base_path + '.speakers', 'w') as speakers_file :

        eaf = Elan.Eaf(file_path)
        for tier in eaf.get_tier_names():
            speaker = normalize_speaker(tier)
            speakers.add(speaker)
            print('Speaker:', speaker)
            utterances = words_to_utterances(
                eaf.get_annotation_data_for_tier(tier))
            for start, end, words in utterances:
                utterance_id = UTT_FORMAT.format(
                    speaker=speaker,
                    recording=recording_id,
                    start=start,
                    end=end)
                # segments file to automatically split
                # a large recording file into utterances
                print('{utterance} {recording} {start} {end}'.format(
                    utterance=utterance_id,
                    recording=recording_id,
                    start=start,
                    end=end),
                    file=segments_file)
                # utterance -> text
                print('{utterance} {words}'.format(
                    utterance=utterance_id,
                    words=words),
                    file=text_file)
                # utterance -> speaker
                print('{utterance} {speaker}'.format(
                    utterance=utterance_id,
                    speaker=speaker),
                    file=utt2spk_file)
        # speakers present in this recording
        for speaker in sorted(speakers):
            print(speaker, file=speakers_file)

if __name__ == '__main__':
    for file_path in sorted(glob('20*/*/*.eaf')):
        process_eaf(file_path)
