'''Run: mpiexec -n 4 python3 md5.py <password> <is_random=True/False>'''
# Python 2/3 compatibility
import sys
import imutils
PY3 = sys.version_info[0] == 3

if PY3:
    xrange = range
from mpi4py import MPI
from datetime import datetime
import numpy
import hashlib
import string
import random

DEBUG = False
import sys
try:
    word = sys.argv[1]
except:
    word = 'cuongvm'
    print(__doc__)
try:
    is_random = sys.argv[2]
except:
    is_random = False
    print(__doc__)
mdfive = hashlib.md5
word = word.encode('utf-8')
hashed_word = mdfive(word).digest()
comm = MPI.COMM_WORLD
if DEBUG:
    print('**********************************************')
    print('mdfive = ', mdfive)
    print('word = ', word)
    print('hashed_word = ', hashed_word)
    print('comm = ', comm)

rank = comm.Get_rank()
if DEBUG:
    print('rank = ', rank)
num_processes = comm.Get_size()
if DEBUG:
    print('num_processes = ', num_processes)
word_len = len(word)
if DEBUG:
    print('len(word) = ', word_len)
LOWERCASE_AND_DIGITS = list(string.ascii_lowercase + string.digits)
if DEBUG:
    print('len LOWERCASE_AND_DIGITS = ', len(LOWERCASE_AND_DIGITS))

def deep_first_search_root(guess_word, found, recv_req):
    guess_word_len = len(guess_word)
    hashed_guess_word = mdfive(guess_word.encode('utf-8')).digest()
    for i in range(num_processes - 1):
        req_test = recv_req[i].test()
        # if req still is not avalable
        if req_test[0] and (req_test[1] != None):
            print('Root ', num_processes -1, ' recieved result from Client ', i)
            return None, True
    # Compare current hashed guess word with hashed word
    if (guess_word_len == word_len):
        # if DEBUG:
            # print(guess_word)
        if (hashed_word == hashed_guess_word):
            return guess_word, True
        else:
            return None, False
    # Add 1 more character to current string and call deep_first_search_root for new string
    res = None
    added_charater_guess_words = [guess_word + c for c in LOWERCASE_AND_DIGITS]
    if is_random:
        random.shuffle(added_charater_guess_words)
    for added_charater_guess_word in added_charater_guess_words:
        res, found = deep_first_search_root(added_charater_guess_word, found, recv_req)
        if found:
            break
    return res, found


def deep_first_search(guess_word, found, req):
    guess_word_len = len(guess_word)
    hashed_guess_word = mdfive(guess_word.encode('utf-8')).digest()
    if req.Test():
        return None, True
    # Compare current hashed guess word with hashed word
    if (guess_word_len == word_len):
        # if DEBUG:
        #     print(guess_word)
        if (hashed_word == hashed_guess_word):
            return guess_word, True
        else:
            return None, False
    # Add 1 more character to current string and call deep_first_search_root for new string
    added_charater_guess_words = [guess_word + c for c in LOWERCASE_AND_DIGITS]
    if is_random:
        random.shuffle(added_charater_guess_words)
    for added_charater_guess_word in added_charater_guess_words:
        res, found = deep_first_search(added_charater_guess_word, found, req)
        if found:
            break
    return res, found

def main():
    base = int(len(LOWERCASE_AND_DIGITS)/num_processes)
    if DEBUG:
        print('base = ', base)
    is_finish_find = False
    # found mean is_found_request in Client and mean is_found_result_mess in Root
    found = False
    res = None
    print(datetime.now())
    #  Run process root
    if (rank == (num_processes - 1)):
        recv_req = []
        for i in range(num_processes - 1):
            recv_req.append(comm.irecv(source = i, tag = 2))
            print('Root ', rank, ' is waiting for recieving result from ', i)
        while not found:
            for i in range(num_processes - 1):
                if recv_req[i].Test:
                    found = True
                    break
            if not is_finish_find:
                characters = LOWERCASE_AND_DIGITS[(num_processes - 1)*base:]
                if is_random:
                    random.shuffle(characters)
                for c in characters:
                    res, found = deep_first_search_root(c, found, recv_req)
                    if found:
                        break
                is_finish_find = True
        for i in range(num_processes - 1):
            send_req = comm.isend(True, dest = i, tag = 1)
            print('Root ', rank, ' sended for ', i, ' (Do not need Client anymore.)')
        if (res != None):
            print('Root ', rank, ' matched the word = ', res, ' !')

    # Run processes compute  (Clients)
    for i in range(0, num_processes - 1):
        # If rank is Client
        if (rank == i):
            recv_req = comm.irecv(source = num_processes - 1, tag = 1)
            print('Client ', rank, ' is waiting for recieving from Root.')
            while not found:
                # If req was sent from root
                if recv_req.Test():
                    found = True
                    print('Client ', rank, ' recieved')
                if not is_finish_find:
                    characters = LOWERCASE_AND_DIGITS[i*base:(i+1)*base]
                    if is_random:
                        random.shuffle(characters)
                    for c in characters:
                        res, found = deep_first_search(c, found, recv_req)
                        if found:
                            break
                    is_finish_find = True
                    send_req = comm.isend(res, dest = num_processes - 1, tag = 2)
                    print('Client ', rank, 'is sending result to Root.')
            if (res != None):
                print('CLIENT ', rank, ' MATCHED THE WORD = ', res, ' !')
    print(datetime.now())

if __name__ == '__main__':
    main()
            