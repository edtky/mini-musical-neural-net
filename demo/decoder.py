import os
import dill as pickle
from pathlib import Path
import random
import numpy as np
import pandas as pd
from math import floor
from pyknon.genmidi import Midi
from pyknon.music import NoteSeq, Note
import music21
import random
import os, argparse

# default settings: sample_freq=12, note_range=62

def main(filename):
    
    filedir = 'output/text/'

    notetxt = filedir + filename

    with open(notetxt, 'r') as file:
        notestring=file.read()

    score_note = notestring.split(" ")

    # define some parameters (from encoding script)
    sample_freq=12
    note_range=62
    note_offset=33
    chamber=0
    numInstruments=1

    # define variables and lists needed for chord decoding
    speed=1./sample_freq
    piano_notes=[]
    violin_notes=[]
    time_offset=0

    # start decoding here
    score = score_note

    i=0

    # for outlier cases, not seen in sonat-1.txt
    # not exactly sure what scores would have "p_octave_" or "eoc" (end of chord?)
    # it seems to insert new notes to the score whenever these conditions are met
    while i<len(score):
        if score[i][:9]=="p_octave_":
            add_wait=""
            if score[i][-3:]=="eoc":
                add_wait="eoc"
                score[i]=score[i][:-3]
            this_note=score[i][9:]
            score[i]="p"+this_note
            score.insert(i+1, "p"+str(int(this_note)+12)+add_wait)
            i+=1
        i+=1


    # loop through every event in the score
    for i in range(len(score)):

        # if the event is a blank, space, "eos" or unknown, skip and go to next event
        if score[i] in ["", " ", "<eos>", "<unk>"]:
            continue

        # if the event starts with 'end' indicating an end of note
        elif score[i][:3]=="end":

            # if the event additionally ends with eoc, increare the time offset by 1
            if score[i][-3:]=="eoc":
                time_offset+=1
            continue

        # if the event is wait, increase the timestamp by the number after the "wait"
        elif score[i][:4]=="wait":
            time_offset+=int(score[i][4:])
            continue

        # in this block, we are looking for notes   
        else:
            # Look ahead to see if an end<noteid> was generated
            # soon after.  
            duration=1
            has_end=False
            note_string_len = len(score[i])
            for j in range(1,200):
                if i+j==len(score):
                    break
                if score[i+j][:4]=="wait":
                    duration+=int(score[i+j][4:])
                if score[i+j][:3+note_string_len]=="end"+score[i] or score[i+j][:note_string_len]==score[i]:
                    has_end=True
                    break
                if score[i+j][-3:]=="eoc":
                    duration+=1

            if not has_end:
                duration=12

            add_wait = 0
            if score[i][-3:]=="eoc":
                score[i]=score[i][:-3]
                add_wait = 1

            try: 
                new_note=music21.note.Note(int(score[i][1:])+note_offset)    
                new_note.duration = music21.duration.Duration(duration*speed)
                new_note.offset=time_offset*speed
                if score[i][0]=="v":
                    violin_notes.append(new_note)
                else:
                    piano_notes.append(new_note)                
            except:
                print("Unknown note: " + score[i])




            time_offset+=add_wait

    # list of all notes for each instrument should be ready at this stage

    # creating music21 instrument objects      
    violin=music21.instrument.fromString("Violin")
    piano=music21.instrument.fromString("Piano")

    # insert instrument object to start (0 index) of notes list
    violin_notes.insert(0, violin)
    piano_notes.insert(0, piano)

    # create music21 stream object for individual instruments
    violin_stream=music21.stream.Stream(violin_notes)
    piano_stream=music21.stream.Stream(piano_notes)

    # merge both stream objects into a single stream of 2 instruments
    note_stream = music21.stream.Stream([violin_stream, piano_stream])

    
    note_stream.write('midi', fp="output/midi/"+filename[:-4]+".mid")
    print("Done! Decoded midi file saved to '/output/midi/'")

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str, help="Copy file into the folder 'output/text/'.")
    args = parser.parse_args()
    
    main(args.filename)